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
        
        #image from allas
        import requests
        import io
        @st.cache_data()
        def allas_get(filepath):
            r = requests.get(filepath, stream=True)
            data = io.BytesIO(r.content)
            return data
        st.image(allas_get("https://a3s.fi/swift/v1/AUTH_19865241c6944749b4a9f63633e85127/arvodev/app_data/logot.png"))
        

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
