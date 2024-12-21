# LogCast
A simple Python socket server and client application to monitor a log file on a remote linux server for specific keywords and send audio alerts to a Windows client. 

# How it works

server.py monitors file changes and, when it finds the specified keyword in a continuously writing file, it broadcasts a message to connected socket clients.
The Windows client uses win11toast for visual notifications and pyttsx for audio notifications.

![How it works](logcast.png)


## Features

### Server
- Monitors a specified log file in real-time for specific keywords.
- Uses the FreeSWITCH Event Socket Library to broadcast notifications to connected clients.
- Sends periodic `keep-alive` messages to maintain active client connections.
- Implements SSL/TLS for secure communication.
- Handles multiple concurrent client connections using threading.

### Client
- Connects securely to the server using SSL/TLS.
- Displays real-time notifications using `win11toast`.
- Plays audio alerts for specific keywords using `pyttsx3`.
- Includes a system tray icon that updates based on the server connection status.
- Automatically retries connection if the server is unavailable or the connection is lost.

---

## How It Works

1. **Server:**
   - The server monitors a log file for changes using its inode.
   - When a specific keyword is detected, the server broadcasts an alert to all connected clients.
   - The server periodically sends `keep-alive` messages to ensure clients remain connected.

2. **Client:**
   - The client connects to the server and listens for incoming notifications.
   - Notifications containing the specified keyword trigger both visual and audio alerts.
   - The system tray icon changes color to indicate the connection status (e.g., green for connected, red for disconnected).

---

## Setup

### Prerequisites
- Python 3.7 or higher installed on both server and client systems.
- `pip` for installing dependencies.

### Install Dependencies
Run the following command on both server and client systems:
```bash
pip install -r requirements.txt
```

### Security
	•	The system uses SSL/TLS for secure communication between the server and clients.
	•	Ensure the server.crt and server.key files are properly configured and available on both the server and client system

### Future Improvements
	•	Add support for multiple log files on the server.
	•	Enhance client-side notification customization.
	•	Introduce a web-based interface for monitoring logs.

# Need help ?

- Write your comments and issues in issues section of this repository . Or you can mail at balusreekanthATgmailDOTcom

# Would you like to improve this ?
- I Love to  see pull requests to improve this script further . 
