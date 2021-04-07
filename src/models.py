from enum import unique
import json
from flask import session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exists
from secrets import token_hex

#import random for now to randomly create URLs
import random

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)

    given_name = db.Column(db.String, nullable=True)
    family_name = db.Column(db.String, nullable=True)
    avatar_url = db.Column(db.String, nullable=True)

    auth_token = db.Column(db.String, nullable=True)

    # Store OAuth credentials as a JSON string, use getter and setter to handle directly as JSON
    _oauth_credentials = db.Column(db.String, nullable=True)

    @property
    def oauth_credentials(self):
        return json.loads(self._oauth_credentials)

    @oauth_credentials.setter
    def oauth_credentials(self, creds):
        self._oauth_credentials = json.dumps(creds)

    def generate_auth_token(self):
        """
        Creates a secret auth token to store user session in client.
        """

        self.auth_token = token_hex(32)

    @classmethod
    def get_current(cls):
        """
        Returns current user, based on stored auth token
        """

        auth_token = session.get("auth_token")
        if not auth_token:
            return None

        return cls.query.filter_by(auth_token=auth_token).first()

class OneTimeURL(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    URL = db.Column(db.String, nullable=True)
    # IDToken = db.Column(db.String, unique=True, nullable=True)

    """
    Creates n URLS
    """
    def CreateURL(numberOfURLS):
        Chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        # for i in range(numberOfURLS):
        #     URL = ''.join(random.choice(Chars) for c in range(5))
        #     onetimeurl = OneTimeURL(URL=URL)
        #     db.session.add(onetimeurl)
        u = OneTimeURL(URL="abc")
        db.session.add(u)
        db.session.flush()

    def CheckURLExists(URL):
        exists = db.session.query(db.exists().where(OneTimeURL.URL == URL)).scalar()
        return exists

# class URLTokens():
