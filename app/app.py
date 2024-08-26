import streamlit as st
import utils

st.set_page_config(page_title="ARVO demot", layout="wide", initial_sidebar_state='expanded')
st.markdown("""
<style>
button[title="View fullscreen"]{
        visibility: hidden;}
</style>
""", unsafe_allow_html=True)

#title
st.sidebar.image('https://figbc.fi/media/arvo_logo.png')
st.sidebar.header("A R V O demot",divider='green')
st.sidebar.markdown("T&K-demot alueviherkertoimen kehitykseen [ARVO](https://figbc.fi/arvo-viherrakenteen-arviointi-ja-vahvistaminen-kaupunkien-maankayton-suunnittelussa)-hankkeessa.")
st.sidebar.caption('Työversio beta 1.4')

with st.container():
    if "logged_in" not in st.session_state or st.session_state.logged_in == False:
        st.session_state.logged_in = False
        with st.empty():
            utils.check_password()
        #spons logos
        aalto = "https://figbc.fi/media/aalto-yliopisto-logo-2024.png"
        espoo = "https://figbc.fi/media/espoo-logo-2024.png"
        figbc = "https://figbc.fi/media/green-building-council-finland-logo-valkoisilla-reunoilla.png"
        hel = "https://figbc.fi/media/helsinki-logo-2024.jpg"
        vantaa = "https://figbc.fi/media/vantaa-logo-2024.png"

        s1,s2,s3,s4,s5,s6 = st.columns(6)
        s1.image(aalto)
        s2.image(espoo)
        s3.image(figbc)
        s4.image(hel)
        s5.image(vantaa)

home_page = st.Page("home.py", title="Miksi demot?", default=True)
feedback_page = st.Page("feedback.py", title="Kehitysideat")

location = st.Page("location.py", title="Kohdealueen analyysi")
plans = st.Page("plans.py", title="Suunnitelman analyysi", )
saved = st.Page("saved.py", title="Tallennetut analyysit", )

if st.session_state.logged_in:
    menu = st.navigation(
        {
            "Info": [home_page,feedback_page],
            "Demot": [location,plans,saved]
        }
    )
    menu.run()


#sidebar footer
st.sidebar.markdown('---')
footer_title = '''
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/teemuja/arvo_dev/blob/main/LICENSE) 
'''
st.sidebar.markdown(footer_title)
