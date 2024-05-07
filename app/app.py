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
    latlon,loc = utils.getlatlon(add)
    if loc.quality != 1:
        st.warning('Anna tarkempi osoite')
        st.stop()
        
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
                area_col = "area"
                type_col="type"
                df_for_edit = gdf.drop(columns='geometry')
                #plots
                bar_osm = utils.plot_area_bars(gdf)
                st.plotly_chart(bar_osm, use_container_width=True, config = {'displayModeBar': False})
                map_osm = utils.plot_landuse(gdf,name=name,col=type_col,zoom=15)
                st.plotly_chart(map_osm, use_container_width=True, config = {'displayModeBar': False})
            except TimeoutError:
                st.warning('Ei yhteyttä dataan')
                st.stop()
    elif sorsa == 'HSY':
        #with st.expander('HSY avoin data tasot'):
        #    utils.print_wfs_layers()
        if add:
            try:
                gdf = utils.get_hsy_maanpeite(latlon=latlon,radius=r)
                area_col = "p_ala_m2"
                type_col = "kuvaus"
                df_for_edit = gdf.drop(columns='geometry')
            except TimeoutError:
                st.warning('Ei yhteyttä dataan')
                st.stop()

        if gdf is not None and len(gdf) > 0:
            name = f"Maanpeite {add}"
            colors_hsy = {
                "Muu avoin matala kasvillisuus":"DarkKhaki",
                "puusto, 2 m - 10 m":"DarkSeaGreen",
                "puusto, 10 m - 15 m":"OliveDrab",
                "puusto, 15 m - 20 m":"DarkOliveGreen",
                "Puusto yli 20 m":"DarkGreen"
                }
            bar_hsy = utils.plot_area_bars(gdf,x='p_ala_m2',y='kuvaus',color='kuvaus',color_map=colors_hsy)
            st.plotly_chart(bar_hsy, use_container_width=True, config = {'displayModeBar': False})
            map_hsy = utils.plot_landuse(gdf,name=name,col=type_col,color_map=colors_hsy,zoom=15)
            st.plotly_chart(map_hsy, use_container_width=True, config = {'displayModeBar': False})
        else:
            st.warning('Ei dataa osoitteessa')
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

    if gdf is not None:
        with st.expander('Viherkerroinlaskenta'):
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_cls = conn.read()
            #st.data_editor(df_cls)
            elist = df_cls['ELINYMPÄRISTÖ'].tolist()
            
            def gen_selectors(df, elist, type_col):
                selections = {}
                areas = df[type_col].tolist()
                key = 0
                for area in areas:
                    key += 1
                    selected_option = st.selectbox(area, options=elist, key=f"{area}{key}")
                    selections[area] = selected_option
                return selections
            
            s1,s2 = st.columns([1,2])
            with s1:
                grouped_df = df_for_edit.groupby(by=type_col, group_keys=True).sum().reset_index()
                grouped_df[area_col] = round(grouped_df[area_col],-1)
                
                selections = gen_selectors(grouped_df, elist, type_col)
                
                ecols = df_cls.columns.tolist()[1:]
                for type_col, selected in selections.items():
                    for e in ecols:
                        # Get the value from df_cls based on the selection
                        kx = df_cls.loc[df_cls['ELINYMPÄRISTÖ'] == selected, e]
                        if not kx.empty:
                            # Assuming 'kx' could be a series with a single value; we use `.iloc[0]` to get the scalar
                            kx_value = kx.iloc[0]
                            # Update grouped_df where 'TypeCol' matches 'type_col'
                            # Here we assume 'type_col' refers to values that correspond to 'TypeCol' in 'grouped_df'
                            grouped_df.loc[grouped_df['type'] == type_col, e] = kx_value
                        else:
                            print(f"No data found for {selected} in column {e}")
            s2.markdown('###')
            edited_df = s2.data_editor(
                            grouped_df,
                            hide_index=True,
                            height=300,
                            #column_config={"Select": st.column_config.CheckboxColumn(required=True)},
                            #disabled=df_for_edit.columns,
                            use_container_width=True
                        )
            st.markdown('---')
            
            #calc
            non_sel_columns = [col for col in edited_df.columns if 'sel' not in col]
            sel_columns = [col for col in edited_df.columns if 'sel' in col]
            
            for col in non_sel_columns:
                edited_df[col] = pd.to_numeric(edited_df[col], errors='coerce')
            edited_df['kxAla'] = edited_df[non_sel_columns].multiply(edited_df[area_col], axis=0).sum(axis=1)
  
            #plotter
            def sun_plot(df,path,values,color,hover):
                fig = px.sunburst(df, path=path, values=values,
                    color=color, hover_data=hover,
                    color_continuous_scale='RdBu',
                    color_continuous_midpoint=np.average(df[color], weights=df[values]))
                return fig
            path_cols = sel_columns   # make sure type_col is defined in your context
            value_col = 'kxAla'  # This column is used for the sizes of sectors
            color_col = non_sel_columns[0]  # Example: use the first non-sel column for coloring

            # Call the plotting function
            sun_fig = sun_plot(df=edited_df, path=path_cols, values=value_col, color=color_col, hover=non_sel_columns)

            kxAla = edited_df['kxAla'].sum()
            tot_ala = (3.14 * r*r) #hakualue
            eAla = edited_df[area_col].sum()
            arvo = round((eAla + kxAla)/tot_ala,2)
            
            #results
            s1,s2 = st.columns([1,2])
            s1.plotly_chart(sun_fig, use_container_width=True, config = {'displayModeBar': False})
            s2.markdown('###')
            s2.markdown('###')
            s2.markdown('###')
            s2.markdown('###')
            latex_code = r"""
                        $
                        \frac{\sum eAla + \sum eAla*Kx}{\sum totAla}
                        $
                        """
            s2.metric("AVK",value=arvo)
            s2.markdown(latex_code,unsafe_allow_html=True)


with tab2:
    gdf3 = None
    uploaded_file = st.file_uploader("Lataa suunnitelma", type=['zip'], key='slu')
    if uploaded_file:
        try:
            gdf3 = utils.extract_shapefiles_from_zip(uploaded_file,'Polygon')
            if 'area' not in gdf3.columns or gdf3['area'].isna().all():
                utm = gdf3.estimate_utm_crs()
                gdf3['area'] = round(gdf3.to_crs(utm).area,-1)
            else:
                pass
        except Exception as err_bu:
            print(f"Data error: {err_bu}")
            st.warning('Tarkista data')
            
    if gdf3 is not None:
        #if 'x' not in gdf.columns or gdf['x'].isna().all():
        #    gdf['x'] = np.round(np.random.uniform(0, 1.5, size=len(gdf)), 1)
            
        if 'name' not in gdf3.columns or gdf3['name'].isna().all():
            gdf3['name'] = "Lorem area.."
        if 'K_selite' not in gdf3.columns or gdf3['K_selite'].isna().all():
            gdf3['K_selite'] = "Ipsum biotoop.."
            
        cols = ['name','area','K_selite','x']
        df = st.data_editor(gdf3[cols], hide_index=True, height=200, use_container_width=True)
        df['Kx'] = df['area'] * df['x']
        gdf3['Kx'] = df['Kx']
        
        col = "Kx"
        fig_slu = utils.plot_landuse(gdf3,name='Testislu',hover_name='name',col=col, zoom=15)
        st.plotly_chart(fig_slu, use_container_width=True, config = {'displayModeBar': False})
        avk = round((df.loc[df['x'].notna()]['area'].sum() + df['Kx'].sum()) / df['area'].sum(),2)
        st.metric('Hankeviherkerroin',value=avk)
            
#footer
st.markdown('---')
footer_title = '''
[![MIT license](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/teemuja/arvo_dev/blob/main/LICENSE) 
'''
st.markdown(footer_title)