import streamlit as st

st.set_page_config(page_title="ARVO demot", layout="wide")
st.header("A R V O demot",divider='green')

home_page = st.Page("home.py", title="Miksi demot?", default=True)
feedback_page = st.Page("feedback.py", title="Kehitysideat")

location = st.Page("location.py", title="Kohdealueen analyysi")
plans = st.Page("plans.py", title="Suunnitelman analyysi", )

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.switch_page(home_page)

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Info": [home_page,feedback_page],
            "Demot": [location,plans]
        }
    )
else:
    pg = st.navigation([home_page])

pg.run()

#footer
st.markdown('---')
footer_title = '''
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/teemuja/arvo_dev/blob/main/LICENSE) 
'''
st.markdown(footer_title)