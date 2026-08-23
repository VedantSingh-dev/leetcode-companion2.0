import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def run_analysis(stats_data: dict) -> str:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "API key missing. Make sure GOOGLE_API_KEY is defined in your .env file."
        )

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite", google_api_key=api_key, temperature=0.3
    )

    template = """
    You are an elite Data Structures and Algorithms (DSA) coach.
    Analyze the following LeetCode performance data for a candidate:

    1. Questions Solved: {questions_solved}
    2. Topicwise Breakdown: {topicwise}
    3. Contest Rating & History: {contest_history}
    4. Recent 20 Submissions: {recent_submissions}

    Provide a concise, highly structured evaluation containing:
    - **Current Standing**: Assess problem difficulty ratio (Easy/Medium/Hard) and contest performance.
    - **Weak Spots & Blind Spots**: Highlight specific topics where problem count is low.
    - **4-Week Actionable Roadmap**: Present as a Markdown Table with columns (Week, Focus Area, Goal).
    - **Top 5 Priority Topics**: Specific DSA tags to solve next.
    """

    prompt = PromptTemplate(
        input_variables=[
            "questions_solved",
            "topicwise",
            "contest_history",
            "recent_submissions",
        ],
        template=template,
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "questions_solved": str(stats_data["Questions_Solved"]),
            "topicwise": str(stats_data["Topicwise_Question_Solved"]),
            "contest_history": str(stats_data["Contest_History"]),
            "recent_submissions": str(stats_data["Last_20_Accepted_Submissions"]),
        }
    )

    # Handle LangChain output types cleanly
    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, list) and len(content) > 0:
            # Handle list of blocks/dicts
            first = content[0]
            if isinstance(first, dict):
                return str(first.get("text", ""))
            elif hasattr(first, "text"):
                return str(first.text)
            return str(content[0])
        return str(content)

    return str(response)