"""
Author: Sreekanth Balu
Email: balusreekanth@gmail.com
Date: 2024-12-21
Description: 

This script sets up a secure server that monitors a log file for specific keywords and broadcasts messages to connected clients when the keyword is found. 
It includes:
- Configurable server settings such as IP, port, log file paths, and SSL certificates.
- Real-time log file monitoring using file inodes to detect changes and updates.
- A keep-alive mechanism to maintain active client connections.
- Integration with `win11toast` and `pyttsx` for client-side notifications (if used with a compatible client).

The server is designed to handle multiple clients simultaneously, using SSL for secure communication and threading for efficiency.
"""
import socket
import threading
import time
import ssl
import logging
import os

# Configurable parameters
CONFIG = {
    "server_ip": os.getenv("SERVER_IP", "0.0.0.0"),
    "server_port": int(os.getenv("SERVER_PORT", 7777)),
    "log_file_path": os.getenv("LOG_FILE_PATH", "/opt/logmonitor/server.log"),
    "log_file_to_watch": os.getenv("LOG_FILE_TO_WATCH", "/opt/server/logs/web.log"),
    "log_keyword": os.getenv("LOG_KEYWORD", "LoggedIn"),
    "cert_file": os.getenv("CERT_FILE", "server.crt"),
    "key_file": os.getenv("KEY_FILE", "server.key"),
    "keep_alive_interval": int(os.getenv("KEEP_ALIVE_INTERVAL", 2)),
    "monitor_poll_interval": int(os.getenv("MONITOR_POLL_INTERVAL", 1)),
    
}

# Set up logging configuration
logging.basicConfig(
    filename=CONFIG["log_file_path"],
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("Server logging started.")
clients = set()
client_lock = threading.Lock()

def send_keep_alive():
    """Send keep-alive messages to all connected clients."""
    while True:
        with client_lock:
            for client_socket in list(clients):
                try:
                    client_socket.sendall("keep-alive".encode("utf-8"))
                except (socket.error, BrokenPipeError, ConnectionResetError) as e:
                    logging.warning(f"Error sending keep-alive to {client_socket.getpeername()}: {e}")
                    clients.remove(client_socket)
                    client_socket.close()
                except Exception as e:
                    logging.error(f"Unexpected error with client {client_socket.getpeername()}: {e}")
        time.sleep(CONFIG["keep_alive_interval"])

def watch_log_file_by_inode(file_path, keyword):
    """Monitor a log file for a specific keyword."""
    current_inode = None
    file_handle = None
    while True:
        try:
            if not os.path.exists(file_path):
                logging.warning(f"Log file '{file_path}' not found. Waiting...")
                time.sleep(CONFIG["monitor_poll_interval"])
                continue

            file_stat = os.stat(file_path)
            if current_inode != file_stat.st_ino:
                if file_handle:
                    logging.info(f"File '{file_path}' replaced. Reopening...")
                    file_handle.close()

                file_handle = open(file_path, "r")
                current_inode = file_stat.st_ino
                logging.info(f"Monitoring log file '{file_path}' with inode {current_inode}.")
                file_handle.seek(0, os.SEEK_END)

            line = file_handle.readline()
            if not line:
                time.sleep(CONFIG["monitor_poll_interval"])
                continue

            if keyword in line:
                logging.info(f"Keyword '{keyword}' found in log file: {line.strip()}")
                with client_lock:
                    for client_socket in list(clients):
                        try:
                            message = f"Keyword alert: {line.strip()}"
                            client_socket.sendall(message.encode("utf-8"))
                        except (socket.error, BrokenPipeError, ConnectionResetError) as e:
                            logging.warning(f"Error sending alert to {client_socket.getpeername()}: {e}")
                            clients.remove(client_socket)
                            client_socket.close()
                        except Exception as e:
                            logging.error(f"Unexpected error with client {client_socket.getpeername()}: {e}")

        except Exception as e:
            logging.error(f"Error watching log file '{file_path}': {e}")
            time.sleep(CONFIG["monitor_poll_interval"])

        finally:
            if file_handle and file_handle.closed:
                current_inode = None

def handle_client(client_socket):
    """Handles communication with a client."""
    try:
        peername = client_socket.getpeername()
        logging.info(f"Client connected: {peername}")
        while True:
            data = client_socket.recv(1024)
            if not data:
                logging.info(f"Client {peername} disconnected.")
                break
            logging.info(f"Received data from {peername}: {data}")
    except Exception as e:
        logging.error(f"Error with client {peername}: {e}")
    finally:
        with threading.Lock():
            if client_socket in clients:
                clients.remove(client_socket)
        client_socket.close()

def start_server():
    """Start the server and accept client connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((CONFIG["server_ip"], CONFIG["server_port"]))
    server_socket.listen(100)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CONFIG["cert_file"], keyfile=CONFIG["key_file"])

    logging.info(f"Server started on {CONFIG['server_ip']}:{CONFIG['server_port']} with SSL")

    threading.Thread(target=send_keep_alive, daemon=True).start()
    threading.Thread(target=watch_log_file_by_inode, args=(CONFIG["log_file_to_watch"], CONFIG["log_keyword"]), daemon=True).start()

    try:
        while True:
            client_socket, addr = server_socket.accept()
            logging.info(f"Connection from {addr}")
            try:
                secure_socket = context.wrap_socket(client_socket, server_side=True)
                logging.info(f"Secure connection established with {addr}")
                with client_lock:
                    clients.add(secure_socket)
                threading.Thread(target=handle_client, args=(secure_socket,), daemon=True).start()
            except ssl.SSLError as e:
                logging.error(f"SSL error with client {addr}: {e}")
                client_socket.close()
    except KeyboardInterrupt:
        logging.info("Shutting down server.")
    finally:
        with client_lock:
            for client in list(clients):
                client.close()
                clients.remove(client)
        server_socket.close()
        logging.info("Server socket closed.")

if __name__ == "__main__":
    start_server()
