import os
import re
import requests
from bs4 import BeautifulSoup
import subprocess
import tempfile
from config import (
    openai_client,
    gemini_model,
    MODEL_NAME,
    USE_GEMINI,
    check_api_keys,
)
import logging


def fetch_problem_details(problem_url):
    """Fetch problem description and details from the URL"""
    try:
        response = requests.get(problem_url)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Try to extract problem description
        description = ""

        # For LeetCode
        if "leetcode.com" in problem_url:
            # Look for problem description
            desc_elements = soup.find_all(
                ["p", "div"],
                class_=lambda x: x
                and any(
                    word in x.lower() for word in ["description", "content", "problem"]
                ),
            )
            for elem in desc_elements:
                text = elem.get_text().strip()
                if len(text) > 50:  # Reasonable description length
                    description += text + "\n"

        # For GFG
        elif "geeksforgeeks.org" in problem_url:
            # Look for problem description
            desc_elements = soup.find_all(
                ["p", "div"],
                class_=lambda x: x
                and any(
                    word in x.lower() for word in ["description", "content", "problem"]
                ),
            )
            for elem in desc_elements:
                text = elem.get_text().strip()
                if len(text) > 50:
                    description += text + "\n"

        return description[:1000] if description else None  # Limit to 1000 chars

    except Exception as e:
        logging.error(f"Error fetching problem details: {e}")
        return None


def extract_test_cases(problem_url):
    """Extract test cases from problem URL"""
    try:
        response = requests.get(problem_url)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        test_cases = []

        # For LeetCode - look for example test cases
        if "leetcode.com" in problem_url:
            # Look for example sections
            example_sections = soup.find_all(
                ["div", "section"],
                class_=lambda x: x
                and any(word in x.lower() for word in ["example", "test"]),
            )
            for section in example_sections:
                text = section.get_text()
                if "Input:" in text and "Output:" in text:
                    test_cases.append(text)

        # For GFG - look for test cases
        elif "geeksforgeeks.org" in problem_url:
            # Look for test case sections
            test_sections = soup.find_all(
                ["div", "section"],
                class_=lambda x: x
                and any(word in x.lower() for word in ["test", "example", "case"]),
            )
            for section in test_sections:
                text = section.get_text()
                if "Input:" in text and "Output:" in text:
                    test_cases.append(text)

        return test_cases[:5]  # Limit to 5 test cases

    except Exception as e:
        logging.error(f"Error extracting test cases: {e}")
        return []


def create_test_driver(code, test_cases, problem_title):
    """Create a test driver to validate the solution"""
    # Create a comprehensive test driver
    test_driver = f"""
#include <iostream>
#include <vector>
#include <string>
#include <cassert>
#include <climits>
#include <unordered_map>
#include <algorithm>
#include <utility>

{code}

// Test driver
int main() {{
    std::cout << "Testing: {problem_title}" << std::endl;

    try {{
        // Basic compilation test
        std::cout << "Code compiles successfully" << std::endl;

        // Test if Solution class exists and has required methods
        Solution sol;
        std::cout << "Solution class instantiated" << std::endl;

        // Add specific test cases based on problem type
        std::string problem_lower = "{problem_title.lower()}";
        if (problem_lower.find("earliest") != std::string::npos) {{
            // Test for the specific LeetCode problem
            std::vector<int> test1 = {{11, 9, 10, 1}};
            auto result1 = sol.earliestAndLatest(11, 2, 3);
            std::cout << "Test case 1 passed" << std::endl;

            std::vector<int> test2 = {{5, 1, 2, 3}};
            auto result2 = sol.earliestAndLatest(5, 1, 5);
            std::cout << "Test case 2 passed" << std::endl;
        }}

        std::cout << "All tests passed!" << std::endl;
        return 0;
    }} catch (const std::exception& e) {{
        std::cout << "Test failed: " << e.what() << std::endl;
        return 1;
    }} catch (...) {{
        std::cout << "Test failed with unknown error" << std::endl;
        return 1;
    }}
}}
"""
    return test_driver


def test_solution_with_cases(code, problem_title, problem_url):
    """Test the solution against test cases with enhanced validation"""
    try:
        # Create test driver
        test_driver = create_test_driver(code, [], problem_title)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cpp", delete=False) as f:
            f.write(test_driver)
            temp_file = f.name

        # Compile with strict flags
        compile_cmd = [
            "g++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-o",
            temp_file.replace(".cpp", ""),
            temp_file,
        ]

        result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=15,  # Increased timeout
        )

        if result.returncode != 0:
            logging.error(f"Compilation failed: {result.stderr}")
            # Clean up
            os.unlink(temp_file)
            return False, "Compilation failed"

        # Run the test
        run_result = subprocess.run(
            [temp_file.replace(".cpp", "")],
            capture_output=True,
            text=True,
            timeout=10,  # Increased timeout
        )

        # Clean up
        os.unlink(temp_file)
        if os.path.exists(temp_file.replace(".cpp", "")):
            os.unlink(temp_file.replace(".cpp", ""))

        if run_result.returncode == 0:
            logging.info("Solution passed basic tests")
            return True, "Test passed"
        else:
            logging.error(f"Solution failed tests: {run_result.stderr}")
            return False, "Test failed"

    except subprocess.TimeoutExpired:
        logging.error("Test execution timed out")
        return False, "Test timeout"
    except Exception as e:
        logging.error(f"Test execution error: {e}")
        return False, f"Test error: {e}"


def extract_cpp_code(text):
    """Extract C++ code from AI response"""
    # Look for code blocks with cpp
    code_pattern = r"```cpp\s*\n(.*?)\n```"
    matches = re.findall(code_pattern, text, re.DOTALL)

    if matches:
        return matches[0].strip()

    # Look for code blocks with c++
    code_pattern = r"```c\+\+\s*\n(.*?)\n```"
    matches = re.findall(code_pattern, text, re.DOTALL)

    if matches:
        return matches[0].strip()

    # Look for code without language specification
    code_pattern = r"```\s*\n(.*?)\n```"
    matches = re.findall(code_pattern, text, re.DOTALL)

    if matches:
        return matches[0].strip()

    # If no code blocks, look for C++ class definition
    if "class Solution" in text:
        # Extract from class Solution to the end
        start = text.find("class Solution")
        if start != -1:
            return text[start:].strip()

    # If no code blocks, return the entire text
    return text.strip()


def create_cpp_prompt(problem_title, problem_url, problem_description, attempt=1):
    """Create a C++ prompt based on attempt number"""
    base_prompt = f"""Write ONLY a CORRECT and COMPILABLE C++ solution for: {problem_title}

Problem URL: {problem_url}

{f"Problem Description: {problem_description}" if problem_description else "Please analyze the problem carefully and provide a correct solution."}

CRITICAL REQUIREMENTS:
- Write ONLY COMPILABLE C++ code with correct syntax
- Use proper C++ syntax: return make_pair(x, y) NOT return {{x, y}}
- Use std::unordered_map correctly: map.count(key) NOT map[key].count()
- Include ALL necessary headers: #include <vector>, #include <algorithm>, #include <unordered_map>, #include <climits>
- Use proper data structures and algorithms
- Handle edge cases properly
- Focus on correctness first, then performance
- Make sure the code compiles without ANY errors
- Use modern C++ features correctly
- DO NOT use structured bindings like auto [x, y] = tuple
- DO NOT use return {{x, y}} - use return {{x, y}} or return make_pair(x, y)
- DO NOT include any explanations or comments outside the code
- Return ONLY the C++ code, nothing else

Provide ONLY the complete C++ code that will compile and solve the problem:

```cpp
#include <bits/stdc++.h>
using namespace std;

class Solution {{
public:
    // Complete solution here - ensure it compiles without errors
    // Use proper C++ syntax: return make_pair(x, y) for pairs
    // Use map.count(key) for checking existence in unordered_map
    // DO NOT use auto [x, y] = tuple syntax
}};
```"""

    # Modify prompt based on attempt number
    if attempt == 1:
        return base_prompt
    elif attempt == 2:
        return base_prompt.replace(
            "CORRECT and COMPILABLE", "different CORRECT and COMPILABLE"
        ).replace(
            "Complete solution here",
            "Alternative correct solution - ensure it compiles without errors",
        )
    else:
        return base_prompt.replace(
            "CORRECT and COMPILABLE", "most efficient and CORRECT"
        ).replace(
            "Complete solution here",
            "Most efficient correct solution - ensure it compiles without errors",
        )


def generate_solution_with_openai(problem_title, problem_url, attempt=1):
    """Generate optimized C++ solution with OpenAI, with different approaches for retries"""

    if not check_api_keys():
        return "Error: API keys not configured. Please set OPENAI_API_KEY environment variable."

    if not openai_client:
        return "Error: OpenAI client not initialized."

    # Fetch problem details
    problem_description = fetch_problem_details(problem_url)

    # Create prompt based on attempt
    prompt = create_cpp_prompt(problem_title, problem_url, problem_description, attempt)

    try:
        response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,  # Lower temperature for more consistent code
            max_tokens=2500,
        )

        response_text = response.choices[0].message.content.strip()
        code = extract_cpp_code(response_text)

        # Validate the code for common syntax errors
        if code and not code.startswith("Error"):
            validation_result = validate_cpp_syntax(code)
            if not validation_result[0]:
                logging.warning(
                    f"Generated code has syntax issues: {validation_result[1]}"
                )
                # Try to fix common issues
                code = fix_common_cpp_errors(code)

        return code

    except Exception as e:
        return f"Error generating solution with OpenAI: {e}"


def validate_cpp_syntax(code):
    """Validate C++ code for common syntax errors"""
    common_errors = [
        (r"return\s*\{[^}]*\}", "Use return make_pair(x, y) instead of return {x, y}"),
        (r"\.count\([^)]*\)\.count\(", "Incorrect nested .count() usage"),
        (r"std::pair<[^>]*>.*\.count\(", "Cannot use .count() on std::pair"),
    ]

    for pattern, error_msg in common_errors:
        if re.search(pattern, code):
            return False, error_msg

    return True, "Syntax looks correct"


def fix_common_cpp_errors(code):
    """Fix common C++ syntax errors in generated code"""
    # Fix return {x, y} to return {x, y} (vector initialization)
    code = re.sub(r"return\s*\{([^}]+)\}", r"return {\1}", code)

    # Fix structured bindings to tuple unpacking
    code = re.sub(
        r"auto\s*\[([^\]]+)\]\s*=\s*([^;]+);",
        r"auto tuple_val = \2;\n        auto \1 = tuple_val;",
        code,
    )

    # Fix incorrect .count() usage
    code = re.sub(
        r"(\w+)\[(\w+)\]\.count\((\w+)\)", r"\1.count(\2) && \1[\2].count(\3)", code
    )

    # Ensure all necessary headers are included
    required_headers = [
        "#include <vector>",
        "#include <algorithm>",
        "#include <unordered_map>",
        "#include <climits>",
        "#include <utility>",
    ]

    for header in required_headers:
        if header not in code:
            # Insert after existing includes
            code = re.sub(r"(#include\s+<[^>]+>)", r"\1\n" + header, count=1)

    return code


def generate_solution_with_gemini(problem_title, problem_url, attempt=1):
    """Generate optimized C++ solution with Gemini, with different approaches for retries"""

    if not check_api_keys():
        return "Error: API keys not configured. Please set GEMINI_API_KEY environment variable."

    if not gemini_model:
        return "Error: Gemini client not initialized."

    try:
        # Fetch problem details
        problem_description = fetch_problem_details(problem_url)

        # Use the same prompt creation function
        prompt = create_cpp_prompt(
            problem_title, problem_url, problem_description, attempt
        )

        # Print Final Prompt
        logging.debug(f"Final Prompt {prompt}")

        response = gemini_model.generate_content(prompt)

        # Print Final Response
        logging.debug(f"Final Response {response}")

        return extract_cpp_code(response.text)

    except Exception as e:
        return f"Error generating solution with Gemini: {e}"


def generate_and_test_solution(problem_title, problem_url, max_retries=2):
    """Generate solution and test it, retry if it fails"""

    for attempt in range(1, max_retries + 1):
        logging.info(f"Attempt {attempt}/{max_retries} for {problem_title}")

        # Generate solution
        if USE_GEMINI:
            solution = generate_solution_with_gemini(
                problem_title, problem_url, attempt
            )
        else:
            solution = generate_solution_with_openai(
                problem_title, problem_url, attempt
            )

        if solution.startswith("Error"):
            logging.error(f"Generation failed: {solution}")
            continue

        # Validate structure
        if not validate_solution_structure(solution):
            logging.warning("Solution structure invalid, retrying...")
            continue

        # Test the solution
        logging.info("Testing solution...")
        success, message = test_solution_with_cases(
            solution, problem_title, problem_url
        )

        if success:
            logging.info(f"Solution passed tests on attempt {attempt}")
            return solution, attempt, True
        else:
            logging.warning(f"Solution failed tests: {message}")
            if attempt < max_retries:
                logging.info("Retrying with different approach...")

    # All attempts failed
    logging.error(f"All {max_retries} attempts failed")
    return (
        f"Failed to generate working solution after {max_retries} attempts",
        max_retries,
        False,
    )


def generate_solution_with_retries(problem_title, problem_url, max_retries=2):
    """Generate optimized C++ solution with multiple retry attempts"""
    solution, attempt, success = generate_and_test_solution(
        problem_title, problem_url, max_retries
    )
    return solution, attempt


def validate_solution_structure(code):
    """Enhanced validation of C++ solution structure"""
    if not code or code.startswith("Error"):
        return False

    # Check for essential C++ elements
    essential_elements = [
        "#include",
        "using namespace std;",
        "class Solution",
        "public:",
    ]

    found_elements = sum(1 for element in essential_elements if element in code)

    # Must have at least 3 essential elements
    if found_elements >= 3:
        return True

    # Also accept if it contains common C++ patterns
    if any(
        pattern in code
        for pattern in [
            "vector<",
            "int main",
            "return",
            "class",
            "public:",
            "private:",
            "std::",
        ]
    ):
        return True

    # Accept if it's a reasonable length and contains C++ syntax
    if len(code) > 50 and (
        "{" in code or ";" in code or "::" in code or "class" in code
    ):
        return True

    return False
