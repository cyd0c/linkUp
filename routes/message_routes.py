from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Project, Message
import secrets

message_bp = Blueprint("message", __name__, url_prefix="/project")

@message_bp.route("/<int:project_id>/messages", methods=["GET","POST"])
@login_required
def project_messages(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user.id not in [project.client_id, project.student_id]:
        abort(403)

    if request.method == "POST":
        # normal text message
        if "message_text" in request.form:
            text = request.form["message_text"].strip()
            if text:
                receiver_id = project.student_id if current_user.id == project.client_id else project.client_id
                msg = Message(sender_id=current_user.id, receiver_id=receiver_id, message_text=text)
                db.session.add(msg)
                db.session.commit()
                flash("Message sent!", "success")

        # client approves project and sends approval code
        elif "approve_project" in request.form and current_user.id == project.client_id:
            project.status = "awaiting_code"
            project.approval_code = secrets.token_hex(4).upper()
            db.session.commit()

            msg_text = f"✅ Project Approved! Approval Code: <b>{project.approval_code}</b>"
            msg = Message(sender_id=current_user.id, receiver_id=project.student_id, message_text=msg_text)
            db.session.add(msg)
            db.session.commit()

            flash("Project approved and code sent to student!", "success")

        return redirect(url_for("message.project_messages", project_id=project.id))

    messages = Message.query.filter(
        ((Message.sender_id == project.client_id) & (Message.receiver_id == project.student_id)) |
        ((Message.sender_id == project.student_id) & (Message.receiver_id == project.client_id))
    ).order_by(Message.timestamp.asc()).all()

    return render_template("messages.html", project=project, messages=messages)
