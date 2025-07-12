import requests
from bs4 import BeautifulSoup
import logging


def get_leetcode_potd():
    try:
        url = "https://leetcode.com/graphql"
        query = {
            "operationName": "dailyCodingChallengeQuestion",
            "query": """
            query dailyCodingChallengeQuestion {
              activeDailyCodingChallengeQuestion {
                question {
                  titleSlug
                  title
                }
              }
            }
            """,
        }
        headers = {"Content-Type": "application/json"}
        res = requests.post(url, json=query, headers=headers)

        if res.status_code != 200:
            raise Exception(f"LeetCode API returned status code {res.status_code}")

        data = res.json()
        if (
            "data" not in data
            or "activeDailyCodingChallengeQuestion" not in data["data"]
        ):
            raise Exception("Invalid response format from LeetCode API")

        q = data["data"]["activeDailyCodingChallengeQuestion"]["question"]
        return (
            q["title"],
            q["titleSlug"],
            f"https://leetcode.com/problems/{q['titleSlug']}",
        )
    except Exception as e:
        logging.error(f"Error fetching LeetCode POTD: {e}")
        return "Error fetching LeetCode POTD", "error", "https://leetcode.com"


def get_gfg_potd():
    try:
        # Try multiple URLs for POTD
        urls = [
            "https://practice.geeksforgeeks.org/problem-of-the-day",
            "https://www.geeksforgeeks.org/problem-of-the-day",
            "https://practice.geeksforgeeks.org/explore?page=1&category[]=Problem%20of%20the%20Day",
        ]

        for url in urls:
            try:
                res = requests.get(url)

                if res.status_code != 200:
                    continue

                soup = BeautifulSoup(res.text, "html.parser")

                # Try multiple possible selectors for POTD
                potd_selectors = [
                    "div.potd-card",
                    "div.problem-of-the-day",
                    "div.potd",
                    "div[class*='potd']",
                    "div[class*='problem']",
                    "a[href*='problem-of-the-day']",
                    "a[href*='problems/']",
                ]

                potd_card = None
                for selector in potd_selectors:
                    potd_card = soup.select_one(selector)
                    if potd_card:
                        break

                if not potd_card:
                    # Try to find any link that might be the POTD
                    links = soup.find_all("a", href=True)
                    potd_links = [
                        link
                        for link in links
                        if "problem" in link.get("href", "").lower()
                    ]

                    if potd_links:
                        # Use the first problem link found
                        problem = potd_links[0]
                        title = problem.text.strip() or "Problem of the Day"
                        link = (
                            "https://practice.geeksforgeeks.org" + problem["href"]
                            if problem["href"].startswith("/")
                            else problem["href"]
                        )
                        return title, link
                    else:
                        continue

                problem = potd_card.find("a")
                if not problem:
                    continue

                title = problem.text.strip()
                link = (
                    "https://practice.geeksforgeeks.org" + problem["href"]
                    if problem["href"].startswith("/")
                    else problem["href"]
                )
                return title, link

            except Exception as e:
                logging.error(f"Error with URL {url}: {e}")
                continue

        # If all URLs fail, return the known POTD
        logging.warning("Could not fetch POTD from website, using known POTD")
        return (
            "Gold Mine Problem",
            "https://www.geeksforgeeks.org/problems/gold-mine-problem2608/1",
        )

    except Exception as e:
        logging.error(f"Error fetching GFG POTD: {e}")
        # Return the known POTD as fallback
        return (
            "Gold Mine Problem",
            "https://www.geeksforgeeks.org/problems/gold-mine-problem2608/1",
        )
