# 📧 Email AI Assistant

An AI-powered Gmail assistant that allows users to connect their Gmail account and interact with their emails using natural-language queries. The application combines **Google OAuth, Gmail API, FastAPI, React, and AI** to provide a conversational interface for managing and understanding emails.

## ✨ Features

* 🔐 Google OAuth 2.0 authentication
* 📩 Fetch and display real Gmail messages
* 🤖 Ask AI-powered questions about emails
* 🔎 Search emails using natural-language queries
* 📝 Summarize lengthy emails
* 💬 Chat-based interface for interacting with emails
* 👤 Gmail profile/account information
* 🔌 Connect and disconnect Gmail accounts
* 🧹 Clear email data after logout/disconnection
* ⚡ FastAPI backend for API and AI processing
* 🎨 React-based modern frontend

## 🏗️ Architecture

```text
┌─────────────────────┐
│      React UI       │
│   Frontend / Chat   │
└──────────┬──────────┘
           │
           │ REST API
           ▼
┌─────────────────────┐
│     FastAPI         │
│      Backend        │
└───────┬─────┬───────┘
        │     │
        │     └────────────────┐
        ▼                      ▼
┌───────────────┐      ┌────────────────┐
│   Gmail API   │      │    AI / LLM    │
│               │      │ Query Processing│
└───────────────┘      └────────────────┘
```

## 🛠️ Tech Stack

### Frontend

* React.js
* JavaScript
* HTML5
* CSS3

### Backend

* Python
* FastAPI
* Uvicorn

### APIs & Authentication

* Gmail API
* Google OAuth 2.0

### AI

* Large Language Model (LLM)
* Natural Language Processing

### Development Tools

* Git
* GitHub
* VS Code

## 🔄 Application Workflow

1. The user opens the application.
2. The user connects their Gmail account using Google OAuth 2.0.
3. The application authenticates the user and obtains the required Gmail permissions.
4. Gmail messages are retrieved through the Gmail API.
5. Emails are displayed in the application.
6. The user can ask questions or search for specific information using natural language.
7. The backend processes the request and retrieves the relevant email information.
8. The AI processes the information and generates a concise response.
9. The response is displayed through the conversational interface.
10. The user can disconnect their Gmail account, after which the application's email data is cleared.

## 📂 Project Structure

```text
Email-AI-Assistant/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── .gitignore
└── README.md
```

> The exact folder structure may vary depending on the current implementation.

## ⚙️ Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Email-AI-Assistant.git
cd Email-AI-Assistant
```

### 2. Create a Python Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

Navigate to the frontend directory:

```bash
cd frontend
npm install
```

## 🔑 Environment Variables

Create a `.env` file in the backend directory and add the required credentials.

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=your_redirect_uri

AI_API_KEY=your_ai_api_key
```

> Never commit API keys, OAuth credentials, access tokens, or other sensitive information to GitHub.

## 🔐 Google OAuth Configuration

To enable Gmail integration:

1. Create a project in Google Cloud Console.
2. Enable the **Gmail API**.
3. Configure the OAuth consent screen.
4. Create OAuth 2.0 credentials.
5. Add the application's redirect URI.
6. Add the required Gmail scopes.
7. Store the credentials securely in environment variables.

## ▶️ Running the Application

### Start the Backend

From the backend directory:

```bash
uvicorn main:app --reload
```

The FastAPI server will start locally.

### Start the Frontend

From the frontend directory:

```bash
npm run dev
```

Open the local frontend URL displayed by Vite in your browser.

## 💡 Example Queries

Once Gmail is connected, users can ask questions such as:

```text
Show me my recent emails.

Find emails from my college.

Summarize this email.

Find emails containing internship opportunities.

What are the important emails I received recently?

Find emails from a particular sender.
```

## 🔒 Security

This project uses Google OAuth 2.0 for authentication and does not require users to provide their Gmail password directly to the application.

For production deployment:

* Store secrets using environment variables or a secret manager.
* Never commit `.env` files.
* Use HTTPS.
* Follow Google's OAuth and Gmail API policies.
* Request only the Gmail permissions required by the application.
* Properly handle and revoke authentication tokens.

## 🎯 Future Improvements

* ✉️ AI-generated email replies
* 📤 Send emails using natural-language commands
* 🏷️ Automatic email categorization
* ⭐ Priority email detection
* 📊 Email analytics and insights
* 🔔 Smart notifications
* 📅 Integration with Google Calendar
* 🧠 Personalized email recommendations
* 🌐 Deployment with cloud infrastructure



## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Commit your changes.
5. Push the branch.
6. Open a Pull Request.

## 📄 License

This project is intended for educational and demonstration purposes.

---

⭐ If you found this project useful, consider giving the repository a star!
