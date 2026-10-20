import json
import ssl
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from http import cookies

# Dizionario in memoria per gestire le sessioni (cookie_value -> username)
sessions = {}

class SecureHandler(BaseHTTPRequestHandler):
    
    def get_session_user(self):
        """Estrae l'utente dalla sessione verificando il cookie."""
        if 'Cookie' in self.headers:
            c = cookies.SimpleCookie(self.headers['Cookie'])
            if 'session' in c:
                session_id = c['session'].value
                return sessions.get(session_id)
        return None

    def do_GET(self):
        # 1. TLS server base
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            
        # 2. Login con cookie (Verifica)
        elif self.path == '/me':
            user = self.get_session_user()
            if user:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"user": user}).encode('utf-8'))
            else:
                self.send_response(401)
                self.end_headers()
                
        # 3. mTLS Client Authentication
        elif self.path == '/whoami':
            # Estrae il certificato del client (popolato solo su porta 8444)
            cert = self.request.getpeercert()
            if not cert:
                self.send_response(401)
                self.end_headers()
                return
                
            # Cerca il Common Name (CN) nel dizionario del certificato
            client_cn = None
            for sub in cert.get('subject', []):
                for key, value in sub:
                    if key == 'commonName':
                        client_cn = value
                        
            if client_cn:
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(client_cn.encode('utf-8'))
            else:
                self.send_response(401)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        # 2. Login
        if self.path == '/login':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                if data.get('password') == 'netsec':
                    user = data.get('user', 'unknown')
                    # Genera un ID di sessione sicuro e lo salva
                    session_id = str(uuid.uuid4())
                    sessions[session_id] = user
                    
                    # Prepara il cookie con attributi di sicurezza richiesti
                    cookie_str = f"session={session_id}; Secure; HttpOnly"
                    
                    self.send_response(200)
                    self.send_header('Set-Cookie', cookie_str)
                    self.end_headers()
                else:
                    self.send_response(401) # Wrong password
                    self.end_headers()
            except (ValueError, json.JSONDecodeError):
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def start_tls_server():
    """Avvia il server TLS normale sulla porta 8443"""
    httpd = HTTPServer(('0.0.0.0', 8443), SecureHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print("Server TLS in ascolto su porta 8443...")
    httpd.serve_forever()

def start_mtls_server():
    """Avvia il server mTLS (richiede cert. client) sulla porta 8444"""
    httpd = HTTPServer(('0.0.0.0', 8444), SecureHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    
    # REGOLE mTLS: Richiede certificato client e verifica tramite la CA del corso
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_verify_locations(cafile="ca.crt")
    
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print("Server mTLS in ascolto su porta 8444...")
    httpd.serve_forever()

if __name__ == '__main__':
    # Esegue i due server in parallelo usando i thread
    t1 = threading.Thread(target=start_tls_server, daemon=True)
    t2 = threading.Thread(target=start_mtls_server, daemon=True)
    t1.start()
    t2.start()
    
    try:
        # Mantiene in vita il thread principale
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        print("\nArresto dei server...")