import streamlit as st
import json
from datetime import datetime
import re

def save_progress(username, lesson_id, completed):
    with open(f"{username}_progress.json", "w") as f:
        json.dump({"lesson_id": lesson_id, "completed": completed, "timestamp": str(datetime.now())}, f)

def clean_text(text):
    return re.sub(r'[,.]', '', text.lower().strip())

def get_next_word(correct_answer, user_answer):
    correct_words = clean_text(correct_answer).split()
    user_words = clean_text(user_answer).split()
    for i, word in enumerate(correct_words):
        if i >= len(user_words) or user_words[i] != word:
            return f"-> {word}"
    return "Your answer is correct, but incomplete. Try adding more words."

def check_answer():
    user_answer = st.session_state.user_input
    correct_answer = st.session_state.correct_answer
    if clean_text(user_answer) == clean_text(correct_answer):
        st.session_state.feedback = "Correct! Well done."
        st.session_state.show_next = True
    else:
        st.session_state.feedback = get_next_word(correct_answer, user_answer)
        st.session_state.show_next = False

def main():
    st.set_page_config(layout="wide")
    
    # User authentication (simplified for this example)
    if "username" not in st.session_state:
        st.session_state.username = ""
    
    if not st.session_state.username:
        username = st.text_input("Enter your username:")
        if username:
            st.session_state.username = username
            st.experimental_rerun()
        return

    # Display username in top-right corner
    st.markdown(f'<div style="position: fixed; top: 10px; right: 10px; z-index: 1000; background-color: white; padding: 5px; border-radius: 5px;">{st.session_state.username}</div>', unsafe_allow_html=True)

    st.title("Language Learning App")

    # Load lessons data
    with open("lessons.json", "r") as f:
        lessons = json.load(f)

    # Lesson selection
    lesson_id = st.selectbox("Select a lesson:", list(lessons.keys()))
    current_lesson = lessons[lesson_id]

    # Initialize session state
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0
    if "show_next" not in st.session_state:
        st.session_state.show_next = False
    if "feedback" not in st.session_state:
        st.session_state.feedback = ""

    # Get current question
    if st.session_state.question_index < len(current_lesson["questions"]):
        question = current_lesson["questions"][st.session_state.question_index]
        
        st.write(question["prompt"])
        
        st.session_state.correct_answer = question["answer"]
        
        st.text_input("Your answer:", key="user_input", on_change=check_answer)
        
        if st.session_state.feedback:
            st.write(st.session_state.feedback)

        if st.session_state.show_next:
            if st.button("Next Question"):
                st.session_state.question_index += 1
                st.session_state.feedback = ""
                st.session_state.show_next = False
                st.experimental_rerun()
    else:
        st.success("Congratulations! You've completed all questions in this lesson.")
        if st.button("Complete Lesson"):
            save_progress(st.session_state.username, lesson_id, True)
            st.success(f"Lesson completed: {current_lesson['title']}")
            st.session_state.question_index = 0
            st.session_state.feedback = ""
            st.session_state.show_next = False

if __name__ == "__main__":
    main()
