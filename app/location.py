import streamlit as st
import pandas as pd
import random
import utils
import plotly.express as px
import score_module

st.subheader("Kohdealueen analyysi")
loc_text = """
    Paikkatietopohjainen laskenta eri datalähteillä 
    ([HSY](https://www.hsy.fi/ymparistotieto/paikkatiedot/rajapinnat/avoimet-paikkatietorajapinnat/),
    [OSM](https://wiki.openstreetmap.org/wiki/Land_use)).
"""
st.markdown(loc_text)

#reset session_states df when query changed
def reset_session_state():
    if "loc_df_updated" in st.session_state:
        del st.session_state.loc_df_updated
    if "group_toggle" in st.session_state:
        st.session_state.group_toggle = False
            
gdf = None
r = 250
s1,s2 = st.columns([1,2])
add = s1.text_input('Kohdeosoite', on_change=reset_session_state)
sorsa = s2.radio('Datalähde',['HSY','OSM'],horizontal=True, on_change=reset_session_state)

try:
    latlon = utils.getlatlon(add)
except:
    st.warning('Tarkenna osoite')
    st.stop()
    
with st.expander('Elinympäristöt datassa',expanded=True):
            
    if latlon:
        minarea = st.slider('Min. pinta-ala elinympäristölle (m2)',0,1000,200,100, on_change=reset_session_state)
    
        if sorsa == 'OSM':
            tag = 'Maanpeite' #s3.radio('Lähtötieto',['Maanpeite','Maankäyttö','Luontoalueet'],horizontal=True)
            if tag == 'Maankäyttö':
                tags = {'landuse':True}
                name = f"Maankäyttö {add}"
            elif tag == 'Luontoalueet':
                tags = {'natural':True}
                name = f"Luontoalueet {add}"
            else:
                tags = {'natural':True,'landuse':['grass','meadow','forest']}
                name = f"Elinympäristöt: {add}"
            
            try:
                gdf = utils.get_osm_landuse(latlon=latlon,tags=tags,radius=r)
                if gdf is not None and not gdf.empty:
                    name_col = "nimi"
                    area_col = "pinta-ala"
                    type_col="luokka"
                    #plots
                    gdf = gdf[gdf[area_col] >= minarea]
                    bar_osm = utils.plot_area_bars(gdf,x=area_col,y=type_col,color=type_col,color_map=None,title='Elinympäristötyypit datassa')
                    st.plotly_chart(bar_osm, use_container_width=True, config = {'displayModeBar': False})
                    map_osm = utils.plot_landuse(gdf,title=name,col=type_col,name_col=name_col,zoom=15)
                    st.plotly_chart(map_osm, use_container_width=True, config = {'displayModeBar': False})
                    
                else:
                    st.warning('Ei dataan')
            except TimeoutError:
                st.warning('Ei yhteyttä dataan')
                st.stop()
                    
        elif sorsa == 'HSY':
            #with st.expander('HSY avoin data tasot'):
            #    utils.print_wfs_layers()
            
            try:
                gdf = utils.get_hsy_maanpeite(latlon=latlon,radius=r)
                if gdf is not None and len(gdf) > 1: 
                    gdf.reset_index(inplace=True)
                    name_col = "index"
                    area_col = "p_ala_m2"
                    type_col = "kuvaus"
                    title = f"Elinympäristöt: {add}"
                    colors_hsy = {
                        "Muu avoin matala kasvillisuus":"DarkKhaki",
                        "puusto, 2 m - 10 m":"DarkSeaGreen",
                        "puusto, 10 m - 15 m":"OliveDrab",
                        "puusto, 15 m - 20 m":"DarkOliveGreen",
                        "Puusto yli 20 m":"DarkGreen"
                        }
                    gdf = gdf[gdf[area_col] >= minarea]
                    bar_hsy = utils.plot_area_bars(gdf,x='p_ala_m2',y='kuvaus',color='kuvaus',color_map=colors_hsy)
                    st.plotly_chart(bar_hsy, use_container_width=True, config = {'displayModeBar': False})
                    map_hsy = utils.plot_landuse(gdf,title,col=type_col,name_col=name_col,color_map=colors_hsy,zoom=15)
                    st.plotly_chart(map_hsy, use_container_width=True, config = {'displayModeBar': False})
                    #st.write(gdf.columns.tolist())
                    #st.stop()
            except TimeoutError:
                st.warning('Ei yhteyttä dataan')
                st.stop()

        else:
            gdf_oma = None
            uploaded_file_oma = st.file_uploader("Lataa oma aineisto", type=['zip'], key='oma')
            if uploaded_file_oma:
                try:
                    gdf_oma = utils.extract_shapefiles_from_zip(uploaded_file_oma,'Polygon')
                    if 'area' not in gdf_oma.columns or gdf_oma['area'].isna().all():
                        utm = gdf_oma.estimate_utm_crs()
                        gdf_oma['area'] = round(gdf_oma.to_crs(utm).area,-1)
                    else:
                        pass
                except Exception as err_bu:
                    print(f"Data error: {err_bu}")
                    st.warning('Tarkista data')
                st.data_editor(gdf_oma.drop(columns='geometry'))
                st.warning('Oman aineiston analyysi ei vielä käytössä.')
                st.stop()


if gdf is not None and not gdf.empty:
    with st.expander(f'Viherkerroinlaskenta (min {minarea} m² alueet)',expanded=True):
        #try:
        scoring_df = score_module.loc_scoring_table(gdf=gdf,
                            source=sorsa,
                            name_col=name_col,area_col=area_col,type_col=type_col,
                            classification_file="classification_landcover.csv")
        #download
        csv_to_save = scoring_df.to_csv().encode('utf-8')
        file_name = f"ana_{add}.csv"
        file_name = file_name.lower().replace(' ', '_').replace(',', '_')
        st.download_button(label="Lataa arviointitaulukko (csv)",
                            data=csv_to_save,
                            file_name=file_name,
                            mime='text/csv')

        #except:
        #    st.warning('Tarkenna osoite')
            
