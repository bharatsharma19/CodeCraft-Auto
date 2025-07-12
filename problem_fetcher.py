import requests
import logging


def get_leetcode_potd():
    """Fetches the LeetCode Problem of the Day using the GraphQL API."""
    try:
        url = "https://leetcode.com/graphql"
        query = {
            "query": "query dailyCodingChallengeQuestion { activeDailyCodingChallengeQuestion { question { title titleSlug } } }"
        }
        response = requests.post(url, json=query, timeout=10)
        response.raise_for_status()
        data = response.json()
        question = data["data"]["activeDailyCodingChallengeQuestion"]["question"]
        title = question["title"]
        slug = question["titleSlug"]
        problem_url = f"https://leetcode.com/problems/{slug}/"
        return title, slug, problem_url
    except Exception as e:
        logging.error(f"Error fetching LeetCode POTD: {e}", exc_info=True)
        return "Error fetching LeetCode POTD", "error", "https://leetcode.com"


# The GFG fetching logic is now handled by the browser in SubmissionManager
# This file no longer needs a get_gfg_potd function.
