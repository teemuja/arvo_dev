import streamlit as st
import utils

st.set_page_config(page_title="ARVO demot", layout="wide", initial_sidebar_state='expanded')
# st.markdown("""
#     <style>
#     button {
#         background-color: #4CAF50; /* Green */
#         color: white;
#     }
#     </style>
#     """, unsafe_allow_html=True)

#title
st.sidebar.image('https://figbc.fi/media/arvo_logo.png')
st.sidebar.header("A R V O demot",divider='green')
st.sidebar.markdown("T&K-demot alueviherkertoimen kehitykseen [ARVO](https://figbc.fi/arvo-viherrakenteen-arviointi-ja-vahvistaminen-kaupunkien-maankayton-suunnittelussa)-hankkeessa.")
st.sidebar.caption('V 2025:11')

home_page = st.Page("home.py", title="Miksi demot?", default=True)
location = st.Page("location.py", title="Aineistotestit")
poc = st.Page("poc.py", title="Laskentademo", )

menu = st.navigation(
    {
        "Info": [home_page],
        "Demot": [location,poc]
    }
)

menu.run()


#sidebar footer
st.sidebar.markdown('---')
footer_title = '''
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/teemuja/arvo_dev/blob/main/LICENSE) 
'''
st.sidebar.markdown(footer_title)
