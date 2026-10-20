import hashlib
from quart import Quart, request, Response

app = Quart(__name__)

@app.route('/', methods=['GET'])
async def index():
    http_version = request.scope.get('http_version', '1.1')
    headers = {}
    
    if http_version != '3':
        headers['Alt-Svc'] = 'h3=":4433"'
        
    return Response("OK\n", status=200, headers=headers)

@app.route('/proto', methods=['GET'])
async def proto():
    http_version = request.scope.get('http_version', '1.1')
    if http_version == '3':
        return "HTTP/3\n"
    elif http_version == '2':
        return "HTTP/2\n"
    else:
        return "HTTP/1.1\n"

@app.route('/hash', methods=['POST'])
async def hash_body():
    body = await request.get_data()
    hash_hex = hashlib.sha256(body).hexdigest()
    return f"{hash_hex}\n"