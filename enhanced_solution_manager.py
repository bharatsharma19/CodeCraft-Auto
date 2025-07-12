import os
import re
import requests
from bs4 import BeautifulSoup
import subprocess
import tempfile
import logging
from config import (
    openai_client,
    gemini_model,
    OPENAI_MODEL_NAME,
    USE_GEMINI,
    check_api_keys,
)


def fetch_problem_details(problem_url):
    """Fetch problem description, constraints, and examples from the URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(problem_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # --- KEY FIX: More specific and combined extraction ---
        if "leetcode.com" in problem_url:
            content_div = soup.select_one("div[data-track-load='description_content']")
        elif "geeksforgeeks.org" in problem_url:
            content_div = soup.select_one(
                "div.problem-statement, div.problem-tabs__content"
            )

        if content_div:
            # Extract text, preserving some structure with newlines
            full_text = content_div.get_text(separator="\n", strip=True)

            # Clean up excessive newlines
            cleaned_text = re.sub(r"\n\s*\n", "\n\n", full_text)

            # Truncate to a reasonable length for the prompt
            final_text = (
                (cleaned_text[:4000] + "...")
                if len(cleaned_text) > 4000
                else cleaned_text
            )
            logging.info(f"Problem details extracted ({len(final_text)} chars).")
            return final_text
        else:
            logging.warning(
                f"Could not find problem description element on {problem_url}."
            )
            return None
    except Exception as e:
        logging.error(
            f"Error fetching problem details from {problem_url}: {e}", exc_info=True
        )
        return None


def create_cpp_prompt(problem_title, problem_url, problem_description, attempt=1):
    """
    Creates a highly detailed and structured C++ prompt to maximize the chances
    of getting a correct, optimized, and complete solution.
    """
    # --- THE MOST IMPORTANT FIX: Advanced Prompt Engineering ---
    prompt = f"""
You are an expert C++ competitive programmer tasked with writing a solution for a daily coding challenge.
Your goal is to produce a 100% correct, efficient, and robust solution that will pass all test cases, including edge cases and performance tests.

**Problem Information:**
- **Title:** {problem_title}
- **URL:** {problem_url}

**Full Problem Description (including constraints and examples):**
---
{problem_description or "Description not available. You must infer the requirements from the title and common problem patterns."}
---

**CRITICAL INSTRUCTIONS:**

1.  **Analyze Thoroughly:** Carefully read the entire problem description, paying close attention to:
    - **Input/Output Format:** Match the required data types and structure exactly (e.g., `vector<int>`, `ListNode*`).
    - **Constraints:** Note the size of inputs (e.g., `n <= 10^5`), value ranges, and time/memory limits. This will determine the required algorithmic complexity.
    - **Edge Cases:** Consider empty inputs, single-element inputs, large values, etc.

2.  **Choose the Optimal Algorithm:** Based on the constraints, select the most efficient algorithm.
    - If `N` is small (e.g., < 20), recursion or brute force might be acceptable.
    - If `N` is large (e.g., 10^5), a solution of O(N log N) or O(N) is likely required. Avoid O(N^2).
    - Think about data structures: Hash maps for lookups, heaps for priority, etc.

3.  **Write Complete and Compilable Code:**
    - Provide a single, complete C++ code block.
    - **Include ALL necessary headers.** Using `<bits/stdc++.h>` is perfectly acceptable and preferred for simplicity.
    - The solution MUST be encapsulated within a `class Solution { ... };` structure.
    - Ensure the code is syntactically perfect and compiles with a C++17 compiler without any warnings.

4.  **DO NOT:**
    - Do not include `int main()` or any test driver code.
    - Do not add any explanations, comments, or markdown formatting outside the code block.
    - Do not use any non-standard libraries.

**Attempt-Specific Strategy:**
"""
    if attempt == 1:
        prompt += (
            "**Attempt 1:** Provide your best, most direct, and efficient solution."
        )
    else:
        prompt += f"**Attempt {attempt}:** The previous attempt failed. Re-evaluate the problem completely. Consider a different approach, data structure, or algorithm. Common failure points are off-by-one errors, integer overflows, or incorrect handling of edge cases. Provide a new, alternative solution."

    prompt += "\n\n```cpp\n"
    return prompt


# ... (The rest of the file remains the same as the previous answer)
def create_compilation_driver(code):
    return f"""
#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
#include <queue>
#include <stack>
#include <map>
#include <unordered_map>
#include <set>
#include <unordered_set>
#include <cmath>
#include <climits>
#include <cassert>
#include <utility>
{code}
int main() {{
    std::cout << "Compilation check successful." << std::endl;
    return 0;
}}
"""


def test_solution_compilation(code):
    if not code or not isinstance(code, str):
        return False, "Invalid code provided for compilation test."
    try:
        driver_code = create_compilation_driver(code)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cpp", delete=False) as f:
            temp_cpp_file = f.name
            f.write(driver_code)
        temp_exe_file = temp_cpp_file.replace(".cpp", "")
        compile_cmd = ["g++", "-std=c++17", "-Wall", "-o", temp_exe_file, temp_cpp_file]
        result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=20)
        os.unlink(temp_cpp_file)
        if os.path.exists(temp_exe_file):
            os.unlink(temp_exe_file)
        if result.returncode != 0:
            error_message = f"Compilation failed: {result.stderr}"
            logging.error(error_message)
            return False, error_message
        else:
            logging.info("Solution passed compilation test.")
            return True, "Compilation successful"
    except Exception as e:
        return False, f"Test execution error: {e}"


def extract_cpp_code(text):
    code_pattern = r"```(?:cpp|c\+\+)\s*\n(.*?)\n```"
    matches = re.findall(code_pattern, text, re.DOTALL)
    if matches:
        return matches[0].strip()
    if "class Solution" in text:
        return text.strip()
    return ""


def generate_solution_with_ai(problem_title, problem_url, attempt=1):
    if not check_api_keys():
        return "Error: API key not configured."
    problem_description = fetch_problem_details(problem_url)
    prompt = create_cpp_prompt(problem_title, problem_url, problem_description, attempt)
    try:
        logging.info(
            f"Generating solution with {'Gemini' if USE_GEMINI else 'OpenAI'} (Attempt {attempt})..."
        )
        if USE_GEMINI:
            if not gemini_model:
                return "Error: Gemini client not initialized."
            response = gemini_model.generate_content(prompt)
            response_text = response.text
        else:
            if not openai_client:
                return "Error: OpenAI client not initialized."
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2 + (attempt * 0.1),
                max_tokens=2048,
            )
            response_text = response.choices[0].message.content
        return extract_cpp_code(response_text)
    except Exception as e:
        return f"Error generating solution with AI: {e}"


def generate_and_test_solution(problem_title, problem_url, max_retries=2):
    for attempt in range(1, max_retries + 1):
        logging.info(
            f"--- Generation Attempt {attempt}/{max_retries} for '{problem_title}' ---"
        )
        solution = generate_solution_with_ai(problem_title, problem_url, attempt)
        if not solution or solution.startswith("Error"):
            logging.error(f"Solution generation failed: {solution}")
            continue
        if not validate_solution_structure(solution):
            logging.warning("Generated solution has invalid structure. Retrying...")
            continue
        success, message = test_solution_compilation(solution)
        if success:
            return solution, attempt, True
        else:
            logging.warning(f"Solution failed compilation test: {message}")
    return None, max_retries, False


def validate_solution_structure(code):
    return (
        code and isinstance(code, str) and len(code) > 50 and "class Solution" in code
    )
