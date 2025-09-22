from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Init extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register Blueprints
from routes.auth_routes import auth_bp
from routes.client_routes import client_bp
from routes.student_routes import student_bp
from routes.admin_routes import admin_bp
from routes.message_routes import message_bp
from routes.blog_routes import blog_bp ,explore_bp


app.register_blueprint(auth_bp)
app.register_blueprint(client_bp)
app.register_blueprint(student_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(message_bp)
app.register_blueprint(blog_bp)
app.register_blueprint(explore_bp) 

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
