
#utils.py
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, box, LineString
import random
import geocoder
import pyproj
from pyproj import Transformer
import requests
from io import BytesIO
import json
import tempfile
import zipfile
import os
import plotly.express as px
import osmnx as ox
ox.config(use_cache=True, log_console=True)

px.set_mapbox_access_token(st.secrets['plotly']['MAPBOX_TOKEN'])
mbtoken = st.secrets['plotly']['MAPBOX_TOKEN']
arvo_style = st.secrets['plotly']['MAPBOX_STYLE']

#auth
def check_password():
    def password_entered():
        if (
            st.session_state["password"]
            == st.secrets["passwords"]["cfua"]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input(label="password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(label="password", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

def getlatlon(add):
    loc = geocoder.mapbox(add, key=mbtoken)
    if loc.ok and loc.country == 'Finland':
        lon = loc.lng
        lat = loc.lat
        latlon = (lat,lon)
        return latlon,loc
    else:
        return None


import xml.etree.ElementTree as ET
def print_wfs_layers(url = 'https://kartta.hsy.fi/geoserver/wfs'):
    # Add or adjust parameters as needed for the specific WFS service
    params = {
        'service': 'WFS',
        'request': 'GetCapabilities'
    }
    
    response = requests.get(url, params=params, verify=False)
    if response.status_code == 200:
        # Parse the XML response
        xml_root = ET.fromstring(response.content)
        
        # Define the namespace to parse the XML correctly
        # This namespace is found in the XML response and may vary between services
        # You might need to adjust the namespace according to the WFS service response
        namespace = {'wfs': 'http://www.opengis.net/wfs/2.0'}
        
        # Find and print all layer names (FeatureType Names)
        for ft in xml_root.findall('.//wfs:FeatureType', namespace):
            layer_name = ft.find('wfs:Name', namespace)
            if layer_name is not None:
                st.text(layer_name.text)
    else:
        print(f"Failed to get capabilities from WFS service, status code: {response.status_code}")

        
def get_hsy_maanpeite(latlon, radius=250):
    
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3879", always_xy=True)
    lng_3879, lat_3879 = transformer.transform(latlon[1], latlon[0])
    
    layer_names = ['asuminen_ja_maankaytto:maanpeite_puusto_2_10m_2022',
                   'asuminen_ja_maankaytto:maanpeite_puusto_10_15m_2022',
                   'asuminen_ja_maankaytto:maanpeite_puusto_15_20m_2022',
                   'asuminen_ja_maankaytto:maanpeite_puusto_yli20m_2022',
                   'asuminen_ja_maankaytto:maanpeite_muu_avoin_matala_kasvillisuus_2022'
                   ]
    
    def fetch_wfs_layer(layer_name,lng,lat,radius=500):
        cql_filter = f"WITHIN(geom, BUFFER(POINT({lat} {lng}), {radius}))" #INTERSECTS
        url = 'https://kartta.hsy.fi/geoserver/wfs'
        params = {
            'service': 'WFS',
            'version': '2.0',
            'request': 'GetFeature',
            'typeName': layer_name,
            'outputFormat': "json",
            'srsName': 'EPSG:3879', # for FIN ETRS89 GK25FIN
            'CQL_FILTER': cql_filter
        }
        response = requests.get(url, params=params, verify=False)
        if response.status_code == 200:
            geojson = response.json()  # Get the response as a JSON object
            if geojson['features']:  # Check if there are any features
                return gpd.GeoDataFrame.from_features(geojson)
            else:
                print("No features found.")
                return gpd.GeoDataFrame([], columns=['geometry'])
        else:
            print(response.text)
            return None
        
    #loop multiple layers
    layers = []
    for layer_name in layer_names:
        layer_gdf = fetch_wfs_layer(layer_name, lng=lng_3879, lat=lat_3879, radius=radius)
        if layer_gdf is not None:
            layers.append(layer_gdf)
        else:
            return st.warning('Ei tuloksia.')
    if layers:
        result = gpd.GeoDataFrame(pd.concat(layers, ignore_index=True),geometry='geometry',crs=3879)
        result["p_ala_m2"] = round(result["p_ala_m2"],0)
        return result.to_crs(4326)
        
def get_osm_landuse(latlon,radius=250,tags = {'natural':True,'landuse':True},exclude=['bay'],removeoverlaps=False):
    data = ox.features_from_point(center_point=latlon,dist=radius,tags=tags).reset_index()
    gdf = data.loc[data['geometry'].geom_type.isin(['Polygon', 'MultiPolygon'])]
    
    if tags == {'landuse':True}:
        gdf['type'] = gdf.apply(lambda row: row['landuse'], axis=1)
    elif tags == {'natural':True}:
        gdf['type'] = gdf.apply(lambda row: row['natural'], axis=1)
    else:
        def determine_type(row):
            if 'landuse' in row and pd.notna(row['landuse']):
                return row['landuse']
            elif 'natural' in row and pd.notna(row['natural']):
                return row['natural']
            else:
                return 'Unknown'
        gdf['type'] = gdf.apply(determine_type, axis=1)
        #gdf['type'] = gdf.apply(lambda row: row['landuse'] if pd.notna(row['landuse']) else row['natural'], axis=1)
    
    #clip & filter
    center_gdf = gpd.GeoDataFrame(geometry=[Point(latlon[1],latlon[0])], crs="EPSG:4326")
    utm = center_gdf.estimate_utm_crs()
    gdf_utm = gdf[~gdf['type'].isin(exclude)].to_crs(utm)
    buffer = center_gdf.to_crs(utm).buffer(radius)
    filtered_gdf = gpd.clip(gdf_utm, buffer)
    filtered_gdf['area'] = filtered_gdf.area
    
    #remove overlaps
    if removeoverlaps:
        to_remove = []
        for index, polygon in filtered_gdf.iterrows():
            others = filtered_gdf.drop(index)
            overlaps = others[others.geometry.overlaps(polygon.geometry)]
            total_overlap_area = sum(overlaps.geometry.intersection(polygon.geometry).area)
            overlap_percentage = total_overlap_area / polygon.geometry.area
            if overlap_percentage > 0.01:
                to_remove.append(index)
        filtered_gdf = filtered_gdf.drop(to_remove)
        #recalc area
        filtered_gdf['pinta-ala'] = filtered_gdf.area
    
    #round area
    filtered_gdf['pinta-ala'] = round(filtered_gdf['area'],0)
    filtered_gdf.rename(columns={'name':'nimi','type':'luokka'},inplace=True)
    #cols
    columns = ['nimi', 'luokka', 'pinta-ala', 'geometry']
    existing_columns = [col for col in columns if col in filtered_gdf.columns]
    result_gdf = filtered_gdf.to_crs(4326)[existing_columns]
    return result_gdf

def plot_landuse(gdf,title,hover_name=None,col='type',color_map=None,zoom=14):

    #scale cirle
    lat = gdf.unary_union.centroid.y
    lng = gdf.unary_union.centroid.x
    center_gdf = gpd.GeoDataFrame(geometry=[Point(lng, lat)], crs="EPSG:4326")
    center_gdf = center_gdf.to_crs("EPSG:3879")
    circle = center_gdf.iloc[0].geometry.buffer(250)
    ring = gpd.GeoDataFrame(geometry=[circle], crs="EPSG:3879").to_crs("EPSG:4326")

    if color_map is None:
        unique_categories = gdf[col].unique()
        colors = px.colors.qualitative.Set2
        color_map = {category: colors[i % len(colors)] for i, category in enumerate(unique_categories)}
        cat_order = list(color_map.keys())
    else:
        cat_order = list(color_map.keys())
    
    lat = gdf.unary_union.centroid.y
    lon = gdf.unary_union.centroid.x
    fig_map = px.choropleth_mapbox(gdf,
                            geojson=gdf.geometry,
                            locations=gdf.index,
                            title=title,
                            color=col,
                            hover_name=hover_name,
                            color_continuous_scale="Greens",
                            color_discrete_map=color_map,
                            category_orders={col:cat_order},
                            center={"lat": lat, "lon": lon},
                            mapbox_style=arvo_style,
                            zoom=zoom,
                            opacity=0.5,
                            width=1200,
                            height=700
                            )
    if ring is not None:
        fig_map.update_layout(
            mapbox={
                "layers": [
                    {
                        "source": json.loads(ring.to_crs(4326).to_json()),
                        "type": "line",
                        "color": "black",
                        "line": {"width": 0.5, "dash": [5, 5]},
                    }
                ]
            }
        )

    fig_map.update_layout(margin={"r": 10, "t": 50, "l": 10, "b": 10}, height=700,
                                legend=dict(
                                    yanchor="top",
                                    y=0.97,
                                    xanchor="left",
                                    x=0.02
                                )
                                )
    fig_map.update_layout(
                            coloraxis_colorbar=dict(
                                title='Arvo',
                                tickvals=[gdf[col].min(),gdf[col].max()],
                                ticktext=['matala','korkea']
                            )
                        )
    return fig_map

def plot_area_bars(gdf,x='area',y='type',color='type',color_map=None,title='Elinympäristötyypit datassa'):
    
    if color_map is None:
        unique_categories = gdf[color].unique()
        colors = px.colors.qualitative.Set2
        color_map = {category: colors[i % len(colors)] for i, category in enumerate(unique_categories)}
    
    cat_order = list(color_map.keys())
    fig = px.bar(gdf,x,y,color,color_discrete_map=color_map,category_orders={color:cat_order},title=title)
    #fig.update_xaxes(range=[0,gdf[x].quantile(0.99)])
    return fig


def extract_shapefiles_from_zip(file, geom_type):
    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)
        
        potential_files = []
        for filename in os.listdir(tmp_dir):
            if filename.endswith(".shp"):
                shapefile_path = os.path.join(tmp_dir, filename)
                data = gpd.read_file(shapefile_path)

                for col in data.columns:
                    if data[col].dtype == object:
                        data[col] = pd.to_numeric(data[col], errors='ignore')  # Convert to numeric if possible
                
                if any(data.geometry.geom_type == geom_type):
                    potential_files.append((data, filename))
                
        for data, filename in potential_files:
            if data.crs is None:
                prj_file_path = os.path.splitext(shapefile_path)[0] + ".prj"
                if os.path.exists(prj_file_path):
                    with open(prj_file_path, 'r') as prj_file:
                        prj_text = prj_file.read().strip()
                    crs = pyproj.CRS.from_string(prj_text)
                    data.crs = crs

            if data.crs != 'EPSG:4326':
                data = data.to_crs('EPSG:4326')
            
            return data #, filename
    
    return None, None