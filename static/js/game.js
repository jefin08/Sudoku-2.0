/**
 * Sudoku Game - Client Logic
 * Handles grid, timer, validation, and API calls
 */

let puzzle = [];
let solution = [];
let startTime = null;
let timerInterval = null;
let initialPrefilled = []; // Track which cells were prefilled

const gridEl = document.getElementById('sudoku-grid');
const timerEl = document.getElementById('timer');
const messageEl = document.getElementById('message');
const conflictReportEl = document.getElementById('conflict-report');
const modalEl = document.getElementById('modal');
const modalTimeEl = document.getElementById('modal-time');
const modalBtn = document.getElementById('modal-btn');

function showMessage(text, type = '') {
    messageEl.textContent = text;
    messageEl.className = 'message ' + type;
}

function clearMessage() {
    messageEl.textContent = '';
    messageEl.className = 'message';
    conflictReportEl.classList.add('hidden');
    conflictReportEl.innerHTML = '';
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function startTimer() {
    stopTimer();
    startTime = Date.now();
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        timerEl.textContent = formatTime(elapsed);
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function getElapsedSeconds() {
    if (!startTime) return 0;
    return Math.floor((Date.now() - startTime) / 1000);
}

function getBoardState() {
    const cells = gridEl.querySelectorAll('.sudoku-cell');
    const board = [];
    for (let i = 0; i < 9; i++) {
        board[i] = [];
        for (let j = 0; j < 9; j++) {
            const idx = i * 9 + j;
            const input = cells[idx].querySelector('input');
            const val = input ? parseInt(input.value, 10) : 0;
            board[i][j] = isNaN(val) ? 0 : val;
        }
    }
    return board;
}

function validateInput(row, col, num) {
    if (num < 1 || num > 9) return false;
    const board = getBoardState();
    board[row][col] = num;

    // Check row
    const rowNums = board[row].filter(n => n !== 0);
    if (rowNums.length !== new Set(rowNums).size) return false;

    // Check column
    const colNums = [];
    for (let i = 0; i < 9; i++) colNums.push(board[i][col]);
    const colFiltered = colNums.filter(n => n !== 0);
    if (colFiltered.length !== new Set(colFiltered).size) return false;

    // Check 3x3 box
    const br = Math.floor(row / 3) * 3, bc = Math.floor(col / 3) * 3;
    const boxNums = [];
    for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
            boxNums.push(board[br + i][bc + j]);
        }
    }
    const boxFiltered = boxNums.filter(n => n !== 0);
    return boxFiltered.length === new Set(boxFiltered).size;
}

function renderGrid(puzzleData, solutionData = null) {
    gridEl.innerHTML = '';
    puzzle = puzzleData;
    solution = solutionData || puzzleData;

    for (let i = 0; i < 9; i++) {
        for (let j = 0; j < 9; j++) {
            const cell = document.createElement('div');
            const val = puzzle[i][j];
            const isPrefilled = val !== 0;

            cell.className = 'sudoku-cell ' + (isPrefilled ? 'prefilled' : 'user-input');
            cell.dataset.row = i;
            cell.dataset.col = j;

            const input = document.createElement('input');
            input.type = 'number';
            input.min = 1;
            input.max = 9;
            input.inputMode = 'numeric';
            input.autocomplete = 'off';

            if (isPrefilled) {
                input.value = val;
                input.readOnly = true;
            } else {
                input.placeholder = '';
                input.addEventListener('input', (e) => {
                    let v = e.target.value.replace(/\D/g, '').slice(-1);
                    if (v === '') {
                        e.target.value = '';
                        cell.classList.remove('error');
                        return;
                    }
                    const num = parseInt(v, 10);
                    e.target.value = num;
                    cell.classList.remove('error');
                    if (!validateInput(i, j, num)) {
                        cell.classList.add('error');
                        showMessage('Duplicate in row, column, or 3×3 box', 'error');
                    } else {
                        clearMessage();
                    }
                });
                input.addEventListener('keydown', (e) => {
                    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                        e.preventDefault();
                        moveFocus(i, j, e.key);
                    }
                });
            }

            cell.appendChild(input);
            gridEl.appendChild(cell);
        }
    }
}

function moveFocus(row, col, key) {
    let nr = row, nc = col;
    if (key === 'ArrowUp') nr = Math.max(0, row - 1);
    if (key === 'ArrowDown') nr = Math.min(8, row + 1);
    if (key === 'ArrowLeft') nc = Math.max(0, col - 1);
    if (key === 'ArrowRight') nc = Math.min(8, col + 1);
    const idx = nr * 9 + nc;
    const cells = gridEl.querySelectorAll('.sudoku-cell');
    const target = cells[idx].querySelector('input');
    if (target && !target.readOnly) target.focus();
}

async function loadNewGame() {
    showMessage('Loading...');
    try {
        const res = await fetch('/api/new-game');
        const data = await res.json();
        renderGrid(data.puzzle, data.solution);
        startTimer();
        clearMessage();
    } catch (err) {
        showMessage('Failed to load puzzle. Try again.', 'error');
    }
}

async function checkSolution() {
    const board = getBoardState();
    showMessage('Checking...');
    try {
        const res = await fetch('/api/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ board })
        });
        const data = await res.json();
        if (data.valid) {
            stopTimer();
            modalTimeEl.textContent = formatTime(getElapsedSeconds());
            modalEl.classList.remove('hidden');
            showMessage('', 'success');
        } else {
            showMessage(data.message, 'error');
        }
    } catch (err) {
        showMessage('Check failed. Try again.', 'error');
    }
}

async function getHint() {
    const board = getBoardState();
    if (!solution || solution.length === 0) {
        showMessage('No solution loaded.', 'error');
        return;
    }
    try {
        const res = await fetch('/api/hint', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ board, solution })
        });
        const data = await res.json();
        if (data.success && data.hint) {
            const { row, col, value } = data.hint;
            const idx = row * 9 + col;
            const cells = gridEl.querySelectorAll('.sudoku-cell');
            const cell = cells[idx];
            const input = cell.querySelector('input');
            input.value = value;
            cell.classList.add('hint');
            cell.classList.remove('error');
            setTimeout(() => cell.classList.remove('hint'), 600);
            clearMessage();
        } else {
            showMessage('Puzzle complete or no hints available.', 'error');
        }
    } catch (err) {
        showMessage('Hint failed. Try again.', 'error');
    }
}

async function aiSolve() {
    const board = getBoardState();
    showMessage('Analyzing & solving...');
    try {
        const res = await fetch('/api/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ board, puzzle })
        });
        const data = await res.json();
        if (data.success) {
            solution = data.solution;
            renderGrid(data.solution, data.solution);
            stopTimer();
            if (data.conflicts && data.conflicts.length > 0) {
                showMessage(data.message, 'success');
                conflictReportEl.innerHTML =
                    '<h4>Errors found and cleared (backtrack analysis):</h4><ul>' +
                    data.conflicts.map(c =>
                        `<li>Cell (${c.row + 1},${c.col + 1}): ${c.value} — ${c.reason}</li>`
                    ).join('') + '</ul>';
                conflictReportEl.classList.remove('hidden');
            } else {
                showMessage(data.message || 'AI solved the puzzle!', 'success');
            }
        } else {
            showMessage(data.message || 'Could not solve.', 'error');
        }
    } catch (err) {
        showMessage('Solve failed. Try again.', 'error');
    }
}

function resetGame() {
    if (puzzle.length) {
        renderGrid(puzzle, solution);
        startTimer();
        clearMessage();
    }
}

// Event listeners
document.getElementById('btn-check').addEventListener('click', checkSolution);
document.getElementById('btn-hint').addEventListener('click', getHint);
document.getElementById('btn-solve').addEventListener('click', aiSolve);
document.getElementById('btn-reset').addEventListener('click', resetGame);
document.getElementById('btn-new').addEventListener('click', loadNewGame);
modalBtn.addEventListener('click', () => {
    modalEl.classList.add('hidden');
    loadNewGame();
});

// Start game on load
loadNewGame();
