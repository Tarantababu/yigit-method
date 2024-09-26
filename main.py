import streamlit as st
import json
from datetime import datetime
import re
import random
import time
from gtts import gTTS
import os
import base64

def save_progress(username, lesson_id, score):
    with open(f"{username}_progress.json", "w") as f:
        json.dump({"lesson_id": lesson_id, "score": score, "timestamp": str(datetime.now())}, f)

def clean_text(text):
    return re.sub(r'[,.]', '', text.lower().strip())

def get_colored_answer(user_answer, correct_answer):
    user_words = clean_text(user_answer).split()
    correct_words = clean_text(correct_answer).split()
    colored_words = []
    for i, word in enumerate(user_words):
        if i < len(correct_words) and word == correct_words[i]:
            colored_words.append(f'<span style="color: darkgreen;">{word}</span>')
        else:
            colored_words.append(f'<span style="color: red;">{word}</span>')
    return " ".join(colored_words)

def get_next_word(correct_answer, user_answer):
    correct_words = clean_text(correct_answer).split()
    user_words = clean_text(user_answer).split()
    for i, word in enumerate(correct_words):
        if i >= len(user_words) or user_words[i] != word:
            return word
    return ""

def text_to_speech(text, lang='en'):
    tts = gTTS(text=text, lang=lang, slow=False)
    filename = f"temp_audio_{hash(text)}.mp3"
    tts.save(filename)
    with open(filename, "rb") as f:
        audio_bytes = f.read()
    os.remove(filename)
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_tag = f'<audio autoplay="true" src="data:audio/mp3;base64,{audio_base64}">'
    st.markdown(audio_tag, unsafe_allow_html=True)

def check_answer():
    user_answer = st.session_state.get('user_input', '')
    correct_answer = st.session_state.correct_answer
    if clean_text(user_answer) == clean_text(correct_answer):
        st.session_state.feedback = "🎉 Correct! Moving to next question..."
        st.session_state.score += 10
        st.session_state.streak += 1
        st.session_state.answer_correct = True
        st.session_state.move_to_next = True
        st.session_state.colored_answer = None
        st.session_state.review_items.append({
            "question": st.session_state.current_question["prompt"],
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "is_correct": True
        })
    else:
        next_word = get_next_word(correct_answer, user_answer)
        st.session_state.feedback = f"Not quite. Try again! Hint: {next_word}"
        st.session_state.streak = 0
        st.session_state.answer_correct = False
        st.session_state.colored_answer = get_colored_answer(user_answer, correct_answer)
        st.session_state.review_items.append({
            "question": st.session_state.current_question["prompt"],
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "is_correct": False
        })
    st.session_state.attempts += 1

def next_question():
    st.session_state.question_index += 1
    st.session_state.feedback = ""
    st.session_state.attempts = 0
    st.session_state.answer_correct = False
    st.session_state.move_to_next = False
    st.session_state.reset_input = True
    st.session_state.colored_answer = None

def main():
    st.set_page_config(layout="wide", page_title="Language Learning Game")
    
    if "username" not in st.session_state:
        st.session_state.username = ""
    
    if "review_items" not in st.session_state:
        st.session_state.review_items = []
    
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
            st.session_state.answer_correct = False
            st.session_state.move_to_next = False
            st.session_state.reset_input = True
            st.session_state.colored_answer = None
            st.session_state.review_items = []
            st.experimental_rerun()

    current_lesson = lessons[lesson_id]

    # Initialize session state
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0
    if "feedback" not in st.session_state:
        st.session_state.feedback = ""
    if "attempts" not in st.session_state:
        st.session_state.attempts = 0
    if "answer_correct" not in st.session_state:
        st.session_state.answer_correct = False
    if "move_to_next" not in st.session_state:
        st.session_state.move_to_next = False
    if "reset_input" not in st.session_state:
        st.session_state.reset_input = False
    if "colored_answer" not in st.session_state:
        st.session_state.colored_answer = None

    # Main game area
    st.title("Language Learning Game")
    
    # Progress bar
    progress = st.session_state.question_index / len(current_lesson["questions"])
    st.progress(progress)

    # Get current question
    if st.session_state.question_index < len(current_lesson["questions"]):
        question = current_lesson["questions"][st.session_state.question_index]
        st.session_state.current_question = question
        
        st.header(question["prompt"])
        
        st.session_state.correct_answer = question["answer"]
        
        # Text-to-speech button
        if st.button("Listen to the answer"):
            text_to_speech(question["answer"], lang=current_lesson.get("language", "en"))
        
        # Reset input if flag is set
        if st.session_state.reset_input:
            st.session_state.user_input = ""
            st.session_state.reset_input = False
        
        user_input = st.text_input("Your answer:", key="user_input", on_change=check_answer)
        
        if st.session_state.feedback:
            if "Correct" in st.session_state.feedback:
                st.success(st.session_state.feedback)
                time.sleep(1)  # Wait for 1 second
                next_question()
                st.experimental_rerun()
            else:
                st.warning(st.session_state.feedback)
                if st.session_state.colored_answer:
                    st.markdown(f"Your answer so far: {st.session_state.colored_answer}", unsafe_allow_html=True)
        
        if st.session_state.move_to_next:
            next_question()
            st.experimental_rerun()

    else:
        st.balloons()
        st.success("🎉 Congratulations! You've completed all questions in this lesson.")
        st.write(f"Your final score: {st.session_state.score}")
        
        # Review mode
        st.subheader("Review Mode")
        for i, item in enumerate(st.session_state.review_items):
            with st.expander(f"Question {i+1}: {item['question']}"):
                st.write(f"Correct answer: {item['correct_answer']}")
                st.write(f"Your answer: {item['user_answer']}")
                if item['is_correct']:
                    st.success("Correct!")
                else:
                    st.error("Incorrect")
                if st.button(f"Listen to correct answer (Q{i+1})", key=f"listen_{i}"):
                    text_to_speech(item['correct_answer'], lang=current_lesson.get("language", "en"))
        
        if st.button("Play Again"):
            save_progress(st.session_state.username, lesson_id, st.session_state.score)
            st.session_state.question_index = 0
            st.session_state.feedback = ""
            st.session_state.attempts = 0
            st.session_state.answer_correct = False
            st.session_state.move_to_next = False
            st.session_state.reset_input = True
            st.session_state.colored_answer = None
            st.session_state.review_items = []
            st.experimental_rerun()

    # Fun facts or tips
    if random.random() < 0.3:  # 30% chance to show a tip
        st.sidebar.info("💡 Tip: Practice regularly to improve your language skills!")

if __name__ == "__main__":
    main()
