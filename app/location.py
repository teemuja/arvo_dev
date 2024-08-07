import streamlit as st
import pandas as pd
import random
import utils
import plotly.express as px
import score_module

st.subheader("Kohdealueen analyysi")
loc_text = """
    Paikkatietopohjainen laskenta eri datalähteillä 
    ([HSY](https://www.hsy.fi/ymparistotieto/paikkatiedot/rajapinnat/avoimet-paikkatietorajapinnat/),
    [OSM](https://wiki.openstreetmap.org/wiki/Land_use)).
"""
st.markdown(loc_text)

gdf = None
r = 250
s1,s2 = st.columns([1,2])
add = s1.text_input('Kohdeosoite')
sorsa = s2.radio('Datalähde',['HSY','OSM','oma'],horizontal=True)

try:
    latlon = utils.getlatlon(add)
except:
    st.warning('Tarkenna osoite')
    st.stop()
    
with st.expander('Elinympäristöt datassa',expanded=True):
    if sorsa == 'OSM':
        tag = 'Maanpeite' #s3.radio('Lähtötieto',['Maanpeite','Maankäyttö','Luontoalueet'],horizontal=True)
        if tag == 'Maankäyttö':
            tags = {'landuse':True}
            name = f"Maankäyttö {add}"
        elif tag == 'Luontoalueet':
            tags = {'natural':True}
            name = f"Luontoalueet {add}"
        else:
            tags = {'natural':True,'landuse':['grass','meadow','forest']}
            name = f"Maanpeite {add}"
        if latlon:
            try:
                gdf = utils.get_osm_landuse(latlon=latlon,tags=tags,radius=r)
                if gdf is not None and not gdf.empty:
                    name_col = "nimi"
                    area_col = "pinta-ala"
                    type_col="luokka"
                    #plots
                    bar_osm = utils.plot_area_bars(gdf,x=area_col,y=type_col,color=type_col,color_map=None,title='Elinympäristötyypit datassa')
                    st.plotly_chart(bar_osm, use_container_width=True, config = {'displayModeBar': False})
                    map_osm = utils.plot_landuse(gdf,title=name,col=type_col,zoom=15)
                    st.plotly_chart(map_osm, use_container_width=True, config = {'displayModeBar': False})
                    
                else:
                    st.warning('Ei dataan')
            except TimeoutError:
                st.warning('Ei yhteyttä dataan')
                st.stop()
                
    elif sorsa == 'HSY':
        #with st.expander('HSY avoin data tasot'):
        #    utils.print_wfs_layers()
        if latlon:
            try:
                gdf = utils.get_hsy_maanpeite(latlon=latlon,radius=r)
                if gdf is not None and len(gdf) > 1: 
                    
                    name_col = "nimi"
                    area_col = "p_ala_m2"
                    type_col = "kuvaus"
                    title = f"Maanpeite {add}"
                    colors_hsy = {
                        "Muu avoin matala kasvillisuus":"DarkKhaki",
                        "puusto, 2 m - 10 m":"DarkSeaGreen",
                        "puusto, 10 m - 15 m":"OliveDrab",
                        "puusto, 15 m - 20 m":"DarkOliveGreen",
                        "Puusto yli 20 m":"DarkGreen"
                        }
                    
                    bar_hsy = utils.plot_area_bars(gdf,x='p_ala_m2',y='kuvaus',color='kuvaus',color_map=colors_hsy)
                    st.plotly_chart(bar_hsy, use_container_width=True, config = {'displayModeBar': False})
                    map_hsy = utils.plot_landuse(gdf,title,col=type_col,color_map=colors_hsy,zoom=15)
                    st.plotly_chart(map_hsy, use_container_width=True, config = {'displayModeBar': False})
                    #st.write(gdf.columns.tolist())
                    #st.stop()
            except TimeoutError:
                st.warning('Ei yhteyttä dataan')
                st.stop()

    else:
        gdf_oma = None
        uploaded_file_oma = st.file_uploader("Lataa oma aineisto", type=['zip'], key='oma')
        if uploaded_file_oma:
            try:
                gdf_oma = utils.extract_shapefiles_from_zip(uploaded_file_oma,'Polygon')
                if 'area' not in gdf_oma.columns or gdf_oma['area'].isna().all():
                    utm = gdf_oma.estimate_utm_crs()
                    gdf_oma['area'] = round(gdf_oma.to_crs(utm).area,-1)
                else:
                    pass
            except Exception as err_bu:
                print(f"Data error: {err_bu}")
                st.warning('Tarkista data')
            st.data_editor(gdf_oma.drop(columns='geometry'))

if gdf is not None and not gdf.empty:
    with st.expander('Viherkerroinlaskenta',expanded=True):
        try:
            score_module.scoring_table(gdf=gdf,
                                source=sorsa,
                                name_col=name_col,area_col=area_col,type_col=type_col,
                                classification_file="classification.csv")
        except:
            st.warning('Tarkenna osoite')
            
