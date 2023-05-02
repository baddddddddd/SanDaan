from flask import Flask, jsonify, request, session
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_bcrypt import bcrypt
import mysql.connector
import os
import osmnx as ox
import networkx as nx

app = Flask(__name__)
app.secret_key = os.urandom(24)
jwt = JWTManager(app)
bcrypt = bcrypt(app)

db = mysql.connector.connect(
    host=os.getenv("HOST"),
    user=os.getenv("USERNAME"),
    passwd=os.getenv("PASSWORD"), 
    database=os.getenv("DATABASE")  
)

cursor = db.cursor()

@app.route('/register', methods=['POST'])
def register():

    id = request.json['user_id']
    email = request.json.get['email']
    user = request.json.get['username']
    pswd = request.json.get['password']
    salt = bcrypt.gensalt()
    hashed_pswd = bcrypt.generate_password_hash((pswd + salt).encode('utf-8')).decode('utf-8')
    if id and email and user and hashed_pswd and salt and request.method == 'POST':
        query = ("INSERT INTO users(user_id, email, username, password, salt) VALUES(%s, ?, ?, ?)", (email, user, hashed_pswd, salt))
        data = (email, user, pswd, id)            
        db.execute(query, data)
        cursor.commit()
        response = jsonify('REGISTERED SUCCESSFULLY')
        response.status_code = 200
        return response
    else:
        return showMessage()
    
@app.route('/login', methods=['POST'])
def login():
    user = request.json.get('username')
    pswd = request.json.get('password')

    result = db.execute("SELECT salt FROM users WHERE username = ?", (user,))
    user = result.fetchone()

    if user:
        hashed_pswd = user['password']
        salt = user['salt']
        hashed_input_password = bcrypt.generate_password_hash((pswd + salt).encode('utf-8'))

        if bcrypt.check_password_hash(hashed_pswd, hashed_input_password):
            access_token = create_access_token(identity=user)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    else:
        return jsonify({'message': 'User not found'}), 404
    
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    user_id = jwt.get_jwt_identity()

    cursor = db.cursor()
    query = "SELECT user_id, username FROM users WHERE user_id = %s"
    data = (user_id,)
    cursor.execute(query, data)
    user = cursor.fetchone()

    return jsonify({'user': {'id': user[0], 'username': user[1]}}), 200

@app.errorhandler(404)
def showMessage(error=None):
    message = {
        'status': 404,
    }
    response = jsonify(message)
    response.status_code = 404
    return response


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
        
