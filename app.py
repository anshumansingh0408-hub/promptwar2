"""
ElectionGuide - A neutral and non-partisan AI assistant for election education.

This Flask application serves the ElectionGuide web interface, providing an AI chatbot
powered by the Google Gemini API. It handles routes for the main interface, a visual
timeline, an interactive quiz, and securely processes chat requests with rate limiting
and input validation.
"""

import os
import time
import random
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

app = Flask(__name__)

# System Prompt for the AI
SYSTEM_PROMPT = (
    "You are ElectionGuide, a neutral and non-partisan AI assistant that helps people "
    "understand how elections work. Be educational, clear, and concise. Never advocate "
    "for any party or candidate. Use numbered lists for multi-step processes. Default to "
    "the INDIA election system (Election Commission of India, Lok Sabha, Vidhan Sabha, EVM voting, EPIC voter ID card, NVSP portal) unless the user specifically asks about another country. "
    "When talking about voter ID in India, refer to it as EPIC (Electors Photo Identity Card), explain that registration is done via the NVSP portal (nvsp.in) or Voter Helpline App, and eligibility requires being an Indian citizen aged 18 or above as on the qualifying date (January 1st of the registration year). "
    "If asked anything partisan, politely decline and redirect to civics facts."
)

# Configuration settings
CONFIG = {
    "MAX_MESSAGE_LENGTH": 500,
    "MAX_HISTORY_LENGTH": 10,
    "RATE_LIMIT_REQUESTS": 20,
    "RATE_LIMIT_WINDOW": 60,
    "MAX_TOKENS": 1024,
    "MODEL": "gemini-2.5-flash"  # Note: Updated from gemini-2.0-flash as it is deprecated
}

GEMINI_API_URL_TEMPLATE = f"https://generativelanguage.googleapis.com/v1beta/models/{CONFIG['MODEL']}:generateContent?key={{}}"

# Simple in-memory rate limiting dictionary
# Format: { "ip_address": {"count": int, "window_start": float} }
ip_requests = {}

# Hardcoded list of quiz questions
QUIZ_QUESTIONS = [
    {
        "question": "What is the primary purpose of the Electoral College?",
        "options": ["To elect the President and Vice President", "To make laws", "To judge Supreme Court cases", "To manage the economy"],
        "correct_index": 0,
        "explanation": "The Electoral College is a process, not a place. The founding fathers established it in the Constitution as a compromise between election of the President by a vote in Congress and election of the President by a popular vote of qualified citizens."
    },
    {
        "question": "When is Election Day held in the United States?",
        "options": ["First Monday in November", "First Tuesday after the first Monday in November", "November 1st", "Last Tuesday in October"],
        "correct_index": 1,
        "explanation": "Election Day is statutorily set by the U.S. government as the Tuesday following the first Monday in November."
    },
    {
        "question": "How many total electoral votes are there in the U.S. Electoral College?",
        "options": ["435", "50", "538", "100"],
        "correct_index": 2,
        "explanation": "There are 538 electoral votes in total, corresponding to the 435 Representatives, 100 Senators, and 3 electors for the District of Columbia."
    },
    {
        "question": "What happens if no presidential candidate receives a majority of electoral votes?",
        "options": ["A national run-off election is held", "The current president stays in power", "The House of Representatives elects the President", "The Supreme Court decides"],
        "correct_index": 2,
        "explanation": "If no candidate receives the required 270 electoral votes, the 12th Amendment dictates that the House of Representatives elects the President from the top three candidates."
    },
    {
        "question": "Which of these is a common method of voting in the U.S. prior to Election Day?",
        "options": ["Telepathy", "Mail-in voting", "Voting by proxy", "Internet voting"],
        "correct_index": 1,
        "explanation": "Mail-in voting (or absentee voting) allows voters to cast their ballots through the mail prior to Election Day."
    },
    {
        "question": "What is a 'Primary Election'?",
        "options": ["An election to choose the final president", "An election where political parties choose their candidates", "An election for local mayors only", "An election held every year"],
        "correct_index": 1,
        "explanation": "Primary elections are held by political parties to nominate their candidates for the general election."
    },
    {
        "question": "When are the results of the presidential election officially certified by Congress?",
        "options": ["Election Night", "December 14", "January 6", "January 20"],
        "correct_index": 2,
        "explanation": "Following the general election and the meeting of the electors in December, Congress meets in a joint session on January 6 to count and certify the electoral votes."
    },
    {
        "question": "What is the minimum voting age in the United States?",
        "options": ["16", "18", "21", "25"],
        "correct_index": 1,
        "explanation": "The 26th Amendment to the U.S. Constitution, ratified in 1971, lowered the voting age from 21 to 18."
    },
    {
        "question": "What is Inauguration Day?",
        "options": ["The day candidates announce they are running", "The day the President-elect takes the oath of office", "The day voting begins", "The day the Electoral College votes"],
        "correct_index": 1,
        "explanation": "Inauguration Day occurs on January 20th and marks the formal commencement of a new four-year term for the President of the United States."
    },
    {
        "question": "Who can register to vote in U.S. federal elections?",
        "options": ["Any resident of the U.S.", "U.S. citizens who meet age and residency requirements", "Only property owners", "Anyone who pays taxes"],
        "correct_index": 1,
        "explanation": "To vote in a federal election, you must be a U.S. citizen, meet your state's residency requirements, and be 18 years old on or before Election Day."
    }
]

@app.after_request
def add_security_headers(response):
    """
    Appends security headers to every HTTP response.
    
    Adds headers to prevent MIME-sniffing, block clickjacking (framing), 
    and enable cross-site scripting (XSS) protections.
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route("/")
def index():
    """
    Renders the main chat interface page.
    
    Returns:
        Rendered HTML template for 'index.html'.
    """
    return render_template("index.html")

@app.route("/timeline")
def timeline():
    """
    Renders the visual election timeline page.
    
    Returns:
        Rendered HTML template for 'timeline.html'.
    """
    return render_template("timeline.html")

@app.route("/api/quiz")
def get_quiz():
    """
    Returns a random quiz question from the hardcoded list.
    
    Returns:
        JSON object containing a random question, options, correct_index, and explanation.
    """
    question = random.choice(QUIZ_QUESTIONS)
    return jsonify(question)

@app.route("/chat", methods=["POST"])
def chat():
    """
    Handles chat messages from the user, forwards them to the Gemini API,
    and returns the AI's response.
    
    Implements:
    - IP-based rate limiting
    - Input sanitization and validation
    - Chat history validation and truncation
    
    Returns:
        JSON response with the AI's reply or an error message and code.
    """
    # 1. Rate Limiting
    client_ip = request.remote_addr
    current_time = time.time()
    
    if client_ip in ip_requests:
        ip_data = ip_requests[client_ip]
        if current_time - ip_data["window_start"] > CONFIG["RATE_LIMIT_WINDOW"]:
            # Reset window
            ip_requests[client_ip] = {"count": 1, "window_start": current_time}
        else:
            if ip_data["count"] >= CONFIG["RATE_LIMIT_REQUESTS"]:
                return jsonify({"error": "Too many requests. Please wait a minute.", "code": "RATE_LIMIT_EXCEEDED"}), 429
            ip_requests[client_ip]["count"] += 1
    else:
        ip_requests[client_ip] = {"count": 1, "window_start": current_time}

    # 2. API Key Verification
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"error": "Gemini API key is not configured properly.", "code": "MISSING_API_KEY"}), 500

    # 3. Request Validation
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid request body, expected JSON.", "code": "INVALID_JSON"}), 400

    user_message = data.get("message", "")
    if not isinstance(user_message, str):
        return jsonify({"error": "Message must be a string.", "code": "INVALID_MESSAGE_TYPE"}), 400

    # 4. Input Sanitization
    user_message = user_message.strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty.", "code": "EMPTY_MESSAGE"}), 400
        
    if len(user_message) > CONFIG["MAX_MESSAGE_LENGTH"]:
        return jsonify({"error": f"Message exceeds maximum length of {CONFIG['MAX_MESSAGE_LENGTH']} characters.", "code": "MESSAGE_TOO_LONG"}), 400

    history = data.get("history", [])
    if not isinstance(history, list):
        return jsonify({"error": "History must be a list.", "code": "INVALID_HISTORY_TYPE"}), 400

    # 5. History Validation and Truncation
    # Limit history to the last N messages to prevent abuse
    history = history[-CONFIG["MAX_HISTORY_LENGTH"]:]
    
    gemini_contents = []
    for msg in history:
        if not isinstance(msg, dict):
            continue
            
        role = msg.get("role")
        content = msg.get("content")
        
        # Validate that the item only has 'role' and 'content' keys
        if set(msg.keys()) - {"role", "content"}:
             return jsonify({"error": "History items can only contain 'role' and 'content' keys.", "code": "INVALID_HISTORY_SCHEMA"}), 400

        if role not in ["user", "model", "assistant"]:
             return jsonify({"error": f"Invalid role in history: {role}", "code": "INVALID_HISTORY_ROLE"}), 400

        if not isinstance(content, str):
             return jsonify({"error": "History content must be a string.", "code": "INVALID_HISTORY_CONTENT"}), 400

        if role == "assistant":
            role = "model"
        
        gemini_contents.append({
            "role": role,
            "parts": [{"text": content}]
        })
    
    # Append the latest user message
    gemini_contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": gemini_contents,
        "generationConfig": {
            "maxOutputTokens": CONFIG["MAX_TOKENS"]
        }
    }

    headers = {
        "Content-Type": "application/json"
    }
    
    api_url = GEMINI_API_URL_TEMPLATE.format(api_key)

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        response_data = response.json()
        
        reply_text = ""
        # Extract reply text from Gemini response structure
        try:
            reply_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return jsonify({"error": "I'm sorry, I couldn't generate a response.", "code": "API_RESPONSE_PARSING_ERROR"}), 500

        return jsonify({"reply": reply_text})

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to Gemini API timed out.", "code": "API_TIMEOUT"}), 504
    except requests.exceptions.HTTPError as e:
        try:
            error_details = response.json()
        except Exception:
            error_details = str(e)
        return jsonify({"error": "Gemini API returned an error.", "code": "API_HTTP_ERROR", "details": error_details}), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error when connecting to Gemini API: {str(e)}", "code": "API_NETWORK_ERROR"}), 502
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}", "code": "INTERNAL_SERVER_ERROR"}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
