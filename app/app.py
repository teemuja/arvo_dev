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

tab1,tab2 = st.tabs(["Nykytila-analyysi","Suunnitelma-analyysi"])

with tab1:
    gdf = None
    s1,s2,s3 = st.columns([1,1,2])
    add = s1.text_input('Kohdeosoite')
    sorsa = s2.radio('Datalähde',['OSM','HSY'],horizontal=True)
    if sorsa == 'OSM':
        tag = s3.radio('Lähtötieto',['Maanpeite','Maankäyttö','Luontoalueet'],horizontal=True)
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
            gdf = utils.get_osm_landuse(add=add,tags=tags,radius=250)
            area_col = "area"
            type_col="type"
            df_for_edit = gdf.drop(columns='geometry')
            #plots
            bar_osm = utils.plot_area_bars(gdf)
            st.plotly_chart(bar_osm, use_container_width=True, config = {'displayModeBar': False})
            map_osm = utils.plot_landuse(gdf,name=name,col=type_col,zoom=15)
            st.plotly_chart(map_osm, use_container_width=True, config = {'displayModeBar': False})
    else:
        with st.expander('hsy avoin data tasot'):
            utils.print_wfs_layers()
        if add:
            gdf = utils.get_hsy_maanpeite(add=add,radius=250)
            area_col = "p_ala_m2"
            type_col = "kuvaus"
            df_for_edit = gdf.drop(columns='geometry')

        if gdf is not None and len(gdf) > 0:
            name = f"Maanpeite {add}"
            colors_hsy = {
                "Muu avoin matala kasvillisuus":"DarkKhaki",
                "puusto, 2 m - 10 m":"DarkSeaGreen",
                "puusto, 10 m - 15 m":"OliveDrab",
                "puusto, 15 m - 20 m":"DarkOliveGreen",
                "Puusto yli 20 m":"DarkGreen"
                }
            bar_hsy = utils.plot_area_bars(gdf,x='p_ala_m2',y='kuvaus',color='kuvaus',color_map=colors_hsy)
            st.plotly_chart(bar_hsy, use_container_width=True, config = {'displayModeBar': False})
            map_hsy = utils.plot_landuse(gdf,name=name,col=type_col,color_map=colors_hsy,zoom=15)
            st.plotly_chart(map_hsy, use_container_width=True, config = {'displayModeBar': False})

    if gdf is not None:
            
        with st.expander('Laskelma'):
            grouped_df = df_for_edit.groupby(by=type_col, group_keys=True).sum().reset_index()
            grouped_df[area_col] = round(grouped_df[area_col],-1)
            grouped_df['Kx'] = grouped_df.apply(lambda row: round(random.uniform(0.5, 3.5),1), axis=1)

            grouped_df['Selite'] = "..."
            
            edited_df = st.data_editor(
                            grouped_df,
                            hide_index=True,
                            #column_config={"Select": st.column_config.CheckboxColumn(required=True)},
                            #disabled=df_for_edit.columns,
                            use_container_width=True
                        )
            #calc
            eAla = edited_df[area_col].sum()
            edited_df['kxAla'] = edited_df[area_col] * edited_df['Kx']
            kxAla = edited_df['kxAla'].sum()
            tot_ala = (3.14 * 500 * 500) #hakualue
            arvo = round((eAla + kxAla)/tot_ala,2)
            #results
            s1,s2 = st.columns(2)
            s1.metric('ARVO',value=arvo)
            latex_code = r"""
                        $$
                        \frac{\sum eAla + \sum eAla*Kx}{\sum totAla}
                        $$
                        """
            s2.markdown(latex_code,unsafe_allow_html=True)


with tab2:
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