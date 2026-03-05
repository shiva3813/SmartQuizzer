import pandas as pd
import streamlit as st

from analytics import build_accuracy_distribution, build_progress_chart
from question_generator import generate_questions
from text_extractor import extract_text
from utils.storage import init_db, load_attempts, load_questions, save_attempt, save_questions

st.set_page_config(page_title="SmartQuizzer", page_icon="🧠", layout="wide")
init_db()

if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "answers" not in st.session_state:
    st.session_state.answers = {}

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: 0.2px;
        }
        .sub-title {
            color: #475467;
            margin-bottom: 1rem;
        }
        .metric-box {
            border: 1px solid #eaecf0;
            border-radius: 12px;
            padding: 0.8rem;
            background: #f9fafb;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🧠 SmartQuizzer Live</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Generate quizzes from PDFs, attempt tests, and monitor live performance.</div>',
    unsafe_allow_html=True,
)

menu = st.sidebar.radio("Navigate", ["Generate Quiz", "Take Quiz", "Live Dashboard"])
user_name = st.sidebar.text_input("Candidate Name", value="Guest")
attempt_data = load_attempts(limit=200)

with st.sidebar:
    st.markdown("### Quick Stats")
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Tests", attempt_data["tests_taken"])
    with col_b:
        avg_score = (
            round(sum(attempt_data["scores"]) / len(attempt_data["scores"]), 2)
            if attempt_data["scores"]
            else 0
        )
        st.metric("Avg Score", avg_score)

if menu == "Generate Quiz":
    st.header("Upload Content")
    uploaded_file = st.file_uploader("Upload Study Material (PDF)", type=["pdf"])
    if uploaded_file:
        extracted_text = extract_text(uploaded_file)
        st.success("Text extracted successfully.")
        with st.expander("Preview extracted text"):
            st.write(extracted_text[:800] + ("..." if len(extracted_text) > 800 else ""))

        if st.button("Generate Quiz", type="primary"):
            questions = generate_questions(extracted_text)
            save_questions(questions, source_name=uploaded_file.name)
            st.session_state.answers = {}
            st.session_state.submitted = False
            st.success("New quiz generated and stored in backend.")

elif menu == "Take Quiz":
    st.header("Attempt Quiz")
    questions = load_questions()

    if not questions:
        st.warning("No quiz available yet. Generate one from the Upload page.")
    else:
        st.info(f"{len(questions)} questions loaded from backend.")
        for index, question in enumerate(questions, start=1):
            st.markdown(f"**Q{index}. {question['question']}**")
            selected = st.radio(
                f"Choose an answer for Q{index}",
                question["options"],
                key=f"q_{index}",
                index=None,
            )
            st.session_state.answers[index] = selected
            st.caption(f"Difficulty: {question.get('difficulty', 'unknown').title()}")
            st.divider()

        if st.button("Submit Quiz", type="primary"):
            score = 0
            for idx, question in enumerate(questions, start=1):
                if st.session_state.answers.get(idx) == question["answer"]:
                    score += 1

            save_attempt(score=score, total=len(questions), user_name=user_name.strip() or "Guest")
            st.session_state.submitted = True
            st.success(f"Score: {score} / {len(questions)}")
            st.progress(score / len(questions))
            st.balloons()

            with st.expander("Review answers"):
                for idx, question in enumerate(questions, start=1):
                    user_answer = st.session_state.answers.get(idx)
                    is_correct = user_answer == question["answer"]
                    label = "Correct" if is_correct else "Wrong"
                    st.write(f"Q{idx}: {label}")
                    st.write(f"Your answer: {user_answer}")
                    if not is_correct:
                        st.write(f"Correct answer: {question['answer']}")
                    st.divider()

elif menu == "Live Dashboard":
    st.header("Live Analytics Dashboard")
    if st.button("Refresh Live Data"):
        st.rerun()

    data = load_attempts(limit=100)
    recent_rows = data["recent"]

    if not recent_rows:
        st.warning("No attempts recorded yet.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.metric("Total Attempts", len(recent_rows))
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            best_score = max([row["score"] for row in recent_rows])
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.metric("Best Score", best_score)
            st.markdown("</div>", unsafe_allow_html=True)
        with col3:
            avg_accuracy = round(sum([row["percentage"] for row in recent_rows]) / len(recent_rows), 2)
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            st.metric("Avg Accuracy", f"{avg_accuracy}%")
            st.markdown("</div>", unsafe_allow_html=True)

        progress_chart = build_progress_chart(data["scores"])
        if progress_chart:
            st.plotly_chart(progress_chart, use_container_width=True)

        accuracy_chart = build_accuracy_distribution(recent_rows)
        if accuracy_chart:
            st.plotly_chart(accuracy_chart, use_container_width=True)

        table = pd.DataFrame(recent_rows)
        table = table.rename(
            columns={
                "user_name": "User",
                "score": "Score",
                "total": "Total",
                "percentage": "Accuracy",
                "submitted_at": "Submitted At (UTC)",
            }
        )
        st.subheader("Recent Attempts")
        st.dataframe(table, use_container_width=True, hide_index=True)
