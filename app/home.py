import streamlit as st
import utils

st.header("A R V O demot",divider='green')

home_text = """
    ARVO-hankkeessa on kehitetty **_laskentatapaa_**, 
    jolla kaupunkisuunittelun vaikutusta luonnon monimuotoisuuteen ja ekosysteemipalveluihin voidaan arvottaa 
    sekä maasto- ja paikkatiedosta että suunnitelmista mahdollisimman yhteismitallisesti osana kaavoitusta.
    Laskentatapojen testaus sekä eri lähtötietojen toimivuuden tarkastelu laskennan pohjadatana oli hankkeessa keskeistä.
    Demojen avulla testaus **_joukkoistettiin_** sekä hanketiimin että sidosryhmien kesken.
    """
st.markdown(home_text)

try:
    img_path = utils.allas(f"arvodev/appdata/arvologot.png")
    if img_path:
        st.image(img_path)
except Exception as e:
    print("(Logo ei saatavilla)")