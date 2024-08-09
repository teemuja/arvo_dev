import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
import random
import plotly.express as px
import utils

def scoring_table(gdf=None,source=None,name_col=None,area_col=None,type_col=None,r=250,classification_file=None):

    #make persistent index
    gdf.reset_index(inplace=True)
    gdf.rename(columns={'index':'orig_index'}, inplace=True)
    
    #luokitukset
    if classification_file is not None:
        try:
            df_cls = utils.allas_csv_handler(download_csv=classification_file)
            df_cls.columns = df_cls.columns.str.lower()
            #elinymp_col = 'elinympäristöt'
            elist = df_cls[df_cls.columns[0]].tolist()
        except Exception as e:
            st.error(f"Ei yhteyttä luokittelutiedostoon: {e}")
            st.stop()
    
        ecols = df_cls.columns.tolist()[1:] #remove first col
        kx_columns = [col for col in ecols if 'sel' not in col]
        num_columns = [col for col in ecols if 'sel' not in col] + [area_col]
        str_columns = [col for col in ecols if 'sel' in col] + [type_col]

    #luokitteltava df
    df_for_edit = gdf.drop(columns='geometry')

    #selectors
    s1,s2 = st.columns([1,2])
    metodi = s1.radio('Määritä elinympäristöjä..',['Ryhmiteltynä','Yksittäin'],horizontal=True)
    minarea = s2.slider('Min. pinta-ala elinympäristölle (m2)',0,1000,200,100)
    df_for_edit = df_for_edit[df_for_edit[area_col] >= minarea]

    s1,s2 = st.columns([1,2])
    #luokitteluloota
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
                grouped_df.at[ind, name_col] = random.choice(random_names)
                
            selections = {}
            for type_area in grouped_df[type_col].unique():
                key += 1
                selectbox_label = type_area
                # Determine default index for the selectbox
                try:
                    default_dict = osm_dict if source == "OSM" else hsy_dict
                    default_index = elist.index(default_dict.get(type_area, elist[0]))
                except ValueError:
                    default_index = 0

                # Use the default index in the selectbox
                selected_option = st.selectbox(selectbox_label, options=elist, index=default_index, key=f"{type_area}")
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
                            
            df_for_editor = grouped_df.copy()

        else:
            #..and same for not_grouped..
            not_grouped_df = df_for_edit.copy()
            index_values = not_grouped_df.index
            if name_col not in not_grouped_df.columns:
                random_names = ['Puutiaispuistikko','Perhosniitty','Hiilinielumetsä']
                for ind, row in not_grouped_df.iterrows():
                    not_grouped_df.at[ind, name_col] = random.choice(random_names)

            not_grouped_df.insert(0, 'index', index_values)
            
            selections = {}
            for index, type_area in not_grouped_df[type_col].items():
                selectbox_label = f"{type_area}, Index={index}"
                
                #gen defaults..
                if source == "OSM":
                    try:
                        default_index = elist.index(osm_dict[type_area])
                    except:
                        default_index = 0
                elif source == "HSY":
                    try:
                        default_index = elist.index(hsy_dict[type_area])
                    except:
                        default_index = 0
                else:
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
                            
            df_for_editor = not_grouped_df.copy()
            
    cols_for_editor = [name_col, type_col, area_col] + ecols + ["orig_index"]

    #pisteytyseditori
    with s2.container(height=300):
        st.markdown('**Pisteytys**')
        myeditor = st.empty()

    #plotit
    def plot_editor(df_for_editor,gdf,cols_for_editor):
        
        #editor
        with myeditor:
            edited_df = st.data_editor(
                            df_for_editor[cols_for_editor],
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
        edited_df['kxAla'] = sum(edited_df[col] * edited_df[area_col] for col in kx_columns)

        #add non-green area
        tot_ala = (3.14 * r*r) #hakualue
        eAla = edited_df[area_col].sum()
        rAla = tot_ala - eAla
        rAla_row = {
            'landuse': 'maankäyttö',
            type_col: 'kadut ja rakennukset',
            area_col: rAla
            }
        rAla_df = pd.DataFrame([rAla_row])
        edited_df_plot = pd.concat([edited_df, rAla_df], ignore_index=True)
        edited_df_plot['landuse'] = edited_df_plot['landuse'].fillna('viherrakenne')
        edited_df_plot = edited_df_plot.fillna(0)
        
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
                                    labels={color:'Arvo'},
                                    #color_continuous_midpoint=np.average(df[color], weights=df[values]),
                                    height=400
                                    )
                    fig.update_layout(
                        coloraxis_colorbar=dict(
                            title='Arvo',
                            tickvals=[df[color].min(),df[color].max()],
                            ticktext=['matala','korkea']
                        )
                    )
                    return fig
                
                # sun plot
                path_cols = ['landuse',type_col]
                value_col = area_col  # sectors
                color_col = 'kxAla'
                sun_fig = sun_plot(df=edited_df_plot, path=path_cols, values=value_col, color=color_col, hover=None)
                st.plotly_chart(sun_fig, use_container_width=True, config = {'displayModeBar': False})
                
        else:
            with col1.container():
                #merge to gdf for map plot
                edited_merged = gdf.merge(edited_df_plot, on='orig_index')
                edited_merged.rename(columns={f'{name_col}_y':name_col,
                                            f'{type_col}_y':type_col,
                                            f'{area_col}_y':area_col},
                                                inplace=True
                                            )
                
                keep_cols = [name_col, type_col, area_col,'kxAla','geometry'] + ecols
                color_col = 'kxAla'
                edited_on_map = utils.plot_landuse(edited_merged[keep_cols],title=None,
                                                    hover_name=type_col,
                                                    hover_data=name_col,
                                                    col=color_col,
                                                    zoom=15,
                                                    )
                st.plotly_chart(edited_on_map, use_container_width=True, config = {'displayModeBar': False})
                        
        #..and for col2..
        with col2.container():
            
            #sum results
            kxAla = round(edited_df_plot['kxAla'].sum(),-1)
            tot_ala = (3.14 * r * r) #hakualue
            eAla = edited_df_plot.loc[edited_df_plot['landuse'] != 'maankäyttö'][area_col].sum()
            #st.text(f"tot_ala={tot_ala},hh={kxAla},elinympala={eAla}")
            
            arvo = round((eAla + kxAla)/tot_ala,2)
            base_line = 1
            delta = round(-(base_line - arvo),2)
        
            latex_code = r"""
                        $
                        \frac{\sum eAla + \sum eAla*Kx}{\sum totAla}
                        $
                        """
            st.markdown("###")
            st.markdown("###")
            st.metric("Alueviherkerroin",value=arvo,delta=delta)
            st.markdown(latex_code,unsafe_allow_html=True)
            eselite = """
            eAla = ekotehokkuutta lisäävän osa-alueen ala  
            Kx = osa-alueen elinympäristökerroin  
            totAla = tarkasteluala
            """
            st.caption(eselite)
            
        return edited_df

    #plot the editor
    edited_df_for_save = plot_editor(df_for_editor,gdf,cols_for_editor=cols_for_editor)

    #save mod
    if metodi == "Yksittäin":
        #add geom values from gdf to scoring table
        merged_df = edited_df_for_save.merge(gdf[['orig_index', 'geometry']], on='orig_index', how='left')
        result_gdf = gpd.GeoDataFrame(merged_df, geometry='geometry')
        result_gdf['wkt'] = result_gdf['geometry'].apply(lambda x: x.wkt)
        result_gdf.drop(columns='geometry', inplace=True)
        result_gdf.rename(columns={type_col:'elinymp_luokka'},inplace=True)
        export_cols = ['elinymp_luokka', 'nimi', area_col, 'kxAla', 'lumo', 'lumo_sel', 'melu', 'melu_sel', 'hule', 'hule_sel', 'ilma', 'ilma_sel', 'pöly', 'pöly_sel', 'terv', 'terv_sel', 'wkt']

        st.markdown("---")
        with st.form('Save',clear_on_submit=True):
            name_of_scoring = st.text_input('Nimeä tarkastelu jos haluat tallentaa sen',max_chars=20)
            saveit = st.form_submit_button('Talenna')
            if saveit and name_of_scoring is not None and len(name_of_scoring) > 2:
                file_name_for_save = f"ANA_{name_of_scoring}"
                if utils.allas_csv_handler(upload_df=result_gdf[export_cols],upload_filename=file_name_for_save):
                    st.success('Tallennettu!')


def scoring_table_for_plans(gdf=None,name_col=None,area_col=None,type_col=None,expl_col=None,gfa_col=None,classification_file='classification_landuse.csv'):

    #make persistent index
    gdf.reset_index(inplace=True)
    gdf.rename(columns={'index':'orig_index'}, inplace=True)
    
    #get classifications
    if classification_file is not None:
        try:
            df_cls = utils.allas_csv_handler(download_csv=classification_file)
            df_cls.columns = df_cls.columns.str.lower()
            elist = df_cls[df_cls.columns[0]].tolist()
        except Exception as e:
            st.error(f"Ei yhteyttä luokittelutiedostoon: {e}")
            st.stop()
    
        ecols = df_cls.columns.tolist()[1:] #remove first col
        kx_columns = [col for col in ecols if 'sel' not in col]
        num_columns = [col for col in ecols if 'sel' not in col] + [area_col]

    #define df to edit without geom
    df_for_edit = gdf.drop(columns='geometry')
    
    #add df to session_state
    if "df_updated" not in st.session_state:
        st.session_state.df_updated = df_for_edit
    
    # scoring table and map
    with st.expander('Viherkerroinlaskenta',expanded=True):
        map_container = st.empty()
        map_selector = st.empty()
        
        with st.form('assesment_form'):
            c1,c2 = st.columns([1,2])
            with c1.container(height=300):
                st.markdown('Elinympäristöluokitus')

                #selector to assign defaults to used zoning codes
                grouped_df = df_for_edit.groupby(by=type_col, group_keys=True).sum().reset_index()
                key = 0
                selections = {}                        
                index_values = range(len(grouped_df))
                grouped_df.insert(0, 'index', index_values)
                
                #gen selectbox for each type in the plan
                for type_area in grouped_df[type_col].unique():
                    key += 1
                    selectbox_label = type_area
                    default_index = 0

                    # Use the default index in the selectbox
                    selected_option = st.selectbox(selectbox_label, options=elist, index=default_index, key=f"{type_area}")
                    selections[type_area] = selected_option

                # if elist cols not in df: Update df_for_edit based on user selections and transfer data from df_cls
                all_exist = all(col in df_for_edit.columns for col in elist)
                if all_exist:
                    df_for_editor = df_for_edit.fillna(0)
                else:
                    for ind, row in df_for_edit.iterrows():
                        original_type_area = row[type_col]
                        selected = selections.get(original_type_area)
                        if selected:
                            df_for_edit.at[ind, type_col] = selected
                            # get related data from df_cls to the row
                            for e in ecols:
                                if e not in df_for_edit.columns:
                                    df_for_edit[e] = pd.NA  # ..if it doesn't exist
                                kx = df_cls.loc[df_cls[df_cls.columns[0]] == selected, e]
                                if not kx.empty:
                                    kx_value = kx.iloc[0]
                                    df_for_edit.at[ind, e] = kx_value        
                    df_for_editor = df_for_edit.fillna(0)
                    
                #calc FAR col values
                df_for_editor['e'] = round(df_for_editor[gfa_col].astype(int) / df_for_editor[area_col].astype(int),2)

            with c2.container(height=300):
                st.markdown('Arviointitaulukko')
                cols_for_editor = [name_col,type_col,expl_col] + ['e'] + ecols + [area_col] + ["orig_index"]
                edited_df = st.data_editor(
                                df_for_editor[cols_for_editor],
                                column_config={
                                                type_col: st.column_config.SelectboxColumn(
                                                    "Elinympäristöluokka",
                                                    help="Valitse sopivin tuplaklikkaamalla",
                                                    width="medium",
                                                    options=elist,
                                                    required=True,
                                                ),
                                                'area': None,
                                                'orig_index': None
                                            },
                                hide_index=True,
                                use_container_width=True
                                )
                
                #prepare for calc
                for col in kx_columns:
                    edited_df[col] = pd.to_numeric(edited_df[col], errors='coerce')
                edited_df['kxAla'] = sum(edited_df[col] * edited_df[area_col] for col in kx_columns)

                #area sums
                utm = gdf.estimate_utm_crs()
                tot_ala = int(round(gdf.to_crs(utm).unary_union.convex_hull.area,-1))
                eAla = edited_df[area_col].sum()
                
                #define upper class for sunburst
                edited_df['landuse'] = None
                edited_df.loc[edited_df[type_col].isin(['liikennealue','kortteli']),'landuse'] = 'rakennettuymp.'
                edited_df['landuse'] = edited_df['landuse'].fillna('viherrakenne')
                edited_df_updated = edited_df.fillna(0) #..for sunburst plot
            
            baseline_value = c1.number_input('Aleen lähtötasoarvo',min_value=0,max_value=10,value=5)
            update_df = st.form_submit_button('Päivitä luokitus ja graafit')
        
        #update
        if update_df:
            st.session_state.df_updated = edited_df_updated
        
        #graafit
        c1b,c2b = st.columns([2,1])
        with c1b.container():
            #sun
            def sun_plot(df,path,values,color,hover):
                fig = px.sunburst(df, path=path,
                                values=values,
                                color=color, hover_data=hover,
                                color_continuous_scale='Greens',#'YlGn',
                                labels={color:'Arvo'},
                                #color_continuous_midpoint=np.average(df[color], weights=df[values]),
                                height=400
                                )
                fig.update_layout(
                    coloraxis_colorbar=dict(
                        title='Arvo',
                        tickvals=[df[color].min(),df[color].max()],
                        ticktext=['matala','korkea']
                    )
                )
                return fig
            
            # sun plot
            path_cols = ['landuse',type_col]
            value_col = area_col  # sectors
            color_col = 'kxAla'
            sun_fig = sun_plot(df=edited_df_updated, path=path_cols, values=value_col, color=color_col, hover=None)
            st.plotly_chart(sun_fig, use_container_width=True, config = {'displayModeBar': False})
            
        with c2b.container():
            kxAla = round(edited_df_updated['kxAla'].sum(),-1)
            eAla = edited_df_updated.loc[edited_df_updated['landuse'] != 'liikenneinfra'][area_col].sum()
            arvo = round((eAla + kxAla)/tot_ala,2)
            delta = round(-(baseline_value - arvo),2)
            latex_code = r"""
                        $
                        \frac{\sum eAla + \sum eAla*Kx}{\sum totAla}
                        $
                        """
            st.markdown("###")
            st.markdown("###")
            st.metric("Alueviherkerroinennuste",value=arvo,delta=delta)
            st.markdown(latex_code,unsafe_allow_html=True)
            eselite = """
            eAla = ekotehokkuutta lisäävän osa-alueen ala  
            Kx = osa-alueen elinympäristökerroin  
            totAla = tarkasteluala
            """
            st.caption(eselite)
    
    with map_selector:
        maptype = st.radio('',['Elinymp.luokka','vk-ennuste'],horizontal=True)
        if maptype == 'Elinymp.luokka':
            color_col = type_col
        else:
            color_col = 'kxAla'
            
    with map_container:
        
        #merge to gdf for map plot
        edited_gdf = gdf.merge(edited_df_updated, on='orig_index')
        
        for col in edited_gdf.columns:
            if col.endswith('_x'):
                original_col = col[:-2]
                y_col = original_col + '_y'
                if y_col in edited_gdf.columns:
                    edited_gdf[original_col] = edited_gdf[y_col]
                    edited_gdf.drop(columns=[col, y_col], inplace=True)
                else:
                    edited_gdf.rename(columns={col: original_col}, inplace=True)

        #st.table(edited_gdf.drop(columns='geometry'))

        edited_on_map = utils.plot_landuse(edited_gdf,title="Suunnitelma",
                                            name_col=name_col,
                                            hover_name=name_col,
                                            hover_data=[type_col,expl_col],
                                            col=color_col,
                                            zoom=15,
                                            height=300
                                            )
        st.plotly_chart(edited_on_map, use_container_width=True, config = {'displayModeBar': False})

    #save form
    edited_gdf['wkt'] = edited_gdf['geometry'].apply(lambda x: x.wkt)
    edited_gdf.drop(columns='geometry', inplace=True)
    
    with st.form('Save',clear_on_submit=True):
        edited_gdf.rename(columns={type_col:'elinymp_luokka'},inplace=True)
        export_cols = ['elinymp_luokka', 'nimi', 'kuvaus', 'e', 'kxAla', 'lumo', 'lumo_sel', 'melu', 'melu_sel', 'hule', 'hule_sel', 'ilma', 'ilma_sel', 'pöly', 'pöly_sel', 'terv', 'terv_sel', 'wkt']
        #st.dataframe(edited_gdf[export_cols])
            
        name_of_scoring = st.text_input('Nimeä tarkastelu jos haluat tallentaa sen',max_chars=20)
        saveit = st.form_submit_button('Talenna')
        if saveit and name_of_scoring is not None and len(name_of_scoring) > 2:
            file_name_for_save = f"ANA_{name_of_scoring}"
            if utils.allas_csv_handler(upload_df=edited_gdf[export_cols],upload_filename=file_name_for_save):
                st.success('Tallennettu!')
                    

def ana_score_plot(gdf_ana,name_col,area_col,type_col):
    
    utm = gdf_ana.estimate_utm_crs()
    tot_ala = round(gdf_ana.to_crs(utm).unary_union.convex_hull.area,0)
    
    color_col = 'kxAla'
    edited_on_map = utils.plot_landuse(gdf_ana,title=None,
                                        name_col=name_col,
                                        hover_name=name_col,
                                        hover_data=type_col,
                                        col=color_col,
                                        zoom=15,
                                        )
    st.plotly_chart(edited_on_map, use_container_width=True, config = {'displayModeBar': False})
    
    #graafit
    df_ana = gdf_ana.drop(columns='geometry')
    
    #prepare for sunburst
    df_ana['landuse'] = None
    df_ana.loc[df_ana[type_col].isin(['liikennealue','kortteli']),'landuse'] = 'rakennettuymp.'
    df_ana['landuse'] = df_ana['landuse'].fillna('viherrakenne')
    df_ana = df_ana.fillna(0) #..for sunburst plot
    
    #st.table(df_ana)
    
    c1b,c2b = st.columns([2,1])
    with c1b.container():
        #sun
        def sun_plot(df,path,values,color,hover):
            fig = px.sunburst(df, path=path,
                            values=values,
                            color=color, hover_data=hover,
                            color_continuous_scale='Greens',#'YlGn',
                            labels={color:'Arvo'},
                            #color_continuous_midpoint=np.average(df[color], weights=df[values]),
                            height=400
                            )
            fig.update_layout(
                coloraxis_colorbar=dict(
                    title='Arvo',
                    tickvals=[df[color].min(),df[color].max()],
                    ticktext=['matala','korkea']
                )
            )
            return fig
        
        # sun plot
        path_cols = ['landuse',type_col]
        value_col = 'area'  # sectors
        color_col = 'kxAla'
        #st.text(df_ana.dtypes)
        #st.stop()
        sun_fig = sun_plot(df=df_ana, path=path_cols, values=value_col, color=color_col, hover=None)
        st.plotly_chart(sun_fig, use_container_width=True, config = {'displayModeBar': False})
        
    with c2b.container():
        kxAla = round(df_ana['kxAla'].sum(),-1)
        eAla = df_ana.loc[df_ana['landuse'] != 'liikenneinfra'][area_col].sum()
        arvo = round((eAla + kxAla)/tot_ala,2)
        latex_code = r"""
                    $
                    \frac{\sum eAla + \sum eAla*Kx}{\sum totAla}
                    $
                    """
        st.markdown("###")
        st.markdown("###")
        st.metric("Alueviherkerroinennuste",value=arvo)
        st.markdown(latex_code,unsafe_allow_html=True)
        eselite = """
        eAla = ekotehokkuutta lisäävän osa-alueen ala  
        Kx = osa-alueen elinympäristökerroin  
        totAla = tarkasteluala
        """
        st.caption(eselite)
            
