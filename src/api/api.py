from flask import Flask, jsonify, request

import json
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

        path = nx.shortest_path(graph, origin_node, destination_node, weight="time")

        # Convert all the nodes in the computed path to coordinates
        route = [[graph.nodes[node]['y'], graph.nodes[node]['x']] for node in path]

        return jsonify({
            "route": route
        })
        

@app.route("/route", methods=["POST"])
def get_route():
    if request.method == "POST":
        data = request.get_json()

        pins = data.get("pins", None)

        route_nodes = []
        for coord in pins:
            graph = ox.graph_from_point(tuple(pins[0]), dist=2000, network_type="drive")

            nearest_node = ox.distance.nearest_nodes(graph, coord[1], coord[0])

            if len(route_nodes) > 0:
                if route_nodes[-1] == nearest_node:
                    continue
            else:
                route_nodes.append(nearest_node)
                continue

            path = nx.shortest_path(graph, route_nodes[-1], nearest_node, weight="distance")

            route_nodes += path[1:]

        # get nearest node
        # check if nearest node is last node
        # if not, pathfind from last node to chosen node
        # graph pathfinded route
        # add pathfinded route to route_nodes

        route = [[graph.nodes[node]['y'], graph.nodes[node]['x']] for node in route_nodes]

        with open("res.txt", "a") as f:
            f.write(str(route))

        return jsonify({
            "route": route
        })
    

@app.route("/add_route", methods=["POST"])
def add_route():
    if request.method == "POST":
        data = request.get_json()

        print(data)

        name = data.get("name", None)
        description = data.get("description", None)
        coords = data.get("coords", None)

        params = (name, description, json.dumps(coords))
        query = "INSERT INTO routes (name, description, coords) VALUES (%s, %s, %s)"
        cursor.execute(query,params)
        db.commit()

        return jsonify({
            "success": True
        })
    
# Storing routes in a database
# Routes contain a list of coordinates (lat, lon)
# Routes must have places specified (ie, Batangas City, Alangilan, Laguna)
# Routes must have names and descriptions
# Store routes to databasee in JSON string format

# Finding a commute route in a database
# Get shortest path between starting location and target location
# Convert path to list of Coordinates
# Get all routes that are in the same location or vicinity of target and starting location
# Find intersection between the shortest path and the filtered routes from the previous steps