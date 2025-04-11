import streamlit as st
import os  # Required for file and directory operations
import logging
import bcrypt  # Add bcrypt for secure password hashing
# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def configure_logging():
 logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    # No changes needed for $PLACEHOLDER$ as it is empty.



def check_password():
    """Returns 'True' if the user has entered correct password."""
    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):


            st.text_input("Username", key="username")


            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)



def login_form():
    """Form with widgets to collect user information"""
    with st.form("Credentials"):  # Fixed indentation
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.form_submit_button("Log in", on_click=password_entered)


def password_entered():
    """Checks whether username and password entered by the user are correct."""
    if st.session_state.username in st.secrets.passwords:
        hashed_password = st.secrets.passwords[st.session_state.username].encode('utf-8')  # Fixed indentation
        st.session_state.password_correct = bcrypt.checkpw(st.session_state.password.encode('utf-8'), hashed_password)
    else:
        st.session_state.password_correct = False


    del st.session_state.password  # Don't store password in session state

    if st.session_state.get("password_correct", False):
        return True, st.session_state.username

    login_form()
    if "password_correct" in st.session_state:
        st.error("User or password incorrect")
        logging.warning(f"Failed login attempt for username: {st.session_state.username}")
    return False, st.session_state.username


def check_if_interview_completed(directory, username):
    """Check if interview transcript/time file exists."""
    if not directory or not username:  # Check if directory or username is invalid
        logging.error("Invalid directory or username provided.")
        return False

    try:
        file_path = os.path.join(directory, f"{username}.txt")
        if os.path.exists(file_path):
            logging.info(f"Interview file found for user {username}: {file_path}")
            return True
        logging.info(f"No interview file found for user {username}.")
        return False
    except Exception as e:
        logging.error(f"Error checking interview completion: {e}")
        return False



def save_interview_data(username, transcripts_directory, times_directory, file_name_addition_transcript="", file_name_addition_time=""):
    """Write interview data (transcript and time) to disk with debugging."""
    logging.info(f"save_interview_data() called for user: {username}")

    if not username:
        logging.error("Username is None or empty. Transcript will not be saved.")
        return

    try:
        # Ensure directories exist
        os.makedirs(transcripts_directory, exist_ok=True)
        os.makedirs(times_directory, exist_ok=True)

        transcript_path = os.path.join(transcripts_directory, f"{username}{file_name_addition_transcript}.txt")
        time_path = os.path.join(times_directory, f"{username}{file_name_addition_time}.txt")

        logging.info(f"Saving transcript to: {transcript_path}")
        logging.info(f"Saving time data to: {time_path}")

        # Save chat transcript atomically
        temp_transcript_path = transcript_path + ".tmp"
        with open(temp_transcript_path, "w") as t:
            for message in st.session_state.messages:
                t.write(f"{message['role']}: {message['content']}\n")
        os.replace(temp_transcript_path, transcript_path)
        logging.info(f"Interview transcript saved: {transcript_path}")

        # Save start time and duration atomically
        temp_time_path = time_path + ".tmp"
        duration = (time.time() - st.session_state.start_time) / 60
        with open(temp_time_path, "w") as d:
            d.write(
                f"Start time (UTC): "
                f"{time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(st.session_state.start_time))}\n"
                f"Interview duration (minutes): {duration:.2f}"
            )
        os.replace(temp_time_path, time_path)
        logging.info(f"Interview time data saved: {time_path}")

    except Exception as e:
        logging.error(f"Error saving interview data for user {username}: {e}")

if st.button("Logout", key="logout_button"):
    st.session_state.clear()
    st.experimental_rerun()
    
