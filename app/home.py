import streamlit as st
import utils

st.markdown("T&K-demot alueviherkertoimen kehitykseen [ARVO](https://figbc.fi/arvo-viherrakenteen-arviointi-ja-vahvistaminen-kaupunkien-maankayton-suunnittelussa)-hankkeessa.")

if not utils.check_password():
    st.stop()
    
st.markdown('lorem ipsum...')