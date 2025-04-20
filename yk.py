import streamlit as st
import json
from groq import Groq
from dotenv import dotenv_values
import datetime
import os
import openai

# Load API key and assistant name from .env
config = dotenv_values(".env")
API_KEY = config.get("GroqAPIKey")
OPENAI_API_KEY = config.get("OpenAIAPIKey")
ASSISTANT_NAME = config.get("Assistantname", "Ozilly AI")

client = Groq(api_key=API_KEY)
openai.api_key = OPENAI_API_KEY

POSITIVE_FEEDBACK = [
    "yes", "good", "love it", "like it", "perfect", "awesome", "great",
    "cool", "nice", "this works", "works for me", "i like this",
    "that's the one", "this is good", "amazing", "i love it", "it's perfect",
    "beautiful", "i’m happy with it", "looks good", "this is it", "this is nice"
]

NEGATIVE_FEEDBACK = [
    "no", "not good", "meh", "bad", "try again", "next", "another one",
    "don’t like it", "change it", "not great", "any other", "can you redo?",
    "i don’t like this", "it's okay, but", "not feeling it", "hmm", "not this",
    "ew", "nah", "redo", "something else", "give me another", "not my vibe"
]

SYSTEM_PROMPT = f"""
You are {ASSISTANT_NAME}, a creative and friendly AI that helps users generate unique startup names and logo ideas. 

You understand casual language. When users reject ideas using phrases like 'try again' or 'not good', generate a new name and logo for the *same* concept.
When users respond positively, stop suggesting more ideas until a new prompt is given.
Avoid repeating previous suggestions. Be playful, relevant, and brandable.

Always reply in this format:
Startup Name: <name>
Logo Idea: <logo>
"""

SYSTEM_MESSAGES = [{"role": "system", "content": SYSTEM_PROMPT}]

HISTORY_FILE = "prompts_and_results.json"

def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def is_positive_feedback(text):
    return any(p in text.lower() for p in POSITIVE_FEEDBACK)

def is_negative_feedback(text):
    return any(p in text.lower() for p in NEGATIVE_FEEDBACK)

def save_entry(idea, name, logo):
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []

    history.append({
        "timestamp": now(),
        "idea": idea,
        "startup_name": name,
        "logo_idea": logo
    })

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

def previous_names_for(idea):
    try:
        with open(HISTORY_FILE, 'r') as f:
            data = json.load(f)
            return [d['startup_name'] for d in data if d['idea'].lower() == idea.lower()]
    except:
        return []

def generate_idea(prompt, blacklist=None):
    blacklist = blacklist or []
    filter_msg = f"Avoid using these names: {', '.join(blacklist)}" if blacklist else ""
    combined_prompt = f"{prompt}\n\n{filter_msg}".strip()

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=SYSTEM_MESSAGES + [{"role": "user", "content": combined_prompt}],
        max_tokens=1024,
        temperature=0.9
    )
    return response.choices[0].message.content.strip()

def parse_response(response):
    name = ""
    logo = ""
    for line in response.splitlines():
        if "Startup Name:" in line:
            name = line.split("Startup Name:")[1].strip()
        elif "Logo Idea:" in line:
            logo = line.split("Logo Idea:")[1].strip()
    return name, logo

def generate_dalle_logo(prompt):
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        return None

# Streamlit UI
st.set_page_config(page_title="Ozilly AI - Startup Name Generator", layout="wide")

# Premium Brand Header
st.markdown("""
    <div style="text-align:center; margin-bottom: 3rem; animation: fadeIn 1.2s ease-in-out;">
        <h1 style="font-size: 4rem; font-weight: 900; color: #e50914; font-family: 'Netflix Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;">
            Ozilly Ai
        </h1>
        <h4 style="font-weight: 400; color: #666; font-family: 'Segoe UI', sans-serif; margin-top: -1rem;">
            Your AI-powered Startup Name & Logo Generator
        </h4>
    </div>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .stButton > button {
            background: linear-gradient(to right, #ffffff, #f0f0f0);
            color: #333;
            border-radius: 10px;
            border: 1px solid #ccc;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s ease-in-out;
        }

        .stButton > button:hover {
            background-color: #e50914;
            color: white;
            border: none;
            transform: scale(1.05);
        }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Customize")
    show_history = st.checkbox("Show Previous Suggestions")

prompt = st.text_input("💡 Enter your startup idea:", placeholder="e.g., an app for tracking your mood")
generate_name = st.button("Generate Name")
generate_logo = st.button("Generate Logo")

if generate_name and prompt:
    blacklist = previous_names_for(prompt)
    result = generate_idea(prompt, blacklist)
    name, logo = parse_response(result)

    if name:
        save_entry(prompt, name, logo)
        st.success("✨ Here's your startup name:")
        st.subheader(f"Startup Name: {name}")
        st.session_state.generated_name = name
        st.session_state.generated_logo = logo
    else:
        st.error("⚠️ Couldn't parse the AI's response. Please try again.")

if generate_logo:
    name = st.session_state.get("generated_name", None)
    logo = st.session_state.get("generated_logo", None)
    if name and logo:
        st.success("🖼️ Here's your logo idea:")
        st.write(f"Logo Idea: {logo}")
        dalle_image_url = generate_dalle_logo(logo)
        if dalle_image_url:
            st.image(dalle_image_url, caption="AI-Generated Logo")
        else:
            st.warning("⚠️ DALL·E logo generation failed. Here's a placeholder instead.")
            st.image("https://via.placeholder.com/400x200.png?text=Logo+for+" + name.replace(" ", "+"), caption="AI Logo Sketch Simulation")
    else:
        st.warning("⚠️ Generate a startup name first before generating the logo.")

# Feedback Section
if 'generated_name' in st.session_state:
    feedback = st.text_input("🗣️ What do you think of this suggestion?")
    if is_negative_feedback(feedback):
        st.info("🔁 Generating a better suggestion...")
        blacklist = previous_names_for(prompt)
        result = generate_idea(prompt, blacklist)
        name, logo = parse_response(result)

        if name:
            save_entry(prompt, name, logo)
            st.subheader(f"Startup Name: {name}")
            st.session_state.generated_name = name
            st.session_state.generated_logo = logo
        else:
            st.error("⚠️ Couldn't parse the AI's response. Please try again.")

    elif is_positive_feedback(feedback):
        st.balloons()
        st.success("Glad you liked it! You can enter a new idea above.")

# History Display
if show_history:
    st.markdown("### 📜 History")
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
            for entry in reversed(history[-10:]):
                with st.expander(f"{entry['startup_name']} ({entry['timestamp']})"):
                    st.write(f"Idea: {entry['idea']}")
                    st.write(f"Logo: {entry['logo_idea']}")
    except:
        st.warning("No history available yet.")

st.markdown("---")
st.caption("Crafted with ❤️ using LLaMA 3 via Groq API + Open Journey • By Ozilly Ai")