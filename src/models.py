import json
from flask import session
from flask_sqlalchemy import SQLAlchemy
from secrets import token_hex

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
        Creaes a secret auth token to store user session in client.
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
