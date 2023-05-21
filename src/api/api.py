from flask import Flask, jsonify, request
from flask_bcrypt import bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from mysql.connector.errors import DatabaseError

import datetime
import json
import math
import mysql.connector
import pytz
import os

import osmnx as ox
import networkx as nx

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=30)
jwt = JWTManager(app)

db = mysql.connector.connect(
    host=os.getenv("HOST"),
    user=os.getenv("USERNAME"),
    passwd=os.getenv("PASSWORD"), 
    database=os.getenv("DATABASE"),
)

cursor = db.cursor()

# Set the timezone to Philippines
ph_timezone = pytz.timezone('Asia/Manila')


# Execute queries by force to handle cases where the database connection timed out
def execute_query(query, params = tuple(), force=True):
    if force:
        try:
            cursor.execute(query, params)
        except DatabaseError:
            execute_query(query, params, True)
    else:
        cursor.execute(query, params)


# Check for bad requests
def has_missing_data(required_data: list):
    for data in required_data:
        if data is None:
            return True
        
    return False


@app.route("/verify", methods=["GET"])
@jwt_required()
def verify_token():
    return jsonify(
        msg="Token is currently valid",
    ), 200
    

# Create a route to refresh an expired access token using a refresh token
@app.route("/refresh", methods=["GET"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify(
        access_token=access_token,
    ), 200


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
                "msg": "One of the required fields is missing",
            }), 400
        
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)

        query = "SELECT * FROM users WHERE username=%s OR email=%s"
        params = (username, email)
        execute_query(query, params)
        result = cursor.fetchone()

        if result is not None:
            return jsonify({
                "msg": "Username or email is already taken",
            }), 401

        query = "INSERT INTO users (username, email, password) VALUES(%s, %s, %s)"
        params = (username, email, hashed_pw)            
        execute_query(query, params)
        db.commit()

        return jsonify({
            "msg": "Successfully created account",
        }), 200
        

@app.route("/login", methods=["POST"])
def login():
    json = request.json
    username = json.get("username", None)
    password = json.get("password", None)

    # Return 400 Bad Request if one of these three is None
    if username is None or password is None:
        return jsonify({
            "msg": "One of the required fields is missing",
        }), 400

    query = "SELECT * FROM users WHERE username=%s OR email=%s"
    params = (username, username)
    execute_query(query, params)
    result = cursor.fetchone()

    # Check if user exists in the databse
    if result is None:
        return jsonify({
            "msg": "Username or email is incorrect",
        }), 401

    hashed_pw = result[3].encode("ascii")
    if bcrypt.checkpw(password.encode("utf-8"), hashed_pw):
        user_id = result[0]
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
        }), 200
    
    else:
        return jsonify({
            "msg": "Username or email is incorrect",
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
    data = request.json

    pins = data.get("pins", None)

    center = get_center(pins)
    farthest_dist = 0
    for coord in pins:
        dist = get_distance(center, coord)

        if dist > farthest_dist:
            farthest_dist = dist

    route_nodes = []

    try:
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

            route = [[graph.nodes[node]['y'], graph.nodes[node]['x']] for node in route_nodes]

            return jsonify(
                route=route,
            ), 200
    
    except:
        return jsonify(
            msg="There is no path that connect the pins, try being more precise with the pins.",
        ), 404
    

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
    data = request.json

    name = data.get("name", None)
    description = data.get("description", None)
    start_time = data.get("start_time", None)
    end_time = data.get("end_time", None)
    coords = data.get("coords", None)
    uploader_id = get_jwt_identity()

    region = data.get("region", None)
    region_id = fetch_id_or_insert("regions", "name", region)

    state = data.get("state", None)
    state_id = fetch_id_or_insert("states", "name", state)

    city_id = data.get("city_id", None)

    # Filter out bad requests by checking if one of the required data from the body is missing
    route_info = [name, description, start_time, end_time, coords, region, state, city_id]
    if has_missing_data(route_info):
        return jsonify(msg="Bad Request: Incomplete data"), 400

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

    return jsonify(
        msg="Uploaded route successfully.",
    ), 200


@app.route("/directions", methods=["POST"])
@jwt_required()
def get_directions():
    data = request.json

    origin = data.get("origin", None)
    destination = data.get("destination", None)
    route_area = data.get("route_area", None)

    # Filter out bad requests
    required_data = [origin, destination, route_area]
    if has_missing_data(required_data):
        return jsonify(msg="Bad Request: Incomplete data"), 400

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

    # Get the current time with the specified timezone
    current_time = datetime.datetime.now(ph_timezone).strftime('%H:%M:%S')
    condition += f" AND routes.start_time <= '{current_time}' AND routes.end_time >= '{current_time}'"

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
    route_network_coords = []
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

        for coord in route["coords"]:
            if coord not in route_network_coords:
                route_network_coords.append(coord)
    
    center = get_center([origin, destination])
    radius = (get_distance(origin, destination) * 1500) // 2

    graph = ox.graph_from_point(center, dist=radius, network_type="drive")

    origin_node = ox.distance.nearest_nodes(graph, origin[1], origin[0])
    destination_node = ox.distance.nearest_nodes(graph, destination[1], destination[0])
    
    path = nx.shortest_path(graph, origin_node, destination_node, weight="time")
    shortest_route = [[graph.nodes[node]['y'], graph.nodes[node]['x']] for node in path]

    start_walk = None
    for i, node in enumerate(shortest_route):
        if node in route_network_coords:
            start_walk = shortest_route[:i + 1]
            break

    end_walk = None
    for i, node in reversed(list(enumerate(shortest_route))):
        if node in route_network_coords:
            end_walk = shortest_route[i:]
            break

    if start_walk is None or end_walk is None:
        return jsonify(
            start_walk=[],
            end_walk=[],
            routes=[],
        ), 200 
    
    start = start_walk[-1]
    end = end_walk[0]

    routes = get_complete_routes(candidate_routes, start, end)

    if routes is None:
        routes = []

    return jsonify(
        start_walk=start_walk,
        end_walk=end_walk,
        routes=routes,
    ), 200


def get_complete_routes(candidate_routes, start, end):
    complete_routes = []

    start_routes = []
    end_routes = []
    for candidate_route in candidate_routes:
        for i, coord in enumerate(candidate_route["coords"]):
            if start == coord:
                route = candidate_route.copy()
                route["coords"] = route["coords"][i:]
                start_routes.append(route)

            if end == coord:
                route = candidate_route.copy()
                route["coords"] = route["coords"][:i + 1]
                end_routes.append(route)
    
    # Handle cases where one transport vehicle is already enough to get to destination
    for start_route in start_routes:
        for i, coord in enumerate(start_route["coords"]):
            if end == coord:
                route = start_route.copy()
                route["coords"] = route["coords"][:i + 1]
                complete_routes.append([route])
                break

    if len(complete_routes) > 0:
        return complete_routes

    # Handle cases where more than one transport vehicles is needed to get to destination
    start_network = [[route] for route in start_routes]
    end_network = [[route] for route in end_routes]
    full_network = [[route] for route in candidate_routes]

    for i in range(5):
        complete_routes = get_connected_routes(start_network, end_network)

        if len(complete_routes) > 0:
            return complete_routes
        
        if i % 2 == 0:
            start_network = get_connected_routes(start_network, full_network)
        else:
            end_network = get_connected_routes(full_network, end_network)

        if len(start_network) == 0 or len(end_network) == 0:
            return complete_routes
            
    
# Get a list of all connected routes from two group of routes
def get_connected_routes(group_a: list, group_b: list):
    results = []

    for route_a in group_a:
        for route_b in group_b:
            connected = False

            # Avoid creating looping routes
            for route_a_step in route_a:
                for route_b_step in route_b:
                    if route_a_step["id"] == route_b_step["id"]:
                        continue

            route_a_coords = route_a[-1]["coords"]
            route_b_coords = route_b[0]["coords"]

            for i, coord_a in enumerate(route_a_coords):
                for j, coord_b in enumerate(route_b_coords):
                    if coord_a == coord_b:
                        sliced_route_a = route_a[-1].copy()
                        sliced_route_b = route_b[0].copy()

                        sliced_route_a["coords"] = route_a_coords[:i + 1]
                        sliced_route_b["coords"] = route_b_coords[j:]

                        new_route = route_a.copy()

                        new_route[-1] = sliced_route_a
                        new_route.append(sliced_route_b)

                        results.append(new_route)
                        connected = True
                        break
                
                if connected:
                    break

    return results
        
            
if __name__ == "__main__":
    app.run()
    