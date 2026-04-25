import streamlit as st
import json
import os
from datetime import datetime
from openai import OpenAI

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# SYSTEM PROMPT
# -----------------------------
def system_prompt(unavailable_times, sleep_times):
    return f"""
You are a scheduling aide and your job is to help organize and categorize the user's tasks over the course of a week, or longer if needed, starting today.
The user's unavailable at {unavailable_times}.
The user usually sleeps from: {sleep_times}.
Respect their existing weekly schedule.
Do not schedule tasks during sleeping hours. Mention when the user is unavailable and when they should sleep.
If the user asks for changes, update the weekly schedule or sleep schedule.
The current date and time is {datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")}.
Use emojis.

Respond as JSON in this format:
{{
  "message": "...",
  "schedule": {{
    "Monday": {{
      "tasks": [
        {{"time": "...", "task": "...", "notes": "..."}}
      ],
      "blocked_times": []
    }}
  }},
  "suggestions": "..."
}}
"""

# -----------------------------
# DISPLAY FUNCTION
# -----------------------------
def display_schedule(data):
    if "message" in data:
        st.subheader(data["message"])

    schedule = data.get("schedule", {})

    for day, details in schedule.items():
        with st.expander(day):
            tasks = details.get("tasks", [])
            if tasks:
                st.write("**Tasks:**")
                for t in tasks:
                    st.write(f"- {t['time']} → {t['task']} ({t['notes']})")

            blocked = details.get("blocked_times", [])
            if blocked:
                st.write("**Blocked:**")
                for b in blocked:
                    st.write(f"- {b}")

    if "suggestions" in data:
        st.info(data["suggestions"])

# -----------------------------
# UI
# -----------------------------
st.title("🧠 AI Scheduler")

unavailable_times = st.text_input("When are you unavailable?")
sleep_times = st.text_input("When do you sleep?")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_prompt = st.text_input("What do you want to schedule?")

if st.button("Generate Schedule"):
    if not unavailable_times or not sleep_times or not user_prompt:
        st.warning("Please fill out all fields.")
    else:
        messages = [
            {"role": "system", "content": system_prompt(unavailable_times, sleep_times)},
            *st.session_state.chat_history,
            {"role": "user", "content": user_prompt},
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=messages,
        )

        assistant_response = response.choices[0].message.content

        # Save history
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

        # Display
        try:
            parsed = json.loads(assistant_response)
            display_schedule(parsed)
        except Exception as e:
            st.error("Failed to parse response")
            st.text(assistant_response)
