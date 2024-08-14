import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import wkt
import utils
import plotly.express as px
import requests
import io
import utils,score_module


st.subheader("Tallennetut analyysit")
plan_text = """
    Tarkastele tallennettuja analyysejä
"""
st.markdown(plan_text)

gdf_slu = None

with st.status('Viherkerroinlaskenta',expanded=True):
    file_paths = utils.allas_csv_handler()
    asses = [path.replace("app_data/", "") for path in file_paths if "ANA" in path]
    asses.insert(0,'...')
    myass = st.selectbox('Avaa tarkastelu',asses)
    if myass != "...":
        data = utils.allas_csv_handler(download_csv=myass)
        data['geometry'] = data.wkt.apply(wkt.loads)
        gdf_slu = gpd.GeoDataFrame(data,geometry='geometry',crs=4326)

if gdf_slu is not None:
    with st.status('Viherkerroinanalyysi',expanded=True):
        utm = gdf_slu.estimate_utm_crs()
        gdf_slu['area'] = round(gdf_slu.to_crs(utm).area,-1)
        cols = gdf_slu.columns.tolist()
        name_col = 'nimi'
        type_col = 'elinymp_luokka'
        area_col = 'area'

        score_module.ana_score_plot(gdf_ana=gdf_slu,
                                name_col=name_col,area_col=area_col,type_col=type_col
                                )
    with st.expander('Arviointitaulukko', expanded=False):
        save_df = gdf_slu.drop(columns=['geometry','wkt','lat','lon'])
        save_df.rename(columns={'area':'pinta_ala'},inplace=True)
        st.data_editor(save_df)
        #download
        csv_to_save = save_df.to_csv().encode('utf-8')
        file_name = f"{myass}.csv"
        file_name = file_name.lower().replace(' ', '_').replace(',', '_')
        st.download_button(label="Lataa arviointitaulukko (csv)",
                            data=csv_to_save,
                            file_name=file_name,
                            mime='text/csv')

