import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.agents.email_agent import run_email_agent
from app.services.email_service import (
    LocalEmailService,
    GmailEmailService,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PATHS / CONFIG
# ============================================================

# main.py is expected to be in the backend root.
#
# Example:
#
# backend/
# ├── main.py
# ├── token.json
# ├── oauth_state.json
# ├── .env
# └── app/
#
BASE_DIR = Path(__file__).resolve().parent

TOKEN_PATH = BASE_DIR / "token.json"
OAUTH_STATE_PATH = BASE_DIR / "oauth_state.json"


FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
).rstrip("/")


GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://127.0.0.1:8000/api/auth/google/callback",
)


# ============================================================
# GMAIL SCOPES
# ============================================================

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Email AI Assistant",
    description="AI-powered email management backend",
    version="2.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class EmailRequest(BaseModel):
    request: str
    source: str = "local"


class EmailResponse(BaseModel):
    response: str
    trace: list = []


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str


class GmailTrashRequest(BaseModel):
    email_id: str


# ============================================================
# SERVICES
# ============================================================

def local_service():
    return LocalEmailService()


def gmail_service():
    return GmailEmailService()


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Email AI Assistant Backend is running",
        "status": "success",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ============================================================
# LOCAL EMAIL ROUTES
# ============================================================

@app.get("/api/emails")
def list_local_emails(
    q: str = "",
    limit: int = 50,
):
    return local_service().list_emails(
        q,
        limit,
    )


@app.get("/api/emails/unread")
def unread_local_emails(
    limit: int = 50,
):
    return local_service().get_unread(
        limit,
    )


@app.get("/api/emails/important")
def important_local_emails(
    limit: int = 50,
):
    return local_service().get_important(
        limit,
    )


@app.get("/api/emails/{email_id}")
def get_local_email(
    email_id: str,
):
    result = local_service().get_email(
        email_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Email not found",
        )

    return result


@app.patch("/api/emails/{email_id}/read")
def mark_local_email_read(
    email_id: str,
):
    service = local_service()

    # Your EmailService implementation should use
    # mark_as_read(), not mark_read().
    ok = service.mark_as_read(
        email_id
    )

    if not ok:
        raise HTTPException(
            status_code=404,
            detail="Email not found",
        )

    return {
        "success": True,
    }


# ============================================================
# GMAIL STATUS
# ============================================================

@app.get("/api/gmail/status")
def gmail_status():

    try:

        service = gmail_service()

        authenticated = service.is_authenticated()

        if not authenticated:
            return {
                "connected": False,
                "authenticated": False,
                "email": "",
            }

        # Verify that the Gmail credentials actually work.
        gmail = service._get_service()

        if gmail is None:
            return {
                "connected": False,
                "authenticated": False,
                "email": "",
            }

        profile = (
            gmail.users()
            .getProfile(userId="me")
            .execute()
        )

        email_address = profile.get(
            "emailAddress",
            "",
        )

        return {
            "connected": True,
            "authenticated": True,
            "email": email_address,
        }

    except Exception as error:

        print(
            "Gmail status error:",
            repr(error),
        )

        return {
            "connected": False,
            "authenticated": False,
            "email": "",
        }


# ============================================================
# GMAIL LOGOUT / DISCONNECT
# ============================================================

@app.post("/api/gmail/logout")
def gmail_logout():

    try:

        # Remove Gmail OAuth token.
        if TOKEN_PATH.exists():
            TOKEN_PATH.unlink()

            print(
                f"Deleted Gmail token: {TOKEN_PATH}"
            )

        # Remove any leftover OAuth state.
        if OAUTH_STATE_PATH.exists():
            OAUTH_STATE_PATH.unlink()

            print(
                f"Deleted OAuth state: {OAUTH_STATE_PATH}"
            )

        return {
            "success": True,
            "connected": False,
            "message": "Gmail disconnected successfully.",
        }

    except Exception as error:

        print(
            "Gmail logout error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to disconnect Gmail: "
                f"{str(error)}"
            ),
        )


# ============================================================
# GMAIL PROFILE
# ============================================================

@app.get("/api/gmail/profile")
def gmail_profile():

    service = gmail_service()

    if not service.is_authenticated():
        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected.",
        )

    try:

        gmail = service._get_service()

        if gmail is None:
            raise HTTPException(
                status_code=401,
                detail="Unable to create Gmail service.",
            )

        profile = (
            gmail.users()
            .getProfile(userId="me")
            .execute()
        )

        return {
            "email": profile.get(
                "emailAddress",
                "",
            ),
            "messages_total": profile.get(
                "messagesTotal",
                0,
            ),
            "threads_total": profile.get(
                "threadsTotal",
                0,
            ),
        }

    except HTTPException:
        raise

    except Exception as error:

        print(
            "Gmail profile error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve Gmail profile: "
                f"{str(error)}"
            ),
        )


# ============================================================
# GOOGLE OAUTH - START
# ============================================================

@app.get("/api/auth/google")
def google_auth():

    try:

        from google_auth_oauthlib.flow import Flow

    except ImportError:

        raise HTTPException(
            status_code=500,
            detail=(
                "Google OAuth dependencies are missing. "
                "Run: pip install google-auth-oauthlib"
            ),
        )

    client_id = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    client_secret = os.getenv(
        "GOOGLE_CLIENT_SECRET"
    )

    if not client_id or not client_secret:

        raise HTTPException(
            status_code=503,
            detail=(
                "GOOGLE_CLIENT_ID and "
                "GOOGLE_CLIENT_SECRET "
                "are not configured."
            ),
        )

    # --------------------------------------------------------
    # Create OAuth flow
    # --------------------------------------------------------

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": (
                    "https://accounts.google.com/o/oauth2/auth"
                ),
                "token_uri": (
                    "https://oauth2.googleapis.com/token"
                ),
            }
        },
        scopes=GMAIL_SCOPES,
    )

    flow.redirect_uri = GOOGLE_REDIRECT_URI

    # --------------------------------------------------------
    # Generate Google authorization URL
    # --------------------------------------------------------

    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
    )

    # --------------------------------------------------------
    # Save OAuth state + PKCE verifier
    # --------------------------------------------------------

    oauth_data = {
        "state": state,
        "code_verifier": flow.code_verifier,
    }

    OAUTH_STATE_PATH.write_text(
        json.dumps(
            oauth_data,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "=========================================="
    )
    print(
        "Google OAuth started"
    )
    print(
        f"OAuth state saved: {OAUTH_STATE_PATH}"
    )
    print(
        "PKCE code verifier saved"
    )
    print(
        f"Redirect URI: {GOOGLE_REDIRECT_URI}"
    )
    print(
        "=========================================="
    )

    return RedirectResponse(
        authorization_url
    )


# ============================================================
# GOOGLE OAUTH - CALLBACK
# ============================================================

@app.get("/api/auth/google/callback")
def google_callback(
    code: str,
    state: Optional[str] = None,
):

    try:

        from google_auth_oauthlib.flow import Flow

    except ImportError:

        raise HTTPException(
            status_code=500,
            detail=(
                "Google OAuth dependencies are missing."
            ),
        )

    # --------------------------------------------------------
    # Check OAuth state file
    # --------------------------------------------------------

    if not OAUTH_STATE_PATH.exists():

        raise HTTPException(
            status_code=400,
            detail=(
                "OAuth session expired. "
                "Please click Connect Gmail again."
            ),
        )

    # --------------------------------------------------------
    # Read OAuth information
    # --------------------------------------------------------

    try:

        oauth_data = json.loads(
            OAUTH_STATE_PATH.read_text(
                encoding="utf-8"
            )
        )

    except Exception as error:

        print(
            "OAuth state read error:",
            repr(error),
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth session data.",
        )

    expected_state = oauth_data.get(
        "state"
    )

    code_verifier = oauth_data.get(
        "code_verifier"
    )

    # --------------------------------------------------------
    # Validate OAuth state
    # --------------------------------------------------------

    if (
        not state
        or not expected_state
        or state != expected_state
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state.",
        )

    # --------------------------------------------------------
    # Validate PKCE
    # --------------------------------------------------------

    if not code_verifier:

        raise HTTPException(
            status_code=400,
            detail=(
                "Missing OAuth code verifier. "
                "Please restart Gmail connection."
            ),
        )

    # --------------------------------------------------------
    # Get Google credentials
    # --------------------------------------------------------

    client_id = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    client_secret = os.getenv(
        "GOOGLE_CLIENT_SECRET"
    )

    if not client_id or not client_secret:

        raise HTTPException(
            status_code=503,
            detail=(
                "Google OAuth credentials "
                "are not configured."
            ),
        )

    # --------------------------------------------------------
    # Re-create OAuth flow
    # --------------------------------------------------------

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": (
                    "https://accounts.google.com/o/oauth2/auth"
                ),
                "token_uri": (
                    "https://oauth2.googleapis.com/token"
                ),
            }
        },
        scopes=GMAIL_SCOPES,
        state=state,
    )

    flow.redirect_uri = GOOGLE_REDIRECT_URI

    # --------------------------------------------------------
    # Restore PKCE verifier
    # --------------------------------------------------------

    flow.code_verifier = code_verifier

    # --------------------------------------------------------
    # Exchange authorization code for token
    # --------------------------------------------------------

    try:

        flow.fetch_token(
            code=code
        )

    except Exception as error:

        print(
            "=========================================="
        )
        print(
            "Google token exchange FAILED"
        )
        print(
            repr(error)
        )
        print(
            "=========================================="
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "Google authentication failed. "
                "Please try connecting Gmail again."
            ),
        )

    # --------------------------------------------------------
    # Make sure token credentials exist
    # --------------------------------------------------------

    if not flow.credentials:

        raise HTTPException(
            status_code=500,
            detail=(
                "Google authentication succeeded "
                "but no credentials were returned."
            ),
        )

    # --------------------------------------------------------
    # Save token
    # --------------------------------------------------------

    try:

        TOKEN_PATH.write_text(
            flow.credentials.to_json(),
            encoding="utf-8",
        )

        print(
            "=========================================="
        )
        print(
            "Gmail OAuth authentication successful"
        )
        print(
            f"Token saved to: {TOKEN_PATH}"
        )
        print(
            "=========================================="
        )

    except Exception as error:

        print(
            "Token save error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save Gmail authentication token."
            ),
        )

    # --------------------------------------------------------
    # Delete temporary OAuth state
    # --------------------------------------------------------

    try:

        if OAUTH_STATE_PATH.exists():
            OAUTH_STATE_PATH.unlink()

    except Exception as error:

        print(
            "Could not remove OAuth state file:",
            repr(error),
        )

    # --------------------------------------------------------
    # Verify Gmail access BEFORE redirecting frontend
    # --------------------------------------------------------

    try:

        service = GmailEmailService()

        gmail = service._get_service()

        if gmail is None:

            raise Exception(
                "Could not create Gmail API service."
            )

        profile = (
            gmail.users()
            .getProfile(userId="me")
            .execute()
        )

        connected_email = profile.get(
            "emailAddress",
            "",
        )

        print(
            f"Connected Gmail account: "
            f"{connected_email}"
        )

    except Exception as error:

        print(
            "Gmail verification after OAuth failed:",
            repr(error),
        )

        # Token exists but Gmail API access failed.
        # Remove invalid token so the application does
        # not falsely report Gmail as connected.

        try:

            if TOKEN_PATH.exists():
                TOKEN_PATH.unlink()

        except Exception:
            pass

        raise HTTPException(
            status_code=400,
            detail=(
                "Google authentication completed, "
                "but Gmail API access could not be verified. "
                "Please connect Gmail again."
            ),
        )

    # --------------------------------------------------------
    # Redirect to frontend
    # --------------------------------------------------------

    return RedirectResponse(
        f"{FRONTEND_URL}?gmail=connected"
    )


# ============================================================
# GMAIL EMAIL ROUTES
# ============================================================

@app.get("/api/gmail/emails")
def gmail_emails(
    q: str = "",
    limit: int = 50,
):

    service = gmail_service()

    if not service.is_authenticated():

        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected.",
        )

    return service.list_emails(
        q,
        limit,
    )


@app.get("/api/gmail/emails/unread")
def gmail_unread(
    limit: int = 50,
):

    service = gmail_service()

    if not service.is_authenticated():

        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected.",
        )

    return service.get_unread(
        limit
    )


@app.get("/api/gmail/emails/important")
def gmail_important(
    limit: int = 50,
):

    service = gmail_service()

    if not service.is_authenticated():

        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected.",
        )

    return service.get_important(
        limit
    )


@app.get("/api/gmail/emails/{email_id}")
def gmail_email(
    email_id: str,
):

    service = gmail_service()

    if not service.is_authenticated():

        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected.",
        )

    result = service.get_email(
        email_id
    )

    if not result:

        raise HTTPException(
            status_code=404,
            detail="Gmail message not found",
        )

    return result


# ============================================================
# MARK GMAIL EMAIL AS READ
# ============================================================

@app.patch("/api/gmail/emails/{email_id}/read")
def gmail_read(
    email_id: str,
):

    service = gmail_service()

    if not service.is_authenticated():

        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected.",
        )

    # This requires mark_as_read() to exist in
    # GmailEmailService.
    ok = service.mark_as_read(
        email_id
    )

    if not ok:

        raise HTTPException(
            status_code=404,
            detail="Gmail message not found",
        )

    return {
        "success": True
    }


# ============================================================
# SEND GMAIL
# ============================================================

@app.post("/api/gmail/send")
def gmail_send(
    payload: SendEmailRequest,
):

    service = gmail_service()

    if not service.is_authenticated():

        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected.",
        )

    try:

        message_id = service.send_email(
            payload.to,
            payload.subject,
            payload.body,
        )

        return {
            "success": True,
            "message_id": message_id,
        }

    except Exception as error:

        print(
            "Gmail send error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to send Gmail email: {str(error)}"
            ),
        )


# ============================================================
# TRASH GMAIL
# ============================================================

@app.post("/api/gmail/trash")
def gmail_trash(
    payload: GmailTrashRequest,
):

    service = gmail_service()

    if not service.is_authenticated():

        raise HTTPException(
            status_code=401,
            detail="Gmail is not connected.",
        )

    try:

        service.trash(
            payload.email_id
        )

        return {
            "success": True
        }

    except Exception as error:

        print(
            "Gmail trash error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Unable to trash Gmail email: {str(error)}"
            ),
        )


# ============================================================
# AI EMAIL AGENT
# ============================================================

@app.post(
    "/api/email-agent",
    response_model=EmailResponse,
)
def email_agent(
    payload: EmailRequest,
):

    result = run_email_agent(
        payload.request,
        payload.source,
    )

    return EmailResponse(
        **result
    )


# ============================================================
# ALTERNATIVE ASK ENDPOINT
# ============================================================

@app.post(
    "/ask",
    response_model=EmailResponse,
)
def ask(
    payload: EmailRequest,
):

    result = run_email_agent(
        payload.request,
        payload.source,
    )

    return EmailResponse(
        **result
    )


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )