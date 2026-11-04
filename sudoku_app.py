import tkinter as tk
from tkinter import messagebox
import random

from config import MODE

from sudoku_data import load_puzzles
from sudoku_solver import is_valid_board, is_valid_solution, solve_sudoku 



class SudokuApp:
    def __init__(self, root, robot):
        self.root = root
        self.robot = robot

        root.title("ABB IRB 140 — 4x4 Sudoku")


        self.puzzles = load_puzzles()
        self.puzzle = ""
        self.solution = ""
        self.cells = []

        # Dictionary, to keep a record of what has been sendt
        self.sent_values = {}
        self.initial_clues_sent = False

        self.status = tk.StringVar(value=f'MODE: {MODE}')

        tk.Label(
            root, 
            text="4x4 Sudoku",
            font=("Classic", 18, "bold")
            ).pack(pady=8)


        grid = tk.Frame(root, bg="black")
        grid.pack(padx=12, pady=8)

        for r in range(4):
            row = []

            for c in range(4):
                entry = tk.Entry(
                    grid,
                    width=4,
                    justify="center",
                    font=("Classic", 18),
                    validate="key",
                    validatecommand=(root.register(self.valid_digit), "%P"), relief="flat", bd=0
                ) 

                # Extra black spacing after column 2 and row 2.
                right_gap = 7 if c == 1 else 2
                bottom_gap = 7 if r == 1 else 2

                entry.grid(
                    row=r,
                    column=c,
                    padx=(2, right_gap),
                    pady=(2, bottom_gap),
                    ipady=7
                )

                row.append(entry)

            self.cells.append(row)



        buttons = tk.Frame(root)
        buttons.pack(pady=8)

        # Buttons on the interface
        tk.Button(buttons, text="New puzzle", command=self.new_puzzle).grid(row=0, column=0, padx=4)
        tk.Button(buttons, text="Write to Robot", command=self.send_numbers_to_robot).grid(row=0, column=1, padx=4)
        tk.Button(buttons, text="Show Solution", command=self.show_solution).grid(row=0, column=2, padx=4)
        tk.Button(buttons, text="Check entries", command=self.check_entries).grid(row=0, column=3, padx=4)

        tk.Label(root, textvariable=self.status, wraplength=560).pack(pady=8)

        self.new_puzzle()

    @staticmethod
    def valid_digit(value):
        return value == "" or value in ("1", "2", "3", "4")

    

    def new_puzzle(self):
        self.puzzle, _ = random.choice(self.puzzles)
        self.solution = ""

        # A puzzle starts a new sending sequence.
        self.sent_values.clear()
        self.initial_clues_sent = False

        for r in range(4):
            for c in range(4):
                entry = self.cells[r][c]

                entry.config(state="normal")
                entry.delete(0, tk.END)

                digit = self.puzzle[r * 4 + c]

                if digit != "0":
                    entry.insert(0, digit)
                    entry.config(state="readonly", readonlybackground="#eeeeee")

        self.status.set("New puzzle loaded. First send the original clues.")


    def send_numbers_to_robot(self):
        sent = 0

        try:
            #First send: only teh original cles from the dataset.
            if not self.initial_clues_sent:
                targets = []

                for idx, digit in enumerate(self.puzzle):
                    if digit == "0":
                        continue

                    r, c = divmod(idx, 4)
                    targets.append((r, c, digit))

            # Later sends: only cells whoes vallues have changed
            else:
                targets = []

                for r in range(4):
                    for c in range(4):
                        digit = self.cells[r][c].get().strip()

                        if not digit:
                            continue

                        if self.sent_values.get((r, c)) != digit:
                            targets.append((r, c, digit))

            # Send the selected numbers to the robot
            for r, c, digit in targets:
                command = f"WRITE {r + 1} {c + 1} {digit}"
                reply = self.robot.send_line(command)

                if reply not in ("OK", "SIMULATED"):
                    raise RuntimeError( f'Unexpected response to {command}: {reply}')

                # Record only after a successful response
                self.sent_values[(r, c)] = digit
                sent += 1

            # Marking the initial clues as sent, and updating the status massage 
            if not self.initial_clues_sent:
                self.initial_clues_sent = True 
                self.status.set(
                        f'Sent {sent} original clues. '
                    'Enter new numbers and press the button again.')

            # Sending updated numbers 
            elif sent:
                self.status.set(
                    f"Sent {sent} new or changed cell(s)."
                )

             # Nothing to send
            else:
                self.status.set(
                    "No new numbers to send."
                    )
    
        except Exception as exc:
            messagebox.showerror("Robot communication", str(exc))
            self.status.set("Sending failed. Press the button to retry unsent changes.")




    def show_solution(self):
        try:
            self.solution = solve_sudoku(self.puzzle)
        except ValueError as exc:
            messagebox.showerror("Sudoku", str(exc))
            return 
        
        for r in range(4):
            for c in range(4):
                idx = r * 4 + c

                if self.puzzle[idx] == "0":
                    entry = self.cells[r][c]
                    entry.config(state="normal")
                    entry.delete(0, tk.END)
                    entry.insert(0, self.solution[idx])


        self.status.set("Solution displayed. Press the robot to send changes")



    def check_entries(self):
        current = ""

        for r in range(4):
            for c in range(4):
                current += self.cells[r][c].get().strip() or "0"

        if not is_valid_board(self.puzzle, current):
            messagebox.showinfo("Sudoku", "Invalid entries: some numbers are not valid.")

        elif is_valid_solution(self.puzzle, current):
            messagebox.showinfo("Sudoku", "Correct — valid Sudoku solution!")

        else:
            messagebox.showinfo("Sudoku", "So far correct, but the board is not complete")


if __name__ == "__main__":
    root = tk.Tk()

    # Standalone mode: no robot connection, just the GUI for testing and playing Sudoku.
    class NoRobot:
        def send_line(self, line):
            raise ConnectionError(
                "Start the application through main.py "
                "to use robot communication."
            )

    app = SudokuApp(root, NoRobot())
    root.mainloop()