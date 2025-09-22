from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Blog

blog_bp = Blueprint("blog", __name__, url_prefix="/blog")

# 🔹 Show all approved blogs
@blog_bp.route("/all")
def all_blogs():
    blogs = Blog.query.filter_by(status="approved").order_by(Blog.created_at.desc()).all()
    return render_template("blogs.html", blogs=blogs)

# 🔹 Post a new blog
@blog_bp.route("/post", methods=["GET", "POST"])
@login_required
def post_blog():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        blog = Blog(
            author_id=current_user.id,
            title=title,
            content=content,
            status="approved"  # Or "pending" if you want admin approval
        )
        db.session.add(blog)
        db.session.commit()

        flash("Blog submitted successfully!", "success")
        return redirect(url_for("blog.all_blogs"))

    return render_template("post_blog.html")

# 🔹 My blogs only
@blog_bp.route("/my_posts")
@login_required
def my_posts():
    posts = Blog.query.filter_by(author_id=current_user.id).order_by(Blog.created_at.desc()).all()
    return render_template("my_posts.html", posts=posts)


from flask import Blueprint, render_template

explore_bp = Blueprint("explore", __name__, url_prefix="/explore")

@explore_bp.route("/")
def explore_home():
    # Dummy tech news – later connect to DB
    tech_news = [
        {"title": "AI Breakthrough", "content": "New AI model sets records...", "date": "2025-09-20"},
        {"title": "SpaceX Update", "content": "Starship prepares for launch...", "date": "2025-09-19"}
    ]
    return render_template("explore.html", tech_news=tech_news)
