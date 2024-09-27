import streamlit as st
import json
from datetime import datetime, timedelta
import re
import random
import time
from gtts import gTTS
import os
import base64

# Try to import speech_recognition and pyaudio, but don't fail if they're not available
try:
    import speech_recognition as sr
    import pyaudio
    speech_recognition_available = True
except ImportError:
    speech_recognition_available = False

def initialize_session_state():
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "streak" not in st.session_state:
        st.session_state.streak = 0
    if "lessons_completed" not in st.session_state:
        st.session_state.lessons_completed = 0
    if "question_history" not in st.session_state:
        st.session_state.question_history = {}
    if "achievements" not in st.session_state:
        st.session_state.achievements = {}
    if "custom_lessons" not in st.session_state:
        st.session_state.custom_lessons = {}
    if "feedback" not in st.session_state:
        st.session_state.feedback = ""
    if "answer_correct" not in st.session_state:
        st.session_state.answer_correct = False
    if "colored_answer" not in st.session_state:
        st.session_state.colored_answer = None
    if "current_question" not in st.session_state:
        st.session_state.current_question = None
    if "correct_answer" not in st.session_state:
        st.session_state.correct_answer = ""
    if "user_input" not in st.session_state:
        st.session_state.user_input = ""
    if "attempts" not in st.session_state:
        st.session_state.attempts = 0
    if "current_lesson" not in st.session_state:
        st.session_state.current_lesson = None
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = None

def save_progress(username):
    progress = {
        "score": st.session_state.score,
        "streak": st.session_state.streak,
        "lessons_completed": st.session_state.lessons_completed,
        "question_history": st.session_state.question_history,
        "timestamp": str(datetime.now())
    }
    with open(f"{username}_progress.json", "w") as f:
        json.dump(progress, f)

def load_progress(username):
    try:
        with open(f"{username}_progress.json", "r") as f:
            progress = json.load(f)
        
        # Initialize session state with loaded progress
        st.session_state.score = progress.get("score", 0)
        st.session_state.streak = progress.get("streak", 0)
        st.session_state.lessons_completed = progress.get("lessons_completed", 0)
        st.session_state.question_history = progress.get("question_history", {})
        
        return True
    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        st.error(f"Error reading progress file for {username}. File may be corrupted.")
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
        st.error("Spracherkennung ist nicht verfügbar. Bitte installieren Sie die benötigten Pakete (SpeechRecognition und PyAudio).")
        return ""

    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.write("Sprechen Sie jetzt...")
            audio = r.listen(source)
            st.write("Spracherkennung läuft...")
    
        text = r.recognize_google(audio, language="de-DE")
        return text
    except sr.UnknownValueError:
        st.error("Entschuldigung, ich konnte das nicht verstehen.")
        return ""
    except sr.RequestError as e:
        st.error(f"Konnte keine Ergebnisse vom Google Speech Recognition service abrufen; {e}")
        return ""
    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {str(e)}")
        return ""

def check_answer():
    user_answer = st.session_state.get('user_input', '')
    correct_answer = st.session_state.correct_answer
    if clean_text(user_answer) == clean_text(correct_answer):
        st.session_state.feedback = "🎉 Richtig!"
        st.session_state.score += 10
        st.session_state.streak += 1
        st.session_state.answer_correct = True
        st.session_state.colored_answer = None
    else:
        next_word = get_next_word(correct_answer, user_answer)
        st.session_state.feedback = f"Nicht ganz. Versuchen Sie es nochmal! Tipp: {next_word}"
        st.session_state.streak = 0
        st.session_state.answer_correct = False
        st.session_state.colored_answer = get_colored_answer(user_answer, correct_answer)
    st.session_state.attempts += 1

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

def load_lessons():
    # Load built-in lessons
    try:
        with open("lessons.json", "r") as f:
            built_in_lessons = json.load(f)
    except FileNotFoundError:
        st.error("lessons.json file not found. Please make sure it exists in the same directory as the script.")
        built_in_lessons = {}
    
    # Load custom lessons from session state
    custom_lessons = st.session_state.get('custom_lessons', {})
    
    # Combine built-in and custom lessons
    all_lessons = {}
    all_lessons.update(built_in_lessons)
    all_lessons.update(custom_lessons)
    
    return all_lessons, built_in_lessons, custom_lessons

def save_custom_lesson(lesson_name, questions):
    if 'custom_lessons' not in st.session_state:
        st.session_state.custom_lessons = {}
    
    st.session_state.custom_lessons[lesson_name] = {"questions": questions}

def custom_lesson_manager():
    st.header("Benutzerdefinierte Lektionen verwalten")
    
    lessons_changed = False
    
    # Create new lesson
    st.subheader("Neue Lektion erstellen")
    lesson_name = st.text_input("Lektionsname")
    questions = []
    
    if lesson_name:
        st.write("Fügen Sie Fragen hinzu:")
        new_prompt = st.text_input("Frage")
        new_answer = st.text_input("Antwort")
        if st.button("Frage hinzufügen"):
            questions.append({"prompt": new_prompt, "answer": new_answer})
            st.success("Frage hinzugefügt!")
        
        if questions and st.button("Lektion speichern"):
            save_custom_lesson(lesson_name, questions)
            st.success(f"Lektion '{lesson_name}' wurde gespeichert!")
            lessons_changed = True
    
    # View and delete custom lessons
    st.subheader("Benutzerdefinierte Lektionen")
    custom_lessons = st.session_state.get('custom_lessons', {})
    
    if custom_lessons:
        for lesson, content in custom_lessons.items():
            st.write(f"Lektion: {lesson}")
            if st.button(f"Löschen: {lesson}"):
                del st.session_state.custom_lessons[lesson]
                st.success(f"Lektion '{lesson}' wurde gelöscht!")
                lessons_changed = True
                st.experimental_rerun()
    else:
        st.info("Noch keine benutzerdefinierten Lektionen vorhanden.")
    
    # Download custom lessons as JSON
    if custom_lessons:
        st.download_button(
            label="Benutzerdefinierte Lektionen herunterladen",
            data=json.dumps(custom_lessons, indent=2),
            file_name="custom_lessons.json",
            mime="application/json"
        )
    
    # Upload custom lessons
    uploaded_file = st.file_uploader("Benutzerdefinierte Lektionen hochladen", type="json")
    if uploaded_file is not None:
        uploaded_lessons = json.load(uploaded_file)
        st.session_state.custom_lessons.update(uploaded_lessons)
        st.success("Benutzerdefinierte Lektionen wurden hochgeladen!")
        lessons_changed = True
    
    return lessons_changed

def initialize_question_history(lessons):
    if 'question_history' not in st.session_state:
        st.session_state.question_history = {}
    
    for lesson_name, lesson in lessons.items():
        if lesson_name not in st.session_state.question_history:
            st.session_state.question_history[lesson_name] = {}
        for i, question in enumerate(lesson['questions']):
            if i not in st.session_state.question_history[lesson_name]:
                st.session_state.question_history[lesson_name][i] = {
                    'last_seen': None,
                    'correct_count': 0,
                    'total_count': 0,
                    'easiness_factor': 2.5,
                    'interval': 1,
                    'attempts': []
                }

def get_next_review_date(history):
    if history['last_seen'] is None:
        return datetime.now()
    return history['last_seen'] + timedelta(days=history['interval'])

def update_question_history(lesson_name, question_index, correct, attempt_count):
    history = st.session_state.question_history[lesson_name][question_index]
    history['last_seen'] = datetime.now()
    history['total_count'] += 1
    history['attempts'].append(attempt_count)
    if correct:
        history['correct_count'] += 1
        history['easiness_factor'] = max(1.3, history['easiness_factor'] + (0.1 - (5 - attempt_count) * (0.08 + (5 - attempt_count) * 0.02)))
        if history['interval'] == 1:
            history['interval'] = 6
        elif history['interval'] == 6:
            history['interval'] = 1
        else:
            history['interval'] *= history['easiness_factor']
    else:
        history['easiness_factor'] = max(1.3, history['easiness_factor'] - 0.2)
        history['interval'] = 1

def get_next_question(lesson_name, lesson):
    current_time = datetime.now()
    due_questions = []
    for i, question in enumerate(lesson['questions']):
        history = st.session_state.question_history[lesson_name][i]
        if get_next_review_date(history) <= current_time:
            due_questions.append(i)
    
    if due_questions:
        return random.choice(due_questions)
    else:
        # If no questions are due, choose a random question
        return random.randint(0, len(lesson['questions']) - 1)

def display_spaced_repetition_stats():
    st.sidebar.subheader("Spaced Repetition Statistiken")
    total_questions = 0
    total_correct = 0
    total_attempts = 0
    for lesson in st.session_state.question_history.values():
        for question in lesson.values():
            total_questions += 1
            total_correct += question['correct_count']
            total_attempts += sum(question['attempts'])
    
    if total_questions > 0:
        accuracy = (total_correct / total_questions) * 100
        avg_attempts = total_attempts / total_questions
        st.sidebar.metric("Gesamtgenauigkeit", f"{accuracy:.2f}%")
        st.sidebar.metric("Durchschnittliche Versuche pro Frage", f"{avg_attempts:.2f}")

def main():
    st.set_page_config(layout="wide", page_title="Deutsch Lernspiel")
    
    initialize_session_state()
    
    if not st.session_state.username:
        st.title("Willkommen beim Deutsch Lernspiel!")
        username = st.text_input("Geben Sie Ihren Benutzernamen ein, um zu beginnen:")
        if username:
            st.session_state.username = username
            if load_progress(username):
                st.success("Willkommen zurück! Ihr Fortschritt wurde geladen.")
            else:
                st.success(f"Willkommen, {username}! Ein neues Spiel wurde für Sie gestartet.")
            st.experimental_rerun()
        return

    if not st.session_state.achievements:
        st.session_state.achievements = load_achievements()

    all_lessons, built_in_lessons, custom_lessons = load_lessons()
    initialize_question_history(all_lessons)

    # Navigation
    page = st.sidebar.radio("Navigation", ["Lernspiel", "Benutzerdefinierte Lektionen"])

    if page == "Lernspiel":
        with st.sidebar:
            st.title(f"Willkommen, {st.session_state.username}!")
            st.metric("Punktzahl", st.session_state.score)
            st.metric("Serie", st.session_state.streak)
            st.metric("Abgeschlossene Lektionen", st.session_state.lessons_completed)
            
            # Lesson selection
            lesson_options = list(all_lessons.keys())
            selected_lesson = st.selectbox("Wählen Sie eine Lektion:", lesson_options)
            if selected_lesson != st.session_state.current_lesson:
                st.session_state.current_lesson = selected_lesson
                st.session_state.current_question_index = None
                st.experimental_rerun()

            if st.button("Fortschritt zurücksetzen"):
                st.session_state.score = 0
                st.session_state.streak = 0
                st.session_state.lessons_completed = 0
                st.session_state.question_history = {}
                initialize_question_history(all_lessons)
                st.session_state.achievements = {}
                save_progress(st.session_state.username)
                save_achievements({})
                st.experimental_rerun()

            display_spaced_repetition_stats()

        display_achievements(st.session_state.achievements)

        st.title("Deutsch Lernspiel")

        if st.session_state.current_lesson:
            current_lesson = all_lessons[st.session_state.current_lesson]
            if st.session_state.current_question_index is None:
                st.session_state.current_question_index = get_next_question(st.session_state.current_lesson, current_lesson)
            
            question = current_lesson["questions"][st.session_state.current_question_index]
            st.session_state.current_question = question
            
            st.header(question["prompt"])
            st.session_state.correct_answer = question["answer"]
            
            # Text-to-speech button
            if st.button("Hören Sie die Antwort"):
                text_to_speech(question["answer"], lang='de')
            
            # Voice input option
            if speech_recognition_available:
                input_method = st.radio("Wie möchten Sie antworten?", ("Text", "Stimme"))
            else:
                input_method = "Text"
                st.warning("Spracherkennung ist nicht verfügbar. Bitte verwenden Sie die Texteingabe.")
            
            if input_method == "Text":
                user_input = st.text_input("Ihre Antwort:", key="user_input", on_change=check_answer)
            else:
                if st.button("Klicken Sie hier, um zu sprechen"):
                    user_input = voice_to_text()
                    if user_input:
                        st.session_state.user_input = user_input
                        st.write(f"Erkannte Antwort: {user_input}")
                        check_answer()
            
            if st.session_state.feedback:
                if "Richtig" in st.session_state.feedback:
                    st.success(st.session_state.feedback)
                    update_question_history(st.session_state.current_lesson, st.session_state.current_question_index, True, st.session_state.attempts)
                    save_progress(st.session_state.username)
                    
                    new_achievements, st.session_state.achievements = check_achievements(st.session_state.achievements)
                    if new_achievements:
                        st.success(f"Neue Errungenschaften freigeschaltet: {', '.join(new_achievements)}")
                    
                    st.session_state.feedback = ""
                    st.session_state.attempts = 0
                    st.session_state.current_question_index = None
                    st.experimental_rerun()
                else:
                    st.warning(st.session_state.feedback)
                    if st.session_state.colored_answer:
                        st.markdown(f"Ihre Antwort bisher: {st.session_state.colored_answer}", unsafe_allow_html=True)
            
            if st.button("Nächste Frage"):
                update_question_history(st.session_state.current_lesson, st.session_state.current_question_index, False, st.session_state.attempts)
                st.session_state.attempts = 0
                st.session_state.current_question_index = None
                st.experimental_rerun()

        else:
            st.warning("Bitte wählen Sie eine Lektion aus.")

    elif page == "Benutzerdefinierte Lektionen":
        lessons_changed = custom_lesson_manager()
        if lessons_changed:
            all_lessons, _, _ = load_lessons()
            initialize_question_history(all_lessons)
            st.experimental_rerun()

    # Fun facts or tips
    if random.random() < 0.3:
        st.sidebar.info("💡 Tipp: Üben Sie regelmäßig, um Ihre Deutschkenntnisse zu verbessern!")

if __name__ == "__main__":
    main()
