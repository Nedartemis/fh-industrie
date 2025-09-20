import time
from enum import Enum

import streamlit as st

log_enabled = False


class LogLevel(Enum):
    INFO = 1
    WARNING = 2
    ERROR = 3


def enable_log() -> None:
    global log_enabled

    log_enabled = True


def log(log_level: LogLevel, message: str):
    if not log_enabled or not st.session_state.get("app_launched"):
        return

    st.session_state.logs.append((log_level, time.strftime("%H:%M:%S"), message))


def create_console():
    st.markdown("### Messages")

    # Create a placeholder for logs
    log_container = st.container()

    logs = [
        f"[{log_level.name.capitalize()}] {time} - {message}"
        for log_level, time, message in st.session_state.logs
    ]

    # Scrollable log display
    with log_container:

        st.markdown(
            """
            <div style="height: 200px; overflow-y: scroll; background-color: #111; padding: 10px; border-radius: 5px;">
            <code>"""
            + "<br>".join(logs)
            + """</code></div>
            """,
            unsafe_allow_html=True,
        )
