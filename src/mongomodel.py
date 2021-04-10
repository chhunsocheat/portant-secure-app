from flask import Flask, jsonify, request, session, redirect
from app import db
import uuid
import json


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