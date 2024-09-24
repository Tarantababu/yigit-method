import streamlit as st
import spacy
import json
from datetime import datetime

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load lessons data
with open("lessons.json", "r") as f:
    lessons = json.load(f)

def check_answer(user_input, correct_answer):
    user_doc = nlp(user_input.lower())
    correct_doc = nlp(correct_answer.lower())
    
    if user_doc.similarity(correct_doc) > 0.8:
        return True
    return False

def save_progress(username, lesson_id, completed):
    # In a real app, you'd save this to a database
    with open(f"{username}_progress.json", "w") as f:
        json.dump({"lesson_id": lesson_id, "completed": completed, "timestamp": str(datetime.now())}, f)

def main():
    st.title("Language Learning App")

    # User authentication (simplified for this example)
    username = st.text_input("Enter your username:")
    if not username:
        st.warning("Please enter a username to begin.")
        return

    # Lesson selection
    lesson_id = st.selectbox("Select a lesson:", list(lessons.keys()))
    current_lesson = lessons[lesson_id]

    st.header(current_lesson["title"])
    st.write(current_lesson["description"])

    # Lesson content
    for i, question in enumerate(current_lesson["questions"]):
        st.subheader(f"Question {i+1}")
        st.write(question["prompt"])
        user_answer = st.text_input(f"Your answer for question {i+1}:", key=f"q{i}")
        
        if user_answer:
            if check_answer(user_answer, question["answer"]):
                st.success("Correct! Well done!")
            else:
                st.error(f"Not quite. The correct answer is: {question['answer']}")
                st.write("Explanation:", question["explanation"])

    # Complete lesson button
    if st.button("Complete Lesson"):
        save_progress(username, lesson_id, True)
        st.success(f"Congratulations! You've completed the lesson: {current_lesson['title']}")

if __name__ == "__main__":
    main()
