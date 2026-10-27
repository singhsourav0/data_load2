# Ritikda Autonomous Parallel Ping & Uptime Engine

Automated, non-blocking parallel monitoring engine for **Tracker** (`tracker.bepcssa.in`) and **Demo** (`demo.bepcssa.in`).

## Features
- **Parallel Testing:** Sends requests to both `tracker.bepcssa.in` and `demo.bepcssa.in` concurrently.
- **Controlled Load:** Exactly **5 requests** per target using **2 concurrent worker threads**.
- **100% Autonomous:** Includes an automated 5-minute scheduler loop.
- **Fail-Safe & Resilient:** Catches all timeouts, SSL warnings, and connection drops without crashing.
- **GitHub Actions Ready:** Included workflow runs every 5 minutes (`- cron: '*/5 * * * *'`).

## Files
- `ritikda_auto_ping.py` - Core autonomous parallel ping engine.
- `auto_ping_history.log` - Persistent timestamped log of each cycle.
- `.github/workflows/ritikda-load-test.yml` - 5-minute autonomous GitHub Actions workflow.

## Usage

### 1. Run in Autonomous Loop (Triggers every 5 minutes continuously)
```powershell
python ritikda_auto_ping.py
```
*(Optionally change interval: `python ritikda_auto_ping.py --interval 180` for 3 minutes)*

### 2. Run Single Cycle (For CI/CD or Cron)
```powershell
python ritikda_auto_ping.py --once
```

### 3. Deploy to GitHub Actions
1. Push this folder to your GitHub repository.
2. The workflow at `.github/workflows/ritikda-load-test.yml` will automatically trigger every 5 minutes.
3. Execution logs are saved as downloadable artifacts under the Actions tab.
