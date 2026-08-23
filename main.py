import ast
import plotly.express as px
import streamlit as st
from src.leetcode_client import fetch_leetcode_stats
from src.llm_chain import run_analysis

st.set_page_config(
    page_title="LeetCode Companion 2.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stMetric {
        background-color: #1e1e2e;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #313244;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("⚡ LeetCode AI Companion 2.0")
st.caption("Personalized DSA Roadmap Powered by Gemini & LangChain")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    st.info("🔑 Gemini API key loaded from environment variables.")
    if st.button("Clear Cache", type="secondary"):
        st.session_state.clear()
        st.rerun()

# User Input Form
col_input, col_btn = st.columns([3, 1])
with col_input:
    username = st.text_input(
        "Enter LeetCode Username",
        placeholder="e.g. tourist",
        label_visibility="collapsed",
    )
with col_btn:
    analyze_btn = st.button("Analyze Profile", type="primary", use_container_width=True)

# App State Management
if analyze_btn:
    if not username:
        st.warning("Please enter a valid LeetCode username.")
    else:
        try:
            with st.spinner("Fetching profile stats from LeetCode..."):
                stats_data = fetch_leetcode_stats(username)
                st.session_state["stats"] = stats_data

            with st.spinner("Gemini is analyzing your weak spots..."):
                raw_res = run_analysis(stats_data)

                # Unpack list or dict wrappers if returned
                clean_text = raw_res
                if isinstance(raw_res, list) and len(raw_res) > 0:
                    raw_res = raw_res[0]

                if isinstance(raw_res, dict):
                    clean_text = raw_res.get("text", str(raw_res))
                elif isinstance(raw_res, str) and (
                    raw_res.startswith("[") or raw_res.startswith("{")
                ):
                    try:
                        parsed = ast.literal_eval(raw_res)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            parsed = parsed[0]
                        if isinstance(parsed, dict):
                            clean_text = parsed.get("text", raw_res)
                    except Exception:
                        pass

                st.session_state["analysis"] = str(clean_text)

        except Exception as e:
            st.error(f"Error processing request: {str(e)}")

# Display Results View
if "stats" in st.session_state:
    stats = st.session_state["stats"]
    solved = stats["Questions_Solved"]
    contest = stats["Contest_History"]
    topics = stats.get("Topicwise_Question_Solved", {})

    st.divider()

    # Metrics Overview
    st.subheader("📊 Performance Overview")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Solved", solved["total"])
    m2.metric("Easy", solved["easy"])
    m3.metric("Medium", solved["medium"])
    m4.metric("Hard", solved["hard"])
    m5.metric("Contest Rating", int(contest["overall_rating"]))

    # Visual Charts
    if topics:
        st.write("")
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.subheader("🎯 Difficulty Breakdown")
            diff_data = {
                "Difficulty": ["Easy", "Medium", "Hard"],
                "Count": [solved["easy"], solved["medium"], solved["hard"]],
            }
            fig_pie = px.pie(
                diff_data,
                names="Difficulty",
                values="Count",
                color="Difficulty",
                color_discrete_map={
                    "Easy": "#00b8a3",
                    "Medium": "#ffc01e",
                    "Hard": "#ff375f",
                },
                hole=0.4,
            )
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_chart2:
            st.subheader("🏷️ Top Solved Topics")
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[
                :8
            ]
            if sorted_topics:
                top_names, top_counts = zip(*sorted_topics)
                fig_bar = px.bar(
                    x=top_counts,
                    y=top_names,
                    orientation="h",
                    labels={"x": "Problems Solved", "y": "Topic"},
                    color=top_counts,
                    color_continuous_scale="Viridis",
                )
                fig_bar.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=False,
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # Formatted AI Roadmap Output
    if "analysis" in st.session_state:
        st.subheader("💡 AI Coach Evaluation & Roadmap")
        st.markdown(st.session_state["analysis"])

        st.write("")
        st.download_button(
            label="📥 Download Study Plan",
            data=st.session_state["analysis"],
            file_name=f"{username}_leetcode_roadmap.md",
            mime="text/markdown",
        )