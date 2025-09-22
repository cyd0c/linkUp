from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False,nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="pending")

    # Existing fields
    badge = db.Column(db.String(100), default=None)
    bio = db.Column(db.Text, default="")
    skills = db.Column(db.Text, default="")
    resume = db.Column(db.String(200), default=None)
    profile_pic = db.Column(db.String(200), default="static/default_avatar.png")

    # 🔹 New proof fields
    email = db.Column(db.String(120), unique=True, nullable=True)

    # Student-specific
    college_id = db.Column(db.String(200), nullable=True)

    # Client-specific
    company_name = db.Column(db.String(200), nullable=True)
    company_address = db.Column(db.String(300), nullable=True)
    contact_number = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(200), nullable=True)

    # File uploads (optional proofs)
    proof_file = db.Column(db.String(200), nullable=True)  # uploaded proof doc

    @property
    def average_rating(self):
        from models import Review, Project
        reviews = (
            Review.query.join(Project)
            .filter(Project.student_id == self.id)
            .all()
        )
        if not reviews:
            return None
        return sum(r.rating for r in reviews) / len(reviews)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship("User", foreign_keys=[client_id])

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job", backref="applications")
    student = db.relationship("User", foreign_keys=[student_id])

import secrets

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    client_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    status = db.Column(db.String(50), default="in_progress")  # in_progress, submitted, completed
    progress = db.Column(db.String(255))
    final_file = db.Column(db.String(300))
    approval_code = db.Column(db.String(12), nullable=True)   # generated when approved
    verified = db.Column(db.Boolean, default=False)           # set by admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job")
    student = db.relationship("User", foreign_keys=[student_id])
    client = db.relationship("User", foreign_keys=[client_id])


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id], backref="messages_sent")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="messages_received")


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
    payer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    payee_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1–5 stars
    text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", backref="reviews")
    reviewer = db.relationship("User", foreign_keys=[reviewer_id])

class RemovedUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(200))  # e.g. "Rejected", "Removed by admin"
    removed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship("User", backref="blogs")
