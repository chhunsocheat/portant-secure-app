import json
import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session,jsonify
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token
from functools import wraps

###############################
# for MongoDB
from bson.objectid import ObjectId
import uuid
import pymongo
import datetime
import random
import string
###########################
load_dotenv()  # Load dotenv before importing project level packages

from drive import GoogleDrive
from flow import get_flow, login_user
from Encryption import encryption, keyGen
# from models import User, OneTimeURL, db

app = Flask(__name__)
#register route blueprint
app.secret_key = os.getenv("SECRET_KEY")
#mongoDB
client=pymongo.MongoClient("localhost",27017)
db=client.portant_app
#try to import route but doesnt work
from user import routesMongo
from secrets import token_hex
#SQL
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db.sqlite"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# db.init_app(app)

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for _ in range(size))

#########################################
# Custom form creation and save to mongoDB database
class Form:

    def createForm(self):
        # generate key pair
        # after keypair is generated, send public and private key into mongoDB. Also send public key into web browser form.
        # public key will be send into the form creation and onto the web browser for js encryption.
        # use public key to make verifyCode eventually
        keyPair = keyGen.genKeys()
        # print(keyPair[1])

        data = json.loads(request.data)
        form = {
            "_id": uuid.uuid4().hex,
            "createBy": User().get_current().get("email"),
            "formObj": data,
            "date": datetime.datetime.now(),
            "verifyCode":id_generator(),
            "pubKey": (str(keyPair[0]['n']), str(keyPair[0]['e'])), # (n, e). PubKey structure
            "privKey": (str(keyPair[1]['n']), str(keyPair[1]['e']), str(keyPair[1]['d']), str(keyPair[1]['p']), str(keyPair[1]['q'])),  # (n, e, d, p, q). PrivKey structure
        }
        if(db.forms.insert_one(form)):
            return jsonify(message="Success",data=data,form=form), 200
        return jsonify(message="failed"), 400


############################################
#routes related to request Form
@app.route('/rec-user-form', methods=['POST'])
def rec_user_form():

    return Form().createForm()



# when user create their own request form
@app.route("/createform")
def createForm():
    
    return render_template("createform.html")

@app.route('/verify-form/', methods=['POST', 'GET'])
def verify_form():
    formID = request.args.get("formID")
    return render_template("verify_modal.html")

@app.route('/verify-form-redirect/', methods=['POST'])
def verify_form1():
    print(request.args.get("verifyCode"))
    verifyCodeClient = json.loads(request.data)
    formID = request.args.get("formID")
    form = db.forms.find_one({"_id": formID})
    if(verifyCodeClient==form.get("verifyCode")):
        print("Correct")
        return jsonify(message="Verify Success",formID=formID), 200

    return jsonify(message="Verify Code Not Correct",verify=False), 404

# Search For Form created By user
# get an id from the link and search for that document in the database to send back the custom form
@app.route('/respond-form/', methods=['POST', 'GET'])
def respond_form():
    formID= request.args.get("formID")
    form=db.forms.find_one({ "_id": formID })
    pubKey = form["pubKey"]
    # print(form)
    return render_template("respond_form.html", formID=formID, form=form, pubKey=pubKey, userEmail=User().get_current().get("email"))


############################################
# Respondant Form
class ResForm:
    def resForm(self):
        print("Before Data")

        data = json.loads(request.data)
        print(data, "data that got from client")
        # encrypt data and send off to server
        

        # add the responded form to its own schema
        respondantForm = {
            "_id": uuid.uuid4().hex,
            "sendBy": data.get("sentFrom"),
            "formObj": data,
            "date": datetime.datetime.now()
        }
        print("Before Success")

        # add the responded form to the user schema
        if(db.respondantForms.insert_one(respondantForm)):
            data["formId"] = respondantForm.get("_id")
            db.user.update({"email": data.get("sentFrom")},
                           {'$push': {'respondForm': data, "listOfForm": respondantForm.get("_id")},
                            })
            print("Success")
            return jsonify(message="Success", respondantForm=respondantForm, data=data), 200
        return jsonify(data=data), 200



@app.route('/respond-user-form', methods=['POST'])
def respond_user_form():
    # testing encryption
    data = json.loads(request.data)
    print("data:")
    print(data[1])
    pkey = db.forms.find_one({"_id": data[0]})
    # make pkey(private key) array into original dictionary structure
    msg = encryption.decrypt(request.data, )
    print("plain Text:")
    print(msg)

    ######################
    return ResForm().resForm()


############################################


GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive",
]

# User Class
class User:
    def login_user(self,code):
        flow = get_flow()

        flow.fetch_token(code=code)

        creds = flow.credentials
        idinfo = verify_oauth2_token(creds.id_token, requests.Request(), GOOGLE_CLIENT_ID)

        email = idinfo["email"]
        
        user = db.user.find_one({"email":email})
            
        # if there is no user in our database
        #create user then return them
        if not user:
            user={
                "_id":uuid.uuid4().hex,
                "email":idinfo.get("email"),
                "given_name": idinfo.get("given_name"),
                "family_name":idinfo.get("family_name"),
                "avatar_url": idinfo.get("picture"),
                "auth_token" : token_hex(32),
                "oauth_credentials":{
                    "token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri": creds.token_uri,
                    "scopes": creds.scopes,
                }
            }
            db.user.insert_one(user)
            return user
        #otherwise return the user that was found by email in the database
        return user
    def get_current(self):
        """
        Returns current user, based on stored auth token
        """
        auth_token = session.get("auth_token")
        print(auth_token)
        if not auth_token:
            return None
        user = db.user.find_one({"auth_token":auth_token})

        return user 


@app.route("/list-all-resp-forms")
def allRespForms():
    return render_template("all_forms.html")


































@app.context_processor
def inject_user():
    return dict(user=User().get_current())


#main route
@app.route("/")
def index():
    return render_template("index.html")




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


# varible_name = "hello"
# example of dynamic routing and capturing variable from url
# https://dev.to/ketanip/routing-in-flask-23ff#:~:text=Dynamic%20routing%20means%20getting%20dynamic,dynamic%20input%20from%20the%20URL.&text=You%20may%20get%20data%20from,but%20is%20recommended%20to%20use.&text=It%20will%20convert%20the%20given,pass%20it%20to%20the%20function.
# @app.route('/<varible_name>/')
# def DynamicUrl(varible_name):
#     OneTimeURL.CreateURL(1)
#     return str(varible_name)

############################################
#routes related to Google Drive API stuff

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

@app.route("/")



@app.route("/make-document", methods=["POST"])
def make_document():
    data = json.loads(request.data)
    print(data)

    # user = User.get_current()
    # drive = GoogleDrive(user)

    # document_id = drive.create_document(data["document-title"])
    # drive.append_document_text(document_id, data["document-body"])

    # payload = {"url": f"https://docs.google.com/document/d/{document_id}"}
    payload = {"url": f"https://docs.google.com/document/d/"}
    return (json.dumps(payload), 200)

############################################

@app.route("/oauth-callback")
def oauth_callback():
    code = request.args.get("code")

    # user = login_user(code)
    user= User().login_user(code)
    print(user["auth_token"],"USER###################")
    session["auth_token"] = user["auth_token"]

    return redirect("/")

@app.route("/logout")
def logout():
    del session["auth_token"]
    return redirect("/")


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)

