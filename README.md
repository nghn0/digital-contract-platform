# Digital Contract Platform

A comprehensive digital contract platform with AI-powered negotiation and risk analysis.

---

## 🏃‍♂️ How to Run the Project

### 1️⃣ Run the Model Server (AI Backend)

1. Open a new terminal in VS Code.
2. Go to the model folder:
   ```bash
   cd model
   ```
3. Install dependencies and start the gRPC server:
   ```bash
   # Make sure you are using Python 3.9+
   python3 -m pip install -r requirements.txt
   python3 grpc_server.py
   ```
   *⚠️ Keep this terminal running (do not stop it). Ensure your `env` or `.env` file is present in the `model` root with `GEMINI_API_KEY` defined.*

---

### 2️⃣ Run the Backend (Node.js)

1. Open another new terminal.
2. Go to the backend folder:
   ```bash
   cd backend
   ```
3. Run:
   ```bash
   npm install
   npm run dev
   ```
   *⚠️ Keep this terminal running.*

---

### 3️⃣ Run the Frontend (Next.js)

1. Open a third new terminal.
2. Go to the frontend folder:
   ```bash
   cd frontend
   ```
3. Run:
   ```bash
   npm install
   npm run dev
   ```

---

## 🌐 Open in Browser

Go to:
[http://localhost:3000/signup](http://localhost:3000/signup)

---

## 🧹 Repository Structure
- **/frontend**: Next.js React application representing the dashboard and review interface.
- **/backend**: Express.js REST API interacting with Supabase and serving as a bridge to the AI Model via gRPC.
- **/model**: Python-driven automated contract analysis orchestrator using LLMs.
- **/proto**: Protocol buffer schemas shared between Node.js and Python.
