import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai

from app.services.email_service import (
    EmailService,
    LocalEmailService,
    GmailEmailService,
)

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def _trace(trace, message, detail=None, kind="step"):
    item = {"type": kind, "message": message}
    if detail:
        item["detail"] = detail
    trace.append(item)


def _choose_database_operation(request: str):
    text = request.lower()

    if "unread" in text and ("high priority" in text or "high-priority" in text):
        return "unread_high_priority", None

    if "unread" in text:
        return "unread", None

    if "important" in text or "urgent" in text:
        return "important", None

    # Common natural-language sender search:
    marker = "from "
    if marker in text:
        query = text.split(marker, 1)[1].strip()
        query = query.split(" and ", 1)[0].strip(" .,!?:;")
        if query:
            if query.startswith("my "):
                query = query[3:]
            return "search", query

    # For general AI requests without specific keywords, return all recent emails
    if "summarize" in text or "action item" in text or "what are" in text or "all my emails" in text:
        return "search", ""

    # Fallback for other natural language questions
    if len(text.split()) > 3:
        return "search", ""

    return "search", request.strip()


def _compact_emails(emails: List[Dict[str, Any]]):
    compact = []
    for e in emails:
        compact.append({
            "id": e.get("id"),
            "sender": e.get("sender"),
            "subject": e.get("subject"),
            "body": e.get("body", "")[:4000],
            "timestamp": e.get("timestamp"),
            "read": e.get("read"),
            "priority": e.get("priority"),
            "important": e.get("important"),
            "requires_reply": e.get("requires_reply"),
        })
    return compact


def run_email_agent(user_request: str, source: str = "local"):
    trace = []
    _trace(trace, "Understanding request", user_request)

    if source == "gmail":
        service: EmailService = GmailEmailService()
        if not service.is_authenticated():
            _trace(trace, "Gmail not connected", "Connect Gmail before using Gmail mode.")
            return {
                "response": "Gmail is not connected. Click 'Connect Gmail' and authorize your Google account first.",
                "trace": trace,
            }
    else:
        service = LocalEmailService()

    operation, query = _choose_database_operation(user_request)

    labels = {
        "unread": "get_unread_emails",
        "important": "get_important_emails",
        "unread_high_priority": "get_unread_high_priority_emails",
        "search": "search_emails",
    }

    tool_name = labels[operation]
    detail = query if query else tool_name
    _trace(trace, "Database tool", f"{tool_name}: {detail}", "tool")

    if operation == "unread":
        emails = service.get_unread()
    elif operation == "important":
        emails = service.get_important()
    elif operation == "unread_high_priority":
        emails = service.get_unread_high_priority()
    else:
        emails = service.list_emails(query or "", limit=50)

    _trace(trace, "Database search completed", f"{len(emails)} email(s) found")

    if not emails:
        _trace(trace, "No matching emails", "The database returned no matching messages.")
        return {
            "response": "I couldn't find any emails matching that request.",
            "trace": trace,
        }

    prompt = f"""
You are an AI Email Assistant.

The user asked:
{user_request}

These are the emails returned from the application's email database:
{_compact_emails(emails)}

Answer the user's request using ONLY the supplied email data.
Do not claim you have access to anything else.
If the user asked for a summary, summarize the matching emails.
If the user asked to find/list emails, provide a concise useful list.
If the request asks for an action such as sending or deleting an email, do NOT perform it.
Instead explain that the user must explicitly approve that action in the UI.

Keep the response concise and readable.
"""

    _trace(trace, "Sending results to Gemini", "Analyzing matching emails")
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        response_text = response.text or "No response generated."
        _trace(trace, "AI response generated", "Gemini generated the email response")
    except:
        _trace(trace, "AI request failed", "An error occurred with the AI model.")
        response_text = "The AI model is currently experiencing high demand or an error occurred. Please try again later."

    return {
        "response": response_text,
        "trace": trace,
    }


if __name__ == "__main__":
    result = run_email_agent(
        "Find my unread high priority emails.",
        source="local",
    )

    print("\n" + "=" * 60)
    print("AI RESPONSE")
    print("=" * 60)
    print(result["response"])

    print("\n" + "=" * 60)
    print("AGENT EXECUTION TRACE")
    print("=" * 60)
    for item in result["trace"]:
        prefix = "→" if item["type"] == "tool" else "✓"
        print(prefix, item["message"])
        if item.get("detail"):
            print("   ", item["detail"])
