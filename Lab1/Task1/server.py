import socket
import threading

HOST = '0.0.0.0'
PORT = 9001

# Questo è il nostro Key-Value store condiviso tra tutte le connessioni
store = {}

def process_command(line):
    """
    Analizza la singola riga inviata dal client e restituisce la risposta formattata.
    """
    # Rimuoviamo il \n o \r\n finale, ma preserviamo gli spazi interni
    line = line.rstrip('\r\n')
    
    # Se la riga è vuota, è un errore
    if not line:
        return "ERR\n"
        
    # Dividiamo al massimo in due parti: il COMANDO e il RESTO della stringa
    parts = line.split(' ', 1)
    command = parts[0]
    
    # 1. PING
    if command == "PING":
        return "PONG\n"
        
    # 2. ECHO <text>
    elif command == "ECHO":
        if len(parts) > 1:
            return parts[1] + "\n"
        else:
            return "ERR\n" # ECHO senza testo
            
    # 3. SET <key> <value>
    elif command == "SET":
        if len(parts) > 1:
            # Dividiamo la parte restante in <key> e <value> (al massimo in due)
            subparts = parts[1].split(' ', 1)
            if len(subparts) == 2:
                key = subparts[0]
                value = subparts[1]
                store[key] = value
                return "OK\n"
        return "ERR\n" # SET senza valore o parametri mancanti
        
    # 4. GET <key>
    elif command == "GET":
        if len(parts) > 1:
            key = parts[1]
            # La chiave non deve contenere spazi
            if ' ' in key:
                return "ERR\n"
            # Restituisce il valore o NOT_FOUND
            return store.get(key, "NOT_FOUND") + "\n"
        return "ERR\n" # GET senza chiave
        
    # Comando sconosciuto
    return "ERR\n"

def handle_client(conn, addr):
    """
    Gestisce la connessione attiva con un singolo client.
    """
    print(f"[NUOVA CONNESSIONE] Client connesso da {addr}")
    
    # Usiamo makefile per gestire la lettura/scrittura ASCII riga per riga (\n)
    try:
        with conn.makefile('r', encoding='ascii') as infile, \
             conn.makefile('w', encoding='ascii') as outfile:
            
            # Legge riga per riga finché il client non chiude la connessione
            for line in infile:
                # 1. Elabora la riga
                response = process_command(line)
                
                # 2. Scrive la risposta e svuota il buffer (flush) per forzare l'invio
                outfile.write(response)
                outfile.flush()
                
    except Exception as e:
        print(f"[ERRORE] Connessione con {addr} interrotta: {e}")
    finally:
        conn.close()
        print(f"[DISCONNESSO] Client {addr} disconnesso")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[START] Server TCP in ascolto su {HOST}:{PORT}")

    try:
        while True:
            # Accetta una nuova connessione
            conn, addr = server.accept()
            
            # Crea un nuovo thread per gestire questo specifico client
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            # Daemon=True assicura che i thread si chiudano se chiudiamo il server
            thread.daemon = True 
            thread.start()
    except KeyboardInterrupt:
        print("\n[STOP] Spegnimento del server in corso...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()