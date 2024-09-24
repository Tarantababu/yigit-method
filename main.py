import streamlit as st
import json
from datetime import datetime

def save_progress(username, lesson_id, completed):
    with open(f"{username}_progress.json", "w") as f:
        json.dump({"lesson_id": lesson_id, "completed": completed, "timestamp": str(datetime.now())}, f)

def split_sentence(sentence):
    words = sentence.split()
    chunks = []
    for i in range(len(words)):
        chunks.append(" ".join(words[:i+1]))
    return chunks

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

    # Initialize session state for question index if not exists
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0

    # Get current question
    if st.session_state.question_index < len(current_lesson["questions"]):
        question = current_lesson["questions"][st.session_state.question_index]
        
        st.write(question["prompt"])
        
        correct_answer = question["answer"]
        chunks = split_sentence(correct_answer)
        
        # Initialize session state for this question's progress if not exists
        if "current_progress" not in st.session_state:
            st.session_state.current_progress = 0
        
        if st.session_state.current_progress < len(chunks):
            user_answer = st.text_input("Complete the sentence:", value=chunks[st.session_state.current_progress], key="user_input")
            
            if user_answer:
                if user_answer.lower().strip() == correct_answer[:len(chunks[st.session_state.current_progress])].lower().strip():
                    st.session_state.current_progress += 1
                    if st.session_state.current_progress < len(chunks):
                        st.success("Correct! Continue with the next part.")
                    else:
                        st.success("Correct! You've completed this sentence.")
                        st.write("Explanation:", question["explanation"])
                        if st.button("Next Question"):
                            st.session_state.question_index += 1
                            st.session_state.current_progress = 0
                            st.experimental_rerun()
                else:
                    st.error("Not quite. Try again.")
        else:
            st.success(f"Completed sentence: {correct_answer}")
            st.write("Explanation:", question["explanation"])
            if st.button("Next Question"):
                st.session_state.question_index += 1
                st.session_state.current_progress = 0
                st.experimental_rerun()
    else:
        st.success("Congratulations! You've completed all questions in this lesson.")
        if st.button("Complete Lesson"):
            save_progress(username, lesson_id, True)
            st.success(f"Lesson completed: {current_lesson['title']}")
            st.session_state.question_index = 0
            st.session_state.current_progress = 0

if __name__ == "__main__":
    main()
