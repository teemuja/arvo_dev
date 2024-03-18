import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
from streamlit_gsheets import GSheetsConnection
import utils

st.header("A R V O dev",divider='green')
st.markdown("Tutkimusappi alueviherkertoimen kehitykseen [Aalto](##)")

conn = st.connection("gsheets", type=GSheetsConnection)

tab1,tab2 = st.tabs(["OpenStreetMap","Testisuunnitelmat"])

with tab1:
    gdf = None
    s1,s2 = st.columns(2)
    add = s1.text_input('Kohdeosoite')
    tag = s2.radio('',['Land cover','Land-use','Natural'],horizontal=True)
    if tag == 'Land-use':
        tags = {'landuse':True}
        name = f"Maankäyttö {add}"
    elif tag == 'Natural':
        tags = {'natural':True}
        name = f"Luontoalueet {add}"
    else:
        tags = {'natural':True,'landuse':['grass','meadow','forest']}
        name = f"Maanpeite {add}"
    if add:
        gdf = utils.get_landuse(add=add,tags=tags,radius=500)
        col="type"
        fig_bar = utils.plot_osm_areas(gdf)
        st.plotly_chart(fig_bar, use_container_width=True, config = {'displayModeBar': False})
        
    if gdf is not None:  
        fig_osm = utils.plot_landuse(gdf,name=name,col=col)
        st.plotly_chart(fig_osm, use_container_width=True, config = {'displayModeBar': False})
        
with tab2:
    data = None
    VE = st.radio("Valitse testisuunnitelman versio",['VE1','VE2'],horizontal=True)
    if VE == 'VE1':
        data = conn.read(worksheet="2027374130",ttl="30min")
    elif VE == 'VE2':
        data = conn.read(worksheet="1190105635",ttl="30min")
    else:
        st.stop()
        element_list = [f"K{i}" for i in range(1, 30 + 1)]
        elements = st.multiselect('Valitse testailatavat elementit',element_list,max_selections=5)
        with st.form('Elementit'):
            slider_values = {}
            for e in sorted(elements):
                slider_values[e] = st.slider(
                    label=f"{e} Value", 
                    min_value=0, 
                    max_value=100, 
                    value=50,
                    key=e
                    )
            st.text(slider_values)
            ana = st.form_submit_button('Analysoi')
            
    if data is not None:
        name = f"Esimerkki {VE}"
        df = st.data_editor(data, hide_index=True, height=200, disabled=("wkt"), use_container_width=True)
        feats = df.drop(columns='wkt').columns.tolist()
        col = st.selectbox('Visualisoi tieto',feats[1:-1])
        if col != '..':
            try: 
                df['geometry'] = df.wkt.apply(wkt.loads)
                gdf = gpd.GeoDataFrame(df,geometry='geometry',crs=4326)
            except:
                st.stop()
        
        if gdf is not None:
                fig_slu = utils.plot_landuse(gdf,name=name,col=col)
                st.plotly_chart(fig_slu, use_container_width=True, config = {'displayModeBar': False})
            
            
            
