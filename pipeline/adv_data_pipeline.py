from transformers import AutoTokenizer, AutoModel
from transformers import MarianMTModel, MarianTokenizer
import nltk
import torch as F
import string
import re
import streamlit as st

# Download NLTK data only once
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))

# 1. Cache and load tokenizer and model
model_name = "microsoft/deberta-v3-base"
model_name_for_translation = "Helsinki-NLP/opus-mt-en-es"

@st.cache_resource
def load_models():
    tokenizer_for_translation = MarianTokenizer.from_pretrained(model_name_for_translation)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model_for_translation = MarianMTModel.from_pretrained(model_name_for_translation)
    return tokenizer_for_translation, tokenizer, model, model_for_translation

tokenizer_for_translation, tokenizer, model, model_for_translation = load_models()

def run_adv_pipeline(user_sentence, user_target_words):
    # 2. Define a sentence
    sentence = user_sentence
    target_word = user_target_words
    target_words_array = target_word.split(", ")
    # 3. Tokenize and get embeddings


    inputs = tokenizer(sentence, return_tensors="pt")
    with F.no_grad():
        outputs = model(**inputs)

    last_hidden_state = outputs.last_hidden_state  # Shape: [1, seq_len, 768]
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    print(tokens)

    filtered_tokens = []
    filtered_embeddings = []
    final_translated_sentence = []
    punct_ts = []
    ## Filter tokens
    for word, embedding in zip(tokens, last_hidden_state[0]):
        if word not in tokenizer.all_special_tokens and word[1:].lower() not in stop_words and word not in string.punctuation:
            filtered_tokens.append(word)
            filtered_embeddings.append(embedding)
        if word not in tokenizer.all_special_tokens and word not in string.punctuation:
            final_translated_sentence.append(word)

    print("Filtered embeddings:", filtered_tokens)
    print("Filtered embeddings:", final_translated_sentence)

    # Merge subword tokens into full words
    merged_words = []
    merged_embeddings = []

    current_word = ""
    current_vectors = []

    for token, vector in zip(filtered_tokens, filtered_embeddings):
        if token.startswith("▁"):  # Start part of another word
            if current_word:  # Save previous word
                word_embedding = F.stack(current_vectors).mean(dim=0)
                merged_words.append(current_word)
                merged_embeddings.append(word_embedding)

            current_word = token[1:]
            current_vectors = [vector]
        else:
            current_word += token
            current_vectors.append(vector)

    #Add the last word
    if current_word:
        word_embedding = F.stack(current_vectors).mean(dim=0)
        merged_words.append(current_word)
        merged_embeddings.append(word_embedding)
    print("Merged words:", merged_words)

    merged_fts = []
    current_word_translated = ""

    ## Exclusively for the final sentence
    for word in final_translated_sentence:
        if word.startswith("▁"):  # Start part of another word
            if current_word_translated:  # Save previous word
                merged_fts.append(current_word_translated)
                print(merged_fts)
            current_word_translated = word[1:]
        else:
            current_word_translated += word

    # Add the last word
    if current_word_translated:
        merged_fts.append(current_word_translated)
    print("Final sentence:", merged_fts)

    ## Find the target word embedding
    target_word_indexes = [i for i, w in enumerate(merged_words) if w in target_words_array]
    print(len(merged_embeddings))
    target_word_embeddings = [merged_embeddings[i] for i in target_word_indexes]  ## START SOLVING HERE ##
    target_word_embeddings = [e / e.norm(dim=0, keepdim = True) for e in target_word_embeddings]



    similarity_words = []
    ## Function for finding cosine similarity
    similarities = []
    def find_support_words(top_k):
        for word, embeddings in zip(merged_words, merged_embeddings):
            if word in target_words_array:
                continue
            norm_embeddings = embeddings / embeddings.norm(dim=0, keepdim = True)
            ## sim = F.nn.functional.cosine_similarity(target_word_embedding.squeeze(0), norm_embeddings.squeeze(0), dim=0) ## START SOLVING HERE ##
            sim = [F.nn.functional.cosine_similarity(embedding.squeeze(0), norm_embeddings.squeeze(0), dim=0) for embedding in target_word_embeddings]
            for scalar in sim:
                similarities.append((word, scalar.item()))   ##.item() just turns it into a scalar
        filtered_sim = sorted(similarities, key=lambda x: x[1], reverse=True) [:top_k] ## Sorts the words from most to least and grabs the top number of words

        for word, score in filtered_sim:
            similarity_words.append(word)
        print(similarity_words, type(similarity_words))

        print("Cosine similarities with target word:", target_words_array)
        for word, score in similarities:
            print(f"{word} --> {score:.4f}")
        print("")
        print(filtered_sim)
        return filtered_sim


    find_support_words(4)




    ##--------------------------------------------Translation Part BELOW -----------------------------------------------------------##
    """
    Note: You will have to seperate the words that were the top_k chosen context words, input them as an array into this model for
    tokenization, encoding, then decoding, then take the decoded output and string it back into the original sentence

    model_name_for_translation = "Helsinki-NLP/opus-mt-en-es"
    tokenizer_for_translation = MarianTokenizer.from_pretrained(model_name_for_translation)
    from transformers import AutoTokenizer, AutoModel
    """
    def translate_the_word(word):
        tokens = tokenizer_for_translation(word, return_tensors = 'pt', paddings = True)
        translated_token = model_for_translation.generate(**tokens)
        return tokenizer_for_translation.decode(translated_token[0], skip_special_tokens = True)

    translated_words = [translate_the_word(w) for w in similarity_words]
    print(translated_words)



    sorted_pairs = sorted(zip(similarity_words, translated_words), key = lambda pair: sentence.lower().find(pair[0].lower())) ## Is sorting the pair of english and translated words based on the location of the english word in the sentence
                                                                                                                        ## Both are being sorted because there is no t for _, t in zip(...)
    similarity_words_sorted, translated_words_sorted = zip(*sorted_pairs)  ## Splits the tuples list into two separate lists (one translated and the other english)
    translation_map = {w.lower(): t for w, t in zip(similarity_words_sorted, translated_words_sorted)}

    tokens = re.findall(r"\w+|[^\w\s]", sentence, re.UNICODE)  ## Creates a list called 'tokens' where each token is a word or a puncatuation in the sentence

    for i, token in enumerate(tokens):
        lower_token = token.lower()
        if lower_token in translation_map:
            translation = translation_map[lower_token]
            # Keep English word, add Spanish in parentheses
            if token[0].isupper():
                tokens[i] = f"{token} ({translation.capitalize()})"
            else:
                tokens[i] = f"{token} ({translation})"

    # Reconstruct final sentence
    final_sentence = ""
    for i, t in enumerate(tokens):
        if i > 0 and not re.match(r"[^\w\s]", t):
            final_sentence += " "
        final_sentence += t

    return final_sentence