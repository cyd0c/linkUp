from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint("auth", __name__)

from flask_login import current_user
from models import Blog, Job, User

@auth_bp.route("/")
def index():
    blogs = Blog.query.filter_by(status="approved").order_by(Blog.created_at.desc()).all()

    jobs = []
    user_posts = []

    if current_user.is_authenticated:
        if current_user.role == "Student":
            jobs = Job.query.filter_by(status="open").order_by(Job.created_at.desc()).all()
            user_posts = Blog.query.join(User).filter(User.role == "Client", Blog.status=="approved").order_by(Blog.created_at.desc()).all()

        elif current_user.role == "Client":
            user_posts = Blog.query.join(User).filter(User.role == "Student", Blog.status=="approved").order_by(Blog.created_at.desc()).all()

    return render_template("index.html", blogs=blogs, jobs=jobs, user_posts=user_posts)

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/proofs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@auth_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]
        email = request.form["email"]

        # Optional fields
        college_id = request.form.get("college_id") if role == "Student" else None
        company_name = request.form.get("company_name") if role == "Client" else None
        company_address = request.form.get("company_address") if role == "Client" else None
        contact_number = request.form.get("contact_number") if role == "Client" else None
        website = request.form.get("website") if role == "Client" else None

        # Handle proof file
        proof = None
        if role == "Student":
         proof = request.files.get("student_proof")
        elif role == "Client":
         proof = request.files.get("client_proof")

        proof_path = None
        if proof and proof.filename:
            filename = secure_filename(proof.filename)
            proof.save(os.path.join(UPLOAD_FOLDER, filename))
            proof_path = f"proofs/{filename}"

        if role == "Admin":
            flash("You cannot register as Admin directly!", "danger")
            return redirect(url_for("auth.register"))

        user = User(
            username=username,
            password=password,
            role=role,
            email=email,
            college_id=college_id,
            company_name=company_name,
            company_address=company_address,
            contact_number=contact_number,
            website=website,
            proof_file=proof_path,
            status="pending"
        )
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully! Awaiting admin approval." if role == "Student" else "Registered successfully!", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid credentials", "danger")
            return redirect(url_for("auth.login"))

        # ✅ Check if account is approved
        if user.status != "approved":
            flash("Your account is awaiting admin approval. Please try later.", "warning")
            return redirect(url_for("auth.login"))

        # ✅ Login if approved
        login_user(user)
        if user.role == "Admin":
            return redirect(url_for("admin.admin_dashboard"))
        elif user.role == "Client":
            return redirect(url_for("client.dashboard"))
        else:
            return redirect(url_for("student.dashboard"))

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for("auth.login"))
