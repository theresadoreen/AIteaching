import streamlit as st
import os  # Required for file and directory operations
import logging
import time # Required for time operations
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
    if "password_correct" not in st.session_state:
        login_form()
        return False

    return st.session_state.get("password_correct", False)



def login_form():
    """Form with widgets to collect user information"""
    with st.form("Credentials"):  # Create a form for login
        st.text_input("Username", key="username")  # Input for username
        st.text_input("Password", type="password", key="password")  # Input for password
        if st.form_submit_button("Log in"):  # Submit button
            # Validate empty inputs
            if not st.session_state.username or not st.session_state.password:
                st.error("Username and password cannot be empty.")
                return

            # Call the function to handle login
            if password_entered():
                st.success("Login successful!")
            else:
                st.error("Invalid username or password. Please try again.")


def password_entered():
    """Checks whether username and password entered by the user are correct."""
    # Check if username and password exist in session state
    if "username" not in st.session_state or "password" not in st.session_state:
        logging.error("Username or password not provided in session state.")
        return False

    # Validate credentials
    if st.session_state.username in st.secrets.passwords:
        hashed_password = st.secrets.passwords[st.session_state.username].encode('utf-8')
        st.session_state.password_correct = bcrypt.checkpw(st.session_state.password.encode('utf-8'), hashed_password)
    else:
        st.session_state.password_correct = False

    # Remove password from session state for security
    del st.session_state.password

    # Return the result of the validation
    if st.session_state.get("password_correct", False):
        return True

    # Log failed login attempt
    logging.warning(f"Failed login attempt for username: {st.session_state.username}")
    return False


def check_if_interview_completed(directory, username):
    """Check if interview transcript/time file exists."""
    if not directory:
        logging.error("Invalid directory provided.")
        return False
    if not username:
        logging.error("Invalid username provided.")
        return False
    if not os.path.exists(directory):
        logging.error(f"Directory does not exist: {directory}")
        return False

    try:
        file_path = os.path.join(directory, f"{username}.txt")
        logging.info(f"Checking for file: {file_path}")
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

    # Validate inputs
    if not username:
        logging.error("Username is None or empty. Transcript will not be saved.")
        return False
    if not transcripts_directory:
        logging.error("Transcripts directory is None or empty. Transcript will not be saved.")
        return False
    if not times_directory:
        logging.error("Times directory is None or empty. Time data will not be saved.")
        return False
    if "messages" not in st.session_state or not st.session_state.messages:
        logging.error("No messages found in session state. Transcript will not be saved.")
        return False
    if "start_time" not in st.session_state:
        logging.error("Start time not found in session state. Time data will not be saved.")
        return False
    if not isinstance(file_name_addition_transcript, str):
        logging.error("File name addition for transcript is not a valid string.")
        return False
    if not isinstance(file_name_addition_time, str):
        logging.error("File name addition for time is not a valid string.")
        return False

    try:
        # Ensure directories exist
        os.makedirs(transcripts_directory, exist_ok=True)
        os.makedirs(times_directory, exist_ok=True)
        
        # Define file paths
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
        
        return True

    except OSError as e:
        logging.error(f"File operation failed for user {username}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error while saving data for user {username}: {e}")
        return False

# logout button with feedback      
if st.button("Logout", key="logout_button"):
    st.session_state.clear()
    st.success("You have been logged out successfully.")