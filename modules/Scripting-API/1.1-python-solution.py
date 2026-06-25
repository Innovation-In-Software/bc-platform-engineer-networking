from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import psutil
import subprocess
import platform

managed_routes = []

class NetworkRequestHandler(BaseHTTPRequestHandler):

    def  do_DELETE(self):
        """
        curl -X DELETE localhost:8000/routes/ -H "Content-Type: application/json" -d '{"route": "127.0.0.1" }'
        """

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        body_json = json.loads(body) # turn the raw body text into a dictionary

        match self.path:
            case p if p.startswith('/routes/'):
                if "route" in body_json:
                    for i in range(len(managed_routes)):
                        if managed_routes[i][0]== body_json["route"]:
                            response = {
                                "message":{
                                    "deleted_route": managed_routes[i]
                                }
                            }
                            del managed_routes[i]
                            self.send_response(200)
                    else: 
                        response = {"message":"Route not Found" }
                        self.send_response(400)
                else: 
                    response = {"message":"Route not Found" }
                    self.send_response(400)

                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            case _: # all other requests
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"message": "File Not Found"}).encode())
                return

    def do_PUT(self):

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        body_json = json.loads(body) # turn the raw body text into a dictionary

        match self.path:
            case p if p.startswith('/routes/'):
                if "route" in body_json:
                    for i in range(len(managed_routes)):
                        if body_json['route'][0] ==  managed_routes[i][0]:
                            response = {"message":{
                                "old_route": managed_routes[i]
                            }}
                            managed_routes[i][1] = body_json['route'][1]
                            response["new_route"] = managed_routes[i]
                            self.send_response(200)
                            break
                    else:
                        self.send_response(400)
                        response = {"message": "Route Not Found"}
                else:
                    self.send_response(400)
                    response = {"message": "Missing the route in requests body"}

                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
                return
            case _: # all other requests
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"message": "File Not Found"}).encode())
                return

    def do_POST(self):

        print("DOING POST....", flush=True)

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        body_json = json.loads(body) # turn the raw body text into a dictionary

        self.send_response(201)
        self.send_header('Content-Type', 'application/json')

        match self.path:
            case p if p.startswith("/route/"):
                if 'new_route' in body_json \
                    and isinstance(body_json['new_route'], list) \
                        and len(body_json['new_route']) == 2:
                    
                    managed_routes.append(body_json['new_route'])

                    response = {
                        "message": "New Route Added", 
                        "route" : body_json["new_route"],
                        "managed_routes": managed_routes
                    }
                else:
                    self.send_response(400)
                    response = {"message": "No Route Was Added"}

                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                return
            case _: # all other requests
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"message": "File Not Found"}).encode())
                return
    
    def do_GET(self):

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')

        match self.path:
            case p if p.startswith('/interfaces/'): 
                self.end_headers()
                self.wfile.write(json.dumps({"INTERFACES":list(psutil.net_if_stats().keys())}).encode())
                return
            
            case p if p.startswith('/macs/'):
                self.end_headers()
                response = { i:v[0].address  for i,v in psutil.net_if_addrs().items() }
                self.wfile.write(json.dumps(response).encode())
                return
            
            case p if p.startswith('/routes/'):
                self.end_headers()
                my_os = platform.system()
                routes = {"message":None}

                if "Windows" in my_os:
                    routes['message'] = subprocess.check_output(["route", "print"], text=True)
                else:
                    routes['message'] = subprocess.check_output(["ip", "route", "show"], text=True)

                # include any routes that were added via the API
                routes['managed_routes'] = managed_routes

                self.wfile.write(json.dumps(routes).encode())
                return
            case _: # all other requests
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({"message": "File Not Found"}).encode())
                return
        return
    
def run(server_class=HTTPServer, handler_class=NetworkRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    print('Starting server on port 8000...')
    httpd.serve_forever()

if __name__ == "__main__":
    run()