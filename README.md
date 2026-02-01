# AMD Strategy Pro (Multi-Engine)

**The Ultimate Command Center for 0-14 DTE Options.**
Tracks 3 distinct strategies simultaneously based on your rules.

## The Strategy Engines

### 1. TREND (Breakouts)
-   **Method**: Debit Spreads (Calls/Puts).
-   **Trigger**: Price breaking SMA20/SMA50 with Momentum.
-   **Why**: Defined risk participation in strong moves without paying high IV.

### 2. RANGE (Chop)
-   **Method**: Iron Condors / Credit Spreads.
-   **Trigger**: Price compressing near SMA50 (Low ADX).
-   **Why**: "Selling the Chop" to decay Theta while waiting for a move.

### 3. CATALYST (Vol)
-   **Method**: Straddles / Calendars.
-   **Trigger**: High IV relative to history (Earnings/News).
-   **Why**: Capturing the expected move or IV crush.

## 4. Headless Mode (Discord Bot)
Want updates without the browser open? Use the Python bot.

1.  **Get a Webhook**:
    -   Open Discord -> Server Settings -> Integrations -> Webhooks.
    -   Create New Webhook -> Copy Webhook URL.
2.  **Edit Config**:
    -   Open `monitor.py` in a text editor.
    -   Paste your URL into: `DISCORD_WEBHOOK = '...'`
3.  **Run It**:
    -   Open Terminal.
    -   Run: `python3 monitor.py`
    -   It will check every 5 mins and message you!

## 5. How to Run in Background (24/7)
To leave the bot running even if you close the terminal:

1.  **Start it**:
    ```bash
    nohup python3 monitor.py &
    ```
    (It will print a number like `[1] 12345`. This is the Process ID).

2.  **Stop it**:
    ```bash
    pkill -f monitor.py
    ```
