import streamlit as st 
import pandas as pd 
import plotly.express as px
import plotly.graph_objects as go
import random
import utils

#st.image("https://cdn.loppi.fi/uploads/sites/2/2023/04/vanhakoski.jpg?strip=all&lossy=1&ssl=1",use_column_width=True)
st.header("Arviontilogiikan kehitys")
hover_text = """
            **LUMO-kaava:** Luontotyypin peruspiste x ekologinen tila x luontotyypin pinta-ala = hm2  
            [hm2 = Habitaattineliömetrit=ekotehokas pinta-ala]   
            [ekologinen tila = laatupiste ko. luontotyypin indikaattoripisteiden keskiarvona, jos arvioitu]   
              
            **LUMO-arvo** = Habitaattineliömetrit / arvioidun alueen kokonaisala  
              
            **ESP-arvo** = ekologinen tila x luontotyypin pinta-ala / arvioidun alueen kokonaisala
            """
#malli = st.radio("Laskentakaava",['LUMO','ESP'], help=hover_text,horizontal=True)

@st.cache_data()
def load_table():
    df = utils.allas_csv_handler(download_csv="kaupunkiluontotyypit.csv")
    return df
df = load_table()

#get main_classes from table
main_class_name = 'PÄÄLUOKKA'
sec_class_name = 'KAUPUNKILUONTOTYYPPI'
main_classes = df[main_class_name].dropna().unique().tolist()

# Define variable types
lumo_var_types = ['Laatu1', 'Laatu2', 'Laatu3']
esp_var_types = ['ESP1', 'ESP2', 'ESP3']

#scoring func
def scoring_sliders(class_name, sec_classes):
    # Initialize dictionaries to store scores for all secondary classes
    class_scores_lumo = {}
    class_scores_esp = {}

    for sec_class in sec_classes:
        with st.expander(sec_class, expanded=False):
            # Slider generation function
            def score_sliders(score_name, class_name, sec_class, var_types, element_area):
                scores = {}
                base_score = st.slider(
                    f"{score_name} peruspiste", 
                    0.0, 1.0, step=0.1, 
                    key=f"{score_name}_{class_name}_{sec_class}_base"
                )
                
                scores[sec_class] = {}
                value_score = 0
                
                if st.toggle('Käytä laatukertoimia', key=f"{score_name}_{class_name}_{sec_class}_vars"):
                    for var in var_types:
                        slider_value = st.slider(
                            f"{var}", 0.0, 1.0, step=0.1, 
                            key=f"{score_name}_{class_name}_{sec_class}_{var}"
                        )
                        scores[sec_class][var] = slider_value
                        value_score += slider_value
                
                # Calculate scores based on area and sliders
                if element_area > 0:
                    scores[sec_class]['area'] = element_area
                    if value_score > 0:
                        scores[sec_class]['hm2'] = base_score * value_score / len(var_types) * element_area
                    else:
                        scores[sec_class]['hm2'] = base_score * 1 * element_area
                else:
                    scores[sec_class]['area'] = 0
                    scores[sec_class]['hm2'] = 0
                    
                return scores
            
            # Slider for area
            element_area = st.slider("Pinta-ala", 0, 10000, 0, step=1000, key=f"{class_name}_{sec_class}_area")
            
            # Columns for LUMO and ESP
            lumo_col, esp_col = st.columns(2)
            with lumo_col:
                lumo_scores = score_sliders(
                    score_name='LUMO',
                    class_name=class_name,
                    sec_class=sec_class,
                    var_types=lumo_var_types,
                    element_area=element_area
                )
                # Update LUMO scores dictionary
                class_scores_lumo.update(lumo_scores)

            with esp_col:
                esp_scores = score_sliders(
                    score_name='ESP',
                    class_name=class_name,
                    sec_class=sec_class,
                    var_types=esp_var_types,
                    element_area=element_area
                )
                # Update ESP scores dictionary
                class_scores_esp.update(esp_scores)

    return class_scores_lumo, class_scores_esp



# Generate dynamic tabs
tabs = st.tabs(main_classes)
all_lumo_scores = {}
all_esp_scores = {}
    
# Generate similar content dynamically for each tab for both lumo and esp
for tab, class_name in zip(tabs, main_classes):
    with tab:
        
        with st.container(border=True):
            st.markdown(f'**{class_name}**')
            sec_df = df[df[main_class_name] == class_name]
            sec_classes = sec_df[sec_class_name].unique().tolist()
            
            lumo_scores, esp_scores = scoring_sliders(class_name,sec_classes)
            
            all_lumo_scores[class_name] = lumo_scores
            all_esp_scores[class_name] = esp_scores

#func to gen score df
def gen_score_df(scores):
    score_rows = []
    for main_class, sec_scores in scores.items():
        for sec_class, vars_dict in sec_scores.items():
            for var, score in vars_dict.items():
                score_rows.append({
                    main_class_name: main_class,
                    sec_class_name: sec_class,
                    'indikaattori': var,
                    'ekotehokas_ala': round(score,0),
                    'kokonaisala': sec_scores[sec_class].get('area', 0)
                })
    scores_df = pd.DataFrame(score_rows)
    scores_df_out = scores_df[scores_df['indikaattori'] == "hm2"].drop(columns='indikaattori')
    return scores_df_out

# Generate a DataFrame with the scores FOR both lumo and esp
lumo_scores_df = gen_score_df(all_lumo_scores)
esp_scores_df = gen_score_df(all_esp_scores)

suns = st.container(border=True)

s1,s2 = st.columns(2)
tot_factor = s1.slider('Kokonaisalalle kerroin (Tarkastelualueen laajuus = x kertaa arvioidut alat)',1.0,2.0,1.3,step=0.1, key=f"tot_ala")
total_area = int(lumo_scores_df['kokonaisala'].sum() * tot_factor)
non_arvo_area = total_area - lumo_scores_df['kokonaisala'].sum()
# jotta ei-viheralueeksi arvioidun alueen saa piirakkaan mukaan 
# tulee sille antaa joku kerroin, jolla siitä tulee "habitaattihehtaari" =  alueen kontribuutio hha
non_arvo_factor = s2.slider('Ei-arvioitujen alueiden laatukerroinpotentiaali)',0.0,1.0,0.1,step=0.1, key=f"non_arvo_factor")
if non_arvo_factor > 0.0:                     #['arvioimaton alue', 'arvioimaton alue', 'ekotehokas_ala','kokonaisala']
    non_arvo_area_hha = non_arvo_area * non_arvo_factor
    lumo_scores_df.loc[len(lumo_scores_df)] = ['arvioimaton alue', 'arvioimaton alue', round(non_arvo_area_hha,0), round(non_arvo_area,0)]
    esp_scores_df.loc[len(esp_scores_df)] = ['arvioimaton alue', 'arvioimaton alue', round(non_arvo_area_hha,0), round(non_arvo_area,0)]

def score_plot(df,path,type):
    custom_colors = {
        main_classes[0]: 'darkgreen', 
        main_classes[1]: 'olivedrab',
        main_classes[2]: 'seagreen'
        }
    sun_fig = px.sunburst(df, path=path,
                    values='ekotehokas_ala',
                    title=type,
                    color=main_class_name,
                    color_discrete_map=custom_colors,
                    hover_name='ekotehokas_ala',
                    template='ggplot2',
                    height=400
                    )
    return sun_fig

with suns:
    col1,col2 = st.columns(2)
    with col1:
        lumo_fig = score_plot(lumo_scores_df,path=[main_class_name,sec_class_name],type='LUMO')
        st.plotly_chart(lumo_fig, key='lumo_plot')
        lumo_arvo = round(lumo_scores_df['ekotehokas_ala'].sum() / total_area,2)
        st.metric(f"Lumo-arvo",value=lumo_arvo)
    with col2:
        esp_fig = score_plot(esp_scores_df,path=[main_class_name,sec_class_name],type='ESP')
        st.plotly_chart(esp_fig, key='esp_plot')
        esp_arvo = round(esp_scores_df['ekotehokas_ala'].sum() / total_area,2)
        st.metric(f"ESP-arvo",value=esp_arvo)

with st.expander('Arvointitaulukko',expanded=False):
    lumo_df = lumo_scores_df.rename(columns={'ekotehokas_ala':'hha2'}).reset_index().fillna(0)
    esp_df = esp_scores_df.rename(columns={'ekotehokas_ala':'ESP_ala'}).drop(columns='kokonaisala').reset_index().fillna(0)
    my_scores = pd.concat([lumo_df,esp_df])[[main_class_name,sec_class_name,'kokonaisala','hha2','ESP_ala']].fillna(0)
    st.data_editor(my_scores)