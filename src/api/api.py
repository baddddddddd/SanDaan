from flask import Flask, jsonify, request, session

import mysql.connector
import os
import osmnx as ox
import networkx as nx

app = Flask(__name__)

app.secret_key = os.urandom(24)

db = mysql.connector.connect(
    host=os.getenv("HOST"),
    user=os.getenv("USERNAME"),
    passwd=os.getenv("PASSWORD"), 
    database=os.getenv("DATABASE")  
)

cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register():
    json = request.json
    email = json['email']
    user = json['username']
    pswd = json['password']
    if email and user and pswd and request.method == 'POST':
        query = "INSERT INTO login(email, username, password) VALUES(%s, %s, %s)"
        data = (email, user, pswd)            
        db.execute(query, data)
        cursor.commit()
        response = jsonify('REGISTERED SUCCESSFULLY')
        response.status_code = 200
        return response
    else:
        return showMessage()
    
@app.route('/login', methods=['GET'])
def login():
    if 'loggedin' in session:
        return jsonify('User is already logged in')
    
    email = request.form['email']
    password = request.form['password']

    if email and password:
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['id'] = user[0]
            session['email'] = user[1]
            session['username'] = user[2]
            return jsonify('Logged in successfully')
        else:
         return jsonify('Invalid email or password')
    else:
        return jsonify('Email and password are required')
@app.route('/update', methods=['PUT'])
def update_login():
    try:
        json = request.json
        id = json['user_id']
        email = json['email']
        user = json['username']
        pswd = json['password']
        if email and user and pswd and request.method == 'POST':
            query = "UPDATE users SET email=%s, username=%s, password=%s WHERE user_id=%s"
            data = (id, email, user, pswd)
            db.execute(data, query)
            cursor.commit()
            response = jsonify('UPDATED SUCCESSFULLY')
            response.status_code = 200
            return response
        else:
            return showMessage()
    except Exception as e:
        print(e)
@app.errorhandler(404)
def showMessage(error=None):
    message = {
        'status': 404,
    }
    response = jsonify(message)
    response.status_code = 404
    return response

@app.route('/logout')
def logout():
    session.pop('email', None)
    return "Logged out successfully"

@app.route('/protected')
def protected():
    if 'email' in session:
        return "This is a protected route"
    else:
        return "You are not logged in"

@app.route("/account", methods=["GET"])
def manage_account():
    if request.method == "GET":
        cursor.execute("SELECT * FROM users WHERE username=\"eluxe\"")
        user = cursor.fetchone()
        print(user)
        return "done"

    elif request.method == "POST":
        pass

        

@app.route("/directions", methods=["POST"])
def get_directions():
    if request.method == "POST":
        data = request.get_json()

        origin = data.get("origin", None)
        destination = data.get("destination", None)
        mode = data.get("mode", None)

        graph = ox.graph_from_point(tuple(origin), dist=5000, network_type=mode)

        origin_node = ox.distance.nearest_nodes(graph, origin[1], origin[0])
        destination_node = ox.distance.nearest_nodes(graph, destination[1], destination[0])

        path = nx.shortest_path(graph, origin_node, destination_node, weight="time")

        # Convert all the nodes in the computed path to coordinates
        route = [[graph.nodes[node]['y'], graph.nodes[node]['x']] for node in path]

        return jsonify({
            "route": route
        })
        
