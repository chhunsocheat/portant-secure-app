import json
import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session,jsonify
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token
from functools import wraps
import uuid
import pymongo
load_dotenv()  # Load dotenv before importing project level packages

from drive import GoogleDrive
from flow import get_flow, login_user

# from models import User, OneTimeURL, db

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
#mongoDB
client=pymongo.MongoClient("localhost",27017)
db=client.portant_app

# import routes
#SQL
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db.sqlite"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# db.init_app(app)


#########################################
# Custom form creation and save to mongoDB database
class Form:

    def createForm(self):

        data = json.loads(request.data)
        form={
            "_id":uuid.uuid4().hex,
            "createBy":"Socheat",
            "formObj":data
        }
        db.forms.insert_one(form)
        return jsonify(message="Success",data=data), 200

@app.route('/rec-user-form',methods=['POST'])
def rec_user_form():
    return Form().createForm()

# when user create their own form 
@app.route("/createform")
def createForm():
    
    return render_template("createform.html")

############################################

# @app.context_processor
# def inject_user():
#     return dict(user=User.get_current())

#main route
@app.route("/")
def index():
    



    return render_template("index.html")
# //in app sign in









@app.route("/signup")
def signup():
    return render_template("signup.html")


    


# def check_Valid_URL(function):
#     @wraps(function)
#     def wrapper(URL):
#         print("Checking URL sxists")
#         if (OneTimeURL.CheckURLExists(URL) == False):
#             print("URL doesn't exist")
#             redirect("/")
#         return function()
#     return wrapper


# @app.route("/page/<URL>")
# @check_Valid_URL
# def respondents_Submission(URL):
#     context = {}
#     return render_template("respondents_submission_page.html", **context)


varible_name = "hello"
# example of dynamic routing and capturing variable from url
# https://dev.to/ketanip/routing-in-flask-23ff#:~:text=Dynamic%20routing%20means%20getting%20dynamic,dynamic%20input%20from%20the%20URL.&text=You%20may%20get%20data%20from,but%20is%20recommended%20to%20use.&text=It%20will%20convert%20the%20given,pass%20it%20to%20the%20function.
# @app.route('/<varible_name>/')
# def DynamicUrl(varible_name):
#     OneTimeURL.CreateURL(1)
#     return str(varible_name)


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


# @app.route("/make-document", methods=["POST"])
# def make_document():
#     data = json.loads(request.data)

#     user = User.get_current()
#     drive = GoogleDrive(user)

#     document_id = drive.create_document(data["document-title"])
#     drive.append_document_text(document_id, data["document-body"])

#     payload = {"url": f"https://docs.google.com/document/d/{document_id}"}
#     return (json.dumps(payload), 200)


@app.route("/logout")
def logout():
    del session["auth_token"]
    return redirect("/")


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
