"""
Author: Sreekanth Balu
Email: balusreekanth@gmail.com
Date: 2024-12-21
Description:

This script implements a client for monitoring server log notifications. It includes:
- A secure connection to the server using SSL.
- Real-time notifications displayed via the system tray and `win11toast`.
- Text-to-speech (TTS) alerts for specified keywords using `pyttsx3`.
- A system tray icon that updates based on the server connection status.

The client continuously listens to the server and provides both visual and audio alerts when specified keywords are detected in the server logs. The script also handles reconnection in case of errors or timeouts.
"""
import os
import socket
import ssl
import sys
import pyttsx3
import time
import logging
from win11toast import toast
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
KEYWORD = "LoggedIn"
SPEAK_ALERT = "New User logged in"
CERT_FILE = "server.crt"  # Use the same certificate that you are using on the server
SERVER_IP = "0.0.0.0"  # Change this to your server's IP address
SERVER_PORT = 7777      # Change this to your desired port

# Globals for system tray
server_connected = False
icon = None

# Initialize Text-to-Speech
tts_engine = pyttsx3.init()

def speak_text(text):
    """Speak the given text using TTS."""
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        logging.error(f"Error with text-to-speech: {e}")

def show_notification(title, message):
    """Show a notification using Win11Toast."""
    try:
        toast(title, message, duration=50)
    except Exception as e:
        logging.error(f"Notification error: {e}")

def create_image(color1, color2):
    """Create an image with the given colors for the system tray icon."""
    image = Image.new("RGB", (64, 64), color1)
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill=color2)
    return image

def update_icon():
    """Update the system tray icon based on connection status."""
    global icon, server_connected
    if icon:
        if server_connected:
            icon.icon = create_image("green", "white")
        else:
            icon.icon = create_image("red", "white")

def resource_path(relative_path):
    """Get the absolute path to a resource, considering PyInstaller packaging."""
    try:
        base_path = sys._MEIPASS  # PyInstaller extracts files here
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def start_client(server_ip, server_port):
    """Connect to the server and handle incoming messages."""
    global server_connected

    while True:
        client_socket = None
        try:
            cert_path = resource_path(CERT_FILE)
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.load_verify_locations(cert_path)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Establish connection
            raw_socket = socket.create_connection((server_ip, server_port))
            client_socket = ssl_context.wrap_socket(raw_socket, server_hostname=server_ip)

            logging.info("Connected to LogCast server.")
            server_connected = True
            update_icon()

            while True:
                client_socket.settimeout(60)  # Timeout for receiving data
                try:
                    data = client_socket.recv(1024)
                    if data:
                        decoded_message = data.decode("utf-8").strip()
                        logging.info(f"Received from server: {decoded_message}")
                        
                        if decoded_message == "keep-alive":
                            server_connected = True
                            update_icon()
                            continue
                        
                        show_notification("Login Alert", decoded_message)
                        
                        if KEYWORD in decoded_message:
                            speak_text(SPEAK_ALERT)
                    else:
                        logging.warning("No data received. Closing connection.")
                        break
                except socket.timeout:
                    logging.warning("Connection timeout. Closing connection.")
                    break
        except (ssl.SSLError, socket.timeout, ConnectionRefusedError, OSError) as e:
            logging.error(f"Connection error: {e}")
            server_connected = False
            update_icon()
            time.sleep(5)  # Retry delay
        finally:
            if client_socket:
                try:
                    client_socket.close()
                    logging.info("Socket closed.")
                except OSError as e:
                    logging.error(f"Error closing socket: {e}")

def run_system_tray():
    """Run the system tray in the main thread."""
    global icon
    icon = Icon("LogCast Client")
    icon.menu = Menu(MenuItem("Exit", lambda: icon.stop()))
    icon.icon = create_image("red", "white")
    icon.run()

if __name__ == "__main__":
    # Start the system tray icon in a separate thread
    tray_thread = Thread(target=run_system_tray)
    tray_thread.start()

    # Start the client connection
    start_client(SERVER_IP, SERVER_PORT)
