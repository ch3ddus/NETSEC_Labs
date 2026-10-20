import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# Variabili globali per simulare il database
notes_store = {}
next_note_id = 1

class RESTHandler(BaseHTTPRequestHandler):
    
    def send_json_response(self, status_code, payload=None):
        """Invia una risposta HTTP completa con intestazione JSON."""
        self.send_response(status_code)
        if payload is not None:
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        else:
            self.end_headers()

    def send_empty_response(self, status_code):
        """Invia una risposta HTTP senza corpo (es. 204, 404)."""
        self.send_response(status_code)
        self.end_headers()

    def dispatch(self):
        """Router centrale: analizza URL e Metodo HTTP per decidere cosa fare."""
        parsed = urlparse(self.path)
        path = parsed.path
        method = self.command

        # 1. Routing base
        if path == '/':
            if method == 'GET':
                return self.send_empty_response(200)
            return self.send_empty_response(405)

        # 2. JSON echo
        if path == '/echo':
            if method == 'GET':
                # Estrae il parametro 'msg' decodificato (es. "%20" diventa spazio)
                query = parse_qs(parsed.query)
                msg = query.get('msg', [''])[0]
                return self.send_json_response(200, {"msg": msg})
            return self.send_empty_response(405)

        # 3. POST /notes
        if path == '/notes':
            if method == 'POST':
                return self.handle_post_notes()
            return self.send_empty_response(405)

        # 4. GET o DELETE su /notes/<id>
        match = re.match(r'^/notes/([^/]+)$', path)
        if match:
            id_str = match.group(1)
            # Se l'id non è numerico, la regola dice di restituire 404
            if not id_str.isdigit():
                return self.send_empty_response(404)
            
            note_id = int(id_str)
            if method == 'GET':
                return self.handle_get_note(note_id)
            elif method == 'DELETE':
                return self.handle_delete_note(note_id)
            else:
                return self.send_empty_response(405) # Es. PUT su /notes/1

        # 5. Any other path -> 404
        self.send_empty_response(404)

    # --- Gestori delle risorse specifiche ---

    def handle_post_notes(self):
        global next_note_id
        
        # Controllo Content-Type
        content_type = self.headers.get('Content-Type', '')
        # Divide per gestire casi come 'application/json; charset=utf-8'
        if content_type.split(';')[0].strip() != 'application/json':
            return self.send_empty_response(415)
        
        # Lettura del body JSON
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            return self.send_empty_response(400) # Malformed JSON
            
        # Validazione campo text
        if 'text' not in data or not isinstance(data['text'], str):
            return self.send_empty_response(400) # Missing o non-string
            
        # Salvataggio nota
        note_id = next_note_id
        notes_store[note_id] = data['text']
        next_note_id += 1
        
        self.send_json_response(201, {"id": note_id})

    def handle_get_note(self, note_id):
        if note_id in notes_store:
            self.send_json_response(200, {"id": note_id, "text": notes_store[note_id]})
        else:
            self.send_empty_response(404) # Missing note

    def handle_delete_note(self, note_id):
        if note_id in notes_store:
            del notes_store[note_id]
            self.send_empty_response(204)
        else:
            self.send_empty_response(404) # Missing note

    # Mappiamo tutti i metodi standard HTTP alla nostra funzione 'dispatch'
    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = dispatch

def run(port=8080):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, RESTHandler)
    print(f"Server HTTP avviato sulla porta {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArresto del server...")
    finally:
        httpd.server_close()

if __name__ == '__main__':
    run()