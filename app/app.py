import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
from streamlit_gsheets import GSheetsConnection
import utils

st.header("A R V O dev",divider='green')
st.markdown("Tutkimusappi alueviherkertoimen kehitykseen [ARVO](https://figbc.fi/arvo-viherrakenteen-arviointi-ja-vahvistaminen-kaupunkien-maankayton-suunnittelussa)-hankkeessa.")

conn = st.connection("gsheets", type=GSheetsConnection)

tab1,tab2 = st.tabs(["Kohdealue-analyysi","Testisuunnitelmat"])

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
        gdf = utils.get_landuse(add=add,tags=tags,radius=500)
        col="type"
        fig_bar = utils.plot_osm_areas(gdf)
        st.plotly_chart(fig_bar, use_container_width=True, config = {'displayModeBar': False})
        
    if gdf is not None:
        with st.status('Kartta'):
            fig_osm = utils.plot_landuse(gdf,name=name,col=col)
            st.plotly_chart(fig_osm, use_container_width=True, config = {'displayModeBar': False})
            df_e = gdf.drop(columns="geometry")
            df_e = df_e.loc[df_e['area'] > 100]
            df_e['area'] = round(df_e['area'],-1)
            df_edit = df_e.groupby(by='type').sum()
            df_edit['K'] = None
            df_edit['X'] = 0.0
            
        with st.expander('Vihertaselaskelma'):
            cols = ['area','K','X']
            new_df = st.data_editor(df_edit[cols],use_container_width=True)
            new_df['Kx'] = new_df['area']*new_df['X']
            avk = round((new_df.loc[new_df['K'].notna()]['area'].sum() + new_df['Kx'].sum()) / new_df['area'].sum(),2)
            kx_med = round(new_df['X'].median(),2)
            s1,s2 = st.columns(2)
            s1.metric('Aluevihertase',value=avk)
            latex_code = r"""
                        $$
                        \frac{\sum eAla + \sum eAla*Kx}{\sum totAla}
                        $$
                        """
            s2.markdown(latex_code,unsafe_allow_html=True)

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
        elements = st.multiselect('Valitse testailtavat elementit',element_list,max_selections=5)
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
        try:
            name = f"Esimerkki {VE}"
            df = st.data_editor(data, hide_index=True, height=200, disabled=("wkt"), use_container_width=True)
            feats = df.drop(columns='wkt').columns.tolist()
            col = st.selectbox('Visualisoi tieto',feats[1:-1])
            if col != '..':
                df['geometry'] = df.wkt.apply(wkt.loads)
                gdf = gpd.GeoDataFrame(df,geometry='geometry',crs=4326)
                df_edit = gdf.drop(columns="geometry")
                df_edit = df_edit.loc[df_edit['area'] > 1000]
                df_edit['area'] = round(df_edit['area'],-1)
                if "K" not in df_edit.columns:
                    df_edit['K'] = df_edit['element_type']
                if "X" not in df_edit.columns:
                    df_edit['X'] = df_edit['coef']
        except:
            st.warning("lähtötiedossa virhe")
            st.stop()
        
        if gdf is not None:
            with st.status('Kartta'):
                fig_slu = utils.plot_landuse(gdf,name=name,col=col)
                st.plotly_chart(fig_slu, use_container_width=True, config = {'displayModeBar': False})
            with st.expander('Viherkerroinlaskelma'):
                cols = ['area','K','X']
                new_df = st.data_editor(df_edit[cols],use_container_width=True)
                new_df['Kx'] = new_df['area']*new_df['X']
                avk = round((new_df.loc[new_df['K'].notna()]['area'].sum() + new_df['Kx'].sum()) / new_df['area'].sum(),2)
                kx_med = round(new_df['X'].median(),2)
                st.metric('Hankeviherkerroin',value=avk)
            
#footer
st.markdown('---')
footer_title = '''
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/teemuja/arvo_dev/blob/main/LICENSE) 
'''
st.markdown(footer_title)