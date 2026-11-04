"""
4x4 Sudoku + ABB IRB 140 starter.
The PC hosts a TCP server. The ABB controller/RAPID program connects as a client.
Start with SIMULATION=True; do not connect to a live robot until the RAPID side,
coordinates, tool, workobject and safety checks have been verified.
"""


import tkinter as tk
from tkinter import messagebox

from robot_connection import RobotConnection
from sudoku_app import SudokuApp


def main():
    root = tk.Tk()
    robot = RobotConnection()

    try:
        robot.start_server()
        SudokuApp(root, robot)
        root.mainloop()

    except Exception as exc:
        messagebox.showerror("Startup error", str(exc))
        raise

    finally:
        robot.close()

if __name__ == "main":
    main()

