import requests


def fetch_leetcode_stats(username: str) -> dict:
    url = "https://leetcode.com/graphql"

    query = """
    query getUserFullProfile($username: String!) {
      matchedUser(username: $username) {
        submitStats {
          acSubmissionNum {
            difficulty
            count
          }
        }
        tagProblemCounts {
          fundamental { tagName problemsSolved }
          intermediate { tagName problemsSolved }
          advanced { tagName problemsSolved }
        }
      }
      userContestRanking(username: $username) {
        rating
      }
      userContestRankingHistory(username: $username) {
        contest {
          title
        }
        problemsSolved
        attended
      }
      recentAcSubmissionList(username: $username, limit: 20) {
        id
        title
        titleSlug
        timestamp
      }
    }
    """

    payload = {
        "query": query,
        "variables": {"username": username},
        "operationName": "getUserFullProfile",
    }

    response = requests.post(
        url, json=payload, headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        raise Exception(f"GraphQL request failed with status code {response.status_code}")

    data = response.json().get("data", {})
    matched_user = data.get("matchedUser") or {}

    # 1. Parse Solved Counts
    ac_list = matched_user.get("submitStats", {}).get("acSubmissionNum", [])
    questions_solved = {"easy": 0, "medium": 0, "hard": 0, "total": 0}
    for item in ac_list:
        diff = (item.get("difficulty") or "").lower()
        cnt = int(item.get("count") or 0)
        if diff in ("easy", "medium", "hard"):
            questions_solved[diff] = cnt
        elif diff == "all":
            questions_solved["total"] = cnt

    if questions_solved["total"] == 0:
        questions_solved["total"] = (
            questions_solved["easy"]
            + questions_solved["medium"]
            + questions_solved["hard"]
        )

    # 2. Parse Topic/Tag Distribution
    tpc = matched_user.get("tagProblemCounts", {}) or {}
    topicwise = {}
    for category in ("fundamental", "intermediate", "advanced"):
        for tag in tpc.get(category) or []:
            name = (tag.get("tagName") or "").strip()
            if name:
                topicwise[name] = topicwise.get(name, 0) + int(
                    tag.get("problemsSolved") or 0
                )

    # 3. Parse Contest Data
    ranking = data.get("userContestRanking") or {}
    history = data.get("userContestRankingHistory") or []
    attended = [h for h in history if h.get("attended")]
    contests = [
        {
            "contest_name": (item.get("contest") or {}).get("title", ""),
            "questions_solved": int(item.get("problemsSolved") or 0),
        }
        for item in attended[-10:]
    ]
    contest_history = {
        "overall_rating": float(ranking.get("rating") or 0.0),
        "contests": contests,
    }

    # 4. Parse Recent Submissions
    recent_submissions = {
        f"Q{i}": item.get("title", "")
        for i, item in enumerate(data.get("recentAcSubmissionList") or [], start=1)
    }

    return {
        "Questions_Solved": questions_solved,
        "Topicwise_Question_Solved": topicwise,
        "Contest_History": contest_history,
        "Last_20_Accepted_Submissions": recent_submissions,
    }