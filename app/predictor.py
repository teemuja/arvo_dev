import streamlit as st
import pandas as pd

st.title("Zoning Designation Analysis")

st.cache_data()
def load_data():
    try:
        ground_truth_df = pd.read_csv("https://a3s.fi/swift/v1/AUTH_19865241c6944749b4a9f63633e85127/arvodev/appdata/hki_maanpeite_4326.csv")
        plan_df = pd.read_csv("https://a3s.fi/swift/v1/AUTH_19865241c6944749b4a9f63633e85127/arvodev/appdata/hki_kaavayksikot_4326.csv")
        return ground_truth_df, plan_df
    except:
        st.warning('DB error')
        return None

ground_truth_df, plan_df = load_data()

mem_gt = round(ground_truth_df.memory_usage(deep=True).sum() / (1024**2),2)  # Output in MB
mem_zo = round(plan_df.memory_usage(deep=True).sum() / (1024**2),2)  # Output in MB

st.success(f"Memory usage {mem_gt}(landcover) + {mem_zo}(zoning) MB")

st.data_editor(ground_truth_df)

st.stop()
