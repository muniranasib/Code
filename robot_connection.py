
import socket
import threading

from config import HOST, PORT, MODE



class RobotConnection:
    
    def __init__(self):
        self.client = None
        self.lock = threading.Lock()
        self.server_thread = None
        self.server_socket = None
        self.connected_event = threading.Event()

    def start_server(self):
        if MODE == "print":
            print("Print mode: TCP server is not started")
            return

        if self.server_thread and self.server_thread.is_alive():
            return

        self.server_thread = threading.Thread( 
            target=self._server_loop,
            daemon=True
        )

        self.server_thread.start()

    def _server_loop(self):
        # Oppretter kominikasjon med roboten
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                self.server_socket = server
                server.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
                )
                server.bind((HOST, PORT))
                server.listen(1)

                print(f'TCP server listening on port {PORT}')

                while True:
                    client, address = server.accept()
                    client.settimeout(30)

                    # Binding the client made to the robot class's client 
                    with self.lock:
                        if self.client is not None:
                            client.close()
                            continue

                        self.client = client
                        self.connected_event.set()

                    print(f'Client connected: {address}')

        except OSError as exc:
            print(f'TCP server stopped: {exc}')

        finally:
            # Resetting
            self.connected_event.clear()
            with self.lock:
                self.client = None
            self.server_socket = None



    def send_line(self, line):
        if MODE == "print":
            print('[SIMULATED SEND]', line)
            return "SIMULATED"

        with self.lock:
            client = self.client

            if client is None:
                raise ConnectionError( "No client connected to the PC server." )

            try:
                client.sendall((line + "\n").encode("utf-8"))

                # Read one newline terminal reply
                data = bytearray()

                while not data.endswith(b"\n"):
                    chunk = client.recv(128)

                    if not chunk:
                        raise ConnectionError( " Client disconedted before replying" )

                    data.extend(chunk)

                return data.decode("utf-8").strip()  

            except (OSError, socket.timeout) as exc:
                self.client = None
                self.connected_event.clear()
                client.close()

                raise ConnectionError(f'TCP communicatoin falied: {exc}') from exc



    def close(self):
        with self.lock:
            if self.client:
                self.client.close()
                self.client = None

            self.connected_event.clear()

        # If it is connected, then close it 
        if self.server_socket:
            self.server_socket.close()