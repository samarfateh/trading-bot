# 🦅 The Strategy Lab: Master Manual (Classified)

> **CONFIDENTIAL**: This document contains sensitive keys, passcodes, and control protocols for the Automated Trading System.

---

## 🔑 Vault: Credentials & Keys

### Access Control
*   **Web Dashboard:** [https://web-production-7cc7a.up.railway.app](https://web-production-7cc7a.up.railway.app)
*   **Passcode:** `EarninCeo`
*   **Security:** Rate-limited (5/min), blocked shortcuts, anti-scraping active.

### API Keys (Hardcoded / Configured)
*   **AlphaVantage:** `POPZN5W6J3DCL2WE` (Market Data)
*   **Alpaca (Paper):** Configured in Environment Variables (Railway)
*   **Discord Webhook:** Hardcoded in `runner.py` (for alerts)

---

## 🗺️ System Architecture: The Map

### 1. The Core (Root Folder)
*   **`app.py`**: **The Brain.** Starts the Web Server AND the Trading Bot background thread.
*   **`index.html`**: **The Face.** The Vue.js dashboard you see in the browser.
*   **`login.html`**: **The Gate.** The dark-themed security check.
*   **`data_lake.db`**: **The Memory.** SQLite database storing all trades, signal history, and raw market data.
*   **`requirements.txt`**: **The Fuel.** List of all Python libraries needed to run.
*   **`Dockerfile`**: **The Blueprint.** Instructions for building the cloud container.

### 2. The Logic (`/strategy_lab` folder)
*   **`runner.py`**: **The Heartbeat.** The main loop that runs every 60 seconds.
*   **`judge.py`**: **The Decision Maker.** AI logic that decides BUY/SELL based on data.
*   **`paper_trader.py`**: **The Executioner.** Sends orders to Alpaca (Paper Mode).
*   **`risk_manager.py`**: **The Shield.** Checks VIX, SPY Crash, and Max Loss limits.
*   **`social_sentiment.py`**: **The Ear.** Listens to Reddit (WallStreetBets) for sentiment.
*   **`market_features.py`**: **The Eyes.** Calculus for Technical Analysis (RSI, MACD, Bollinger).

---

## 🕹️ Operations Guide

### A. The Cloud (Railway) - "Autopilot"
*   **Status:** **ACTIVE** (Runs 24/7)
*   **Updating:**
    1.  Edit code on your Mac.
    2.  `git add .`
    3.  `git commit -m "update"`
    4.  `git push`
    5.  **Done.** Railway automatically rebuilds and redeploys in ~2 minutes.

### B. The Kill Switch
**Emergency Stop Protocol:**
1.  **Metric Trigger:** If Daily Loss > 5% ($1000) -> **AUTO-STOP**.
2.  **Manual Trigger:**
    *   Log into Railway -> Click "Stop".
    *   **OR** Create a file named `STOP_TRADING.txt` in the root folder and push to git.

### C. Maintenance
*   **Logs:** Check Railway Dashboard -> "Deployments" -> "View Logs".
*   **Database:** `data_lake.db` grows over time. Use `sqlite3` to query it if needed.

---

## 🚨 Troubleshooting
*   **"502 Bad Gateway":** The server is restarting or crashed. Check Logs.
*   **"Access Denied":** You typed the passcode wrong (EarninCeo).
*   **"Rate Limit Exceeded":** You tried to login too fast. Wait 1 minute.
*   **"Bot Not Trading":** Check if the market is open (9:30 AM - 4:00 PM ET).

---

*Generated for: EarninCeo*
*System Status: SECURE*
