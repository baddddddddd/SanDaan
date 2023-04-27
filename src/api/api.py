from flask import Flask, jsonify, request

import mysql.connector
import os
import osmnx as ox
import networkx as nx

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

        optimal_route = nx.shortest_path(graph, origin_node, destination_node, weight="time")

        return jsonify({
            "route": optimal_route
        })
    
    
@app.route('/programming_languages', methods=['GET', 'POST'])
def programming_languages_route():
   if request.method == 'GET':
       return "hey"
   elif request.method == "POST":
       return jsonify(request.get_json(force=True))
        