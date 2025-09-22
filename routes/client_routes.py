from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Job, Application, Project,Payment
import secrets

client_bp = Blueprint("client", __name__, url_prefix="/client")

@client_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "Client":
        abort(403)
    jobs = Job.query.filter_by(client_id=current_user.id).all()
    projects = Project.query.filter_by(client_id=current_user.id).all()
    return render_template("client_dashboard.html", jobs=jobs, projects=projects)

@client_bp.route("/post_job", methods=["GET","POST"])
@login_required
def post_job():
    if current_user.role != "Client":
        abort(403)
    if request.method == "POST":
        job = Job(
            client_id=current_user.id,
            title=request.form["title"],
            description=request.form["description"],
            budget=float(request.form["budget"])
        )
        db.session.add(job)
        db.session.commit()
        flash("Job posted!", "success")
        return redirect(url_for("client.dashboard"))
    return render_template("post_job.html")

@client_bp.route("/project/<int:project_id>")
@login_required
def view_project(project_id):
    if current_user.role != "Client":
        abort(403)
    project = Project.query.get_or_404(project_id)
    if project.client_id != current_user.id:
        abort(403)
    return render_template("client_view_project.html", project=project)

@client_bp.route("/project/<int:project_id>/approve", methods=["POST"])
@login_required
def approve_project(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user.id != project.client_id:
        abort(403)

    project.status = "awaiting_code"
    project.approval_code = secrets.token_hex(4).upper()
    db.session.commit()
    payment = Payment(
        project_id=project.id,
        payer_id=current_user.id,        # client
        payee_id=project.student_id,     # student
        amount=project.job.budget,       # use job budget
        status="completed")
    
    db.session.add(payment)
    db.session.commit

    flash(f"Project approved! Here is Payment of ${project.job.budget} and approval code  {project.approval_code}", "success")
    return redirect(url_for("client.dashboard"))

@client_bp.route("/application/<int:app_id>/assign", methods=["POST"])
@login_required
def assign_application(app_id):
    app = Application.query.get_or_404(app_id)
    job = app.job

    # Ensure only the job owner (client) can assign
    if current_user.id != job.client_id:
        abort(403)

    # Close the job
    job.status = "closed"

    # Mark this application as accepted, others as rejected
    app.status = "accepted"
    for other in job.applications:
        if other.id != app.id:
            other.status = "rejected"

    # Create a project
    project = Project(
        job_id=job.id,
        student_id=app.student_id,
        client_id=job.client_id,
        status="in_progress"
    )
    db.session.add(project)
    db.session.commit()

    flash("Application accepted. Project created!", "success")
    return redirect(url_for("client.dashboard"))
