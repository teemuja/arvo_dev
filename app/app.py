import streamlit as st
import utils

st.set_page_config(page_title="ARVO demot", layout="wide")
st.sidebar.image('https://figbc.fi/media/arvo_logo.png')
st.sidebar.header("A R V O demot",divider='green')
st.sidebar.markdown("T&K-demot alueviherkertoimen kehitykseen [ARVO](https://figbc.fi/arvo-viherrakenteen-arviointi-ja-vahvistaminen-kaupunkien-maankayton-suunnittelussa)-hankkeessa.")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    with st.sidebar.empty():
        utils.check_password()

home_page = st.Page("home.py", title="Miksi demot?", default=True)
feedback_page = st.Page("feedback.py", title="Kehitysideat")

location = st.Page("location.py", title="Kohdealueen analyysi")
plans = st.Page("plans.py", title="Suunnitelman analyysi", )

if st.session_state.logged_in:
    menu = st.navigation(
        {
            "Info": [home_page,feedback_page],
            "Demot": [location,plans]
        }
    )
    menu.run()
    
#sidebar footer
st.sidebar.markdown('---')
footer_title = '''
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/teemuja/arvo_dev/blob/main/LICENSE) 
'''
st.sidebar.markdown(footer_title)
