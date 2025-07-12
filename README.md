# Enhanced Automated Daily POTD Solver

An enhanced automated system that solves daily problems from LeetCode and GeeksforGeeks (GFG), with **test case validation**, **automatic retries**, **email notifications**, and **LeetCode login support**.

## 🚀 Key Features

- 🤖 **AI-Powered Solutions**: Generates solutions using OpenAI GPT-4 or Google Gemini
- 🧪 **Test Case Validation**: Tests solutions against actual test cases before accepting
- 🔄 **Smart Retry System**: Retries up to 3 times with different approaches if solution fails
- 📧 **Email Notifications**: Sends detailed email alerts when all attempts fail
- 💾 **Local Storage**: Saves working solutions locally to avoid regenerating
- 🚀 **GitHub Actions**: Automated daily execution via GitHub Actions
- ✅ **Compilation Testing**: Ensures generated code compiles successfully
- 🔐 **LeetCode Login**: Supports authenticated submissions to LeetCode

## 🔧 Enhanced Workflow

```
1. Fetch Problem → 2. Generate Solution → 3. Test Solution → 4. Login & Submit or Retry
     ↓                    ↓                    ↓                    ↓
   Problem URL        AI Generation      Test Cases         Success/Email
```

### Detailed Process:

1. **Problem Fetching**: Gets daily problems from LeetCode and GFG
2. **Solution Generation**: AI generates C++ solution with problem context
3. **Test Case Validation**:
   - Compiles the solution
   - Runs basic test cases
   - Validates solution structure
4. **Retry Logic**: If tests fail, generates new solution (max 3 attempts)
5. **Login & Submission**: Logs into LeetCode and submits working solution
6. **Email Notification**: Sends email if all attempts fail

## System Architecture

```
├── enhanced_solution_manager.py  # AI solution generation with testing
├── automated_potd_system.py     # Main orchestration system
├── submission_manager.py         # Web automation, login, and email notifications
├── problem_fetcher.py           # Problem fetching from platforms
├── solution_manager.py          # Local storage management
├── config.py                   # Configuration and credentials
└── test_*.py                   # Test files for various components
```

## 🔐 LeetCode Login Setup

To enable LeetCode submissions, you need to set up your LeetCode credentials:

### 1. Environment Variables

Add these to your `.env` file or set as environment variables:

```bash
# LeetCode Credentials (Required for submissions)
LEETCODE_USERNAME=your-leetcode-username
LEETCODE_PASSWORD=your-leetcode-password

# Existing variables
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### 2. Test Login

Run the login test to verify your credentials:

```bash
python test_leetcode_login.py
```

### 3. Advanced Testing (if login fails)

If the basic login test fails, try these comprehensive tests:

```bash
# Test comprehensive login with advanced button handling
python test_comprehensive_login.py

# Test advanced Cloudflare bypass
python test_cloudflare_advanced.py

# Test manual login simulation
python test_manual_login.py

# Test button enable strategies
python test_button_enable.py
```

### 4. Security Notes

- **Never commit credentials** to version control
- Use environment variables or `.env` files
- Consider using app-specific passwords if available
- Regularly update your credentials

## 🧪 Test Case Validation

The enhanced system includes:

1. **Compilation Testing**: Ensures code compiles without errors
2. **Structure Validation**: Checks for essential C++ elements
3. **Basic Test Cases**: Runs simple test scenarios
4. **Error Handling**: Catches and reports compilation errors

## 🔄 Smart Retry Logic

The system now distinguishes between:

### Solution Correctness Failures

- Wrong Answer, Runtime Error, Time Limit Exceeded
- **Action**: Generate new solution

### UI/Automation Failures

- Could not find submit button, browser issues
- **Action**: Retry submission with same solution

This prevents wasting good solutions when submission fails due to UI issues.

## 📧 Email Notification System

The system sends email notifications when:

- All 3 solution generation attempts fail
- All 3 submission attempts fail
- Solution structure is invalid
- Any critical error occurs

Email includes:

- Platform (LeetCode/GFG)
- Problem title and URL
- Detailed error message
- Number of attempts made

## 🔧 GitHub Actions Setup

1. **Add Secrets** to your GitHub repository:

   - `OPENAI_API_KEY`
   - `GEMINI_API_KEY` (optional)
   - `EMAIL_ADDRESS`
   - `EMAIL_PASSWORD`
   - `LEETCODE_USERNAME`
   - `LEETCODE_PASSWORD`

2. **Workflow**: The system runs daily at 10:00 UTC via GitHub Actions

## 🛠️ Production Deployment & Usage

This system is now production-ready. Only the following files are required:

- `automated_potd_system.py` (main orchestrator)
- `config.py` (configuration loader)
- `enhanced_solution_manager.py` (AI and validation logic)
- `problem_fetcher.py` (fetches problems)
- `solution_manager.py` (solution storage/generation)
- `submission_manager.py` (handles submission and email)
- `requirements.txt`
- `README.md`

All test and debug scripts have been removed for production. For troubleshooting, use logging as described below.

## 🪵 Logging & Error Handling

- All system output now uses Python's `logging` module.
- Logs are output to the console with timestamps and severity levels.
- For production, you can redirect logs to a file or external logging system by adjusting the `logging.basicConfig` call in `automated_potd_system.py`.
- All errors are logged with appropriate severity (`logging.error`, `logging.warning`, etc.).

## 🔧 Configuration

- All credentials and API keys must be set via environment variables or a `.env` file.
- See `config.py` for details on required variables.

## 🚀 Usage

Run the complete system:

```bash
python automated_potd_system.py
```

## 📦 Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

## 📊 Features Summary

| Feature                | Status | Description                           |
| ---------------------- | ------ | ------------------------------------- |
| AI Solution Generation | ✅     | OpenAI GPT-4 or Google Gemini         |
| Test Case Validation   | ✅     | Compilation and basic testing         |
| Smart Retry Logic      | ✅     | Distinguishes solution vs UI failures |
| LeetCode Login         | ✅     | Authenticated submissions             |
| Email Notifications    | ✅     | Failure alerts with details           |
| Local Storage          | ✅     | Saves working solutions               |
| GitHub Actions         | ✅     | Automated daily execution             |
| GFG Support            | ✅     | GeeksforGeeks integration             |

## 🔧 Troubleshooting

### Common Issues

1. **LeetCode Login Fails**

   - Verify credentials are correct
   - Check if 2FA is enabled (may need app password)
   - Ensure account is not locked

2. **Submit Button Not Found**

   - System will retry with same solution
   - Check if LeetCode UI has changed
   - Verify login was successful

3. **Solution Generation Fails**
   - Check API keys are valid
   - Verify internet connection
   - Check API rate limits

### Debug Mode

Run with verbose logging:

```bash
python -u automated_potd_system.py
```

## 📈 Performance

- **Solution Generation**: ~30-60 seconds per attempt
- **Test Case Validation**: ~5-10 seconds
- **LeetCode Submission**: ~15-30 seconds
- **Total Runtime**: ~2-5 minutes per platform

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
