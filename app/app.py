import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import wkt
from streamlit_gsheets import GSheetsConnection
import random
import utils
import plotly.express as px

st.set_page_config(page_title="ARVO dev app", layout="wide")

st.header("A R V O dev",divider='green')
st.markdown("Tutkimusappi alueviherkertoimen kehitykseen [ARVO](https://figbc.fi/arvo-viherrakenteen-arviointi-ja-vahvistaminen-kaupunkien-maankayton-suunnittelussa)-hankkeessa.")

tab1,tab2 = st.tabs(["Nykytila-analyysi","Suunnitelma-analyysi"])

with tab1:
    gdf = None
    r = 250
    s1,s2,s3 = st.columns([1,1,2])
    add = s1.text_input('Kohdeosoite')
    sorsa = s2.radio('Datalähde',['HSY','OSM','oma'],horizontal=True)
    
    location = utils.getlatlon(add)
    
    if location is not None:
        latlon = location[0]
        loc = location[1]
        if loc.quality != 1:
            st.warning('Anna tarkempi osoite')
            st.stop()
    else:
        st.warning('Anna tarkempi osoite')
        st.stop()
    
    with st.expander('Elinympäristöt datassa',expanded=True):
        if sorsa == 'OSM':
            tag = s3.radio('Lähtötieto',['Maanpeite','Maankäyttö','Luontoalueet'],horizontal=True)
            if tag == 'Maankäyttö':
                tags = {'landuse':True}
                name = f"Maankäyttö {add}"
            elif tag == 'Luontoalueet':
                tags = {'natural':True}
                name = f"Luontoalueet {add}"
            else:
                tags = {'natural':True,'landuse':['grass','meadow','forest']}
                name = f"Maanpeite {add}"
            if add:
                try:
                    gdf = utils.get_osm_landuse(latlon=latlon,tags=tags,radius=r)
                    if gdf is not None and not gdf.empty:
                        area_col = "pinta-ala"
                        type_col="luokka"
                        #plots
                        bar_osm = utils.plot_area_bars(gdf,x=area_col,y=type_col,color=type_col,color_map=None,title='Elinympäristötyypit datassa')
                        st.plotly_chart(bar_osm, use_container_width=True, config = {'displayModeBar': False})
                        map_osm = utils.plot_landuse(gdf,title=name,col=type_col,zoom=15)
                        st.plotly_chart(map_osm, use_container_width=True, config = {'displayModeBar': False})
                        
                    else:
                        st.warning('Ei dataan')
                except TimeoutError:
                    st.warning('Ei yhteyttä dataan')
                    st.stop()
                    
        elif sorsa == 'HSY':
            #with st.expander('HSY avoin data tasot'):
            #    utils.print_wfs_layers()
            if add:
                try:
                    gdf = utils.get_hsy_maanpeite(latlon=latlon,radius=r)
                    if gdf is not None and len(gdf) > 0:
                        area_col = "p_ala_m2"
                        type_col = "kuvaus"
                        title = f"Maanpeite {add}"
                        colors_hsy = {
                            "Muu avoin matala kasvillisuus":"DarkKhaki",
                            "puusto, 2 m - 10 m":"DarkSeaGreen",
                            "puusto, 10 m - 15 m":"OliveDrab",
                            "puusto, 15 m - 20 m":"DarkOliveGreen",
                            "Puusto yli 20 m":"DarkGreen"
                            }
                        bar_hsy = utils.plot_area_bars(gdf,x='p_ala_m2',y='kuvaus',color='kuvaus',color_map=colors_hsy)
                        st.plotly_chart(bar_hsy, use_container_width=True, config = {'displayModeBar': False})
                        map_hsy = utils.plot_landuse(gdf,title,col=type_col,color_map=colors_hsy,zoom=15)
                        st.plotly_chart(map_hsy, use_container_width=True, config = {'displayModeBar': False})
                        
                    else:
                        st.warning('Ei dataan')
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

    if gdf is not None and not gdf.empty:
        with st.expander('Viherkerroinlaskenta',expanded=True):
            
            #luokitukset
            conn = st.connection("gsheets", type=GSheetsConnection)
            try:
                df_cls = conn.read()
                df_cls.columns = df_cls.columns.str.lower()
                elist = df_cls[df_cls.columns[0]].tolist()
            except Exception as e:
                st.error(f"Ei yhteyttä luokittelutiedostoon: {e}")
                st.stop()
                
            ecols = df_cls.columns.tolist()[1:] #remove first col = 'ELINYMPÄRISTÖ'
            num_columns = [col for col in ecols if 'sel' not in col] + [area_col]
            str_columns = [col for col in ecols if 'sel' in col] + [type_col]
            
            #luokitteltava df
            df_for_edit = gdf.drop(columns='geometry')
            
            #selectors
            s1,s2 = st.columns([1,2])
            metodi = s1.radio('Määritä elinympäristöjä..',['Ryhmiteltynä','Yksittäin'],horizontal=True)
            minarea = s2.slider('Aseta min.ala m2',0,1000,500,100)
            df_for_edit = df_for_edit[df_for_edit[area_col] >= minarea]
            s1,s2 = st.columns([1,2])
            
            with s1.container(height=300):
                st.markdown('**Luokittelu**')
                
                #dict for default values
                osm_dict = {
                    "grass":'avonurmi',
                    "scrub":'niitty',
                    "grassland":'avonurmi',
                    "wetland":'niitty',
                    "wood":'metsä_nuori',
                    "forest":'metsä_vanha',
                    "bare_rock":"kalliot"
                    }
                hsy_dict = {
                    "Muu avoin matala kasvillisuus":"avonurmi",
                    "puusto, 2 m - 10 m":"metsä_nuori",
                    "puusto, 10 m - 15 m":"metsä_nuori",
                    "puusto, 15 m - 20 m":"metsä_vanha",
                    "Puusto yli 20 m":"metsä_vanha"
                    }
                
                if metodi == 'Ryhmiteltynä':
                    grouped_df = df_for_edit.groupby(by=type_col, group_keys=True).sum().reset_index()
                    area_types = grouped_df[type_col].tolist()
                    key = 0
                    selections = {}                        
                    index_values = range(len(grouped_df))
                    grouped_df.insert(0, 'index', index_values)
                    
                    random_names = ['Puistikot','Pellot','Perhosniityt','Taskupuistot','Hiilinielumetsät']
                    for ind, row in grouped_df.iterrows():
                        grouped_df.at[ind, 'name'] = random.choice(random_names)
                        
                    selections = {}
                    for type_area in grouped_df[type_col].unique():
                        key += 1
                        selectbox_label = type_area
                        # Determine default index for the selectbox
                        try:
                            default_dict = osm_dict if sorsa == "OSM" else hsy_dict
                            default_index = elist.index(default_dict.get(type_area, elist[0]))
                        except ValueError:
                            default_index = 0

                        # Use the default index in the selectbox
                        selected_option = st.selectbox(selectbox_label, options=elist, index=default_index, key=f"{type_area}{key}")
                        selections[type_area] = selected_option

                    # Update grouped_df based on user selections and transfer data from df_cls
                    for ind, row in grouped_df.iterrows():
                        original_type_area = row[type_col]
                        selected = selections.get(original_type_area)
                        if selected:
                            grouped_df.at[ind, type_col] = selected  # Update type_col with the selected value

                            # Transfer related data from df_cls to grouped_df
                            for e in ecols:
                                if e not in grouped_df.columns:
                                    grouped_df[e] = pd.NA  # Initialize the column if it doesn't exist
                                kx = df_cls.loc[df_cls[df_cls.columns[0]] == selected, e]
                                if not kx.empty:
                                    kx_value = kx.iloc[0]
                                    grouped_df.at[ind, e] = kx_value
                                   
                    df_for_cls = grouped_df.copy()

                else:
                    #..and same for not_grouped..
                    not_grouped_df = df_for_edit.copy()
                    selections = {}
                    index_values = not_grouped_df.index
                    if 'name' not in not_grouped_df.columns:
                        random_names = ['Puutiaisen puistikko','Heinänuhapelto','Perhosniitty','Hiilinielumetsä']
                        for ind, row in not_grouped_df.iterrows():
                            not_grouped_df.at[ind, 'name'] = random.choice(random_names)
                    not_grouped_df.insert(0, 'index', index_values)
                    
                    for index, type_area in not_grouped_df[type_col].iteritems():
                        selectbox_label = f"{type_area}, Index={index}"
                        #gen defaults..
                        if sorsa == "OSM":
                            try:
                                default_index = elist.index(osm_dict[type_area])
                            except:
                                default_index = 0
                        else:
                            try:
                                default_index = elist.index(hsy_dict[type_area])
                            except:
                                default_index = 0
                        selected_option = st.selectbox(selectbox_label,options=elist,index=default_index)
                        not_grouped_df.at[index, type_col] = selected_option
                        selections[index] = selected_option
                    
                    for index, _ in not_grouped_df.iterrows():
                        selected = selections.get(index)
                        if selected:
                            for e in ecols:
                                kx = df_cls.loc[df_cls[df_cls.columns[0]] == selected, e]
                                if not kx.empty:
                                    kx_value = kx.iloc[0]
                                    not_grouped_df.at[index, e] = kx_value
                                else:
                                    print(f"No data found for {selected} in column {e}")
                    df_for_cls = not_grouped_df.copy()
                            
            with s2.container(height=300):
                st.markdown('**Pisteytys**')
                use_cols = ['index','name'] + [type_col] + [area_col] + ecols

                edited_df = st.data_editor(
                                df_for_cls[use_cols],
                                hide_index=True,
                                #height=300,
                                #column_config={"Select": st.column_config.CheckboxColumn(required=True)},
                                #disabled=df_for_edit.columns,
                                use_container_width=True
                            )
            
            #prepare for calc
            for col in num_columns:
                edited_df[col] = pd.to_numeric(edited_df[col], errors='coerce')
            edited_df[area_col] = edited_df[area_col].astype(int)
            edited_df['kxAla'] = round(edited_df[num_columns].multiply(edited_df[area_col], axis=0).sum(axis=1),-1).astype(int)
            
            #VISUT
            st.markdown("---")
            col1,col2 = st.columns([2,1])
                
            if metodi == 'Ryhmiteltynä':
                with col1.container():
                    #sun
                    def sun_plot(df,path,values,color,hover):
                        fig = px.sunburst(df, path=path,
                                        values=values,
                                        color=color, hover_data=hover,
                                        color_continuous_scale='Greens',#'YlGn',
                                        #color_continuous_midpoint=np.average(df[color], weights=df[values]),
                                        height=400
                                        )
                        return fig
                    
                    path_cols = ['name',type_col]
                    value_col = area_col  # sectors
                    color_col = 'kxAla'
                    
                    #add non-green area
                    tot_ala = (3.14 * r*r) #hakualue
                    eAla = edited_df[area_col].sum()
                    rAla = tot_ala - eAla
                    rAla_row = {
                        'name': 'maankäyttö',
                        type_col: 'nan',
                        area_col: rAla
                        }
                    rAla_df = pd.DataFrame([rAla_row])
                    edited_df_plot = pd.concat([edited_df, rAla_df], ignore_index=True)

                    # sun plot
                    sun_fig = sun_plot(df=edited_df_plot.fillna(0), path=path_cols, values=value_col, color=color_col, hover=None)
                    st.plotly_chart(sun_fig, use_container_width=True, config = {'displayModeBar': False})
                    
            else:
                with col1.container():
                    #plot the map when not grouped...
                    gdf.reset_index(inplace=True)
                    gdf.rename(columns={'index': 'original_index'}, inplace=True)
                    edited_gdf = edited_df.merge(gdf[['original_index', 'geometry']], left_on='index', right_on='original_index', how='left')
                    edited_gdf.drop('original_index', axis=1, inplace=True)
                    edited_gdf = gpd.GeoDataFrame(edited_gdf)
                    
                    keep_cols = ['name', type_col, area_col,'kxAla','geometry'] + ecols
                    color_col = 'kxAla'
                    edited_on_map = utils.plot_landuse(edited_gdf[keep_cols],title=None,hover_name=type_col,col=color_col,zoom=15)
                    st.plotly_chart(edited_on_map, use_container_width=True, config = {'displayModeBar': False})
                            
            
            #for col2..
            with col2.container():
                
                #sum results
                kxAla = edited_df['kxAla'].sum()
                tot_ala = (3.14 * r*r) #hakualue
                eAla = edited_df[area_col].sum()
                arvo = round((eAla + kxAla)/tot_ala,2)
                base_line = 1000
                delta = -(base_line - arvo)
            
                latex_code = r"""
                            $
                            \frac{\sum eAla + \sum eAla*Kx}{\sum totAla}
                            $
                            """
                
                st.markdown("###")
                st.markdown("###")
                st.markdown("###")
                st.metric("Alueviherkerroin",value=arvo,delta=delta)
                st.markdown("###")
                st.markdown(latex_code,unsafe_allow_html=True)


with tab2:
    gdf_slu = None
    uploaded_file = st.file_uploader("Lataa suunnitelma", type=['zip'], key='slu')
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
            
            
#footer
st.markdown('---')
footer_title = '''
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/teemuja/arvo_dev/blob/main/LICENSE) 
'''
st.markdown(footer_title)