import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import wkt
import utils
import plotly.express as px
import requests
import io
import score_module

st.subheader("Suunnitelman analyysi")
plan_text = """
    Laskenta aluesuunnitelman maankäyttötiedoista.
"""
st.markdown(plan_text)

gdf_slu = None
uploaded_file = st.file_uploader("Lataa suunnitelma", type=['zip'], key='slu')
demo_plan = st.toggle('Käytä esimerkkisuunnitelmaa')

if uploaded_file:
    try:
        gdf_slu = utils.extract_shapefiles_from_zip(uploaded_file,'Polygon')
        if 'area' not in gdf_slu.columns or gdf_slu['area'].isna().all():
            utm = gdf_slu.estimate_utm_crs()
            gdf_slu['area'] = round(gdf_slu.to_crs(utm).area,-1)
        else:
            pass
    except Exception as err_bu:
        print(f"Data error: {err_bu}")
        st.warning('Tarkista data')
else:   
    if demo_plan:
        filepath = "app_data/case_puksu.zip"
        demo_plan_zip = utils.get_zip_from_allas(filepath)
        gdf_slu = utils.extract_shapefiles_from_zip(demo_plan_zip,'Polygon')
        if 'area' not in gdf_slu.columns or gdf_slu['area'].isna().all():
            utm = gdf_slu.estimate_utm_crs()
            gdf_slu['area'] = round(gdf_slu.to_crs(utm).area,-1)
        #st.data_editor(gdf_slu.drop(columns='geometry'))
        #st.stop()
        
if gdf_slu is not None and not gdf_slu.empty:
    if demo_plan:
        demo_plan_df = gdf_slu.copy().drop(columns="geometry")
        name_col = "nimi"
        type_col = "mk_luokka"
        expl_col = "kuvaus"
        gfa_col = "kerrosala"
    else:
        c1,c2,c3,c4 = st.columns(4)
        orig_cols = gdf_slu.drop(columns="geometry").columns.tolist()
        orig_cols.insert(0,'...')
        type_col = c1.selectbox(label='luokittelutieto',options=orig_cols)
        name_col = c2.selectbox(label='kohdenimet',options=orig_cols)
        expl_col = c3.selectbox(label='kuvaus',options=orig_cols)
        gfa_col = c4.selectbox(label='kerrosala',options=orig_cols)
    
    if name_col != "..." and type_col != "..." and expl_col != "..." and gfa_col != "...":

        try:
            df_cls = utils.allas_csv_handler(download_csv="kalu.csv")
            paaluokka_list = df_cls[df_cls.columns[0]].dropna().tolist()
            kalu_list = df_cls[df_cls.columns[2]].dropna().tolist()
            
        except Exception as e:
            st.error(f"Ei yhteyttä luokittelutiedostoon: {e}")
            st.stop()

        # --------------------
        edited_df = score_module.editor(df1=gdf_slu.drop(columns='geometry'), df2=df_cls)
        
        #
        st.markdown("---")
        #st.table(edited_df)