import os
import base64

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from database import SessionLocal, Email

load_dotenv()


# =========================================================
# BASE EMAIL SERVICE
# =========================================================

class EmailService(ABC):
    """
    Common interface for all email sources.

    Both LocalEmailService and GmailEmailService implement
    these methods so the rest of the application can use
    either local database emails or Gmail emails.
    """

    @abstractmethod
    def list_emails(
        self,
        query: str = "",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_unread(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_important(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_unread_high_priority(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_email(
        self,
        email_id: int
    ) -> Optional[Dict[str, Any]]:
        pass

    def is_authenticated(self) -> bool:
        return True


# =========================================================
# HELPER
# =========================================================

def email_to_dict(email) -> Dict[str, Any]:
    """
    Convert SQLAlchemy Email object into a normal dictionary.
    """

    return {
        "id": email.id,
        "sender": email.sender,
        "recipient": getattr(email, "recipient", None),
        "subject": email.subject,
        "body": email.body,
        "timestamp": str(email.timestamp),
        "read": email.read,
        "category": getattr(email, "category", None),
        "priority": getattr(email, "priority", None),
        "sentiment": getattr(email, "sentiment", None),
        "requires_reply": getattr(email, "requires_reply", None),
        "important": getattr(email, "important", None),
    }


# =========================================================
# LOCAL DATABASE SERVICE
# =========================================================

class LocalEmailService(EmailService):
    """
    Email service backed by the local SQLite database.
    """

    # -----------------------------------------------------
    # LIST EMAILS
    # -----------------------------------------------------

    def list_emails(
        self,
        query: str = "",
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        db = SessionLocal()

        try:
            query_db = db.query(Email)

            if query:
                search = f"%{query}%"

                query_db = query_db.filter(
                    (Email.sender.ilike(search))
                    | (Email.subject.ilike(search))
                    | (Email.body.ilike(search))
                    | (Email.category.ilike(search))
                    | (Email.priority.ilike(search))
                )

            emails = (
                query_db
                .order_by(Email.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                email_to_dict(email)
                for email in emails
            ]

        finally:
            db.close()

    # -----------------------------------------------------
    # UNREAD
    # -----------------------------------------------------

    def get_unread(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        db = SessionLocal()

        try:
            emails = (
                db.query(Email)
                .filter(Email.read == False)
                .order_by(Email.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                email_to_dict(email)
                for email in emails
            ]

        finally:
            db.close()

    # -----------------------------------------------------
    # IMPORTANT
    # -----------------------------------------------------

    def get_important(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        db = SessionLocal()

        try:

            # If the Email model has an "important" column,
            # use it directly.
            if hasattr(Email, "important"):

                emails = (
                    db.query(Email)
                    .filter(Email.important == True)
                    .order_by(Email.timestamp.desc())
                    .limit(limit)
                    .all()
                )

            else:

                # Fallback:
                # Treat high-priority emails as important.
                emails = (
                    db.query(Email)
                    .filter(
                        Email.priority.ilike("%high%")
                    )
                    .order_by(Email.timestamp.desc())
                    .limit(limit)
                    .all()
                )

            return [
                email_to_dict(email)
                for email in emails
            ]

        finally:
            db.close()

    # -----------------------------------------------------
    # UNREAD + HIGH PRIORITY
    # -----------------------------------------------------

    def get_unread_high_priority(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        db = SessionLocal()

        try:

            emails = (
                db.query(Email)
                .filter(
                    Email.read == False,
                    Email.priority.ilike("%high%")
                )
                .order_by(Email.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [
                email_to_dict(email)
                for email in emails
            ]

        finally:
            db.close()

    # -----------------------------------------------------
    # GET ONE EMAIL
    # -----------------------------------------------------

    def get_email(
        self,
        email_id: int
    ) -> Optional[Dict[str, Any]]:

        db = SessionLocal()

        try:

            email = (
                db.query(Email)
                .filter(Email.id == email_id)
                .first()
            )

            if not email:
                return None

            return email_to_dict(email)

        finally:
            db.close()

    # -----------------------------------------------------
    # MARK AS READ
    # -----------------------------------------------------

    def mark_as_read(
        self,
        email_id: int
    ) -> bool:

        db = SessionLocal()

        try:

            email = (
                db.query(Email)
                .filter(Email.id == email_id)
                .first()
            )

            if not email:
                return False

            email.read = True

            db.commit()

            return True

        finally:
            db.close()


# =========================================================
# GMAIL SERVICE
# =========================================================

class GmailEmailService(EmailService):
    """
    Gmail email service.

    This service uses OAuth credentials stored in token.json.

    Gmail integration will only work after Google OAuth
    credentials have been configured and the account has
    been authorized.
    """

    def __init__(self):
        self.credentials = None

        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )

        self.token_file = os.getenv(
            "GMAIL_TOKEN_FILE",
            os.path.join(base_dir, "token.json")
        )

        self._load_credentials()

    # -----------------------------------------------------
    # LOAD CREDENTIALS
    # -----------------------------------------------------

    def _load_credentials(self):

        try:

            from google.oauth2.credentials import Credentials

            if not os.path.exists(self.token_file):
                self.credentials = None
                return

            self.credentials = (
                Credentials.from_authorized_user_file(
                    self.token_file
                )
            )

        except Exception as e:

            print("Could not load Gmail credentials:", e)

            self.credentials = None

    # -----------------------------------------------------
    # AUTHENTICATION STATUS
    # -----------------------------------------------------

    def is_authenticated(self) -> bool:

        return self.credentials is not None

    # -----------------------------------------------------
    # GMAIL API SERVICE
    # -----------------------------------------------------

    def _get_service(self):

        if not self.credentials:
            return None

        try:

            from googleapiclient.discovery import build

            return build(
                "gmail",
                "v1",
                credentials=self.credentials
            )

        except Exception as e:

            print("Could not create Gmail service:", e)

            raise

    # -----------------------------------------------------
    # CONVERT GMAIL MESSAGE
    # -----------------------------------------------------

    def _gmail_message_to_dict(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:

        payload = message.get(
            "payload",
            {}
        )

        headers = payload.get(
            "headers",
            []
        )

        sender = ""
        recipient = ""
        subject = ""

        for header in headers:

            name = header.get(
                "name",
                ""
            ).lower()

            value = header.get(
                "value",
                ""
            )

            if name == "from":
                sender = value

            elif name == "to":
                recipient = value

            elif name == "subject":
                subject = value

        label_ids = message.get(
            "labelIds",
            []
        )

        return {
            "id": message.get("id"),
            "sender": sender,
            "recipient": recipient,
            "subject": subject,
            "body": self._extract_gmail_body(payload),
            "timestamp": "",
            "read": "UNREAD" not in label_ids,
            "important": "IMPORTANT" in label_ids,
            "priority": (
                "High"
                if "IMPORTANT" in label_ids
                else "Normal"
            ),
            "category": "",
            "sentiment": None,
            "requires_reply": None,
        }

    # -----------------------------------------------------
    # EXTRACT GMAIL BODY
    # -----------------------------------------------------

    def _extract_gmail_body(
        self,
        payload: Dict[str, Any]
    ) -> str:

        body = payload.get(
            "body",
            {}
        )

        data = body.get("data")

        if data:

            try:

                return base64.urlsafe_b64decode(
                    data + "=="
                ).decode(
                    "utf-8",
                    errors="ignore"
                )

            except Exception:
                pass

        for part in payload.get(
            "parts",
            []
        ):

            result = self._extract_gmail_body(
                part
            )

            if result:
                return result

        return ""

    # -----------------------------------------------------
    # LIST GMAIL EMAILS
    # -----------------------------------------------------

    def list_emails(
        self,
        query: str = "",
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        service = self._get_service()

        if service is None:
            return []

        try:

            result = (
                service.users()
                .messages()
                .list(
                    userId="me",
                    q=query,
                    maxResults=limit
                )
                .execute()
            )

            messages = result.get(
                "messages",
                []
            )

            results = []

            for item in messages:

                message = (
                    service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=item["id"],
                        format="full"
                    )
                    .execute()
                )

                results.append(
                    self._gmail_message_to_dict(
                        message
                    )
                )

            return results

        except Exception as e:

            print(
                "Gmail API error:",
                e
            )

            return []

    # -----------------------------------------------------
    # UNREAD
    # -----------------------------------------------------

    def get_unread(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        return self.list_emails(
            query="is:unread",
            limit=limit
        )

    # -----------------------------------------------------
    # IMPORTANT
    # -----------------------------------------------------

    def get_important(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        return self.list_emails(
            query="is:important",
            limit=limit
        )

    # -----------------------------------------------------
    # UNREAD + HIGH PRIORITY
    # -----------------------------------------------------

    def get_unread_high_priority(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:

        return self.list_emails(
            query="is:unread is:important",
            limit=limit
        )

    # -----------------------------------------------------
    # GET ONE GMAIL EMAIL
    # -----------------------------------------------------

    def get_email(
        self,
        email_id: int
    ) -> Optional[Dict[str, Any]]:

        service = self._get_service()

        if service is None:
            return None

        try:

            message = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=str(email_id),
                    format="full"
                )
                .execute()
            )

            return self._gmail_message_to_dict(
                message
            )

        except Exception as e:

            print(
                "Gmail get email error:",
                e
            )

            return None