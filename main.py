import streamlit as st
import json
from datetime import datetime
import re
import random
import time
from gtts import gTTS
import os
import base64

# Try to import speech_recognition, but don't fail if it's not available
try:
    import speech_recognition as sr
    speech_recognition_available = True
except ImportError:
    speech_recognition_available = False

def save_progress(username):
    progress = {
        "score": st.session_state.score,
        "streak": st.session_state.streak,
        "lessons_completed": st.session_state.lessons_completed,
        "current_lesson": st.session_state.current_lesson,
        "question_index": st.session_state.question_index,
        "timestamp": str(datetime.now())
    }
    with open(f"{username}_progress.json", "w") as f:
        json.dump(progress, f)

def load_progress(username):
    try:
        with open(f"{username}_progress.json", "r") as f:
            progress = json.load(f)
        st.session_state.score = progress["score"]
        st.session_state.streak = progress["streak"]
        st.session_state.lessons_completed = progress["lessons_completed"]
        st.session_state.current_lesson = progress["current_lesson"]
        st.session_state.question_index = progress["question_index"]
        return True
    except FileNotFoundError:
        return False

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

def text_to_speech(text, lang='de'):
    tts = gTTS(text=text, lang=lang, slow=False)
    filename = f"temp_audio_{hash(text)}.mp3"
    tts.save(filename)
    with open(filename, "rb") as f:
        audio_bytes = f.read()
    os.remove(filename)
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_tag = f'<audio autoplay="true" src="data:audio/mp3;base64,{audio_base64}">'
    st.markdown(audio_tag, unsafe_allow_html=True)

def voice_to_text():
    if not speech_recognition_available:
        st.error("Spracherkennung ist nicht verfügbar. Bitte installieren Sie das 'SpeechRecognition' Paket.")
        return ""

    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("Sprechen Sie jetzt...")
        audio = r.listen(source)
        st.write("Spracherkennung läuft...")
    
    try:
        text = r.recognize_google(audio, language="de-DE")
        return text
    except sr.UnknownValueError:
        st.error("Entschuldigung, ich konnte das nicht verstehen.")
        return ""
    except sr.RequestError as e:
        st.error(f"Konnte keine Ergebnisse vom Google Speech Recognition service abrufen; {e}")
        return ""

def check_answer():
    user_answer = st.session_state.get('user_input', '')
    correct_answer = st.session_state.correct_answer
    if clean_text(user_answer) == clean_text(correct_answer):
        st.session_state.feedback = "🎉 Richtig! Weiter zur nächsten Frage..."
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
        st.session_state.feedback = f"Nicht ganz. Versuchen Sie es nochmal! Tipp: {next_word}"
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

def load_achievements():
    try:
        with open(f"{st.session_state.username}_achievements.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_achievements(achievements):
    with open(f"{st.session_state.username}_achievements.json", "w") as f:
        json.dump(achievements, f)

def check_achievements(achievements):
    score = st.session_state.score
    streak = st.session_state.streak
    lessons_completed = st.session_state.lessons_completed
    
    new_achievements = []

    if score >= 100 and "Punktesammler" not in achievements:
        achievements["Punktesammler"] = "100 Punkte erreicht"
        new_achievements.append("Punktesammler")

    if score >= 500 and "Punkteprofi" not in achievements:
        achievements["Punkteprofi"] = "500 Punkte erreicht"
        new_achievements.append("Punkteprofi")

    if streak >= 5 and "Streber" not in achievements:
        achievements["Streber"] = "5er Serie erreicht"
        new_achievements.append("Streber")

    if streak >= 10 and "Serienmeister" not in achievements:
        achievements["Serienmeister"] = "10er Serie erreicht"
        new_achievements.append("Serienmeister")

    if lessons_completed >= 1 and "Anfänger" not in achievements:
        achievements["Anfänger"] = "Erste Lektion abgeschlossen"
        new_achievements.append("Anfänger")

    if lessons_completed >= 5 and "Fleißiger Schüler" not in achievements:
        achievements["Fleißiger Schüler"] = "5 Lektionen abgeschlossen"
        new_achievements.append("Fleißiger Schüler")

    save_achievements(achievements)
    return new_achievements, achievements

def display_achievements(achievements):
    st.sidebar.subheader("Errungenschaften")
    if achievements:
        for badge, description in achievements.items():
            st.sidebar.success(f"🏆 {badge}: {description}")
    else:
        st.sidebar.info("Noch keine Errungenschaften freigeschaltet.")

def main():
    st.set_page_config(layout="wide", page_title="Deutsch Lernspiel")
    
    if "username" not in st.session_state:
        st.session_state.username = ""
    
    if not st.session_state.username:
        st.title("Willkommen beim Deutsch Lernspiel!")
        username = st.text_input("Geben Sie Ihren Benutzernamen ein, um zu beginnen:")
        if username:
            st.session_state.username = username
            if load_progress(username):
                st.success("Willkommen zurück! Ihr Fortschritt wurde geladen.")
            else:
                st.session_state.score = 0
                st.session_state.streak = 0
                st.session_state.lessons_completed = 0
                st.session_state.current_lesson = None
                st.session_state.question_index = 0
            st.experimental_rerun()
        return

    # Load achievements
    if "achievements" not in st.session_state:
        st.session_state.achievements = load_achievements()

    # Load lessons data
    with open("lessons.json", "r") as f:
        lessons = json.load(f)

    # Sidebar for lesson selection and stats
    with st.sidebar:
        st.title(f"Willkommen, {st.session_state.username}!")
        
        # Handle the case where current_lesson might not be set
        if "current_lesson" not in st.session_state or st.session_state.current_lesson not in lessons:
            st.session_state.current_lesson = list(lessons.keys())[0]  # Default to first lesson
        
        lesson_id = st.selectbox(
            "Wählen Sie eine Lektion:", 
            list(lessons.keys()), 
            index=list(lessons.keys()).index(st.session_state.current_lesson)
        )
        st.metric("Punktzahl", st.session_state.score)
        st.metric("Serie", st.session_state.streak)
        st.metric("Abgeschlossene Lektionen", st.session_state.lessons_completed)
        if st.button("Fortschritt zurücksetzen"):
            st.session_state.score = 0
            st.session_state.streak = 0
            st.session_state.question_index = 0
            st.session_state.answer_correct = False
            st.session_state.move_to_next = False
            st.session_state.reset_input = True
            st.session_state.colored_answer = None
            st.session_state.review_items = []
            st.session_state.current_lesson = list(lessons.keys())[0]  # Reset to first lesson
            st.session_state.achievements = {}  # Reset achievements
            save_progress(st.session_state.username)
            save_achievements({})  # Reset achievements file
            st.experimental_rerun()

    # Display achievements
    display_achievements(st.session_state.achievements)

    current_lesson = lessons[lesson_id]
    st.session_state.current_lesson = lesson_id

    # Initialize session state
    if "review_items" not in st.session_state:
        st.session_state.review_items = []
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
    st.title("Deutsch Lernspiel")
    
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
        if st.button("Hören Sie die Antwort"):
            text_to_speech(question["answer"], lang='de')
        
        # Reset input if flag is set
        if st.session_state.reset_input:
            st.session_state.user_input = ""
            st.session_state.reset_input = False
        
        # Add voice input option only if speech recognition is available
        if speech_recognition_available:
            input_method = st.radio("Wie möchten Sie antworten?", ("Text", "Stimme"))
        else:
            input_method = "Text"
        
        if input_method == "Text":
            user_input = st.text_input("Ihre Antwort:", key="user_input", on_change=check_answer)
        else:
            if st.button("Klicken Sie hier, um zu sprechen"):
                user_input = voice_to_text()
                st.session_state.user_input = user_input
                st.write(f"Erkannte Antwort: {user_input}")
                check_answer()
        
        if st.session_state.feedback:
            if "Richtig" in st.session_state.feedback:
                st.success(st.session_state.feedback)
                time.sleep(1)  # Wait for 1 second
                next_question()
                save_progress(st.session_state.username)  # Save progress after each correct answer
                
                # Check for new achievements
                new_achievements, st.session_state.achievements = check_achievements(st.session_state.achievements)
                if new_achievements:
                    st.success(f"Neue Errungenschaften freigeschaltet: {', '.join(new_achievements)}")
                
                st.experimental_rerun()
            else:
                st.warning(st.session_state.feedback)
                if st.session_state.colored_answer:
                    st.markdown(f"Ihre Antwort bisher: {st.session_state.colored_answer}", unsafe_allow_html=True)
        
        if st.session_state.move_to_next:
            next_question()
            save_progress(st.session_state.username)  # Save progress after moving to next question
            st.experimental_rerun()

    else:
        st.balloons()
        st.success("🎉 Herzlichen Glückwunsch! Sie haben alle Fragen in dieser Lektion beantwortet.")
        st.write(f"Ihre Endpunktzahl: {st.session_state.score}")
        
        # Increment completed lessons
        st.session_state.lessons_completed += 1
        save_progress(st.session_state.username)  # Save progress after completing a lesson
        
        # Check for new achievements
        new_achievements, st.session_state.achievements = check_achievements(st.session_state.achievements)
        if new_achievements:
            st.success(f"Neue Errungenschaften freigeschaltet: {', '.join(new_achievements)}")
        
        # Review mode
        st.subheader("Überprüfungsmodus")
        for i, item in enumerate(st.session_state.review_items):
            with st.expander(f"Frage {i+1}: {item['question']}"):
                st.write(f"Richtige Antwort: {item['correct_answer']}")
                st.write(f"Ihre Antwort: {item['user_answer']}")
                if item['is_correct']:
                    st.success("Richtig!")
                else:
                    st.error("Falsch")
                if st.button(f"Hören Sie die richtige Antwort (F{i+1})", key=f"listen_{i}"):
                    text_to_speech(item['correct_answer'], lang='de')
        
        if st.button("Nochmal spielen"):
            st.session_state.question_index = 0
            st.session_state.feedback = ""
            st.session_state.attempts = 0
            st.session_state.answer_correct = False
            st.session_state.move_to_next = False
            st.session_state.reset_input = True
            st.session_state.colored_answer = None
            st.session_state.review_items = []
            save_progress(st.session_state.username)
            st.experimental_rerun()

    # Fun facts or tips
    if random.random() < 0.3:  # 30% chance to show a tip
        st.sidebar.info("💡 Tipp: Üben Sie regelmäßig, um Ihre Deutschkenntnisse zu verbessern!")

if __name__ == "__main__":
    main()
