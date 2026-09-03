from database import SessionLocal, Email
from datetime import datetime, timedelta


emails = [
    # ---------------- PROFESSOR ----------------
    {
        "sender": "professor@university.edu",
        "recipient": "student@gmail.com",
        "subject": "Assignment Submission Deadline",
        "body": "Please submit your machine learning assignment by September 3rd at 11:59 PM.",
        "category": "Professor",
        "priority": "High",
        "sentiment": "Neutral",
        "requires_reply": True,
        "read": False,
    },
    {
        "sender": "professor@university.edu",
        "recipient": "student@gmail.com",
        "subject": "Project Review Meeting",
        "body": "Your project review has been scheduled for Monday at 10 AM. Please prepare your presentation.",
        "category": "Professor",
        "priority": "High",
        "sentiment": "Neutral",
        "requires_reply": True,
        "read": False,
    },
    {
        "sender": "professor@university.edu",
        "recipient": "student@gmail.com",
        "subject": "Viva Schedule",
        "body": "The final viva will be conducted next Friday. Your slot is 2:30 PM.",
        "category": "Professor",
        "priority": "High",
        "sentiment": "Neutral",
        "requires_reply": False,
        "read": True,
    },

    # ---------------- COLLEGE ----------------
    {
        "sender": "placements@college.edu",
        "recipient": "student@gmail.com",
        "subject": "Placement Drive - Data Analyst",
        "body": "A company will conduct a campus placement drive for the Data Analyst role. Registration closes tomorrow.",
        "category": "College",
        "priority": "High",
        "sentiment": "Positive",
        "requires_reply": True,
        "read": False,
    },
    {
        "sender": "training@college.edu",
        "recipient": "student@gmail.com",
        "subject": "Workshop on Generative AI",
        "body": "You are invited to attend a workshop on Generative AI this Saturday at 10 AM.",
        "category": "College",
        "priority": "Medium",
        "sentiment": "Positive",
        "requires_reply": False,
        "read": True,
    },
    {
        "sender": "examcell@college.edu",
        "recipient": "student@gmail.com",
        "subject": "Mid Semester Exam Notice",
        "body": "The mid semester examinations will begin from September 10th. Please check the attached schedule.",
        "category": "College",
        "priority": "High",
        "sentiment": "Neutral",
        "requires_reply": False,
        "read": False,
    },

    # ---------------- WORK ----------------
    {
        "sender": "manager@company.com",
        "recipient": "employee@gmail.com",
        "subject": "Weekly Team Meeting",
        "body": "Our weekly team meeting is scheduled for tomorrow at 11 AM. Please join on time.",
        "category": "Work",
        "priority": "Medium",
        "sentiment": "Neutral",
        "requires_reply": False,
        "read": True,
    },
    {
        "sender": "manager@company.com",
        "recipient": "employee@gmail.com",
        "subject": "Project Update Required",
        "body": "Please send me the latest progress update for the project before 5 PM today.",
        "category": "Work",
        "priority": "High",
        "sentiment": "Neutral",
        "requires_reply": True,
        "read": False,
    },
    {
        "sender": "hr@company.com",
        "recipient": "employee@gmail.com",
        "subject": "Internship Performance Review",
        "body": "Your internship performance review is scheduled for next Wednesday.",
        "category": "Work",
        "priority": "Medium",
        "sentiment": "Positive",
        "requires_reply": False,
        "read": True,
    },
    {
        "sender": "teamlead@company.com",
        "recipient": "employee@gmail.com",
        "subject": "Urgent Production Issue",
        "body": "We noticed an issue in production. Please investigate it immediately and provide an update.",
        "category": "Work",
        "priority": "High",
        "sentiment": "Negative",
        "requires_reply": True,
        "read": False,
    },

    # ---------------- PERSONAL ----------------
    {
        "sender": "friend@gmail.com",
        "recipient": "student@gmail.com",
        "subject": "Birthday Celebration",
        "body": "Hey! We are planning a birthday celebration this weekend. Let me know if you can join.",
        "category": "Personal",
        "priority": "Low",
        "sentiment": "Positive",
        "requires_reply": True,
        "read": False,
    },
    {
        "sender": "friend@gmail.com",
        "recipient": "student@gmail.com",
        "subject": "Lunch Tomorrow?",
        "body": "Are you free for lunch tomorrow around 1 PM?",
        "category": "Personal",
        "priority": "Low",
        "sentiment": "Positive",
        "requires_reply": True,
        "read": True,
    },
    {
        "sender": "travel@gmail.com",
        "recipient": "student@gmail.com",
        "subject": "Trip Planning",
        "body": "Let's finalize the hotel and travel bookings for our trip this weekend.",
        "category": "Personal",
        "priority": "Medium",
        "sentiment": "Positive",
        "requires_reply": True,
        "read": False,
    },

    # ---------------- PROMOTIONAL ----------------
    {
        "sender": "offers@shop.com",
        "recipient": "student@gmail.com",
        "subject": "Big Shopping Sale",
        "body": "Get up to 70% off on selected products during our weekend sale.",
        "category": "Promotional",
        "priority": "Low",
        "sentiment": "Positive",
        "requires_reply": False,
        "read": True,
    },
    {
        "sender": "newsletter@technews.com",
        "recipient": "student@gmail.com",
        "subject": "Weekly Technology Newsletter",
        "body": "Here are this week's top technology and artificial intelligence stories.",
        "category": "Promotional",
        "priority": "Low",
        "sentiment": "Neutral",
        "requires_reply": False,
        "read": True,
    },
    {
        "sender": "offers@store.com",
        "recipient": "student@gmail.com",
        "subject": "Exclusive Discount Offer",
        "body": "You have received an exclusive discount coupon valid until Sunday.",
        "category": "Promotional",
        "priority": "Low",
        "sentiment": "Positive",
        "requires_reply": False,
        "read": False,
    },

    # ---------------- FINANCE ----------------
    {
        "sender": "alerts@bank.com",
        "recipient": "student@gmail.com",
        "subject": "Bank Transaction Alert",
        "body": "A transaction of Rs. 4,500 was made using your account. Contact us if you do not recognize it.",
        "category": "Finance",
        "priority": "High",
        "sentiment": "Neutral",
        "requires_reply": True,
        "read": False,
    },
    {
        "sender": "bank@bank.com",
        "recipient": "student@gmail.com",
        "subject": "Monthly Account Statement",
        "body": "Your monthly account statement is now available.",
        "category": "Finance",
        "priority": "Medium",
        "sentiment": "Neutral",
        "requires_reply": False,
        "read": True,
    },

    # ---------------- INTERVIEW / CAREER ----------------
    {
        "sender": "recruiter@company.com",
        "recipient": "student@gmail.com",
        "subject": "Interview Invitation",
        "body": "We would like to invite you for an interview for the Software Engineer position.",
        "category": "Career",
        "priority": "High",
        "sentiment": "Positive",
        "requires_reply": True,
        "read": False,
    },
    {
        "sender": "hr@startup.com",
        "recipient": "student@gmail.com",
        "subject": "Application Update",
        "body": "Thank you for applying. Your application has been shortlisted for the next round.",
        "category": "Career",
        "priority": "High",
        "sentiment": "Positive",
        "requires_reply": True,
        "read": False,
    },

    # ---------------- SERVICES ----------------
    {
        "sender": "support@cloud.com",
        "recipient": "student@gmail.com",
        "subject": "Password Reset Request",
        "body": "Your password reset request has been received. If you did not request this, contact support.",
        "category": "Services",
        "priority": "High",
        "sentiment": "Neutral",
        "requires_reply": False,
        "read": False,
    },
    {
        "sender": "delivery@shopping.com",
        "recipient": "student@gmail.com",
        "subject": "Your Package Has Been Delivered",
        "body": "Your package has been successfully delivered.",
        "category": "Services",
        "priority": "Low",
        "sentiment": "Positive",
        "requires_reply": False,
        "read": True,
    },
]


def seed_database():
    db = SessionLocal()

    try:
        # Prevent duplicate seeding
        existing_count = db.query(Email).count()

        if existing_count > 0:
            print(f"Database already contains {existing_count} emails.")
            print("Skipping seed operation.")
            return

        base_time = datetime.utcnow()

        for index, email_data in enumerate(emails):
            email = Email(
                sender=email_data["sender"],
                recipient=email_data["recipient"],
                subject=email_data["subject"],
                body=email_data["body"],
                timestamp=base_time - timedelta(hours=index * 3),
                read=email_data["read"],
                category=email_data["category"],
                priority=email_data["priority"],
                sentiment=email_data["sentiment"],
                requires_reply=email_data["requires_reply"],
            )

            db.add(email)

        db.commit()

        print(f"Successfully seeded {len(emails)} emails.")

    except Exception as e:
        db.rollback()
        print("Error while seeding database:", e)

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()