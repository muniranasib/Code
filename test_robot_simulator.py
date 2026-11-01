
# robot_simulator.py

import socket
import time

from config import PORT

# Use the PC's loopback address when both programs run on the same PC.
SERVER_IP = "127.0.0.1"



def run_simulator():
    try:
        with socket.create_connection(
            (SERVER_IP, PORT), timeout=5
        ) as client:
            print("Simulator connected to PC server. Waiting for commands...")

            client.settimeout(None)

            with client.makefile(
                "r", encoding="utf-8", newline="\n"
            ) as reader:
                while True:
                    line = reader.readline()

                    if not line:
                        print("Server disconnected. Simulator stopped.")
                        break

                    command = line.strip()
                    print("[ROBOT SIMULATOR RECEIVED]", command)

                    parts = command.split()

                    if (
                        len(parts) == 4
                        and parts[0] == "WRITE"
                        and parts[1].isdigit()
                        and parts[2].isdigit()
                        and parts[3] in ("1", "2", "3", "4")
                        and 1 <= int(parts[1]) <= 4
                        and 1 <= int(parts[2]) <= 4
                    ):
                        row = int(parts[1])
                        col = int(parts[2])
                        digit = parts[3]

                        print(
                            f"Would write {digit} at row {row}, column {col}"
                        )
                        client.sendall(b"OK\n")
                    else:
                        print("Invalid command:", command)
                        client.sendall(b"ERROR\n")

    except OSError as exc:
        print(f"Simulator could not connect: {exc}")


if __name__ == "__main__":
    run_simulator()
