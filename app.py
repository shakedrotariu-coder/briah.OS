import os

from dotenv import load_dotenv
from flask import Flask, redirect, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")

from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.melave import melave_bp
from routes.metapel import metapel_bp
from routes.lakoach import lakoach_bp
from routes.intake import intake_bp
from routes.whatsapp import wa_bp
from routes.care_manager import cm_bp
from routes.onboarding import ob_bp
from routes.reflection import reflection_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(melave_bp)
app.register_blueprint(metapel_bp)
app.register_blueprint(lakoach_bp)
app.register_blueprint(intake_bp)
app.register_blueprint(wa_bp)
app.register_blueprint(cm_bp)
app.register_blueprint(ob_bp)
app.register_blueprint(reflection_bp)

_ROLE_HOME = {
    "admin": "/admin",
    "melave": "/melave",
    "metapel": "/metapel",
    "lakoach": "/lakoach",
}


@app.route("/")
def root():
    if not session.get("user_id"):
        return redirect("/login")
    return redirect(_ROLE_HOME.get(session.get("role"), "/login"))


if __name__ == "__main__":
    app.run(debug=True)
