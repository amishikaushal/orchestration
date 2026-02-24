import gradio as gr
import requests
import logging
import uuid
import time


# CONFIG


BACKEND_BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BACKEND_BASE_URL}/login"
SIGNUP_URL = f"{BACKEND_BASE_URL}/signup"
ORCHESTRATE_URL = f"{BACKEND_BASE_URL}/orchestrate"

logging.basicConfig(level=logging.INFO)



# AUTH FUNCTIONS


def signup_user(email, password):
    try:
        response = requests.post(
            SIGNUP_URL,
            json={
                "email": email,
                "password": password
            }
        )
        response.raise_for_status()
        return "Signup successful ✅ You can now login."

    except Exception as e:
        logging.exception("Signup failed")
        return f"Signup failed: {str(e)}"


def login_user(email, password):
    try:
        response = requests.post(
            LOGIN_URL,
            data={
                "username": email,
                "password": password
            }
        )
        response.raise_for_status()

        token = response.json()["access_token"]

        return (
            "Login successful ✅",
            token,
            gr.update(visible=True),   # Show orchestration UI
            gr.update(visible=False)   # Hide auth UI
        )

    except Exception as e:
        logging.exception("Login failed")
        return (
            f"Login failed: {str(e)}",
            None,
            gr.update(visible=False),
            gr.update(visible=True)
        )


def logout_user():
    return (
        None,
        initialize_session(),
        "Logged out successfully.",
        gr.update(visible=False),
        gr.update(visible=True)
    )



# SESSION INITIALIZER


def initialize_session():
    session_id = str(uuid.uuid4())
    logging.info(f"[NEW SESSION INITIALIZED] {session_id}")

    return {
        "session_id": session_id,
        "conversation": [],
        "runs": [],
        "last_run": None,
        "created_at": time.time()
    }



# ORCHESTRATION


def run_orchestration(session_state, token):
    try:
        if not token:
            return "You must login first.", session_state

        if not session_state or "session_id" not in session_state:
            session_state = initialize_session()

        session_id = session_state["session_id"]
        request_start = time.time()

        payload = {
            "session_id": session_id,
            "question": None,
            "conversation": session_state["conversation"],
            "num_competitors": 3,
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(
            ORCHESTRATE_URL,
            json=payload,
            headers=headers,
            timeout=900
        )

        response.raise_for_status()

        backend_latency = round(time.time() - request_start, 3)
        data = response.json()

        question = data.get("question", "")
        answers = data.get("answers", [])
        ranking = data.get("ranking", [])
        latency = data.get("latency", {})

        run_record = {
            "run_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "question": question,
            "answers": answers,
            "ranking": ranking,
            "backend_latency": backend_latency,
            "latency_breakdown": latency
        }

        updated_session = {
            **session_state,
            "runs": session_state["runs"] + [run_record],
            "last_run": run_record,
            "conversation": session_state["conversation"] + [{
                "role": "system",
                "question": question,
                "ranking": ranking
            }]
        }

        formatted_output = f"""
SESSION ID: {session_id}

----------------------------------

QUESTION:
{question}

----------------------------------

ANSWERS:
"""

        for idx, ans in enumerate(answers, start=1):
            formatted_output += f"\n--- Model {idx} ---\n{ans}\n"

        formatted_output += "\n----------------------------------\n\nRANKING:\n"
        formatted_output += f"{ranking}\n"

        formatted_output += "\n----------------------------------\n\nLATENCY (seconds):\n"

        for k, v in latency.items():
            formatted_output += f"{k}: {v}\n"

        formatted_output += f"\nfrontend_backend_latency: {backend_latency}\n"
        formatted_output += f"\nTotal Session Runs: {len(updated_session['runs'])}\n"

        return formatted_output, updated_session

    except Exception as e:
        logging.exception("Frontend error")
        return f"Frontend Error: {str(e)}", session_state



# RESET SESSION


def reset_session():
    return initialize_session(), "Session reset successfully."


# GRADIO UI


with gr.Blocks(title="AI Orchestration SaaS") as demo:

    token_state = gr.State(None)
    session_state = gr.State(initialize_session())


    # AUTH SECTION
    
    with gr.Column(visible=True) as auth_section:

        gr.Markdown("## 🔐 Authentication")

        with gr.Tab("Login"):
            login_email = gr.Textbox(label="Email")
            login_password = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Login")
            login_status = gr.Textbox(label="Status")

        with gr.Tab("Signup"):
            signup_email = gr.Textbox(label="Email")
            signup_password = gr.Textbox(label="Password", type="password")
            signup_btn = gr.Button("Signup")
            signup_status = gr.Textbox(label="Status")


    # APP SECTION


    with gr.Column(visible=False) as app_section:

        gr.Markdown("## 🚀 AI Orchestration Dashboard")

        run_btn = gr.Button("Run Orchestration")
        reset_btn = gr.Button("Reset Session")
        logout_btn = gr.Button("Logout")

        output = gr.Textbox(label="Response", lines=30)
        system_status = gr.Textbox(label="System Status")


    # BUTTON BINDINGS
   

    signup_btn.click(
        signup_user,
        inputs=[signup_email, signup_password],
        outputs=signup_status
    )

    login_btn.click(
        login_user,
        inputs=[login_email, login_password],
        outputs=[
            login_status,
            token_state,
            app_section,
            auth_section
        ]
    )

    logout_btn.click(
        logout_user,
        outputs=[
            token_state,
            session_state,
            system_status,
            app_section,
            auth_section
        ]
    )

    run_btn.click(
        run_orchestration,
        inputs=[session_state, token_state],
        outputs=[output, session_state]
    )

    reset_btn.click(
        reset_session,
        outputs=[session_state, system_status]
    )


if __name__ == "__main__":
    demo.launch()
