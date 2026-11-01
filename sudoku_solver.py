""" Solver for 4x4 Sudoku puzzles. """

from __future__ import annotations

DIGITS = "1234"
GRID_SIZE = 4
BOX_SIZE = 2


def _normalise_puzzle(puzzle: str) -> list[str]:
    # Validate and converts a puzzle string into a mutable board
    if not isinstance(puzzle, str):
        raise TypeError("Puzzle must be a string of 16 characters.")

    puzzle = puzzle.strip()

    if (len(puzzle)) != 16:
        raise ValueError("A 4x4 puzzle must containe excalty 16 characters")

    # Cheking that numbers ouside of 0-4 is not used
    if not set(puzzle) <= set("01234"):
        raise ValueError("Puzzle may only contain digits 0-4")

    #  Converting the puzzle string into a mutable list of characters
    board = list(puzzle)

    # Cheking if numbers can be placed in that posistion, and temporary removing digit from its position on the board.
    for pos, digit in enumerate(board):
        if digit != "0":
            board[pos] = "0" 
            valid = _can_place(board, pos, digit)
            board[pos] = digit
            if not valid:
                raise ValueError(f"Puzzle is invalid: digit {digit} cannot be placed at position {pos}") 
    return board


def _can_place(board: list[str], pos: int, digit: str) -> bool:
    # Cheking if it is valid to place a digit at a given position in the board
    row, col = divmod(pos, GRID_SIZE)

    for c in range(GRID_SIZE):
        if board[row * GRID_SIZE + c] == digit:
            return False

    for r in range(GRID_SIZE):
        if board[r * GRID_SIZE + col] == digit:
            return False

    box_row = (row // BOX_SIZE) * BOX_SIZE
    box_col = (col // BOX_SIZE) * BOX_SIZE

    for r in range(box_row, box_row + BOX_SIZE):
        for c in range(box_col, box_col + BOX_SIZE):
                if board[r * GRID_SIZE + c] == digit:
                    return False
    return True


def _search(board: list[str], solutions: list[str], limit: int) -> None:
    # Recursive backtracking search for solutions to the Sudoku puzzle
    if len(solutions) >= limit:
        return

    best_pos = None
    best_candidates = None

    for pos, value in enumerate(board):
        if value != "0":
            continue

        candidates = [d for d in DIGITS if _can_place(board, pos, d)]
        if not candidates:
            return
        
        if best_candidates is None or len(candidates) < len(best_candidates):
            best_pos, best_candidates = pos, candidates
            if len(best_candidates) == 1:
                break

    if best_pos is None:
        solutions.append("".join(board))
        return

    for digit in best_candidates:
        board[best_pos] = digit
        _search(board, solutions, limit)
        board[best_pos] = "0"
        if len(solutions) >= limit:
            return




#### MULIG AT DETTE IKKE ER NØDVENDIG
def count_solutions(puzzle: str, limit: int = 2) -> int:
    """Count the number of solutions for a given 4x4 Sudoku puzzle.
    Stop counting when the number of solutions reaches the specified limit.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")
    
    board = _normalise_puzzle(puzzle)
    solutions: list[str] = []

    _search(board, solutions, limit)
    return len(solutions)


def solve_sudoku(puzzle: str) -> str:
    """Solve a 4x4 Sudoku puzzle and return the solution as a string.
    Raises a ValueError if the puzzle has no solution or multiple solutions.
    """
    board = _normalise_puzzle(puzzle)
    solutions: list[str] = []

    _search(board, solutions, limit=2)

    return solutions[0] if solutions else None


def solve_unique(puzzle: str) -> str | None:
    """Cheking if the puzzle has a solution, only one, or many different solutions (> 2)"""
    board = _normalise_puzzle(puzzle)

    solutions: list[str] = []

    _search(board, solutions, limit=2)
    if not solutions:
        raise ValueError("Puzzle has no solutions.")

    if len(solutions) > 1:
        raise ValueError("Puzzle has multipe solutions.")

    return solutions[0]


def format_board(board: str) -> str:
    """Format a 16-character board as four readable rows."""
    if len(board) != 16:
        raise ValueError("Board must contain 16 characters.")
    rows = [" ".join(board[r * 4:(r + 1) * 4]) for r in range(4)]
    return "\n".join(rows)