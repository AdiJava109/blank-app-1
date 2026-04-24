import sys, os
import streamlit as st
import pandas as pd
import io
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sentence_generator import generate_sentence

# Make the scope of questions global so we can use it in the Kahoot export function
questions = []

#This function converts the questions that we converted into Kahoot friendly format
def generate_kahoot_export(questions):
    rows = []
    for q in questions:
        rows.append({
            "Question": q['sentence'],
            "Answer 1": q['choices']['A'],
            "Answer 2": q['choices']['B'],
            "Answer 3": q['choices']['C'],
            "Answer 4": q['choices']['D'],
            "Time limit (sec)": 20,
            "Correct answer(s)": {"A": 1, "B": 2, "C": 3, "D": 4}[q['correct']]
        })
    return pd.DataFrame(rows)

# Page config
st.set_page_config(
    page_title="Translanguaging Question Generator",
    page_icon="📝",
    layout="centered"
)

# Title
st.title("📝 Translanguaging Question Generator for Teachers")
st.markdown("""
Generate Spanish sentences with English vocabulary words for your students. 
Perfect for worksheets, quizzes, and assessments!
""")

st.markdown("---")

# Input
st.markdown("### Enter Vocabulary Words")
word_input = st.text_area(
    "Enter one or more English words (separate with commas or new lines):",
    placeholder="Example:\nsiblings\nbreakfast\nhappy\nteacher",
    height=100
)

# Settings
st.markdown("### Settings (Optional)")
col1, col2 = st.columns(2)

with col1:
    include_answer_key = st.checkbox("Include Answer Key", value=True)

with col2:
    numbered = st.checkbox("Number Questions", value=True)

# Generate button
if st.button("🎯 Generate Questions", type="primary", use_container_width=True):
    if word_input.strip():
        with st.spinner("🤖 Generating questions..."):
            result = generate_sentence(word_input.strip())
        
        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            # Store in session state
            st.session_state.questions = result["quizzes"]
            st.session_state.total = result["total"]
            st.session_state.include_answers = include_answer_key
            st.session_state.numbered = numbered
    else:
        st.warning("⚠️ Please enter at least one word!")

# Display generated questions
if 'questions' in st.session_state:
    questions = st.session_state.questions
    total = st.session_state.total
    include_answers = st.session_state.include_answers
    numbered = st.session_state.numbered
    
    st.markdown("---")
    st.markdown(f"### ✅ Generated {total} Question(s)")
    
    # Build the formatted text for copying
    formatted_questions = ""
    formatted_answer_key = ""
    
    for idx, q in enumerate(questions, 1):
        # Question section
        if numbered:
            formatted_questions += f"{idx}. "
        
        formatted_questions += f"**{q['sentence']}**\n\n"
        formatted_questions += f"What does '**{q['word']}**' mean?\n\n"
        formatted_questions += f"   A. {q['choices']['A']}\n"
        formatted_questions += f"   B. {q['choices']['B']}\n"
        formatted_questions += f"   C. {q['choices']['C']}\n"
        formatted_questions += f"   D. {q['choices']['D']}\n\n"
        formatted_questions += "---\n\n"
        
        # Answer key section
        if include_answers:
            if numbered:
                formatted_answer_key += f"{idx}. "
            formatted_answer_key += f"{q['word']}: **{q['correct']}** - {q['choices'][q['correct']]}\n"
    
    # Display preview
    st.markdown("### 📄 Preview")
    st.markdown(formatted_questions)
    
    if include_answers:
        st.markdown("### 🔑 Answer Key")
        st.markdown(formatted_answer_key)
    
    # Copyable text boxes
    st.markdown("---")
    st.markdown("### 📋 Copy Questions")
    st.text_area(
        "Questions (copy this to your worksheet):",
        value=formatted_questions.replace("**", "").replace("---", ""),
        height=300,
        key="copy_questions"
    )
    
    if include_answers:
        st.text_area(
            "Answer Key (copy this separately):",
            value=formatted_answer_key.replace("**", ""),
            height=150,
            key="copy_answers"
        )
    
    # Download button
    st.markdown("### 💾 Download")
    
    # Create downloadable file
    download_content = "TRANSLANGUAGING VOCABULARY QUESTIONS\n"
    download_content += "="*50 + "\n\n"
    download_content += formatted_questions.replace("**", "").replace("---", "\n")
    
    if include_answers:
        download_content += "\n\n" + "="*50 + "\n"
        download_content += "ANSWER KEY\n"
        download_content += "="*50 + "\n\n"
        download_content += formatted_answer_key.replace("**", "")
    
    st.download_button(
        label="📥 Download as Text File",
        data=download_content,
        file_name="vocabulary_questions.txt",
        mime="text/plain"
    )

    # Kahoot export conversion (BEFORE you press the button)
    kahoot_df = generate_kahoot_export(questions)

    excel_buffer = io.BytesIO()
    kahoot_df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    # Kahoot download button ACTUAL
    st.download_button(
        label="📥 Download for Kahoot",
        data=excel_buffer,
        file_name="kahoot_vocab.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        # NOTE: The MIME is a cybersecurity concept to let the reciever know (browser Kahoot) that the data is an excel file
    )

        
    # New questions button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Generate New Questions", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Sidebar with instructions
with st.sidebar:
    st.markdown("### 📚 How to Use")
    st.markdown("""
    1. **Enter vocabulary words** (one per line or comma-separated)
    2. **Click Generate Questions**
    3. **Preview** the questions
    4. **Copy & paste** into your worksheet
    5. **Download** as a text file
    """)
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.markdown("""
    - Use simple, common words for best results
    - The Spanish context provides clues to word meaning
    - Students see the English word in a Spanish sentence
    - Perfect for translanguaging pedagogy
    """)
    
    st.markdown("---")
    st.markdown("### 📝 Example Input")
    st.code("""siblings
breakfast
happy
teacher""")

