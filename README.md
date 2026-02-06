# Sudoku Web Game

A Sudoku game built with Python Flask and HTML/CSS/JavaScript. Features a CSP-based AI solver, conflict detection, hints, validation, timer, and a clean modern UI.

## Features

- **9×9 Sudoku grid** with prefilled and user-input cells
- **Real-time validation** – prevents duplicate numbers in rows, columns, and 3×3 boxes
- **Check Solution** – validates your completed puzzle
- **AI Hint** – suggests the next correct number
- **AI Solve (CSP)** – analyzes user errors, clears conflicts, solves using CSP algorithms
- **Conflict report** – when AI solves, shows which cells had errors and why
- **Reset** – clear user inputs and restart the current puzzle
- **New Game** – load a new random puzzle
- **Timer** – tracks completion time
- **Completion modal** – success message with your time
- **Algorithm page** – explains how the CSP solver works

## CSP (Constraint Satisfaction Problem)

The AI solver uses CSP techniques. See **CSP_REQUIREMENTS.txt** for full requirements and details. Visit `/algorithm` for a visual explanation of the algorithm.

## Local Development

```bash
# Create virtual environment (optional)
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open http://localhost:5000 in your browser.

**Pages:**
- http://localhost:5000 – Game
- http://localhost:5000/algorithm – Algorithm & CSP explanation

## Deployment

### Heroku

1. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Login: `heroku login`
3. Create app: `heroku create your-sudoku-app`
4. Deploy: `git push heroku main`
5. Open: `heroku open`

### Render

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`
6. Deploy

### Railway

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Use `gunicorn app:app` as start command
4. Deploy

### Note on Vercel / Netlify / GitHub Pages

These platforms are optimized for static sites. For this Flask app, use **Heroku**, **Render**, or **Railway**. Alternatively, convert the app to a fully client-side version for static hosting.

## Project Structure

```
sudoko 2.0/
├── app.py                 # Flask app, CSP solver, Sudoku logic
├── requirements.txt
├── Procfile               # For Heroku
├── runtime.txt            # Python version for Heroku
├── README.md
├── CSP_REQUIREMENTS.txt   # CSP requirements and technical details
├── templates/
│   ├── index.html         # Main game page
│   └── algorithm.html     # Algorithm & CSP explanation page
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── game.js
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Game page |
| `/algorithm` | GET | Algorithm explanation page |
| `/api/new-game` | GET | Generate new puzzle |
| `/api/check` | POST | Validate solution |
| `/api/hint` | POST | Get AI hint |
| `/api/solve` | POST | AI solve (finds conflicts, clears, solves) |
| `/api/csp-info` | GET | CSP techniques description |
