# ElectionGuide — Interactive Election Process AI Assistant

ElectionGuide is a neutral, non-partisan AI chatbot designed to educate users on election processes, timelines, voter registration, and general civics. By leveraging an interactive conversation interface, the assistant demystifies complex electoral systems to encourage informed and active citizen participation. This project was proudly built for the **Virtual PromptWars hackathon on Hack2skill**.

## Features

*   **Step-by-Step Guidance:** Learn about the entire election lifecycle, from voter registration to result declaration.
*   **Neutral AI Chatbot:** Get immediate, unbiased answers to civics questions powered by Anthropic's Claude.
*   **Quick Topics:** Instantly ask about popular topics like Election Timelines, Mail-in Voting, and the Electoral College via clickable chips.
*   **Modern UI:** A beautiful, responsive interface featuring dynamic chat bubbles, typing animations, and custom typography.
*   **Accessible Design:** High-contrast elements, responsive layout, and readable fonts ensure usability for a diverse audience.

## Tech Stack

- Python + Flask (backend)
- Google Gemini API (gemini-2.0-flash) — Powers the AI chat assistant
- Tailwind CSS via CDN (frontend)
- Vanilla JavaScript (no frameworks)

## Setup & Run

Follow these steps to run the application locally on your machine:

1. **Clone the repository (or navigate to the project folder):**
   ```bash
   cd election-ai-assistant
   ```

2. **Create a virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   
   # Mac/Linux
   python3 -m venv venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

4. **Install the dependencies:**
   ```bash
   pip install flask requests
   ```

5. **Set up your API Key:**
   Create a `.env` file in the root directory (if not already present) and add your Anthropic API key:
   ```env
   ANTHROPIC_API_KEY=your_actual_key_here
   ```
   *(Alternatively, you can export it directly in your terminal: `export ANTHROPIC_API_KEY=your_key`)*

6. **Run the application:**
   ```bash
   python app.py
   ```

7. **Test the app:**
   Open your browser and navigate to `http://127.0.0.1:5000`

## Project Structure

```text
election-ai-assistant/
├── app.py               # Main Flask application and API routes
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (API Key)
├── .gitignore           # Ignored files for Git
├── README.md            # Project documentation
└── templates/
    ├── base.html        # Base Jinja2 template with Tailwind setup
    └── index.html       # Chatbot interface and JavaScript logic
```

## Disclaimer

**This tool is strictly educational and non-partisan.** It does not endorse any political party, candidate, or position. All information provided by the AI should be verified with official government sources, especially regarding critical deadlines and localized voting rules.
