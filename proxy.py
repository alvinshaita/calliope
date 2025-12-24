from flask import Flask, request, Response
import requests

AIOHTTP_PORT = 8050
AIOHTTP_HOST = '127.0.0.1'

app = Flask(__name__)

def proxy(path):
    url = f"http://{AIOHTTP_HOST}:{AIOHTTP_PORT}/{path}"
    method = request.method
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}

    # handle GET and POST
    if method == 'GET':
        resp = requests.get(url, headers=headers, params=request.args, stream=True)
    elif method == 'POST':
        resp = requests.post(url, headers=headers, data=request.get_data(), stream=True)
    else:
        resp = requests.request(method, url, headers=headers, data=request.get_data(), stream=True)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
    
    return Response(resp.content, resp.status_code, headers)

# Catch-all route to proxy all requests
@app.route('/', defaults={'path': ''}, methods=['GET','POST','PUT','DELETE'])
@app.route('/<path:path>', methods=['GET','POST','PUT','DELETE'])
def catch_all(path):
    return proxy(path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
