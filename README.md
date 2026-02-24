# AI Orchestration System

A secure, session-aware AI Orchestration platform built using FastAPI (backend), Gradio (frontend), and MongoDB (database).

---

## 🚀 Overview

This system provides:

- JWT-based authentication (Signup & Login)
- Protected AI orchestration endpoint
- Per-user session isolation
- MongoDB persistence
- Latency tracking & structured logging
- Gradio-based interactive UI

---

## 🏗️ Project Structure

project-root/
│
├── backend/
│   ├── main.py
│   ├── ai_orchestrator.py
│   ├── auth.py
│   ├── models.py
│   ├── schemas.py
│   └── db.py
│
├── frontend/
│   └── app.py
│
├── requirements.txt
└── README.md

---

## ⚙️ Prerequisites

- Python 3.10+
- MongoDB installed and running locally
- pip installed

---

## 📦 Installation & Setup

### 1️⃣ Extract the Project

Unzip the folder and navigate to the project root:

cd project-root


---

## 🖥️ Backend Setup

### Step 1: Install Dependencies

pip install -r requirements.txt


### Step 2: Start MongoDB

Ensure MongoDB is running locally.

Default connection:
mongodb://localhost:27017


### Step 3: Run Backend

uvicorn backend.main:app --reload


Backend runs at:
http://localhost:8000


Test health:
http://localhost:8000/health


---

## 🌐 Frontend Setup (Gradio)

Open a new terminal.

Run:

python frontend/app.py


Gradio UI will open automatically in your browser.

---

## 🔐 How to Use

1. Open the Gradio interface.
2. Sign up as a new user.
3. Log in.
4. Click "Run Orchestration".
5. View:
   - AI responses
   - Ranking
   - Latency metrics
   - Session-isolated behavior

Each session is isolated and maintains its own conversation context.

---

## 🗄️ Database Collections

MongoDB stores:

- users
- orchestration_runs

Each run stores:
- user_id
- session_id
- question
- AI responses
- ranking
- latency
- metadata

---

## 🔒 Security

- Passwords hashed using bcrypt
- JWT-secured endpoints
- Only authenticated users can access orchestration API

---

## 📊 Logging

Backend logs include:

- Request ID
- User ID
- Session ID
- Latency metrics
- Error traces (if any)

Used for debugging rendering and performance issues.

---

## 🛠️ Future Improvements

- Cost/token monitoring
- Load testing
- Production CORS restriction
- Deployment configuration (Docker/Cloud)

---

## 👩‍💻 Author

Amishi  
Backend & Performance Engineering – AI Orchestration System