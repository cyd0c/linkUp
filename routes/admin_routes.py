from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, User, Project, Job

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != "Admin":
        abort(403)
    pending_users = User.query.filter_by(status="pending").all()
    projects = Project.query.all()
    jobs = Job.query.all()
    return render_template("admin_dashboard.html",
                           pending_users=pending_users, projects=projects, jobs=jobs)

@admin_bp.route("/user/<int:user_id>/approve", methods=["POST"])
@login_required
def approve_user(user_id):
    if current_user.role != "Admin":
        abort(403)
    user = User.query.get_or_404(user_id)
    user.status = "approved"
    db.session.commit()
    flash(f"User {user.username} approved!", "success")
    return redirect(url_for("admin.admin_dashboard"))

@admin_bp.route("/user/<int:user_id>/reject", methods=["POST"])
@login_required
def reject_user(user_id):
    if current_user.role != "Admin":
        abort(403)
    user = User.query.get_or_404(user_id)
    user.status = "rejected"
    db.session.commit()
    flash(f"User {user.username} rejected!", "danger")
    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/verify", methods=["GET","POST"])
@login_required
def admin_verify():
    if current_user.role != "Admin":
        abort(403)
    projects = Project.query.filter(Project.approval_code != None,Project.verified == False,Project.status == "submitted").all()
    if request.method == "POST":
        pid = int(request.form["project_id"])
        project = Project.query.get_or_404(pid)
        project.verified = True
        project.status = "completed"
        db.session.commit()
        flash("Project verified!", "success")
        return redirect(url_for("admin.admin_verify"))
    return render_template("admin_verify.html", projects=projects)

@admin_bp.route("/analytics")
@login_required
def admin_analytics():
    if current_user.role != "Admin":
        abort(403)

    total_users = User.query.count()
    total_students = User.query.filter_by(role="Student").count()
    total_clients = User.query.filter_by(role="Client").count()
    pending_students = User.query.filter_by(role="Student", status="pending").count()

    total_jobs = Job.query.count()
    open_jobs = Job.query.filter_by(status="open").count()
    closed_jobs = Job.query.filter_by(status="closed").count()

    total_projects = Project.query.count()
    completed_projects = Project.query.filter_by(status="completed").count()
    verified_projects = Project.query.filter_by(verified=True).count()

    avg_rating = None
    ratings = [u.average_rating for u in User.query.filter_by(role="Student").all() if u.average_rating]
    if ratings:
        avg_rating = sum(ratings) / len(ratings)

    stats = {
        "total_users": total_users,
        "total_students": total_students,
        "total_clients": total_clients,
        "pending_students": pending_students,
        "total_jobs": total_jobs,
        "open_jobs": open_jobs,
        "closed_jobs": closed_jobs,
        "total_projects": total_projects,
        "completed_projects": completed_projects,
        "verified_projects": verified_projects,
        "avg_student_rating": avg_rating,
    }

    projects = Project.query.all()
    users = User.query.all()   # ✅ Fetch all users

    return render_template("admin_analytics.html", stats=stats, projects=projects, users=users)

@admin_bp.route("/user/<int:user_id>")
@login_required
def view_user(user_id):
    if current_user.role != "Admin":
        abort(403)

    user = User.query.get_or_404(user_id)

    # Show profile even if not yet approved
    projects = Project.query.filter_by(student_id=user.id, verified=True).all() if user.role == "Student" else []

    return render_template("admin_view_user.html", user=user, projects=projects)

from models import db, User, RemovedUser

@admin_bp.route("/user/<int:user_id>/remove", methods=["POST"])
@login_required
def remove_user(user_id):
    if current_user.role != "Admin":
        abort(403)

    user = User.query.get_or_404(user_id)

    # Save to RemovedUser table before deleting
    removed = RemovedUser(
        username=user.username,
        email=user.email,
        role=user.role,
        reason="Removed by admin"
    )
    db.session.add(removed)

    # Delete from main User table
    db.session.delete(user)
    db.session.commit()

    flash(f"User {user.username} has been removed and archived.", "danger")
    return redirect(url_for("admin.admin_analytics"))
@admin_bp.route("/archived_users")
@login_required
def archived_users():
    if current_user.role != "Admin":
        abort(403)

    removed_users = RemovedUser.query.all()
    return render_template("archived_users.html", removed_users=removed_users)

from models import Blog

@admin_bp.route("/blogs")
@login_required
def manage_blogs():
    if current_user.role != "Admin":
        abort(403)
    pending_blogs = Blog.query.filter_by(status="pending").all()
    approved_blogs = Blog.query.filter_by(status="approved").all()
    rejected_blogs = Blog.query.filter_by(status="rejected").all()
    return render_template("admin_blogs.html", pending=pending_blogs, approved=approved_blogs, rejected=rejected_blogs)

@admin_bp.route("/blogs/<int:blog_id>/approve", methods=["POST"])
@login_required
def approve_blog(blog_id):
    if current_user.role != "Admin":
        abort(403)
    blog = Blog.query.get_or_404(blog_id)
    blog.status = "approved"
    db.session.commit()
    flash("Blog approved!", "success")
    return redirect(url_for("admin.manage_blogs"))

@admin_bp.route("/blogs/<int:blog_id>/reject", methods=["POST"])
@login_required
def reject_blog(blog_id):
    if current_user.role != "Admin":
        abort(403)
    blog = Blog.query.get_or_404(blog_id)
    blog.status = "rejected"
    db.session.commit()
    flash("Blog rejected!", "danger")
    return redirect(url_for("admin.manage_blogs"))
