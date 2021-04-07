from flask import Flask,render_template
from app import app
from mongomodel import Form


#form from client-side
@app.route('/rec-user-form',methods=['POST','GET'])
def rec_user_form1():
    return Form().createForm()




