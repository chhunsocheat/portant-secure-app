from hashlib import md5
from secrets import token_hex
# from user import routesMongo
from Encryption import encryption, keyGen
from flow import get_flow, login_user
from drive import GoogleDrive
import json
import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, jsonify
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token
from functools import wraps

#################################
#sending Email
import smtplib

# Import the email modules we'll need
from email.message import EmailMessage
#################################
# Crypto Lib
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from base64 import b64decode
# AES
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
# AES 2 Python
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import algorithms
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

###############################
# for MongoDB
from bson.objectid import ObjectId
import uuid
import pymongo
import datetime
import random
import string
import ast
import itertools
###########################
load_dotenv()  # Load dotenv before importing project level packages

# from models import User, OneTimeURL, db

app = Flask(__name__)
# register route blueprint
app.secret_key = os.getenv("SECRET_KEY")
# mongoDB
client = pymongo.MongoClient("localhost", 27017)
db = client.portant_app
# try to import route but doesnt work
# SQL
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
        
       
        formID= uuid.uuid4().hex
        keyPair = keyGen().genKeys(formID)
        print(keyPair)
        data = json.loads(request.data)
        print(data.get("formData"),"form Data")
        print(data.get("recipientEmail"),"recipientEmail")
        form = {
            "_id": formID,
            "createBy": User().get_current().get("email"),
            "formObj": data.get("formData"),
            "date": datetime.datetime.now(),
            "verifyCode": id_generator(),
            "public_key": str(keyPair.get("public_key")),
            "private_key": str(keyPair.get("private_key")),
            # "pubKey": (str(keyPair[0]['n']), str(keyPair[0]['e'])), # (n, e). PubKey structure
            # "privKey": (str(keyPair[1]['n']), str(keyPair[1]['e']), str(keyPair[1]['d']), str(keyPair[1]['p']), str(keyPair[1]['q'])),  # (n, e, d, p, q). PrivKey structure
        }
        #############################
        #email
        # SMTP stuff
        server = smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login("portantdemo@gmail.com","PortantDemo99")
        msg = EmailMessage()
        # me == the sender's email address
        # you == the recipient's email address
        recEmail= data.get("recipientEmail")
        msg.set_content("Verification Code: "+form.get("verifyCode"))
        msg['Subject'] = ' Verification Code'
        msg['From'] = 'Portant <help@portant.com>'
        msg['To'] = f'{recEmail}'
        server.send_message(msg)
        server.quit()
        print("DONE")
        #############################
        if(db.forms.insert_one(form)):
            return jsonify(message="Success", data=data, form=form), 200
        return jsonify(message="failed"), 400


############################################
# routes related to request Form
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
    if(verifyCodeClient == form.get("verifyCode")):
        print("Correct")
        return jsonify(message="Verify Success", formID=formID), 200

    return jsonify(message="Verify Code Not Correct", verify=False), 404

# Search For Form created By user
# get an id from the link and search for that document in the database to send back the custom form


@app.route('/respond-form/', methods=['POST', 'GET'])
def respond_form():

    formID = request.args.get("formID")
    form = db.forms.find_one({"_id": formID})
    publicKey = form["public_key"]

    return render_template("respond_form.html", formID=formID, form=form, pubKey=publicKey, userEmail=User().get_current().get("email"))


#############################################
class AesCrypto(object):
    def __init__(self, key):
        self.key = key.encode('utf-8')[:16]
        self.iv = self.key
        self.mode = AES.MODE_CBC

    @staticmethod
    def pkcs7_padding(data):
        if not isinstance(data, bytes):
            data = data.encode()
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data) + padder.finalize()
        return padded_data

    def encrypt(self, plaintext):
        cryptor = AES.new(self.key, self.mode, self.iv)
        plaintext = plaintext
        plaintext = self.pkcs7_padding(plaintext)
        ciphertext = cryptor.encrypt(plaintext)
        return b2a_hex(ciphertext).decode('utf-8')

    def decrypt(self, ciphertext):
        cryptor = AES.new(self.key, self.mode, self.iv)
        plaintext = cryptor.decrypt(a2b_hex(ciphertext))
        return bytes.decode(plaintext).rstrip('\0')

def Convert(a):
    it = iter(a)
    res_dct = dict(zip(it, it))
    return res_dct
############################################
# Respondant Form
class ResForm:

    def resForm(self):
        print("Before Data")

        data = json.loads(request.data)
        print(data, "data that got from client")
        # encrypt data and send off to server
        # finding the id of the form to get the private key from the database
        formID = request.args.get("formID")
        form = db.forms.find_one({"_id": formID})
        cipherText = data.get("cipherTextAES")

        ###################################
        #RSA Encryption Process
        #open the RSA private key file
        f = open("RSA_private_key\%s.pem" %formID, 'rb')
        key = RSA.importKey(f.read())
        cipher = PKCS1_OAEP.new(key, hashAlgo=SHA256)
        decrypted_message = cipher.decrypt(b64decode(data.get("RSA_Contain_AES_KEY")))
        print(str(decrypted_message.decode()), "DECRYPTED MESSAGE RSA STRING")
        AES_KEY = str(decrypted_message.decode()).strip('"')
        ##################################
        #AES Decryption using the key that was decrypted from RSA that was sent from the client side

        aes = AesCrypto(AES_KEY) #decrypt with AES key that was encrypted with RSA
        decryptedFormObject = aes.decrypt(cipherText)

        ##################################
        #converting a cipher string to a format where eval can accept
        #first the string, we need to replace " with '. 
        #then the cipher text has some string appended at the end after decryption
        #we have to strip that off at the end of the string
        replaceDecrypt=decryptedFormObject.replace("\"","\'").split("]", 1)
        completeString = replaceDecrypt[0]+"]"
        actualData = list(eval(completeString))
        ##################################
        





        # add the responded form to its own schema
        respondantForm = {
            "_id": uuid.uuid4().hex,
            "sendBy": data.get("sentFrom"),
            "formObj": actualData,
            "date": datetime.datetime.now()
        }
        print("Before Success")
        #add the respondArray to the data schema
        data["respondArray"]=actualData
        # add the responded form to the user schema
        if(db.respondantForms.insert_one(respondantForm)):
            data["formId"] = respondantForm.get("_id")
            db.user.update({"email": data.get("sentFrom")},
                           {'$push': {'respondForm': data, "listOfForm": respondantForm.get("_id")},
                            })
            print("Success")
            return jsonify(message="Success", respondantForm=respondantForm, data=data), 200
        return jsonify(data=data), 200



@app.route('/respond-user-form/', methods=['POST'])
def respond_user_form():
    # dMessage = ResForm().decrypt()
    # print(dMessage,"D message")
   
    # print(dMessage,"Decode message")

    # print(ord(dMessage[0]),"D message [0]")
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
        # create user then return them
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
        # otherwise return the user that was found by email in the database
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


# main route
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
# routes related to Google Drive API stuff

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

    user = User().get_current()
    drive = GoogleDrive(user)

    document_id = drive.create_document(data[0])

    formIDs = data[1]


    # Google drive doc builder #
    docTitle = data[0] + "\n"
    charCount = 1
    for formID in formIDs:
        form = db.respondantForms.find_one({"_id":formID})['formObj'][0]
        formHeader = form["inputLabel"][2:].replace("\n\n", "").replace(" ", "") + "\n\n"
        docText = docTitle + formHeader
        docText += form["inputValue"] + "\n"
        drive.append_document_text(document_id, docText)

        if len(docTitle) > 0: 
            # title style
            docStyles = {'bold': True, 'fontSize': {'magnitude': 17, 'unit': 'PT'} }
            docFields = 'bold, fontSize'
            drive.update_document_text_style(document_id, charCount, len(docTitle) + charCount, docStyles, docFields)
            charCount += len(docTitle)
            docTitle = ""

        # form heading style
        docStyles = {'bold': True, 'fontSize': {'magnitude': 14, 'unit': 'PT'} }
        docFields = 'bold, fontSize'
        drive.update_document_text_style(document_id, charCount, len(formHeader) + charCount, docStyles, docFields)
        charCount+= len(formHeader)

        # form body style
        docStyles = {'bold': False, 'fontSize': {'magnitude': 12, 'unit': 'PT'} }
        docFields = 'bold, fontSize'
        drive.update_document_text_style(document_id, charCount, len(docText), docStyles, docFields)
        charCount += len(docText)
        # set charCount to bottom of form data for next loop on next form



    payload = {"url": f"https://docs.google.com/document/d/{document_id}"}
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

