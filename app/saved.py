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
    Tarkastelu tallennettuja analyysejä
"""
st.markdown(plan_text)

gdf_slu = None

with st.status('Viherkerroinlaskenta',expanded=True):
    file_paths = utils.allas_csv_handler()
    asses = [path.replace("app_data/", "") for path in file_paths if "ASS" in path]
    asses.insert(0,'...')
    myass = st.selectbox('Avaa tarkastelu',asses)
    if myass != "...":
        data = utils.allas_csv_handler(download_csv=myass)
        data['geometry'] = data.wkt.apply(wkt.loads)
        gdf_slu = gpd.GeoDataFrame(data,geometry='geometry',crs=4326)

if gdf_slu is not None:
    with st.expander('Viherkerroinlaskenta',expanded=True):
        cols = gdf_slu.columns.tolist()
        name_col = cols[0]
        type_col = cols[1]
        area_col = cols[2]
        scoring_df = cols[3:14]
        
        score_module.scoring(gdf=gdf_slu,source=None,
                                name_col=name_col,area_col=area_col,type_col=type_col,
                                classification_file=None,saved_mode=True)

