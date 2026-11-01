
from main import load_puzzles
import random


DIGITS = {"1", "2", "3", "4"}


def print_board(board):
    """Print a 16-character Sudoku as a 4x4 grid."""
    for r in range(4):
        row = board[r * 4:(r + 1) * 4]
        print(" ".join("." if n == "0" else n for n in row))


def validate_solution(solution):
    """Check rows, columns and 2x2 boxes in a 4x4 Sudoku."""

    if len(solution) != 16 or not set(solution) <= DIGITS:
        return False

    # Check all 4 rows
    for r in range(4):
        row = set(solution[r * 4:r * 4 + 4])
        if row != DIGITS:
            return False

    # Check all 4 columns
    for c in range(4):
        column = {solution[r * 4 + c] for r in range(4)}
        if column != DIGITS:
            return False

    # Check the four 2x2 boxes
    for box_r in (0, 2):
        for box_c in (0, 2):
            box = {
                solution[r * 4 + c]
                for r in range(box_r, box_r + 2)
                for c in range(box_c, box_c + 2)
            }
            if box != DIGITS:
                return False

    return True


def puzzle_matches_solution(puzzle, solution):
    """Check that every given clue agrees with the solution."""
    return all(
        given == "0" or given == solved
        for given, solved in zip(puzzle, solution)
    )


def main():
    puzzles = load_puzzles()

    print(f"Loaded {len(puzzles)} puzzles.\n")

    valid_solutions = 0
    matching_puzzles = 0
    unique_puzzles = 0
    invalid_examples = []

    # Validate every puzzle and its corresponding solution
    for index, (puzzle, solution) in enumerate(puzzles, start=1):
        solution_valid = validate_solution(solution)
        clues_match = puzzle_matches_solution(puzzle, solution)


        # Chekking that every puzzle has a unique solution
        solution_count = count_solutions(puzzle)

        if solution_count == 1:
            unique_puzzles += 1

        if solution_valid:
            valid_solutions += 1

        if clues_match:
            matching_puzzles += 1

        if not solution_valid or not clues_match or solution_count != 1:
            invalid_examples.append(
                (index, puzzle, solution, solution_valid, clues_match)
            )

    print(f"Valid Sudoku solutions: {valid_solutions}/{len(puzzles)}")
    print(f"Puzzles matching their solutions: "
          f"{matching_puzzles}/{len(puzzles)}")
    print(
    f"Puzzles with exactly one solution: "
    f"{unique_puzzles}/{len(puzzles)}")

    if invalid_examples:
        print("\nInvalid entries found:")
        for index, puzzle, solution, valid, matches in invalid_examples[:10]:
            print(
                f"Row {index}: solution_valid={valid}, "
                f"clues_match={matches}"
            )
    else:
        print("\nAll solutions are valid and all clues match!")

    # Display one random example
    puzzle, solution = random.choice(puzzles)

    print("\nExample puzzle:")
    print_board(puzzle)

    print("\nCorresponding solution:")
    print_board(solution)


def count_solutions(puzzle, limit=2):
    """
    Count valid solutions for a 4x4 Sudoku.
    Stop at 'limit', since we only need to distinguish
    zero, one, or multiple solutions.
    """
    board = list(puzzle)
    count = 0

    def is_valid(pos, digit):
        row = pos // 4
        col = pos % 4

        # Check row
        for c in range(4):
            if c != col and board[row * 4 + c] == digit:
                return False

        # Check column
        for r in range(4):
            if r != row and board[r * 4 + col] == digit:
                return False

        # Check 2x2 box
        box_row = (row // 2) * 2
        box_col = (col // 2) * 2

        for r in range(box_row, box_row + 2):
            for c in range(box_col, box_col + 2):
                p = r * 4 + c
                if p != pos and board[p] == digit:
                    return False

        return True

    def backtrack():
        nonlocal count

        if count >= limit:
            return

        try:
            pos = board.index("0")
        except ValueError:
            count += 1
            return

        for digit in "1234":
            if is_valid(pos, digit):
                board[pos] = digit
                backtrack()
                board[pos] = "0"

                if count >= limit:
                    return

    backtrack()
    return count


if __name__ == "__main__":
    
    main()
