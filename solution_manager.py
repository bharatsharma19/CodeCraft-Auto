import os
import logging
from config import (
    openai_client,
    gemini_model,
    MODEL_NAME,
    USE_GEMINI,
    check_api_keys,
)


def load_local_solution(platform, identifier):
    path = f"solutions/{platform}/{identifier}.cpp"
    if os.path.exists(path):
        with open(path) as f:
            return f.read(), True
    return None, False


def save_solution(platform, identifier, code):
    path = f"solutions/{platform}/{identifier}.cpp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(code)


def generate_solution_with_openai(problem_title, problem_url):
    if not check_api_keys():
        return "Error: API keys not configured. Please set OPENAI_API_KEY environment variable."

    if not openai_client:
        return "Error: OpenAI client not initialized."

    try:
        prompt = f"""Write a concise, optimized C++ solution for: {problem_title}

Requirements:
- Write SHORT, EFFICIENT code
- Use optimal algorithms and data structures
- Handle edge cases properly
- Focus on performance, not verbose explanations
- Use modern C++ features

Provide ONLY the concise C++ code:

```cpp
class Solution {{
public:
    // Concise optimized solution
}};
```"""

        response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating solution with OpenAI: {e}"


def generate_solution(problem_title, problem_url):
    if not USE_GEMINI:
        return generate_solution_with_openai(problem_title, problem_url)
    else:
        if not check_api_keys():
            return "Error: API keys not configured. Please set GEMINI_API_KEY environment variable."

        if not gemini_model:
            return "Error: Gemini client not initialized."

        try:
            response = gemini_model.generate_content(
                f"""Write a concise, optimized C++ solution for: {problem_title}

Requirements:
- Write SHORT, EFFICIENT code
- Use optimal algorithms and data structures
- Handle edge cases properly
- Focus on performance, not verbose explanations
- Use modern C++ features

Provide ONLY the concise C++ code."""
            )
            return response.text
        except Exception as e:
            return f"Error generating solution with Gemini: {e}"
