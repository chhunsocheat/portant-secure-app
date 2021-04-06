import json
import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token

load_dotenv()  # Load dotenv before importing project level packages

from drive import GoogleDrive
from flow import get_flow, login_user
from models import User, db

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.context_processor
def inject_user():
    return dict(user=User.get_current())


@app.route("/")
def index():
    return render_template("index.html")
# //in app sign in

@app.route("/signin")
def signin():
    return render_template("signin.html")

@app.route("/signin-data", methods=["POST"])
def signinData():
    print(request)
    data=json.loads(request.data)
    print(data)
    return json.dumps(data)

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/google-api")
def google_api():
    flow = get_flow()

    oauth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
    )

    context = {}
    context["oauth_url"] = oauth_url

    return render_template("google_api.html", **context)


@app.route("/oauth-callback")
def oauth_callback():
    code = request.args.get("code")

    user = login_user(code)
    session["auth_token"] = user.auth_token

    return redirect("/")


@app.route("/make-document", methods=["POST"])
def make_document():
    
    data = json.loads(request.data)

    user = User.get_current()
    drive = GoogleDrive(user)

    document_id = drive.create_document(data["document-title"])
    drive.append_document_text(document_id, data["document-body"])

    payload = {"url": f"https://docs.google.com/document/d/{document_id}"}
    return (json.dumps(payload), 200)


@app.route("/logout")
def logout():
    del session["auth_token"]
    return redirect("/")


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
