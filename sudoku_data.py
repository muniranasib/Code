from pathlib import Path

DATASET_PATH = (
    Path(__file__).resolve().parent
    / "4x4_sudoku_unique_solution.csv"
)




def load_puzzles():
    rows = []

    with open(DATASET_PATH, "r", encoding="utf-8-sig") as f:
        # Split each line on whitespace
        for line in f:
            parts = line.split()

            # Skipping the headers (Puzzle, Solution)
            if len(parts) < 2:
                continue

            puzzle = parts[0].strip()
            solution = parts[1].strip()

            if (len(puzzle) == 16 
                and len(solution) == 16 
                and set(puzzle) <= set("01234") 
                and set(solution) <= set("1234")): rows.append((puzzle, solution))

    if not rows:
        raise RuntimeError("No valid puzzles found. Check the downloaded CSV file.")
    return rows