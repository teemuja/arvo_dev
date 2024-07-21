import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import wkt
import utils
import plotly.express as px
import requests
import io

st.subheader("Suunnitelman analyysi")
plan_text = """
    Laskenta aluesuunnitelman maankäyttötiedoista.
"""
st.markdown(plan_text)

gdf_slu = None
uploaded_file = st.file_uploader("Lataa suunnitelma", type=['zip'], key='slu')
demo_plan = False #st.checkbox('Käytä esimerkkisuunnitelmaa')

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
        filepath = " "
        r = requests.get(filepath, stream=True)
        demo_plan_file = io.BytesIO(r.content)
        gdf_slu = utils.extract_shapefiles_from_zip(demo_plan_file,'Polygon')
        
if gdf_slu is not None:
    st.success('go on..')
    