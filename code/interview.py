from utils import (
    check_password,
    check_if_interview_completed,
    save_interview_data
)
import sys
import os
import logging
import streamlit as st
import time
import config

# Sicherstellen, dass der übergeordnete Pfad im Suchpfad enthalten ist
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code')))

# Load API library
if not config.MODEL or "API_KEY" not in st.secrets:
    st.error("Configuration error: Missing model or API key.")
    logging.error("Configuration error: Missing model or API key.")
    st.stop()
elif "gpt" in config.MODEL.lower():
    api = "openai"
    from openai import OpenAI
    client = OpenAI(api_key=st.secrets["API_KEY"])
elif "claude" in config.MODEL.lower():
    api = "anthropic"
    import anthropic
    client = anthropic.Anthropic(api_key=st.secrets["API_KEY"])
else:
    raise ValueError(
        "Model does not contain 'gpt' or 'claude'; unable to determine API."
    )
    
    
# Verify API configuration
if not config.MODEL or not config.API_KEY:
    st.error("Configuration error: Missing model or API key.")
    logging.error("Configuration error: Missing model or API key.")
    st.stop()
    
    
# Set page title and icon
st.set_page_config(page_title="Interview", page_icon=config.AVATAR_INTERVIEWER)

# Check if usernames and logins are enabled
if config.LOGINS:

    # Check password (displays login screen)
    pwd_correct = check_password()
    if not pwd_correct:
        st.stop()
    else:
        st.session_state.username = st.session_state.get("username")
else:
    st.session_state.username = "testaccount"

# Create directories if they do not already exist
if not os.path.exists(config.TRANSCRIPTS_DIRECTORY):
    os.makedirs(config.TRANSCRIPTS_DIRECTORY)
if not os.path.exists(config.TIMES_DIRECTORY):
    os.makedirs(config.TIMES_DIRECTORY)
if not os.path.exists(config.BACKUPS_DIRECTORY):
    os.makedirs(config.BACKUPS_DIRECTORY)


# Initialise session state
if "interview_active" not in st.session_state:
    st.session_state.interview_active = True

# Initialise messages list in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Store start time in session state
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
    st.session_state.start_time_file_names = time.strftime(
        "%Y_%m_%d_%H_%M_%S", time.localtime(st.session_state.start_time)
    )

# Check if interview previously completed
interview_previously_completed = check_if_interview_completed(
    config.TIMES_DIRECTORY, st.session_state.username
)

# If app started but interview was previously completed
if interview_previously_completed and not st.session_state.messages:

    st.session_state.interview_active = False
    completed_message = "Interview already completed."
    st.markdown(completed_message)

# Add 'Submit chat history' button to dashboard
col1, col2 = st.columns([0.85, 0.15])
# Place where the second column is
with col2:

    # If interview is active and 'Submit chat history' button is clicked
    if st.session_state.interview_active and st.button(
        "Submit chat history", help="Submit the chat history for review."
    ):

        # Set interview to inactive, display submission message, and store data
        st.session_state.interview_active = False
        submit_message = "Your chat history has been submitted for review."
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": submit_message,
            }
        )
        save_interview_data(
            st.session_state.username,
            config.TRANSCRIPTS_DIRECTORY,
            config.TIMES_DIRECTORY,
        )
        st.success(submit_message)

# Sidebar mit Logout-Button
with st.sidebar:
    st.write(f"👤 Logged in as **{st.session_state.username}**")
    if st.button("Logout", key="logout_button"):
        st.session_state.clear()
        st.rerun()

# Upon rerun, display the previous conversation 
# (except system prompt or first message)
    for message in st.session_state.messages[1:]:
        if message["role"] == "assistant":
            avatar = config.AVATAR_INTERVIEWER
        else:
            avatar = config.AVATAR_RESPONDENT
        # Only display messages without codes
        if all(
            code not in message["content"]
            for code in config.CLOSING_MESSAGES.keys()
        ):
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

# Load API client
if api == "openai":
    client = OpenAI(api_key=st.secrets["API_KEY"])
    api_kwargs = {"stream": True}


# API kwargs
api_kwargs["messages"] = st.session_state.messages
api_kwargs["model"] = config.MODEL
api_kwargs["max_tokens"] = config.MAX_OUTPUT_TOKENS
if config.TEMPERATURE is not None:
    api_kwargs["temperature"] = config.TEMPERATURE

print(api_kwargs)

if "proxies" in api_kwargs:
    del api_kwargs["proxies"]

# In case the interview history is still empty, pass system prompt to model
# generate and display its first message
if not st.session_state.messages:

    if api == "openai":

        st.session_state.messages.append(
            {"role": "system", "content": config.SYSTEM_PROMPT}
        )
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            try:
                stream = client.chat.completions.create(**api_kwargs)
            except Exception as e:
                st.error("An error occurred while generating the response. Please try again.")
                logging.error(f"Error during API call: {e}")
                st.stop()
            message_interviewer = st.write_stream(stream)

    st.session_state.messages.append(
        {"role": "assistant", "content": message_interviewer}
    )

    # Store first backup files to record who started the interview
    save_interview_data(
        username=st.session_state.username,
        transcripts_directory=config.BACKUPS_DIRECTORY,
        times_directory=config.BACKUPS_DIRECTORY,
        file_name_addition_transcript=f"_transcript_started_{st.session_state.start_time_file_names}",
        file_name_addition_time=f"_time_started_{st.session_state.start_time_file_names}",
    )


# Main chat if interview is active
if st.session_state.interview_active:

    # Chat input and message for respondent
    if message_respondent := st.chat_input("Your message here"):
        if len(message_respondent.strip()) == 0:
            st.error("Message cannot be empty.")
        else:
            st.session_state.messages.append({"role": "user", "content": message_respondent})

            # Display respondent message
            with st.chat_message("user", avatar=config.AVATAR_RESPONDENT):
                st.markdown(message_respondent)

            # Generate and display interviewer message
            with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
                message_placeholder = st.empty()
                try:
                    message_interviewer = generate_response(client, api_kwargs, api)
                except Exception as e:
                    logging.error(f"Error during response generation: {e}")
                    st.error("An error occurred while generating the response. Please try again.")
                    
                    st.stop()

                # Display the response
                message_placeholder.markdown(message_interviewer)
                st.session_state.messages.append({"role": "assistant", "content": message_interviewer})

                # Regularly store interview progress as backup
                try:
                    save_interview_data(
                        username=st.session_state.username,
                        transcripts_directory=config.TRANSCRIPTS_DIRECTORY,  # noqa: E501
                        times_directory=config.TRANSCRIPTS_DIRECTORY,
                        file_name_addition_transcript=f"_transcript_started_{st.session_state.start_time_file_names}",
                        file_name_addition_time=f"_time_started_{st.session_state.start_time_file_names}",
                    )
                except Exception as e:
                    logging.error(f"Error during backup: {e}")

                # Check for closing codes
                for code in config.CLOSING_MESSAGES.keys():
                    if code in message_interviewer:
                        st.session_state.messages.append({"role": "assistant", "content": message_interviewer})
                        st.session_state.interview_active = False
                        closing_message = config.CLOSING_MESSAGES[code]
                        st.markdown(closing_message)
                        st.session_state.messages.append({"role": "assistant", "content": closing_message})

                        # Store final transcript and time
                        max_retries = 5
                        retries = 0
                        final_transcript_stored = False
                        while not final_transcript_stored and retries < max_retries:
                            save_interview_data(
                                username=st.session_state.username,
                                transcripts_directory=config.TRANSCRIPTS_DIRECTORY,
                                times_directory=config.TIMES_DIRECTORY,
                            )
                            final_transcript_stored = check_if_interview_completed(
                                config.TRANSCRIPTS_DIRECTORY, st.session_state.username
                            )
                            retries += 1
                            time.sleep(0.1)
                        if not final_transcript_stored:
                            logging.error("Failed to save final transcript after multiple attempts.")
                        break