import streamlit as st
import json
from datetime import datetime
import re
import random

def save_progress(username, lesson_id, score):
    with open(f"{username}_progress.json", "w") as f:
        json.dump({"lesson_id": lesson_id, "score": score, "timestamp": str(datetime.now())}, f)

def clean_text(text):
    return re.sub(r'[,.]', '', text.lower().strip())

def get_next_word(correct_answer, user_answer):
    correct_words = clean_text(correct_answer).split()
    user_words = clean_text(user_answer).split()
    for i, word in enumerate(correct_words):
        if i >= len(user_words) or user_words[i] != word:
            return word
    return ""

def check_answer():
    user_answer = st.session_state.get('user_input', '')
    correct_answer = st.session_state.correct_answer
    if clean_text(user_answer) == clean_text(correct_answer):
        st.session_state.feedback = "🎉 Correct! Well done."
        st.session_state.show_next = True
        st.session_state.score += 10
        st.session_state.streak += 1
    else:
        st.session_state.feedback = f"Not quite. Try again! Hint: {get_next_word(correct_answer, user_answer)}"
        st.session_state.show_next = False
        st.session_state.streak = 0
    st.session_state.attempts += 1

def main():
    st.set_page_config(layout="wide", page_title="Language Learning Game")
    
    if "username" not in st.session_state:
        st.session_state.username = ""
    
    if not st.session_state.username:
        st.title("Welcome to the Language Learning Game!")
        username = st.text_input("Enter your username to start:")
        if username:
            st.session_state.username = username
            st.session_state.score = 0
            st.session_state.streak = 0
            st.experimental_rerun()
        return

    # Load lessons data
    with open("lessons.json", "r") as f:
        lessons = json.load(f)

    # Sidebar for lesson selection and stats
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.username}!")
        lesson_id = st.selectbox("Select a lesson:", list(lessons.keys()))
        st.metric("Score", st.session_state.score)
        st.metric("Streak", st.session_state.streak)
        if st.button("Reset Progress"):
            st.session_state.score = 0
            st.session_state.streak = 0
            st.session_state.question_index = 0
            if 'user_input' in st.session_state:
                del st.session_state.user_input
            st.experimental_rerun()

    current_lesson = lessons[lesson_id]

    # Initialize session state
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0
    if "show_next" not in st.session_state:
        st.session_state.show_next = False
    if "feedback" not in st.session_state:
        st.session_state.feedback = ""
    if "attempts" not in st.session_state:
        st.session_state.attempts = 0

    # Main game area
    st.title("Language Learning Game")
    
    # Progress bar
    progress = st.session_state.question_index / len(current_lesson["questions"])
    st.progress(progress)

    # Get current question
    if st.session_state.question_index < len(current_lesson["questions"]):
        question = current_lesson["questions"][st.session_state.question_index]
        
        st.header(question["prompt"])
        
        st.session_state.correct_answer = question["answer"]
        
        user_input = st.text_input("Your answer:", key="user_input", on_change=check_answer)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.feedback:
                if "Correct" in st.session_state.feedback:
                    st.success(st.session_state.feedback)
                else:
                    st.warning(st.session_state.feedback)

        with col2:
            if st.session_state.show_next:
                if st.button("Next Question ➡️"):
                    st.session_state.question_index += 1
                    st.session_state.feedback = ""
                    st.session_state.show_next = False
                    st.session_state.attempts = 0
                    if 'user_input' in st.session_state:
                        del st.session_state.user_input
                    st.experimental_rerun()
    else:
        st.balloons()
        st.success("🎉 Congratulations! You've completed all questions in this lesson.")
        st.write(f"Your final score: {st.session_state.score}")
        if st.button("Play Again"):
            save_progress(st.session_state.username, lesson_id, st.session_state.score)
            st.session_state.question_index = 0
            st.session_state.feedback = ""
            st.session_state.show_next = False
            st.session_state.attempts = 0
            if 'user_input' in st.session_state:
                del st.session_state.user_input
            st.experimental_rerun()

    # Fun facts or tips
    if random.random() < 0.3:  # 30% chance to show a tip
        st.sidebar.info("💡 Tip: Practice regularly to improve your language skills!")

if __name__ == "__main__":
    main()
