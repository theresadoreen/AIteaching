import streamlit as st
import hmac
import time
import os
import logging

# Logging einrichten
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_password():
    """Returns 'True' if the user has entered a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether username and password entered by the user are correct."""
        if st.session_state.username in st.secrets.passwords and hmac.compare_digest(
            st.session_state.password,
            st.secrets.passwords[st.session_state.username],
        ):
            st.session_state.password_correct = True
        else:
            st.session_state.password_correct = False

        del st.session_state.password  # don't store password in session state

    if st.session_state.get("password_correct", False):
        return True, st.session_state.username

    login_form()
    if "password_correct" in st.session_state:
        st.error("User or password incorrect")
    return False, st.session_state.username


def check_if_interview_completed(directory, username):
    """Check if interview transcript/time file exists."""
    file_path = os.path.join(directory, f"{username}.txt")
    
    if os.path.exists(file_path):
        logging.info(f"Interview file found for user {username}: {file_path}")
        return True
    
    logging.info(f"No interview file found for user {username}.")
    return False
    
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def save_interview_data(username, transcripts_directory, times_directory, file_name_addition_transcript="", file_name_addition_time=""):
    """Write interview data (transcript and time) to disk with debugging."""
    logging.info(f"save_interview_data() called for user: {username}")

    if not username:
        logging.error("Username is None or empty. Transcript will not be saved.")
        return
    
    try:
        # Sicherstellen, dass Verzeichnisse existieren
        os.makedirs(transcripts_directory, exist_ok=True)
        os.makedirs(times_directory, exist_ok=True)
        
        transcript_path = os.path.join(transcripts_directory, f"{username}{file_name_addition_transcript}.txt")
        time_path = os.path.join(times_directory, f"{username}{file_name_addition_time}.txt")

        logging.info(f"Saving transcript to: {transcript_path}")
        logging.info(f"Saving time data to: {time_path}")
        
        # Chat-Transkript speichern
        with open(transcript_path, "w") as t:
            for message in st.session_state.messages:
                t.write(f"{message['role']}: {message['content']}\n")
        logging.info(f"Interview transcript saved: {transcript_path}")

        # Startzeit und Dauer speichern
        duration = (time.time() - st.session_state.start_time) / 60
        with open(time_path, "w") as d:
            d.write(
                f"Start time (UTC): {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(st.session_state.start_time))}\n"
                f"Interview duration (minutes): {duration:.2f}"
            )
        logging.info(f"Interview time data saved: {time_path}")
        
    except Exception as e:
        logging.error(f"Error saving interview data for user {username}: {e}")
