![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastF1](https://img.shields.io/badge/FastF1-3.8.1-red)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32-orange)
![License](https://img.shields.io/badge/License-MIT-green)

# 🏎️ Ferrari Strategy Autopsy | AUS GP 2026

> **An interactive Streamlit dashboard for deep-dive Formula 1 race strategy analysis**

Comprehensive lap-by-lap analysis of the 2026 Australian Grand Prix,
examining how Ferrari lost a commanding race lead to Mercedes through
strategic decisions, pit stop timing, and tyre management.

🔗 **[View Live App]([https://f1-australain-gp-2026.streamlit.app/])** ← update after deploy

---

## 📚 Research Foundation

The ERS battery inference methodology in this app is inspired by:

> Kleisarchaki, K. (2026). *An HMM–POMDP Framework for 2026 Formula 1
> Energy Strategy*. arXiv:2603.01290.
> https://arxiv.org/abs/2603.01290

The paper proposes using 5 observable FastF1 signals to infer hidden
battery states. This app implements a simplified version of that
observational pipeline (ERS Delta, super-clipping detection, boost mode
identification) on real 2026 Australian GP race data —
**one of the first empirical applications of this framework on actual
race data, validated the same weekend the paper was published.**

---

## Overview

This application provides a comprehensive, data-driven analysis of the
2026 Australian Grand Prix, focusing on Ferrari's strategic decisions
that led to losing the race lead to Mercedes.

Charles Leclerc started **P4 on the grid** but executed an aggressive
dive into Turn 1 to lead the race from Lap 1. Despite holding P1 for
the majority of the race, Ferrari's pit stop strategy allowed Mercedes'
George Russell to undercut and reclaim the lead permanently.

The dashboard combines FastF1 telemetry, lap timing, and ERS proxy
analysis to answer: **What exactly went wrong for Ferrari?**

---

## 🔍 Key Question

**How did Ferrari lose the 2026 Australian GP despite leading from
Turn 1 after Leclerc's P4 → P1 move?**

This dashboard provides evidence-based answers through:
- Lap-by-lap gap analysis showing the exact lap Mercedes took P1
- Pit stop timing analysis revealing the undercut window
- Tyre degradation patterns comparing Ferrari vs Mercedes strategy
- Telemetry data showing speed, throttle, and braking differences
- ERS deployment inference across the race
- Lap 1 position tracking showing Leclerc's T1 overtake in real time

---

## 🔑 Key Findings

*(Update these with your actual app output after running)*

- **Leclerc led X laps** from his Turn 1 move before losing P1
- **Russell undercut Ferrari** — pitted Lap X vs Ferrari's Lap Y
  (X laps earlier), gaining track position on fresh rubber
- **Tyre degradation**: Ferrari's compound degraded ~X.Xs/lap faster
  in the final stint, forcing an earlier-than-optimal pit window
- **T1 approach**: Leclerc braked Xm later than Russell at Turn 1
  (Xm vs Xm), explaining the aggressive overtake opportunity
- **ERS efficiency**: Mercedes deployed battery X% of their best race
  lap vs Ferrari's X% — more conservative deployment, more consistent
  race pace

---

## Features

### 📋 Race Verdict Cards
At-a-glance summary cards for each driver showing:
- Final race position with podium emojis
- Best lap time of the race
- Number of laps led
- Pit stop lap numbers
- Color-coded by team (Ferrari red, Mercedes cyan)

### 📉 Gap Analysis
Multiple views of time gaps between drivers:
- **LEC vs RUS**: Main battle — exact lap Ferrari lost P1
- **HAM vs ANT**: Secondary Mercedes vs Ferrari comparison
- **All vs Russell**: Baseline showing relative pace across all 4
- Vertical lines marking each pit stop lap
- Shaded regions showing who holds track position
- Hover tooltips with exact gap per lap

### 🏁 Position Tracker
- Line chart: position changes lap-by-lap for all 4 drivers
- Inverted Y-axis (P1 at top, like a real timing tower)
- Red shaded region highlights every lap Ferrari led
- Step-function shape — positions snap on overtakes, not interpolated

### ⏱️ Tyre Degradation Analysis
- Lap time evolution per compound (Soft/Medium/Hard)
- Tyre life degradation curves per driver
- Linear regression degradation rate (seconds/lap) per stint
- Filters out invalid laps (pit laps, safety car, track limits)
- Identifies optimal pit windows from degradation crossover points

### 🔧 Pit Stop Timing
- Pit lap, tyre age, compound, and track position at stop
- Bubble chart: tyre age at stop (size) vs lap number
- Auto-verdict: confirms undercut with lap delta calculation
- Gap before/after pit stop to quantify position change

### 📡 Telemetry Comparison
- Speed, throttle, brake, and gear traces per lap
- Driver-selectable comparison: fresh tyre vs degraded tyre
- Distance-based x-axis (meters around Albert Park)
- Highlights exactly where degraded tyres cost lap time

### 🚦 Initial Speed vs Time (Race Start)
- Speed vs time from lights out — who accelerated fastest
- Milestone table: speed at 2s, 5s, 10s, 15s, 30s, 60s
- Time to 100/200/250 km/h per driver — launch performance
- Acceleration traces showing ERS burst detection at launch
- RPM + gear shift timing panel
- Speed leadership scatter: who had highest speed every 0.5s

### 🏁 T1 Approach Analysis
- Speed, ERS delta, throttle, and brake — 0 to 400m
- Braking point comparison (distance + speed at brake)
- ERS area chart: positive = deploying, negative = super-clipping
- Per-driver metric cards: max speed, peak ERS boost, brake point

### ⚡ ERS Proxy Analysis
Since raw ERS data is proprietary, battery behaviour is
reverse-engineered from 4 derived telemetry signals:

+------------------+----------------------------------+-------------------------------+
| Signal           | Formula                          | Interpretation                |
+------------------+----------------------------------+-------------------------------+
| ERS Delta        | Speed - RPM-predicted speed      | Positive = deploying          |
| Super-clipping   | Full throttle + negative delta   | Harvesting on-throttle (2026) |
| Boost Mode       | High speed + abnormal accel      | Stacked deployment burst      |
| Harvest Zones    | Brake on + part throttle         | Standard regeneration         |
+------------------+----------------------------------+-------------------------------+

Methodology inspired by Kleisarchaki (2026), arXiv:2603.01290

---

## Drivers Analyzed

+--------------------+------+-----------+---------+-------------------------------------------+
| Driver             | Code | Team      | Color   | Race Story                                |
+--------------------+------+-----------+---------+-------------------------------------------+
| George Russell     | RUS  | Mercedes  | #27F4D2 | Pole → lost T1 → undercut to win          |
| Kimi Antonelli     | ANT  | Mercedes  | #00B8A0 | P2 start → clean Mercedes 1-2             |
| Charles Leclerc    | LEC  | Ferrari   | #E8002D | P4 start → T1 dive to P1 → lost at pits  |
| Lewis Hamilton     | HAM  | Ferrari   | #FF6B6B | Ferrari debut → P4 finish                 |
+--------------------+------+-----------+---------+-------------------------------------------+

---

## Installation

### Prerequisites
- Python 3.8+
- pip
- Internet connection (first run only)
- ~500MB free disk space (FastF1 cache)

### Quick Start

    git clone <repository-url>
    cd F1
    pip install -r requirements.txt
    streamlit run aus.py

### requirements.txt

    streamlit>=1.32.0
    fastf1>=3.8.1
    pandas>=2.0.0
    numpy>=1.26.0
    plotly>=5.18.0
    scipy>=1.11.0
    scikit-learn>=1.3.0

### Virtual Environment (Recommended)

    python -m venv venv
    source venv/bin/activate        # Mac/Linux
    venv\Scripts\activate           # Windows
    pip install -r requirements.txt
    streamlit run aus.py

---

## Usage

### First Run (~2-3 mins)
1. Downloads race data from FastF1 API
2. Caches to /tmp/f1_cache
3. Displays "✅ Race data loaded successfully!"

### Subsequent Runs
- Instant load from cache
- No internet required

    streamlit run aus.py                              # Default port 8501
    streamlit run aus.py --server.port 8080           # Custom port
    streamlit run aus.py --server.address 0.0.0.0    # Network access

---

## Technical Architecture

### Data Flow

    FastF1 API (F1 Live Timing + Ergast)
            |
      /tmp/f1_cache  (FastF1 disk cache)
            |
      @st.cache_resource  (session object, shared across users)
            |
      @st.cache_data  (computed DataFrames, per-input memoized)
            |
      Analysis Functions  (ERS proxy, gap calc, degradation)
            |
      Plotly Figures → Streamlit Dashboard

### Caching Strategy

+----------------------+----------------------+---------------+---------------------------+
| Layer                | Decorator            | Scope         | Used For                  |
+----------------------+----------------------+---------------+---------------------------+
| FastF1 disk          | ff1.Cache            | Persistent    | Raw API responses         |
| Session cache        | @st.cache_resource   | App lifetime  | Race session object       |
| Data cache           | @st.cache_data       | Per-input     | Computed DataFrames       |
+----------------------+----------------------+---------------+---------------------------+

### File Structure

    F1/
    ├── aus.py              # Main Streamlit application
    ├── requirements.txt    # Python dependencies
    ├── README.md           # Documentation
    └── .streamlit/
        └── config.toml     # Dark theme configuration

---

## Methodology Notes

### Gap Calculation

    Gap = CumulativeTime(Driver2) - CumulativeTime(Driver1)
    # Positive = Driver1 ahead; Negative = Driver2 ahead

### Tyre Degradation Rate
Computed via linear regression on accurate laps per stint:

    deg_rate = np.polyfit(tyre_life, lap_time, deg=1)[0]
    # Units: seconds per additional lap on tyre

### ERS Inference Pipeline

    rpm_factor    = mean_speed / mean_rpm
    SpeedFromRPM  = RPM * rpm_factor          # ICE-only prediction
    ERS_Delta     = Speed - SpeedFromRPM      # deviation = electric contribution
    SuperClipping = (Throttle > 90%) AND (ERS_Delta < -5)
    BoostMode     = (Speed > 70th pct) AND (Accel > 85th pct)

---

## Data Source

FastF1 wraps official FIA Live Timing data:
- Lap times: ±0.001s precision
- Telemetry: ~10-20 Hz, ±1 km/h speed, ±1% throttle
- GPS position: ±1m
- Coverage: 2018-present

NOTE: ERS/battery SoC data is proprietary — this app uses the
proxy inference method described above and in arXiv:2603.01290.

---

## Troubleshooting

+-----------------------------+---------------------------+--------------------------------------------+
| Issue                       | Cause                     | Fix                                        |
+-----------------------------+---------------------------+--------------------------------------------+
| "Error loading data"        | Network/API timeout       | Clear /tmp/f1_cache, retry                 |
| "Module not found"          | Missing dependencies      | pip install -r requirements.txt            |
| Slow performance            | Large telemetry load      | Disable unused sections in sidebar         |
| Charts not showing          | Browser JS issue          | Use Chrome/Firefox, disable extensions     |
+-----------------------------+---------------------------+--------------------------------------------+

---

## Acknowledgments

- FastF1 — Theresa Hoeglinger & contributors (https://docs.fastf1.dev)
- Streamlit — Web framework (https://streamlit.io)
- Plotly — Interactive visualizations (https://plotly.com)
- FIA — Making timing data publicly accessible
- Kleisarchaki (2026) — ERS inference methodology inspiration
  arXiv:2603.01290 — https://arxiv.org/abs/2603.01290

---

## Contact & Support

- Open a GitHub issue for bugs or feature suggestions
- FastF1 docs:   https://docs.fastf1.dev
- Streamlit docs: https://docs.streamlit.io

---

Built by Karthikeyan L | 2026 Australian GP | Race Day Analysis
