from flask import Flask, request, jsonify, abort, current_app, g, make_response
import secrets
import psutil
import socket
import time
from functools import wraps
import hmac
import hashlib
from datetime import datetime, timedelta
import jwt

"""
Flask
psutil
PyJWT
"""


# should use env variables
HASH_SECRET = b"dev-secret-change-me"
JWT_SECRET = b"dev-secret-change-me"


def hash_key(api_key: str) -> str:
    """
    hash_key("secretapikey123")
    'a9be16b5989c1cffc7e91a81143c6053362340717cbfc98b3a07ffcbe931f396'

    hash_key('secretapikey1')
    'deda7fdcf493cae490ea6b7889bc032799d5c1459085cd59bcb6f38ff6f4045a'

    hash_key('abc123')
    '8e024929eb9be0f39c3fb4e0f58bb5f2e8c9ccf81d1723e4c78729d3d0b135f0'

    hash_key("password1")
    '6cbfeac955cd5296ec7394a3d845c0b2f53603fb6fd49629b2b6371bf39ab4f7'
    
    hash_key("password2")
    'a3a232a44f8017ae2d673ae57b5b132f5153d1f117e89008e2f6098f2880a2f2'
    """
    return hmac.new(HASH_SECRET, api_key.encode(), hashlib.sha256).hexdigest()


def keys_match(api_key: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_key(api_key), stored_hash)


app = Flask(__name__)

# -----------------------
# In-memory data store
# -----------------------
data = {
    "interfaces": {},
    "notes": {}
}

# In-memory user/key database
user_db = {
    "alice": {
        "api_key": ["deda7fdcf493cae490ea6b7889bc032799d5c1459085cd59bcb6f38ff6f4045a"],  # secretapikey1
        "role": "admin",
        "password" : "6cbfeac955cd5296ec7394a3d845c0b2f53603fb6fd49629b2b6371bf39ab4f7" # password1
    },
    "bob": {
        "api_key": ["8e024929eb9be0f39c3fb4e0f58bb5f2e8c9ccf81d1723e4c78729d3d0b135f0"],  # abc123
        "role": "user",
        "password" : "a3a232a44f8017ae2d673ae57b5b132f5153d1f117e89008e2f6098f2880a2f2" # password2
    }
}

def jwt_protected(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.cookies.get('jwt')
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        try:
            g.jwt_payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            abort(401, description="Token Expired")
        except jwt.InvalidTokenError:
            abort(401, description="Invalid Token")
        return func(*args, **kwargs)
    return wrapper

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({
        "error": e.description
    }), 401


def api_protected(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_app.logger.info("api_protected running")

        auth = request.headers.get("Authorization", "")
        username = request.headers.get("Username", "")

        if not username:
            abort(401, description="Missing Username header")

        if auth.startswith("Bearer "):
            key = auth.split(" ", 1)[1]
            info = user_db.get(username)
            
            for v in info.get('api_key', []):
                if keys_match(key, v):
                    return func(*args, **kwargs)

        abort(401, description="Invalid or missing API key or username")

    return wrapper


def load_data():
    data["interfaces"] = {}

    for iface, addrs in psutil.net_if_addrs().items():
        data["interfaces"][iface] = []

        for a in addrs:
            fam = "MAC"
            if a.family == socket.AF_INET:
                fam = "IPv4"
            elif a.family == socket.AF_INET6:
                fam = "IPv6"

            data["interfaces"][iface].append({
                "family": fam,
                "address": a.address
            })

load_data()

@app.route('/login', methods=['POST'])
def login():
    """
    curl -i -X POST http://localhost:8000/login \
    -H "Content-Type: application/json" \
    -d '{"username":"alice","password":"password1"}' \
    -c cookies.txt
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if user_db.get(username)["password"] == hash_key(password):
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(minutes=5)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
        resp = make_response({'message': 'Logged in'})
        resp.set_cookie('jwt', token, httponly=True, samesite='Lax')
        return resp
    abort(401, description='Invalid credentials')


@app.route("/chpasswd", methods=["POST"])
@jwt_protected
def chpasswd():
    """
    Updates a user password
    curl -i -X POST http://localhost:8000/chpasswd \
     -H "Content-Type: application/json" \
     -d '{"new_password":"newsecret123"}' \
     -b cookies.txt
    """
    data = request.get_json()
    new_password = hash_key(data.get('new_password'))
    current_user = g.jwt_payload.get("username")
    
    user_db[current_user]["password"] = new_password
    return jsonify({"message": "Password Updatted"})

@app.route("/api/newkey", methods=["POST"])
@jwt_protected
def api_new_key():
    """
    Updates a user password
    curl -i -X POST http://localhost:8000/api/newkey \
      -H "Content-Type: application/json" \
      -b cookies.txt
    """
    api_key  = secrets.token_urlsafe(32)
    api_hash = hash_key(api_key)
    current_user = g.jwt_payload.get("username")
    
    user_db[current_user]["api_key"].append(api_hash)
    return jsonify({"new_api_key": api_key})

@app.route("/<resource>", methods=["GET"])
@api_protected
def get_all(resource):
    """
    Get all entries for a resource.

    Example:
      curl -i \
        -H "Username: alice" \
        -H "Authorization: Bearer secretapikey1" \
        http://localhost:8000/interfaces
    """
    if resource not in data:
        return jsonify({"error": "not found"}), 404
    return jsonify(data[resource])


@app.route("/<resource>", methods=["POST"])
@api_protected
def create(resource):
    """
    Create a new entry in a resource (requires JSON body with 'id').

    Example:
      curl -i -X POST \
        -H "Content-Type: application/json" \
        -H "Username: alice" \
        -H "Authorization: Bearer secretapikey1" \
        -d '{"id":"test1","value":"hello"}' \
        http://localhost:8000/notes
    """
    body = request.json
    if not body or "id" not in body:
        return jsonify({"error": "id required"}), 400

    data.setdefault(resource, {})
    data[resource][body["id"]] = body
    return jsonify(body), 201


@app.route("/<resource>/<id>", methods=["PUT"])
@api_protected
def update(resource, id):
    """
    Update an existing entry by id.

    Example:
      curl -i -X PUT \
        -H "Content-Type: application/json" \
        -H "Username: alice" \
        -H "Authorization: Bearer secretapikey1" \
        -d '{"value":"updated"}' \
        http://localhost:8000/notes/test1
    """
    if resource not in data or id not in data[resource]:
        return jsonify({"error": "not found"}), 404

    data[resource][id].update(request.json)
    return jsonify(data[resource][id])


@app.route("/<resource>/<id>", methods=["DELETE"])
@api_protected
def delete(resource, id):
    """
    Delete an entry by id.

    Example:
      curl -i -X DELETE \
        -H "Username: alice" \
        -H "Authorization: Bearer secretapikey1" \
        http://localhost:8000/notes/test1
    """
    if resource not in data or id not in data[resource]:
        return jsonify({"error": "not found"}), 404

    del data[resource][id]
    return "", 204


@app.route("/search")
@api_protected
def search():
    """
    Search across all resources for a term.

    Example:
      curl -i \
        -H "Username: alice" \
        -H "Authorization: Bearer secretapikey1" \
        "http://localhost:8000/search?q=ipv4"
    """
    q = request.args.get("q", "").lower()
    results = []

    for res, items in data.items():
        for k, v in items.items():
            blob = str(k).lower() + str(v).lower()
            if q in blob:
                results.append({res: {k: v}})

    return jsonify(results)

if __name__ == "__main__": 
    context = ('cert.pem', 'key.pem')
    app.run(debug=True, host="0.0.0.0", port=8000)
