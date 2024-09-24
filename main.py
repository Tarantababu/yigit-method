import streamlit as st
import json
from datetime import datetime

def save_progress(username, lesson_id, completed):
    with open(f"{username}_progress.json", "w") as f:
        json.dump({"lesson_id": lesson_id, "completed": completed, "timestamp": str(datetime.now())}, f)

def get_hint(correct_answer, user_answer):
    correct_words = correct_answer.lower().split()
    user_words = user_answer.lower().split()
    for i, word in enumerate(correct_words):
        if i >= len(user_words) or user_words[i] != word:
            return f"Hint: The next word is '{word}'"
    return "Your answer is correct, but incomplete. Try adding more words."

def main():
    st.title("Language Learning App")

    # Load lessons data
    with open("lessons.json", "r") as f:
        lessons = json.load(f)

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

    # Initialize session state
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0
    if "user_answer" not in st.session_state:
        st.session_state.user_answer = ""
    if "show_next" not in st.session_state:
        st.session_state.show_next = False

    # Get current question
    if st.session_state.question_index < len(current_lesson["questions"]):
        question = current_lesson["questions"][st.session_state.question_index]
        
        st.write(question["prompt"])
        
        correct_answer = question["answer"]
        
        user_answer = st.text_input("Your answer:", key="user_input", value=st.session_state.user_answer)
        
        if st.button("Submit"):
            st.session_state.user_answer = user_answer
            if user_answer.lower().strip() == correct_answer.lower().strip():
                st.success("Correct! Well done.")
                st.write("Explanation:", question["explanation"])
                st.session_state.show_next = True
            else:
                st.error("Not quite correct. Here's a hint:")
                st.write(get_hint(correct_answer, user_answer))
                st.session_state.show_next = False

        if st.session_state.show_next:
            if st.button("Next Question"):
                st.session_state.question_index += 1
                st.session_state.user_answer = ""
                st.session_state.show_next = False
                st.experimental_rerun()
    else:
        st.success("Congratulations! You've completed all questions in this lesson.")
        if st.button("Complete Lesson"):
            save_progress(username, lesson_id, True)
            st.success(f"Lesson completed: {current_lesson['title']}")
            st.session_state.question_index = 0
            st.session_state.user_answer = ""
            st.session_state.show_next = False

if __name__ == "__main__":
    main()
