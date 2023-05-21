from apscheduler.schedulers.background import BackgroundScheduler
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
import requests

import osmnx as ox
import networkx as nx

from dotenv import load_dotenv
load_dotenv()

# Set up Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=30)
jwt = JWTManager(app)

# Set up connection to database
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


# Helper function for checking bad requests
def has_missing_data(required_data: list):
    for data in required_data:
        if data is None:
            return True
        
    return False


# Endpoint for verifying tokens
@app.route("/verify", methods=["GET"])
@jwt_required()
def verify_token():
    return jsonify(
        msg="Token is currently valid",
    ), 200
    

# Endpoint to refresh an expired access token using a refresh token
@app.route("/refresh", methods=["GET"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify(
        access_token=access_token,
    ), 200


# Endpoint to register a new user
@app.route("/register", methods=["POST"])
def register():
    json = request.json
    
    email = json.get("email", None)
    username = json.get("username", None)
    password = json.get("password", None)

    # Return 400 Bad Request if one of these three is None
    if email is None or username is None or password is None:
        return jsonify(
            msg="One of the required fields is missing",
        ), 400
    
    # Query user accounts with the same username or email, if one is found, return 401 error
    query = "SELECT * FROM users WHERE username=%s OR email=%s"
    params = (username, email)
    execute_query(query, params)
    result = cursor.fetchone()

    if result is not None:
        return jsonify(
            msg="Username or email is already taken",
        ), 401
    
    # Generate a salt and a hash to encrypt passwords before storing to the database
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Insert newly created acccount to the database
    query = "INSERT INTO users (username, email, password) VALUES(%s, %s, %s)"
    params = (username, email, hashed_pw)            
    execute_query(query, params)
    db.commit()

    return jsonify(
        msg="Successfully created account",
    ), 200
        

# Endpoint to verify login credentials
@app.route("/login", methods=["POST"])
def login():
    json = request.json
    username = json.get("username", None)
    password = json.get("password", None)

    # Return 400 Bad Request if one of these two is None
    if username is None or password is None:
        return jsonify(
            msg="One of the required fields is missing",
        ), 400

    # Query the user information from the database using its username or email, and check if it exists
    query = "SELECT * FROM users WHERE username=%s OR email=%s"
    params = (username, username)
    execute_query(query, params)
    result = cursor.fetchone()

    if result is None:
        return jsonify(
            msg="Username or email is incorrect",
        ), 401

    # Hash the inputted password to check against the correct password
    hashed_pw = result[3].encode("ascii")

    if bcrypt.checkpw(password.encode("utf-8"), hashed_pw):
        user_id = result[0]

        # Create new access and refresh tokens to return to the client for authentication
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)

        return jsonify(
            access_token=access_token,
            refresh_token=refresh_token,
        ), 200
    
    else:
        return jsonify(
            msg="Username or email is incorrect",
        ), 401
        

# Compute the distance between two geological points
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


# Computes the center coordinate from a list of coordinates
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


# Endpoint for finding the shortest path that sequentially passes through all a list of geological points
@app.route("/route", methods=["POST"])
@jwt_required()
def get_route():
    data = request.json

    # Get the geological coordinates of all the pins
    pins = data.get("pins", None)

    # Compute the distance of the farthest point from the center point
    center = get_center(pins)
    farthest_dist = 0
    for coord in pins:
        dist = get_distance(center, coord)

        if dist > farthest_dist:
            farthest_dist = dist

    # Store the path by getting the list of intersection or nodes it passes through
    route_nodes = []
    
    # Create a graph of network of streets 
    graph = ox.graph_from_point(center, dist=farthest_dist * 1300, network_type="drive")

    try:
        # Iterate each geological point from the list and get the shortest path to each other
        for coord in pins:
            # Find the nearest node or intersection from each geological point
            nearest_node = ox.distance.nearest_nodes(graph, coord[1], coord[0])

            # Check if the nearest node is the same as the previous node, if yes, disregard, otherwise append to the list of nodes
            if len(route_nodes) > 0:
                if route_nodes[-1] == nearest_node:
                    continue
            else:
                route_nodes.append(nearest_node)
                continue

            # Get the shortest path from the previous node to the current node
            path = nx.shortest_path(graph, route_nodes[-1], nearest_node, weight="distance")

            # Add the path to the list of route nodes
            route_nodes += path[1:]

        # Convert the nodes into geological coordinates
        route = [[graph.nodes[node]['y'], graph.nodes[node]['x']] for node in route_nodes]

        return jsonify(
            route=route,
        ), 200
    
    # Catch exceptions which stem from lack of map data and invalid pin placements
    except:
        return jsonify(
            msg="There is no path that connect the pins, try being more precise with the pins.",
        ), 404
    

# Helper function for obtaining the id of value from a column in the database
def fetch_id_or_insert(table, column, value):
    # Query the database for the given value in a specific columns from specific taable
    query = f"SELECT * FROM {table} WHERE {column}=%s"
    params = (value,)
    execute_query(query, params)
    result = cursor.fetchone()

    # Check if a row was found, if yes, return the id of that row, otherwise insert the new value to the table
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
    

# Endpoint for contributing transport route data to the database
@app.route("/contribute", methods=["POST"])
@jwt_required()
def add_route():
    data = request.json

    # Get all the data from the request body
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


# Endpoint for obtaining the different route combinations that connects the user's location to the destination
@app.route("/directions", methods=["POST"])
@jwt_required()
def get_directions():
    data = request.json

    # Get all the data from the request body
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

    # Get the smallest possible vicinity that contains both the user's locations and destination
    # to limit the number of routes to be queried from the database
    condition = ""
    for column, value in route_area_ids.items():
        if value is not None:
            condition = f" WHERE route_areas.{column}={value}"
            break

    # Get the current time with the specified timezone
    # Limit the query to currently available transport routes at a given time
    current_time = datetime.datetime.now(ph_timezone).strftime('%H:%M:%S')
    condition += f" AND routes.start_time <= '{current_time}' AND routes.end_time >= '{current_time}'"

    # Columns to be obtained from the join query
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

    # Select all the routes that fall within the vicinity of the user's location and destination
    # that is also available currently according to the transport vehicle schedules
    query = f"SELECT {columns} FROM route_areas INNER JOIN routes ON route_areas.route_id = routes.id" + condition
    execute_query(query)
    results = cursor.fetchall()

    # Store all the queried routes as "candidate routes," which are routes that have a good chance to be
    # used by the user to get to their destination
    candidate_routes = []

    # Store all the entire network of transport routes from the candidate routes to be used
    # for finding the nearest nodes where transport vehicles drive through
    route_network_coords = []
    for res in results:
        # Get all the information for each route
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

        # Iterate coordinates of each route and add unique coordinates to the network
        for coord in route["coords"]:
            if coord not in route_network_coords:
                route_network_coords.append(coord)
    
    # Create a graph that contains both the user's location and their destination
    center = get_center([origin, destination])
    radius = (get_distance(origin, destination) * 1500) // 2

    graph = ox.graph_from_point(center, dist=radius, network_type="drive")

    # Convert the user's location and their destination to graph nodes
    # to be used for finding the shortest path
    origin_node = ox.distance.nearest_nodes(graph, origin[1], origin[0])
    destination_node = ox.distance.nearest_nodes(graph, destination[1], destination[0])
    
    path = nx.shortest_path(graph, origin_node, destination_node, weight="time")
    shortest_route = [[graph.nodes[node]['y'], graph.nodes[node]['x']] for node in path]

    # Using the shortest path computed, get the route that the user must walk
    # in order to reach the nearest main road or intersection where transport vehicles drive through
    # from their current location as well as to reach their final locations
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

    # If no walking routes were found, the user's location and the destinationn is not connected
    # by any network of streets, therefore, return empty data to the client
    if start_walk is None or end_walk is None:
        return jsonify(
            start_walk=[],
            end_walk=[],
            routes=[],
        ), 200 
    
    # Get the location where the user will start walking and end walking
    start = start_walk[-1]
    end = end_walk[0]

    # Get the shortest route combinations from the list of candidate routes that connect
    # the user's current location to their destination
    routes = get_complete_routes(candidate_routes, start, end)

    # If none was found, return an empty list
    if routes is None:
        routes = []

    return jsonify(
        start_walk=start_walk,
        end_walk=end_walk,
        routes=routes,
    ), 200


# Helper function for obtaining all the route combinations that connect the user's location to the destination 
def get_complete_routes(candidate_routes, start, end):
    complete_routes = []

    # Get all the route combinations that pass through the starting node and ending node
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
        # Iterate each coordinates of routes that pass through the starting node
        # then check if one of them also happens to be the ending node
        for i, coord in enumerate(start_route["coords"]):
            if end == coord:
                route = start_route.copy()
                route["coords"] = route["coords"][:i + 1]
                complete_routes.append([route])
                break

    # Check if a complete route was found from the previous step
    if len(complete_routes) > 0:
        return complete_routes

    # Handle cases where more than one transport vehicles is needed to get to destination

    # Create network of route combinations that stem from the starting and ending node
    # Additionally, store all the candidate routes as one whole network
    start_network = [[route] for route in start_routes]
    end_network = [[route] for route in end_routes]
    full_network = [[route] for route in candidate_routes]

    # Limit the size of the networks to only 5 to avoid overloading the server ram and cpu
    for i in range(5):
        # Find complete route combinations from the current extension of networks from both ends
        complete_routes = get_connected_routes(start_network, end_network)

        # If at least one was found, return the result immediately
        if len(complete_routes) > 0:
            return complete_routes
        
        # Expand or extend each network of routes from both ends alternately for each iteration
        if i % 2 == 0:
            start_network = get_connected_routes(start_network, full_network)
        else:
            end_network = get_connected_routes(full_network, end_network)

        # If one of the route networks stops finding more routes to expand to from the network
        # of candidate routes, stop the algorithm and return empty results
        if len(start_network) == 0 or len(end_network) == 0:
            return complete_routes
            
    
# Helper function for obtaining all the connected routes from two sets of unique routes
def get_connected_routes(group_a: list, group_b: list):
    results = []

    # Pair each route from both network of routes
    for route_a in group_a:
        for route_b in group_b:
            connected = False

            # Avoid creating looping routes
            for route_a_step in route_a:
                for route_b_step in route_b:
                    if route_a_step["id"] == route_b_step["id"]:
                        continue

            # Only get the coordinates of the ending route of each network
            route_a_coords = route_a[-1]["coords"]
            route_b_coords = route_b[0]["coords"]

            # Find the earliest possible intersection between the two routes by finding
            # intersecting coordinates from both routes sequentially
            for i, coord_a in enumerate(route_a_coords):
                for j, coord_b in enumerate(route_b_coords):
                    if coord_a == coord_b:
                        # Copy the routes to avoid modification of original routes
                        sliced_route_a = route_a[-1].copy()
                        sliced_route_b = route_b[0].copy()

                        # Slice the route based on where they intersected
                        sliced_route_a["coords"] = route_a_coords[:i + 1]
                        sliced_route_b["coords"] = route_b_coords[j:]

                        # Copy the current leg of network to add the route to extend to
                        new_route = route_a.copy()
                        new_route[-1] = sliced_route_a
                        new_route.append(sliced_route_b)

                        results.append(new_route)
                        connected = True
                        break
                
                if connected:
                    break

    return results


# Endpoint for pinging the server periodically to keep it awake
@app.route("/ping", methods=["GET"])
def ping():
    return "I'm awake!"


# Function to ping the server
def send_ping():
    url = "https://sandaan-api.onrender.com/ping"
    print("Sending ping to server...")
    response = requests.get(url)
    print("Ping sent to server:", response.status_code)


# Function to ping and write to the database to prevent it from sleeping
def ping_database():
    query = "INSERT INTO ping () values ()"
    print("Sending ping to database...")
    execute_query(query)

    query = "SELECT LAST_INSERT_ID()"
    execute_query(query)
    count = cursor.fetchone()[0]
    print("Ping sent to database:", count)


# Periodically call the function that sends a ping to the server using a scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_ping, "interval", minutes=12)
scheduler.add_job(ping_database, "interval", days=5)
scheduler.start()
