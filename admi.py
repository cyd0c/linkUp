# create_admin.py
from werkzeug.security import generate_password_hash
from app import app, db
from models import User

def create_admin(username="admin", password="admin123", email="admin@example.com"):
    with app.app_context():
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"⚠️ User '{username}' already exists with role {existing.role}.")
            return

        hashed_pw = generate_password_hash(password)
        admin = User(
            username=username,
            password=hashed_pw,
            role="Admin",
            status="approved",
            email=email
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin user created: username={username}, password={password}")

if __name__ == "__main__":
    create_admin()
