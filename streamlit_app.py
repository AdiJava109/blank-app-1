import streamlit as st
from pipeline.begin_data_pipeline import run_pipline
from pipeline.adv_data_pipeline import run_adv_pipeline

st.title("🎈 Linguage")
st.write(
    "Welcome to Linguage! This is a beta version of my app!"
)
target_word = st.text_input("enter target word here")
text_input = st.text_input("enter text here")
beginner_btn = st.button("Beginner level translation")
adv_btn = st.button("Advanced level translation")
if beginner_btn:
    output = run_pipline(text_input, target_word)
    target_words = [tw.strip().lower() for tw in target_word.split(",")]
    colored_output = " ".join([f"<span style='color:yellow'>{word}</span>" if word.lower() in target_words else word for word in output.split()])
    st.write(f"Here are your target words: {target_word}")
    st.markdown(f"Here is your translated text: {colored_output}", unsafe_allow_html=True)
if adv_btn:
    output = run_adv_pipeline(text_input, target_word)
    target_words = [tw.strip().lower() for tw in target_word.split(",")]
    colored_output = " ".join([f"<span style='color:yellow'>{word}</span>" if word.lower() in target_words else word for word in output.split()])
    st.write(f"Here are your target words: {target_word}")
    st.markdown(f"Here is your translated text: {colored_output}", unsafe_allow_html=True)

## st.sidebar.success("select any page from here")
