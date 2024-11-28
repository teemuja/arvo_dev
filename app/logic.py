import streamlit as st 
import pandas as pd 
import plotly.express as px
import plotly.graph_objects as go
import random
import utils

#st.image("https://cdn.loppi.fi/uploads/sites/2/2023/04/vanhakoski.jpg?strip=all&lossy=1&ssl=1",use_column_width=True)
st.header("Arviontilogiikan kehitys")
hover_text = """
            **K1:** kaikki alueet + osa-alue * laatukerroin / kokonaispinta-ala    
            **K2:** osa-alue * laatukerroin / kokonaispinta-ala
            """
malli = st.radio("Laskentakaava",['K1','K2'], help=hover_text,horizontal=True)

@st.cache_data()
def load_table():
    df = utils.allas_csv_handler(download_csv="kaupunkiluontotyypit.csv")
    return df
df = load_table()

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame() #({mc:0},index=['Arvo']).T
    
main_class_name = 'PÄÄLUOKKA'
sec_class_name = 'KAUPUNKILUONTOTYYPPI'
main_classes = df[main_class_name].dropna().unique().tolist()



# Define variable types
var_types = ['Peruspiste', 'Lumolaatu', 'ESP_ilmasto', 'ESP_hyvinvointi', 'ESP_terveys']

# Get unique main classes
main_classes = df[main_class_name].dropna().unique().tolist()

# Generate dynamic tabs
tabs = st.tabs(main_classes)

# Dictionary to store scores
scores = {}

# Generate similar content dynamically for each tab
for tab, class_name in zip(tabs, main_classes):
    with tab:
        
        class_scores = {}

        # Filter secondary classes for the current main class
        sec_df = df[df[main_class_name] == class_name]
        sec_classes = sec_df[sec_class_name].unique().tolist()

        # Create sliders for each secondary class and variable type
        for sec_class in sec_classes:
            with st.expander(sec_class,expanded=False):
                area_value = st.slider("Pinta-ala", 0, 10000, 0, step=1000, key=f"{sec_class}_area")
                class_scores[sec_class] = {}
                total_score = 1
                for var in var_types:
                    slider_value = st.slider(f"{var}", 0.0, 1.0, step=0.1, key=f"{sec_class}_{var}")
                    class_scores[sec_class][var] = slider_value
                    total_score *= slider_value
                
                #arvo calc
                if malli == "K1":
                    if area_value > 0:
                        tot_value = area_value * 1.3 #total area 30% larger than evaluated areas together
                        class_scores[sec_class]['Arvo'] = round((tot_value + (total_score * area_value)) / tot_value,1)
                    else:
                        class_scores[sec_class]['Arvo'] = 0
                elif malli == "K2":
                    if area_value > 0:
                        class_scores[sec_class]['Arvo'] = round((total_score * area_value) / area_value,2)
                    else:
                        class_scores[sec_class]['Arvo'] = 0
                else:
                    class_scores[sec_class]['Arvo'] = round(random.uniform(0.1,0.9),2)
                

        # Save scores for the main class
        scores[class_name] = class_scores

# Generate a DataFrame with the scores
score_rows = []
for main_class, sec_scores in scores.items():
    for sec_class, vars_dict in sec_scores.items():
        for var, score in vars_dict.items():
            score_rows.append({
                main_class_name: main_class,
                sec_class_name: sec_class,
                'Osa-alue': var,
                'Arvo': score
            })
scores_df = pd.DataFrame(score_rows)



def sun_plot(df,path,values,color,hover):
    custom_colors = {
        main_classes[0]: 'darkgreen', 
        main_classes[1]: 'olivedrab',
        main_classes[2]: 'seagreen'
        }
    fig = px.sunburst(df, path=path,
                    values=values,
                    title="Jakautuuko osa-alueiden kontribuutio arvoon uskottavasti?",
                    color=main_class_name,
                    color_discrete_map=custom_colors,
                    hover_name=hover,
                    template='ggplot2',
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


col1,col2 = st.columns([2,1])

with col1:
    sun_fig = sun_plot(df=scores_df,
                    path=[main_class_name,sec_class_name],
                    values='Arvo', color='Osa-alue',
                    hover=main_class_name
                    )
    st.plotly_chart(sun_fig) #sun_burst_plot(main_classes,sec_class_name))

with col2:
    #sum results
    st.markdown("###")
    st.markdown("###")
    scored_areas_df = scores_df[scores_df['Arvo'] != 0]
    arvo = round(scored_areas_df['Arvo'].mean(),2)
    st.metric("Alueviherkerroin",value=arvo)
    st.caption("Arvioitujen osa-alueiden keskiarvona")
    