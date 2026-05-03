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
    "understand how Indian elections work. Default to India's election system "
    "(ECI, Lok Sabha, Rajya Sabha, EVM, EPIC voter ID, NVSP portal, Aachar Sanhita, BLO, SIR). "
    "Be educational, clear, and concise. Never advocate for any party or candidate. "
    "Use numbered lists for steps. If asked about another country, answer for that country."
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
        "question": "How many seats are there in the Lok Sabha?",
        "options": ["442", "543", "552", "600"],
        "correct_index": 1,
        "explanation": "The Lok Sabha has 543 elected seats. Members are directly elected by Indian citizens."
    },
    {
        "question": "What is the minimum age to vote in India?",
        "options": ["16", "18", "21", "25"],
        "correct_index": 1,
        "explanation": "Indian citizens aged 18 and above are eligible to vote as per Article 326 of the Constitution."
    },
    {
        "question": "Which body conducts elections in India?",
        "options": ["Supreme Court", "Parliament", "Election Commission of India", "UPSC"],
        "correct_index": 2,
        "explanation": "The Election Commission of India (ECI) is an autonomous constitutional authority responsible for administering elections."
    },
    {
        "question": "What is the EPIC card?",
        "options": ["Education Card", "Electors Photo Identity Card", "Election Process ID Card", "Emergency ID Card"],
        "correct_index": 1,
        "explanation": "EPIC stands for Electors Photo Identity Card, commonly known as the Voter ID card in India."
    },
    {
        "question": "How many seats does Rajya Sabha have?",
        "options": ["200", "245", "250", "300"],
        "correct_index": 1,
        "explanation": "Rajya Sabha has 245 seats \u2014 233 elected by state assemblies and 12 nominated by the President."
    },
    {
        "question": "What is the Model Code of Conduct (Aachar Sanhita)?",
        "options": ["A law passed by Parliament", "Guidelines for voters", "Rules for political parties during elections", "ECI internal rules"],
        "correct_index": 2,
        "explanation": "The Model Code of Conduct is a set of guidelines issued by ECI that parties and candidates must follow during campaigns."
    },
    {
        "question": "What portal is used to register as a voter in India?",
        "options": ["india.gov.in", "nvsp.in", "eci.gov.in", "voterportal.eci.gov.in"],
        "correct_index": 3,
        "explanation": "The Voter Service Portal at voterportal.eci.gov.in is the official portal for voter registration."
    },
    {
        "question": "When was the first general election held in India?",
        "options": ["1947", "1950", "1951-52", "1957"],
        "correct_index": 2,
        "explanation": "India's first general election was held in 1951-52, one of the largest democratic exercises in history."
    },
    {
        "question": "What is the ECI voter helpline number?",
        "options": ["100", "1800", "1950", "112"],
        "correct_index": 2,
        "explanation": "1950 is the National Voter Helpline. Citizens can call for voter registration and election information."
    },
    {
        "question": "What does BLO stand for in Indian elections?",
        "options": ["Block Level Officer", "Booth Level Officer", "Ballot Level Officer", "Border Liaison Officer"],
        "correct_index": 1,
        "explanation": "BLO stands for Booth Level Officer \u2014 a government official maintaining voter rolls for their assigned booth area."
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

@app.route("/seats")
def seats():
    """
    Renders the Parliament seat distribution page.
    
    Returns:
        Rendered HTML template for 'seats.html'.
    """
    return render_template("seats.html")

@app.route("/rights")
def rights():
    """
    Renders the voter rights and duties page.
    
    Returns:
        Rendered HTML template for 'rights.html'.
    """
    return render_template("rights.html")

@app.route("/history")
def history():
    """
    Renders the history of Indian elections page.
    
    Returns:
        Rendered HTML template for 'history.html'.
    """
    return render_template("history.html")

@app.route("/register")
def register():
    """
    Renders the voter registration guide page.
    
    Returns:
        Rendered HTML template for 'register.html'.
    """
    return render_template("register.html")

@app.route("/helpline")
def helpline():
    """
    Renders the ECI helplines and contacts page.
    
    Returns:
        Rendered HTML template for 'helpline.html'.
    """
    return render_template("helpline.html")

@app.route("/api/eci-info")
def eci_info():
    """
    Returns ECI contact information as JSON.
    
    Returns:
        JSON object with helpline numbers, email, and website URLs.
    """
    return jsonify({
        "helpline": "1950",
        "toll_free": "1800-111-950",
        "email": "complaints@eci.gov.in",
        "website": "https://eci.gov.in",
        "voter_portal": "https://voterportal.eci.gov.in"
    })

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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
