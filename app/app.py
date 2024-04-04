import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import wkt
from streamlit_gsheets import GSheetsConnection
import random
import utils

st.set_page_config(page_title="ARVO dev app", layout="wide")

st.header("A R V O dev",divider='green')
st.markdown("Tutkimusappi alueviherkertoimen kehitykseen [ARVO](https://figbc.fi/arvo-viherrakenteen-arviointi-ja-vahvistaminen-kaupunkien-maankayton-suunnittelussa)-hankkeessa.")

conn = st.connection("gsheets", type=GSheetsConnection)

tab1,tab2,tab3 = st.tabs(["OSM data","HSY avoin data","Suunnitelmatestit"])

with tab1:
    gdf = None
    s1,s2 = st.columns([1,2])
    add = s1.text_input('Kohdeosoite')
    tag = s2.radio('',['Maanpeite','Maankäyttö','Luontoalueet'],horizontal=True)
    if tag == 'Maankäyttö':
        tags = {'landuse':True}
        name = f"Maankäyttö {add}"
    elif tag == 'Luontoalueet':
        tags = {'natural':True}
        name = f"Luontoalueet {add}"
    else:
        tags = {'natural':True,'landuse':['grass','meadow','forest']}
        name = f"Maanpeite {add}"
    if add:
        gdf = utils.get_osm_landuse(add=add,tags=tags,radius=500)
        col="type"
        fig_bar = utils.plot_area_bars(gdf)
        st.plotly_chart(fig_bar, use_container_width=True, config = {'displayModeBar': False})
        
    if gdf is not None:
        with st.status('Kartta'):
            fig_osm = utils.plot_landuse(gdf,name=name,col=col)
            st.plotly_chart(fig_osm, use_container_width=True, config = {'displayModeBar': False})
            df_e = gdf.drop(columns="geometry")
            df_e = df_e.loc[df_e['area'] > 100]
            df_e['area'] = round(df_e['area'],-1)
            df_edit = df_e.groupby(by='type').sum()
            df_edit['K_selite'] = None
            df_edit['x'] = 0.0
            
        with st.expander('Vihertaselaskelma'):
            cols = ['area','K_selite','x']
            new_df = st.data_editor(df_edit[cols],use_container_width=True)
            new_df['Kx'] = new_df['area']*new_df['x']
            avk = round((new_df.loc[new_df['K_selite'].notna()]['area'].sum() + new_df['Kx'].sum()) / new_df['area'].sum(),2)
            kx_med = round(new_df['x'].median(),2)
            s1,s2 = st.columns(2)
            s1.metric('Aluevihertase',value=avk)
            latex_code = r"""
                        $$
                        \frac{\sum eAla + \sum eAla*Kx}{\sum totAla}
                        $$
                        """
            s2.markdown(latex_code,unsafe_allow_html=True)

with tab2:
    gdf2 = None
    add2 = st.text_input('Kohdeosoite',key='hsy')
    
    if add2:
        try:
            gdf2 = utils.get_hsy_maanpeite(add=add2,radius=250)
        except:
            st.warning('ei tuloksia')
        
    col2="kuvaus"
    if gdf2 is not None and len(gdf2) > 0:
        colors_hsy = {
            "Muu avoin matala kasvillisuus":"DarkKhaki",
            "puusto, 2 m - 10 m":"DarkSeaGreen",
            "puusto, 10 m - 15 m":"OliveDrab",
            "puusto, 15 m - 20 m":"DarkOliveGreen",
            "Puusto yli 20 m":"DarkGreen"
            }
        fig_bar2 = utils.plot_area_bars(gdf2,x='p_ala_m2',y='kuvaus',color='kuvaus',color_map=colors_hsy)
        st.plotly_chart(fig_bar2, use_container_width=True, config = {'displayModeBar': False})
        
        with st.status("Alueet karttalla"):
            fig_osm2 = utils.plot_landuse(gdf2,name=name,col=col2,color_map=colors_hsy,zoom=16)
            st.plotly_chart(fig_osm2, use_container_width=True, config = {'displayModeBar': False})
        with st.expander('hsy avoin data tasot'):
            utils.print_wfs_layers()
    else:
        st.warning('ei tuloksia')


with tab3:
    gdf3 = None
    uploaded_file = st.file_uploader("Lataa suunnitelma", type=['zip'], key='uploaded')
    if uploaded_file:
        try:
            gdf3 = utils.extract_shapefiles_from_zip(uploaded_file,'Polygon')
            if 'area' not in gdf3.columns or gdf3['area'].isna().all():
                utm = gdf3.estimate_utm_crs()
                gdf3['area'] = round(gdf3.to_crs(utm).area,-1)
            else:
                pass
                
        except Exception as err_bu:
            print(f"Buildings data error: {err_bu}")
            st.warning('Tarkista data')
            
    if gdf3 is not None:
        #if 'x' not in gdf.columns or gdf['x'].isna().all():
        #    gdf['x'] = np.round(np.random.uniform(0, 1.5, size=len(gdf)), 1)
            
        if 'name' not in gdf3.columns or gdf3['name'].isna().all():
            gdf3['name'] = "Lorem area.."
        if 'K_selite' not in gdf3.columns or gdf3['K_selite'].isna().all():
            gdf3['K_selite'] = "Ipsum biotoop.."
            
        cols = ['name','area','K_selite','x']
        df = st.data_editor(gdf3[cols], hide_index=True, height=200, use_container_width=True)
        df['Kx'] = df['area'] * df['x']
        gdf3['Kx'] = df['Kx']
        
        col = "Kx"
        fig_slu = utils.plot_landuse(gdf3,name='Testislu',hover_name='name',col=col, zoom=15)
        st.plotly_chart(fig_slu, use_container_width=True, config = {'displayModeBar': False})
        avk = round((df.loc[df['x'].notna()]['area'].sum() + df['Kx'].sum()) / df['area'].sum(),2)
        st.metric('Hankeviherkerroin',value=avk)
            
#footer
st.markdown('---')
footer_title = '''
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/teemuja/arvo_dev/blob/main/LICENSE) 
'''
st.markdown(footer_title)