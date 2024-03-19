#utils.py
import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, box
import random
import plotly.express as px
import osmnx as ox
ox.config(use_cache=True, log_console=True)

px.set_mapbox_access_token(st.secrets['plotly']['MAPBOX_TOKEN'])
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

def get_landuse(add,radius,tags = {'natural':True,'landuse':True},removeoverlaps=False):
    data = ox.features_from_address(add,dist=radius,tags=tags).reset_index()
    gdf = data.loc[data['geometry'].geom_type.isin(['Polygon', 'MultiPolygon'])]
    if tags == {'landuse':True}:
        gdf['type'] = gdf.apply(lambda row: row['landuse'], axis=1)
    elif tags == {'natural':True}:
        gdf['type'] = gdf.apply(lambda row: row['natural'], axis=1)
    else:
        gdf['type'] = gdf.apply(lambda row: row['landuse'] if pd.notna(row['landuse']) else row['natural'], axis=1)
    
    #clip
    loc = ox.geocode(add)
    center_gdf = gpd.GeoDataFrame(geometry=[Point(loc[1],loc[0])], crs="EPSG:4326")
    utm = center_gdf.estimate_utm_crs()
    gdf_utm = gdf.to_crs(utm)
    gdf_utm['area'] = gdf_utm.area
    buffer = center_gdf.to_crs(utm).buffer(radius)
    filtered_gdf = gpd.clip(gdf_utm, buffer)
    
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
        filtered_gdf['area'] = filtered_gdf.area
        
    #cols
    columns_to_select = ['name','type','area','geometry']
    selected_columns = [col for col in columns_to_select if col in filtered_gdf.columns]
    
    return  filtered_gdf.to_crs(4326)[selected_columns]

def plot_landuse(gdf,name,col='type'):
    lat = gdf.unary_union.centroid.y
    lon = gdf.unary_union.centroid.x
    fig_map = px.choropleth_mapbox(gdf,
                            geojson=gdf.geometry,
                            locations=gdf.index,
                            title=name,
                            color=col,
                            hover_name=col,
                            center={"lat": lat, "lon": lon},
                            mapbox_style=arvo_style,
                            zoom=13,
                            opacity=0.5,
                            width=1200,
                            height=700
                            )

    fig_map.update_layout(margin={"r": 10, "t": 50, "l": 10, "b": 10}, height=700,
                                legend=dict(
                                    yanchor="top",
                                    y=0.97,
                                    xanchor="left",
                                    x=0.02
                                )
                                )
    return fig_map

def plot_osm_areas(gdf):
    fig = px.bar(gdf,x='area',y='type',color='type')
    fig.update_xaxes(range=[0,gdf['area'].quantile(0.99)])
    return fig

def create_boxes_from_dict(ks_dict):
    last_bbox = None
    last_corner = None
    data = []  # To hold data for the GeoDataFrame
    
    for k, values in ks_dict.items():
        area, eco_area = values
        side_length = area**0.5  # Assuming square boxes for simplicity
        
        if last_bbox is None:
            # Arbitrarily place the first box
            new_bbox = box(60.2826, 24.9384, side_length, side_length)
        else:
            # Logic to place the new box relative to the last one, avoiding the last corner used
            minx, miny, maxx, maxy = last_bbox.bounds
            corners = [(minx, miny), (minx, maxy), (maxx, miny), (maxx, maxy)]
            if last_corner in corners:
                corners.remove(last_corner)
            new_corner = random.choice(corners)
            # Example placement logic, places new box to the right of the selected corner
            new_bbox = box(new_corner[0], new_corner[1], new_corner[0] + side_length, new_corner[1] + side_length)
            last_corner = new_corner
        
        last_bbox = new_bbox
        data.append([k, new_bbox, area, eco_area])
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(data, columns=['Key', 'geometry', 'Area', 'Eco_Area'])
    return gdf