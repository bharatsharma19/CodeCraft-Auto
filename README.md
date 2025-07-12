# CodeCraft-Auto: Automated Daily POTD Solver

A production-ready automated system that solves the daily coding problems from LeetCode and GeeksforGeeks. It uses AI to generate solutions, validates them, and handles submission with a persistent browser session to bypass modern anti-bot protections.

## 🚀 Key Features

- **🤖 AI-Powered Solutions**: Generates high-quality C++ solutions using OpenAI (GPT-4) or Google Gemini.
- **🛡️ Persistent Login Sessions**: Uses a dedicated Chrome profile to maintain login sessions, bypassing CAPTCHAs and login forms on subsequent runs.
- **✅ Compilation Validation**: Ensures AI-generated code is syntactically correct and compiles successfully before any submission attempt.
- **🔄 Smart Retry Logic**: If the AI generates a non-compiling solution, it retries with a different prompt to get an alternative solution.
- **📧 HTML Email Notifications**: Sends beautifully formatted HTML emails for manual intervention if automation fails, with correctly formatted code blocks.
- **💾 Local Solution Caching**: Saves valid, compiled solutions locally to avoid redundant API calls on the same day.
- **🚀 GitHub Actions Ready**: Designed for automated daily execution via GitHub Actions.
- **🌐 Full GFG & LeetCode Support**: Handles login, scraping, and submission for both platforms.

## 🔧 System Architecture & Workflow

The system is designed for resilience against modern web application challenges like client-side rendering and anti-bot measures.

```
graph TD
    A[Start] --> B{Initialize Browser with Persistent Profile};
    B --> C{Process LeetCode};
    C --> D{Process GFG};
    D --> E[End & Cleanup];

    subgraph Process LeetCode
        C1[Fetch POTD Info] --> C2{Check for Local Solution};
        C2 -- No --> C3[Generate & Compile Solution];
        C2 -- Yes --> C4[Submit Solution];
        C3 --> C4;
        C4 -- Success --> C5[Log Success];
        C4 -- Failure --> C6[Send Email Alert];
    end

    subgraph Process GFG
        D1[Fetch POTD with Browser] --> D2{Check for Local Solution};
        D2 -- No --> D3[Generate & Compile Solution];
        D2 -- Yes --> D4[Submit Solution];
        D3 --> D4;
        D4 -- Success --> D5[Log Success];
        D4 -- Failure --> D6[Send Email Alert];
    end
```

### Detailed Process:

1.  **Initialize Browser**: The script launches a Chrome browser using a persistent user profile, which stores login cookies.
2.  **One-Time Manual Login**: On the very first run, the user must manually log in to LeetCode and GFG in the opened browser window.
3.  **Session Restoration**: On all future runs, the browser loads the profile and is already logged in, bypassing CAPTCHAs.
4.  **Problem Fetching**:
    - **LeetCode**: Fetches POTD info via its GraphQL API.
    - **GFG**: Uses the live browser to navigate to the POTD page, ensuring all JavaScript-rendered content is available for scraping.
5.  **Solution Generation**: If no valid local solution exists, the AI is prompted with a highly detailed request to generate a correct and efficient C++ solution.
6.  **Compilation Check**: The generated code is compiled to ensure it's syntactically valid. If it fails, the system retries with a new prompt.
7.  **Submission**: The validated solution is pasted into the editor and submitted. The script waits for a definitive success or failure result.
8.  **Notification**: If any step fails in a way that requires user intervention (e.g., submission timeout), a detailed HTML email is sent.

## 🛠️ Setup and Usage

### Step 1: Clone the Repository

```
git clone https://github.com/bharatsharma19/CodeCraft-Auto.git
cd CodeCraft-Auto
```

### Step 2: Install Dependencies

It is highly recommended to use a virtual environment.

```
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a file named `.env` in the root of your project and add your credentials.

```
# --- AI Configuration ---
# Set to "True" for Gemini, "False" for OpenAI
USE_GEMINI=True
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key

# --- LeetCode Login Credentials ---
LEETCODE_USERNAME=your-leetcode-username
LEETCODE_PASSWORD=your-leetcode-password

# --- GFG Login Credentials ---
GFG_USERNAME=your-gfg-email@example.com
GFG_PASSWORD=your-gfg-password

# --- Email Notification Credentials (use a Gmail App Password) ---
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### Step 4: One-Time Manual Login (Crucial!)

This step is only required once. It saves your login sessions to bypass CAPTCHAs in the future.

1.  Run the script for the first time:
2.  A Chrome browser window will open. **Do not close it.**
3.  In the opened browser, **manually log in to LeetCode**. Check any "Remember Me" boxes.
4.  In a new tab in the **same browser window**, **manually log in to GeeksforGeeks**.
5.  Once you are logged into both sites, you can close the browser window. The script will have created a `chrome_profile` directory containing your session data.

### Step 5: Run the Automated System

All subsequent runs will be fully automatic.

```
python automated_potd_system.py
```

## 🚀 GitHub Actions Setup

To run this system automatically every day:

1.  **Fork the repository** to your GitHub account.
2.  Go to your repository's **Settings > Secrets and variables > Actions**.
3.  Create the following **Repository secrets** and paste the corresponding values from your `.env` file:
    - `USE_GEMINI`
    - `GEMINI_API_KEY`
    - `OPENAI_API_KEY`
    - `LEETCODE_USERNAME`
    - `LEETCODE_PASSWORD`
    - `GFG_USERNAME`
    - `GFG_PASSWORD`
    - `EMAIL_ADDRESS`
    - `EMAIL_PASSWORD`
4.  The workflow file (`.github/workflows/main.yml`) is already configured to run daily. It will use these secrets to execute the script.

## 🔧 Troubleshooting

- **Login Fails / CAPTCHA Appears:** Your saved session might have expired. Delete the `chrome_profile` directory from your project and re-run the one-time manual login step.
- **GFG Scraper Fails:** GeeksforGeeks may have changed their website layout. The selectors in `submission_manager.py` inside the `get_gfg_potd_with_browser` function may need to be updated.
- `**Read timed out**` **Error:** This can happen if your internet connection is slow or the target website is under heavy load. The script has long timeouts, but this can still occur. Simply re-running it often resolves the issue.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request.

1.  Fork the repository.
2.  Create a new feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

```
python automated_potd_system.py
```
