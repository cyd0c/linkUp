from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Job, Application, Project, Review ,User,Blog
import os, secrets
from werkzeug.utils import secure_filename
from datetime import datetime

student_bp = Blueprint("student", __name__, url_prefix="/student")

UPLOAD_FOLDER = "static/uploads"

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import extract
from models import db, Job, Project, Payment

student_bp = Blueprint("student", __name__, url_prefix="/student")

@student_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "Student":
        abort(403)

    # Jobs available
    jobs = Job.query.filter_by(status="open").all()

    # Projects assigned to student
    projects = Project.query.filter_by(student_id=current_user.id).all()

    # ✅ Calculate Monthly Earnings
    now = datetime.utcnow()
    monthly_payments = (
        db.session.query(Payment)
        .filter(
            Payment.payee_id == current_user.id,  # logged in student
            Payment.status == "completed",       # only completed payments
            extract("year", Payment.created_at) == now.year,
            extract("month", Payment.created_at) == now.month,
        )
        .all()
    )
    monthly_earnings = sum(p.amount for p in monthly_payments)

    return render_template(
        "jobs.html",
        jobs=jobs,
        projects=projects,
        monthly_earnings=monthly_earnings
    )


@student_bp.route("/job/<int:job_id>", methods=["GET","POST"])
@login_required
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == "POST":
        if current_user.role != "Student":
            abort(403)
        existing = Application.query.filter_by(job_id=job.id, student_id=current_user.id).first()
        if existing:
            flash("You already applied!", "warning")
        else:
            app = Application(job_id=job.id, student_id=current_user.id,
                              cover_letter=request.form.get("cover_letter"))
            db.session.add(app)
            db.session.commit()
            flash("Applied successfully!", "success")
        return redirect(url_for("student.job_detail", job_id=job.id))
    applications = Application.query.filter_by(job_id=job.id).all()
    return render_template("job_detail.html", job=job, applications=applications)

from models import Message  # make sure to import

@student_bp.route("/project/<int:project_id>/update", methods=["GET","POST"])
@login_required
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user.id != project.student_id:
        abort(403)

    if request.method == "POST":
        project.progress = request.form.get("progress")

        file = request.files.get("final_file")
        file_link = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            project.final_file = f"uploads/{filename}"
            project.status = "submitted"
            file_link = project.final_file

        db.session.commit()

        # 🔹 Send system message to client
        msg_text = f"📌 Progress Update: {project.progress or 'No details'}"
        if file_link:
            msg_text += f"\n📂 Final File uploaded: <a href='/static/{file_link}' target='_blank'>Download</a>"

        msg = Message(
            sender_id=current_user.id,
            receiver_id=project.client_id,
            message_text=msg_text
        )
        db.session.add(msg)
        db.session.commit()

        flash("Project updated and client notified!", "success")
        return redirect(url_for("student.dashboard"))

    return render_template("update_project.html", project=project)


@student_bp.route("/submit_code", methods=["GET","POST"])
@login_required
def submit_code():
    if current_user.role != "Student":
        abort(403)

    if request.method == "POST":
        code = request.form["approval_code"].strip().upper()
        project = Project.query.filter_by(student_id=current_user.id, approval_code=code).first()

        if project:
            # Mark project as awaiting verification
            project.status = "submitted"
            db.session.commit()

            flash("Code submitted! Waiting for admin verification.", "info")
        else:
            flash("Invalid code!", "danger")

    return render_template("submit_code.html")

@student_bp.route("/portfolio/<int:student_id>")
def portfolio(student_id):
    student = User.query.get_or_404(student_id)
    projects = Project.query.filter_by(student_id=student.id, verified=True).all()
    return render_template("portfolio.html", student=student, projects=projects)

@student_bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if current_user.role != "Student":
        abort(403)

    if request.method == "POST":
        current_user.bio = request.form.get("bio")
        current_user.skills = request.form.get("skills")

        # Resume upload
        file = request.files.get("resume")
        if file and file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            current_user.resume = f"uploads/{filename}"

        # Profile picture upload
        pic = request.files.get("profile_pic")
        if pic and pic.filename:
            filename = secure_filename("pic_" + str(current_user.id) + "_" + pic.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            pic.save(path)
            current_user.profile_pic = f"uploads/{filename}"

        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for("student.portfolio", student_id=current_user.id))

    return render_template("edit_profile.html", student=current_user)

@student_bp.route("/post_blog", methods=["GET", "POST"])
@login_required
def post_blog():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        blog = Blog(author_id=current_user.id, title=title, content=content)
        db.session.add(blog)
        db.session.commit()
        flash("Blog posted successfully!", "success")
        return redirect(url_for("auth.index"))
    return render_template("post_blog.html")
