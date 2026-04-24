from transformers import MarianMTModel, MarianTokenizer
import streamlit as st

model_name = "Helsinki-NLP/opus-mt-en-es"

@st.cache_resource
def load_translation_models():
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    return tokenizer, model

tokenizer, model = load_translation_models()

def run_pipline(user_sentence, user_target_words):
    sentence = user_sentence
    target_words = user_target_words
    spanish_targets_array = []

    # 1. Filter target words into an array
    target_words_array = target_words.split(", ")
    print(target_words_array)

    def translate(text):
        tokens = tokenizer(text, return_tensors="pt", padding=True)
        output = model.generate(**tokens)
        return tokenizer.decode(output[0], skip_special_tokens=True)

    # 1. Translate full sentence
    spanish_sentence = translate(sentence)

    # 2. Translate target words into new array
    for word in target_words_array:
        spanish_targets_array.append(translate(word))

    print(spanish_targets_array)

    # 3. Replace Spanish translation with original English word
    for english_word, spanish_word in zip(target_words_array, spanish_targets_array):
        print("English word:", english_word)
        print("Spanish word:", spanish_word)
        spanish_sentence = spanish_sentence.replace(spanish_word, english_word)

    final_sentence = spanish_sentence

   
 


    return final_sentence