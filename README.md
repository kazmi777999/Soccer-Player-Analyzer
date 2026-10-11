# ⚽ Soccer Player Analyzer

### Football Analytics & Live Match Intelligence Platform

A full-stack football analytics application built using **Python, React, Next.js, and TypeScript**.

Soccer Player Analyzer transforms football statistics into an interactive experience, allowing users to explore player performance, compare footballers, analyze teams, visualize advanced metrics, and follow live football scores.

The project combines **data analysis, software engineering, interactive visualization, and REST API integration** to demonstrate practical full-stack development skills.

---

## 🚀 Key Features

### 👤 Player Profiles
- Search football players by name.
- Explore player statistics, including goals, assists, appearances, and minutes played.
- Analyze individual performance across available datasets.
- View advanced statistics such as goals per 90 minutes and expected goals (xG).

### ⚔️ Player Comparison
- Search and select two football players.
- Compare their statistics side by side.
- Evaluate goals, assists, minutes played, and per-90 metrics.
- Identify statistical differences between players.

### 🏆 Team Analysis
- Explore football clubs and their players.
- Analyze individual contributions within teams.
- Review team rosters and leading performers.
- Compare attacking contributions across players.

### 📊 Advanced Analytics
- Goals per 90 minutes
- Assists per 90 minutes
- Expected goals (xG)
- Expected assisted goals (xAG)
- Player rankings and performance visualizations

### 🔴 Live Football Matches
- Retrieve football match information through SportAPI.
- Display match scores, teams, and match status.
- Filter fixtures by supported competitions.
- View live and scheduled matches where supported.
- Refresh scores to retrieve updated match information.

*Live data availability depends on API coverage and subscription limits.*

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| Programming Languages | Python, TypeScript, JavaScript |
| Frontend | React, Next.js |
| Data Analysis | Pandas |
| Data Visualization | Matplotlib, React-based visualizations |
| Data Formats | CSV, JSON |
| Database | SQLite |
| API Integration | SportAPI |
| Version Control | Git, GitHub |
| Development Environment | Visual Studio Code |

---

## 📁 Project Structure

```text
soccer-player-analyzer/
│
├── frontend/
│   ├── app/
│   │   ├── api/
│   │   │   └── matches/
│   │   │       └── route.ts
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── lib/
│   │   ├── players.ts
│   │   └── players-data.json
│   │
│   ├── public/
│   ├── package.json
│   └── next.config.ts
│
├── soccer_analyzer/
│   ├── analysis.py
│   ├── api.py
│   └── database.py
│
├── data/
│   └── players_data_light-2025_2026.csv
│
├── app.py
├── database.py
├── requirements.txt
└── README.md
```

---

## 💻 Installation & Setup

### Prerequisites

- Node.js
- Python 3
- Git
- SportAPI API key for live match data

### 1. Clone the Repository

```bash
git clone https://github.com/kazmi777999/Soccer-Player-Analyzer.git
cd Soccer-Player-Analyzer
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Configure the API

Create a `.env.local` file inside the `frontend` directory:

```env
SPORTAPI_KEY=your_api_key_here
```

Replace `your_api_key_here` with your own SportAPI key.

**Never upload API keys or environment files containing credentials to GitHub.**

### 4. Run the Application

```bash
npm run dev
```

Open:

http://localhost:3000

### 5. Install Python Dependencies (Optional)

From the project's root directory:

```bash
pip install -r requirements.txt
```

---

## 📈 Data Analysis

The application uses structured football datasets to support player and team analysis.

Key analytical operations include:

- Data loading and preprocessing
- Player search and filtering
- Statistical comparisons
- Player performance rankings
- Goals and assists analysis
- Per-90-minute performance calculations
- Data visualization

### Example: Goals per 90 Minutes

Goals per 90 measures how frequently a player scores relative to their playing time.

**Formula:**

Goals per 90 = (Goals / Minutes Played) × 90

For example, a player who scores 20 goals in 2,000 minutes has:

Goals per 90 = (20 / 2000) × 90 = **0.90**

This metric helps compare players with different amounts of playing time.

---

## 📸 Application Screenshots

Screenshots of the application can be added here to demonstrate:

1. Homepage
2. Player Profiles
3. Player Comparison
4. Team Analysis
5. Advanced Metrics
6. Live Match Dashboard

---

## 🎯 Project Goals

This project was developed to strengthen practical skills in:

- Python programming and data analysis
- Full-stack web application development
- REST API integration
- Data visualization
- TypeScript and React
- Git and GitHub version control
- Organizing and maintaining a multi-component software project

---

## 🔮 Future Enhancements

- Machine learning models for match predictions
- Historical player performance tracking
- Expanded league coverage
- Interactive team comparison dashboards
- Automated data updates
- Public cloud deployment

---

## 👨‍💻 Developer

**Kazim Ali Jatoi**

Computer Science | University of Houston

Interested in **Data Science, Machine Learning, and Software Engineering**.

**GitHub:** https://github.com/kazmi777999

---

⭐ If you find this project interesting, consider starring the repository!
