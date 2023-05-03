from flask import Flask, jsonify, request, session
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_bcrypt import bcrypt
import mysql.connector
import os
import osmnx as ox
import networkx as nx

app = Flask(__name__)
app.secret_key = os.urandom(24)
jwt = JWTManager(app)

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
    salt = bcrypt.gensalt()
    hashed_pswd = bcrypt.hashpw(pswd.encode('utf-8'), salt)
    if email and user and hashed_pswd and request.method == 'POST':
        query = "INSERT INTO app_users(email, username, password) VALUES( %s, %s, %s)"
        data = (email, user, hashed_pswd)            
        cursor.execute(query, data)
        db.commit()
        response = jsonify('REGISTERED SUCCESSFULLY')
        response.status_code = 200
        return response
    else:
        return showMessage()
    
@app.route('/login', methods=['POST'])
def login():
    user = request.json.get('username')
    pswd = request.json.get('password').encode("utf-8")

    cursor.execute("SELECT * FROM app_users WHERE username = %s", (user,))
    result = cursor.fetchone()

    if result is not None:
        hashed_pswd = result[3].encode("ascii")
        if bcrypt.checkpw(pswd, hashed_pswd):
            access_token = create_access_token(identity=result[0])
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    else:
        return jsonify({'message': 'User not found'}), 404
    
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user),200

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
        
