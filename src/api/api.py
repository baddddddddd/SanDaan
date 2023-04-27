from flask import Flask, request

import mysql.connector
import os

app = Flask(__name__)

db = mysql.connector.connect(
    host=os.getenv("HOST"),
    user=os.getenv("USERNAME"),
    passwd=os.getenv("PASSWORD"), 
    database=os.getenv("DATABASE")  
)

cursor = db.cursor()


@app.route("/account", methods=["GET"])
def manage_account():
    if request.method == "GET":
        cursor.execute("SELECT * FROM users WHERE username=\"eluxe\"")
        user = cursor.fetchone()
        print(user)
        return "done"

    elif request.method == "POST":
        pass

        
        