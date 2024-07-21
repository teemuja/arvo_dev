import streamlit as st
import utils
import pandas as pd
import time

st.subheader("Kehitysideat")

# https://github.com/streamlit/gsheets-connection/blob/main/examples/pages/Service_Account_Example.py
fb_text = """
    Demoja testailemalla syntyviä huomioita ja ideoita voit kirjoittaa alla olevaan lomakkeeseen 
    ja lähettää ne hanketiimille.
    """
st.markdown(fb_text)

with st.status('Aiemmat ideat & huomiot'):
    feedback_file = "data/feedback.csv"
    try:
        #df_fb = utils.feedback_editor(feedback_file = "data/feedback.csv")
        df_fb = pd.read_csv(feedback_file)
        for row in df_fb.itertuples():
            st.write(f"- {row.ideat} ")
            st.markdown("###")
    except:
        st.warning('Ei yhteyttä tietokantaan.')
    
#form
with st.form(key="feedback_form",clear_on_submit=True):
    user_idea = st.text_area(label="Uusi idea/huomio",max_chars=200)
    submit_button = st.form_submit_button(label="Lähetä")
    if submit_button:
        if not user_idea:
            st.stop()
        else:
            new_idea = pd.DataFrame(
                [
                    {
                        "ideat": user_idea
                    }
                ]
            )
            updated_df = pd.concat([df_fb, new_idea], ignore_index=True)
            updated_df.to_csv(feedback_file)
            st.success("Idea tallennettu!")
            time.sleep(2)
            st.rerun()
