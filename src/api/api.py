from flask import Flask, jsonify, request
from flask_bcrypt import bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from mysql.connector.errors import DatabaseError

import json
import mysql.connector
import os
import osmnx as ox
import networkx as nx
import math

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
jwt = JWTManager(app)

db = mysql.connector.connect(
    host=os.getenv("HOST"),
    user=os.getenv("USERNAME"),
    passwd=os.getenv("PASSWORD"), 
    database=os.getenv("DATABASE"),
)

cursor = db.cursor()


# Execute queries by force to handle cases where the database connection timed out
def execute_query(query, params = tuple(), force=True):
    if force:
        try:
            cursor.execute(query, params)
        except DatabaseError:
            execute_query(query, params, True)
    else:
        cursor.execute(query, params)


@app.route("/register", methods=["POST"])
def register():
    if request.method == "POST":
        json = request.json
        
        email = json.get("email", None)
        username = json.get("username", None)
        password = json.get("password", None)
    
        # Return 400 Bad Request if one of these three is None
        if email is None or username is None or password is None:
            return jsonify({
                "message": "One of the required fields is missing",
            }), 400
        
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)

        query = "SELECT * FROM users WHERE username=%s OR email=%s"
        params = (username, email)
        execute_query(query, params)
        result = cursor.fetchone()

        if result is not None:
            return jsonify({
                "message": "Username or email is already taken",
            }), 401

        query = "INSERT INTO users (username, email, password) VALUES(%s, %s, %s)"
        params = (username, email, hashed_pw)            
        execute_query(query, params)
        db.commit()

        return jsonify({
            "message": "Successfully created account",
        }), 200
        

@app.route("/login", methods=["POST"])
def login():
    json = request.json
    username = json.get("username", None)
    password = json.get("password", None)

    # Return 400 Bad Request if one of these three is None
    if username is None or password is None:
        return jsonify({
            "message": "One of the required fields is missing",
        }), 400

    query = "SELECT * FROM users WHERE username=%s OR email=%s"
    params = (username, username)
    execute_query(query, params)
    result = cursor.fetchone()

    # Check if user exists in the databse
    if result is None:
        return jsonify({
            "message": "Username or email is incorrect",
        }), 401

    hashed_pw = result[3].encode("ascii")
    if bcrypt.checkpw(password.encode("utf-8"), hashed_pw):
        access_token = create_access_token(identity=result[0])
        id = result[0]
        return jsonify({
            "access_token": access_token,
            "id": id,
        }), 200
    
    else:
        return jsonify({
            "message": "Username or email is incorrect",
        }), 401
        

# Computes the distance between two geological points
def get_distance(point_1, point_2):
     # Define the radius of the Earth in kilometers
    radius = 6371

    # Convert latitude and longitude from decimal degrees to radians
    lat1, lon1 = math.radians(point_1[0]), math.radians(point_1[1])
    lat2, lon2 = math.radians(point_2[0]), math.radians(point_2[1])

    # Compute the differences between the latitudes and longitudes
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Compute the Haversine distance
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = radius * c

    return distance


# Computes the center coordinate among a list of coordinates
def get_center(points: list):
    lat_sum = 0.0
    lon_sum = 0.0
    count = len(points)
    
    for point in points:
        lon_sum += point[0]
        lat_sum += point[1]

    center_lat = lat_sum / count
    center_lon = lon_sum / count
    return (center_lon, center_lat)


@app.route("/route", methods=["POST"])
@jwt_required()
def get_route():
    if request.method == "POST":
        data = request.json

        pins = data.get("pins", None)

        center = get_center(pins)
        farthest_dist = 0
        for coord in pins:
            dist = get_distance(center, coord)

            if dist > farthest_dist:
                farthest_dist = dist

        route_nodes = []
        for coord in pins:
            graph = ox.graph_from_point(center, dist=farthest_dist * 1100, network_type="drive")

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

        return jsonify({
            "route": route
        })
    

def fetch_id_or_insert(table, column, value):
    query = f"SELECT * FROM {table} WHERE {column}=%s"
    params = (value,)
    execute_query(query, params)
    result = cursor.fetchone()

    if result is not None:
        id = result[0]
        return id
    else:
        query = f"INSERT INTO {table} ({column}) VALUES (%s)"
        params = (value,)
        execute_query(query, params)
        db.commit()
        
        query = "SELECT LAST_INSERT_ID()"
        execute_query(query)
        id = cursor.fetchone()[0]
        return id
    

@app.route("/contribute", methods=["POST"])
@jwt_required()
def add_route():
    if request.method == "POST":
        data = request.json

        name = data.get("name", None)
        description = data.get("description", None)
        start_time = data.get("start_time", None)
        end_time = data.get("end_time", None)
        coords = data.get("coords", None)
        uploader_id = data.get("uploader_id", None)

        region = data.get("region", None)
        region_id = fetch_id_or_insert("regions", "name", region)

        state = data.get("state", None)
        state_id = fetch_id_or_insert("states", "name", state)

        city_id = data.get("city_id", None)

        # Insert route information into routes table
        query = "INSERT INTO routes (name, description, start_time, end_time, coords, uploader_id) VALUES (%s, %s, %s, %s, %s, %s)"
        params = (name, description, start_time, end_time, json.dumps(coords), uploader_id)
        execute_query(query, params)
        db.commit()

        # Get the resulting route id
        query = "SELECT LAST_INSERT_ID()"
        execute_query(query)
        route_id = cursor.fetchone()[0]

        # Insert route area into route_areas table
        query = "INSERT INTO route_areas (region_id, state_id, city_id, route_id) VALUES (%s, %s, %s, %s)"
        params = (region_id, state_id, city_id, route_id)
        execute_query(query, params)
        db.commit() 

        return jsonify({
            "message": "Uploaded route successfully."
        }), 200

@app.route("/directions", methods=["POST"])
@jwt_required()
def get_directions():
    if request.method == "POST":
        data = request.json

        origin = data.get("origin", None)
        destination = data.get("destination", None)
        route_area = data.get("route_area", None)

        region = route_area.get("region", None)
        region_id = fetch_id_or_insert("regions", "name", region) if region is not None else None
        
        state = route_area.get("state", None)
        state_id = fetch_id_or_insert("states", "name", state) if state is not None else None
        
        city_id = route_area.get("city_id", None)

        route_area_ids = {
            "city_id": city_id,
            "state_id": state_id,
            "region_id": region_id,
        }

        condition = ""
        for column, value in route_area_ids.items():
            if value is not None:
                condition = f" WHERE route_areas.{column}={value}"
                break

        columns = ", ".join([
            "routes.id",
            "routes.name",
            "routes.description",
            "routes.start_time",
            "routes.end_time",
            "routes.coords",
            "routes.connections",
            "routes.uploader_id",
        ])

        query = f"SELECT {columns} FROM route_areas INNER JOIN routes ON route_areas.route_id = routes.id" + condition
        execute_query(query)
        results = cursor.fetchall()

        candidate_routes = []
        for res in results:
            route = {
                "id": res[0],
                "name": res[1],
                "description": res[2],
                "start_time": str(res[3]),
                "end_time": str(res[4]),
                "coords": json.loads(res[5]),
                "connections": res[6],
                "uploader_id": res[7],
            }
            candidate_routes.append(route)
        
        center = get_center([origin, destination])
        radius = (get_distance(origin, destination) * 1100) // 2

        graph = ox.graph_from_point(center, dist=radius, network_type="drive")

        origin_node = ox.distance.nearest_nodes(graph, origin[1], origin[0])
        destination_node = ox.distance.nearest_nodes(graph, destination[1], destination[0])

        path = nx.shortest_path(graph, origin_node, destination_node, weight="time")

        shortest_route = [[graph.nodes[node]['y'], graph.nodes[node]['x']] for node in path]

        # Determine which routes will get the user from their current location to the target location

        viable_routes = []
        all_route = []
        for route in candidate_routes:
            all_route += route["coords"]


        first_stop = None
        for i, node in enumerate(shortest_route):
            if node in all_route:
                first_stop = node
                break

        last_stop = None
        for i, node in reversed(list(enumerate(shortest_route))):
            if node in all_route:
                last_stop = node
                break

        for idx, route in enumerate(candidate_routes):
            found_first_stop = False

            for i, node in enumerate(route["coords"]):
                if not found_first_stop and node == first_stop:
                    found_first_stop = True

                if node == last_stop:
                    if not found_first_stop:
                        break

                    viable_routes.append(candidate_routes[idx])
                    break

        return jsonify({
            "routes": viable_routes
        })

if __name__ == "__main__":
    app.run()
    