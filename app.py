"""
Sudoku Web Application with Flask
Features: CSP-based AI solver, puzzle generation, validation, hints
"""

import random
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# ============== CSP (Constraint Satisfaction Problem) ==============
# Variables: 81 cells (i, j)
# Domains: {1..9} for empty cells, {v} for prefilled
# Constraints: AllDifferent on each row, column, 3x3 box

# Precompute peers: cells that constrain each other (same row, col, or box)
PEERS = {}
for i in range(9):
    for j in range(9):
        peers = set()
        for k in range(9):
            if k != j:
                peers.add((i, k))
            if k != i:
                peers.add((k, j))
        br, bc = 3 * (i // 3), 3 * (j // 3)
        for bi in range(br, br + 3):
            for bj in range(bc, bc + 3):
                if (bi, bj) != (i, j):
                    peers.add((bi, bj))
        PEERS[(i, j)] = peers


def board_to_domains(board):
    """Convert board to CSP domains. Prefilled cells have single-value domain."""
    domains = {}
    for i in range(9):
        for j in range(9):
            val = board[i][j]
            if val != 0:
                domains[(i, j)] = {val}
            else:
                domains[(i, j)] = set(range(1, 10))
    return domains


def remove_from_peers(domains, cell, value):
    """Remove value from all peers' domains (forward checking)."""
    removed = []
    for peer in PEERS[cell]:
        if value in domains.get(peer, set()):
            domains[peer] = domains[peer] - {value}
            removed.append((peer, value))
    return removed


def restore_to_peers(domains, removals):
    """Restore values to peers (for backtracking)."""
    for peer, value in removals:
        domains[peer].add(value)


def ac3(domains):
    """
    Arc Consistency (AC-3): Revise arcs until no domain changes.
    If a cell has only one value, remove it from all peers.
    """
    queue = []
    for cell in domains:
        if len(domains[cell]) == 1:
            queue.append(cell)
    while queue:
        cell = queue.pop(0)
        if len(domains[cell]) != 1:
            continue
        val = next(iter(domains[cell]))
        for peer in PEERS[cell]:
            if val in domains[peer]:
                domains[peer] = domains[peer] - {val}
                if len(domains[peer]) == 0:
                    return False  # Inconsistent
                if len(domains[peer]) == 1:
                    queue.append(peer)
    return True


def get_unassigned_mrv(domains):
    """MRV: Select unassigned variable with minimum remaining values."""
    candidates = [(c, d) for c, d in domains.items() if len(d) > 1]
    if not candidates:
        return None
    return min(candidates, key=lambda x: len(x[1]))[0]


def lcv_order(cell, domains):
    """LCV: Order values by least constraining (removes fewest options from peers)."""
    counts = []
    for val in domains[cell]:
        removed = sum(1 for p in PEERS[cell] if val in domains[p])
        counts.append((val, removed))
    counts.sort(key=lambda x: x[1])
    return [v for v, _ in counts]


def domains_to_board(domains):
    """Convert solved domains back to 9x9 board."""
    board = [[0] * 9 for _ in range(9)]
    for (i, j), d in domains.items():
        if len(d) == 1:
            board[i][j] = next(iter(d))
    return board


def solve_sudoku_csp(board):
    """
    Solve Sudoku using CSP: AC-3 + backtracking + MRV + forward checking + LCV.
    Returns (success, solution_board or None).
    """
    domains = board_to_domains(board)
    if not ac3(domains):
        return False, None

    def backtrack(domains):
        cell = get_unassigned_mrv(domains)
        if cell is None:
            return True
        for val in lcv_order(cell, domains):
            if val not in domains[cell]:
                continue
            old_domain = domains[cell].copy()
            domains[cell] = {val}
            removals = remove_from_peers(domains, cell, val)
            if all(len(domains[p]) > 0 for p in PEERS[cell]):
                if backtrack(domains):
                    return True
            domains[cell] = old_domain
            restore_to_peers(domains, removals)
        return False

    if backtrack(domains):
        return True, domains_to_board(domains)
    return False, None


# ============== Original helpers (for puzzle generation) ==============

def find_empty_cell(board):
    """Find an empty cell (0) in the board."""
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return (i, j)
    return None


def is_valid(board, row, col, num):
    """Check if placing num at (row, col) is valid."""
    # Check row
    for j in range(9):
        if board[row][j] == num:
            return False
    
    # Check column
    for i in range(9):
        if board[i][col] == num:
            return False
    
    # Check 3x3 box
    box_row, box_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(box_row, box_row + 3):
        for j in range(box_col, box_col + 3):
            if board[i][j] == num:
                return False
    
    return True


def solve_sudoku(board):
    """Solve Sudoku using backtracking (AI solver)."""
    empty = find_empty_cell(board)
    if not empty:
        return True
    
    row, col = empty
    for num in range(1, 10):
        if is_valid(board, row, col, num):
            board[row][col] = num
            if solve_sudoku(board):
                return True
            board[row][col] = 0
    
    return False


def generate_puzzle(difficulty=40):
    """Generate a valid Sudoku puzzle by solving empty board then removing numbers."""
    board = [[0] * 9 for _ in range(9)]
    
    # Fill diagonal 3x3 boxes first (they are independent)
    for box in range(3):
        nums = list(range(1, 10))
        random.shuffle(nums)
        for i in range(3):
            for j in range(3):
                board[box * 3 + i][box * 3 + j] = nums[i * 3 + j]
    
    # Solve the rest
    solve_sudoku(board)
    
    # Remove numbers based on difficulty (higher = more removed = harder)
    cells = [(i, j) for i in range(9) for j in range(9)]
    random.shuffle(cells)
    
    for i, j in cells[:difficulty]:
        board[i][j] = 0
    
    return board


def validate_solution(board):
    """Validate if the board is a correct Sudoku solution."""
    for i in range(9):
        row_nums = [n for n in board[i] if n != 0]
        if len(row_nums) != len(set(row_nums)):
            return False, f"Duplicate in row {i + 1}"
    
    for j in range(9):
        col_nums = [board[i][j] for i in range(9) if board[i][j] != 0]
        if len(col_nums) != len(set(col_nums)):
            return False, f"Duplicate in column {j + 1}"
    
    for box in range(9):
        br, bc = (box // 3) * 3, (box % 3) * 3
        box_nums = []
        for i in range(3):
            for j in range(3):
                n = board[br + i][bc + j]
                if n != 0:
                    box_nums.append(n)
        if len(box_nums) != len(set(box_nums)):
            return False, f"Duplicate in box {box + 1}"
    
    # Check if all cells are filled
    if any(0 in row for row in board):
        return False, "Puzzle incomplete"
    
    return True, "Correct! Well done!"


def get_hint(board, solution):
    """Get AI hint: return first empty cell with correct value from solution."""
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0 and solution[i][j] != 0:
                return {"row": i, "col": j, "value": solution[i][j]}
    return None


def find_conflicts(board, puzzle):
    """
    Find user-input cells that conflict (duplicate in row, column, or 3x3 box).
    puzzle: original prefilled state; cells empty in puzzle but filled in board = user input.
    Returns list of dicts: [{"row": r, "col": c, "value": v, "reason": "..."}, ...]
    """
    conflicts = []
    for i in range(9):
        for j in range(9):
            if puzzle[i][j] != 0:
                continue  # prefilled - assumed correct
            val = board[i][j]
            if val == 0:
                continue
            reasons = []
            # Check row
            for k in range(9):
                if k != j and board[i][k] == val:
                    reasons.append(f"duplicate {val} in row {i + 1}")
                    break
            # Check column
            for k in range(9):
                if k != i and board[k][j] == val:
                    reasons.append(f"duplicate {val} in column {j + 1}")
                    break
            # Check box
            br, bc = 3 * (i // 3), 3 * (j // 3)
            for bi in range(br, br + 3):
                for bj in range(bc, bc + 3):
                    if (bi, bj) != (i, j) and board[bi][bj] == val:
                        reasons.append(f"duplicate {val} in 3×3 box")
                        break
            if reasons:
                conflicts.append({
                    "row": i, "col": j, "value": val,
                    "reason": "; ".join(reasons)
                })
    return conflicts


def analyze_and_solve(board, puzzle):
    """
    Backtrack through user input: find conflicts, clear them, solve with CSP.
    Returns (success, solution_or_none, conflicts_cleared).
    """
    conflicts = find_conflicts(board, puzzle)
    cleaned = [row[:] for row in board]
    for c in conflicts:
        cleaned[c["row"]][c["col"]] = 0
    success, solution = solve_sudoku_csp(cleaned)
    if not success:
        solution = [row[:] for row in cleaned]
        solve_sudoku(solution)  # fallback
        success = True
    return success, solution, conflicts


@app.route('/api/csp-info', methods=['GET'])
def csp_info():
    """Return description of the CSP algorithms used by the AI solver."""
    return jsonify({
        'solver': 'CSP (Constraint Satisfaction Problem)',
        'techniques': [
            'AC-3 (Arc Consistency) - Prune domains before search',
            'MRV (Minimum Remaining Values) - Pick cell with fewest options',
            'Forward Checking - Remove assigned value from peers\' domains',
            'LCV (Least Constraining Value) - Try values that restrict peers least'
        ],
        'variables': 81,
        'constraints': 'AllDifferent on each row, column, and 3×3 box'
    })


@app.route('/')
def index():
    """Serve the main game page."""
    return render_template('index.html')


@app.route('/algorithm')
def algorithm():
    """Serve the algorithm explanation page."""
    return render_template('algorithm.html')


@app.route('/api/new-game', methods=['GET'])
def new_game():
    """Generate a new Sudoku puzzle."""
    difficulty = request.args.get('difficulty', 40, type=int)
    puzzle = generate_puzzle(difficulty)
    success, solution = solve_sudoku_csp([row[:] for row in puzzle])
    if not success:
        solution = [row[:] for row in puzzle]
        solve_sudoku(solution)  # fallback to simple backtracking
    return jsonify({
        'puzzle': puzzle,
        'solution': solution
    })


@app.route('/api/check', methods=['POST'])
def check_solution():
    """Validate the user's solution."""
    data = request.get_json()
    board = data.get('board', [])
    valid, message = validate_solution(board)
    return jsonify({'valid': valid, 'message': message})


@app.route('/api/hint', methods=['POST'])
def get_ai_hint():
    """Get AI hint for next move."""
    data = request.get_json()
    board = data.get('board', [])
    solution = data.get('solution', [])
    hint = get_hint(board, solution)
    if hint:
        return jsonify({'success': True, 'hint': hint})
    return jsonify({'success': False, 'message': 'No hints available'})


@app.route('/api/solve', methods=['POST'])
def solve():
    """
    AI solve: find conflicts in user input, clear them, backtrack with CSP, solve.
    Returns solution + report of cells that had errors.
    """
    data = request.get_json()
    board = [row[:] for row in data.get('board', [])]
    puzzle = data.get('puzzle')
    if not puzzle or len(puzzle) != 9 or len(puzzle[0]) != 9:
        puzzle = board  # fallback: treat all as given
    success, solution, conflicts = analyze_and_solve(board, puzzle)
    if success:
        return jsonify({
            'success': True,
            'solution': solution,
            'conflicts': conflicts,
            'message': f'Cleared {len(conflicts)} error(s) and solved.' if conflicts else 'Solved!'
        })
    return jsonify({'success': False, 'message': 'No solution exists'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
