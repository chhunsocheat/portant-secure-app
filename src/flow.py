import os

from flask import session
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token
from google_auth_oauthlib.flow import Flow

from models import db, User

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive",
]


def get_flow():
    """
    Create flow for authorising Google APIs.
    """

    flow = Flow.from_client_secrets_file("client_secret.json", scopes=SCOPES)
    flow.redirect_uri = "http://localhost:5000/oauth-callback"

    return flow


def login_user(code):
    flow = get_flow()

    flow.fetch_token(code=code)

    creds = flow.credentials
    idinfo = verify_oauth2_token(creds.id_token, requests.Request(), GOOGLE_CLIENT_ID)

    email = idinfo["email"]

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email)
        user.generate_auth_token()

    user.given_name = idinfo.get("given_name")
    user.family_name = idinfo.get("family_name")
    user.avatar_url = idinfo.get("picture")

    user.oauth_credentials = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "scopes": creds.scopes,
    }

    db.session.add(user)
    db.session.commit()

    return user
