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
            [ekologinen tila = laatupiste ko. luontotyypin indikaattoripisteiden keskiarvona]   
              
            **Alueviherkerroin** = Habitaattineliömetrit / arvioidun alueen kokonaisala  
              
            **ESP-kaava:** tbd..
            """
malli = st.radio("Laskentakaava",['LUMO','ESP'], help=hover_text,horizontal=True)

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
var_types = ['Laatu1', 'Laatu2', 'Laatu3']

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
                element_area = st.slider("Pinta-ala", 0, 10000, 0, step=1000, key=f"{sec_class}_area")
                base_score = st.slider("Peruspiste", 0.0, 1.0, step=0.1, key=f"{sec_class}_base")
                st.markdown("---")
                class_scores[sec_class] = {}
                total_score = 1
                value_score = 0
                for var in var_types:
                    slider_value = st.slider(f"{var}", 0.0, 1.0, step=0.1, key=f"{sec_class}_{var}")
                    class_scores[sec_class][var] = slider_value
                    value_score += slider_value
                
                #arvo calc
                if malli == "LUMO":
                    if element_area > 0:
                        class_scores[sec_class]['area'] = element_area
                        class_scores[sec_class]['hm2'] = base_score * value_score/len(var_types) * element_area
                    else:
                        class_scores[sec_class]['area'] = 0
                        class_scores[sec_class]['hm2'] = 0
                elif malli == "ESP":
                    if element_area > 0:
                        class_scores[sec_class]['area'] = 1
                        class_scores[sec_class]['hm2'] = 1
                    else:
                        class_scores[sec_class]['area'] = 0
                        class_scores[sec_class]['Arvo'] = 0
                else:
                    class_scores[sec_class]['area'] = round(random.uniform(1000,5000),1000)
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
                'hm2': score,
                'm2': sec_scores[sec_class].get('area', 0)
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
            title='hm2',
            tickvals=[df[color].min(),df[color].max()],
            ticktext=['matala','korkea']
        )
    )
    return fig

with st.container(border=True):
    col1,col2 = st.columns([2,1])
    with col1:
        sun_fig = sun_plot(df=scores_df,
                        path=[main_class_name,sec_class_name],
                        values='hm2', color='Osa-alue',
                        hover=main_class_name
                        )
        st.plotly_chart(sun_fig) #sun_burst_plot(main_classes,sec_class_name))

    with col2:
        #sum results
        st.markdown("###")
        st.markdown("###")
        tot_factor = st.slider('Kokonaisalalle kerroin (x kertaa arvioidut alat)',1.0,2.0,1.5,step=0.1)
        total_area = scores_df['m2'].sum() * tot_factor
        arvo = round(scores_df['hm2'].sum() / total_area,2)
        st.metric("Alueviherkerroin",value=arvo)
        st.caption("..")
    