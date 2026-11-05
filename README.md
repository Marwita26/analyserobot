# 🤖 Mobile Robot Performance Dashboard

Streamlit dashboard analysing the telemetry of 8 differential-drive mobile robots
(speed, distance, heading, energy, battery, motor health, slip, incidents).
Project for **YaneCode Academy** – by **BEDDIAF Marwa**.

## Features
- 🔐 Login page (username/password, password stored as a SHA-256 hash)
- 🧹 **Data cleaning**: types, duplicates, missing values, impossible values, IQR outliers, downloadable clean CSV
- 🎯 **KPIs**: missions completed, distance, Wh/m, speed & trajectory error, battery autonomy,
  collisions, wheel blockages, slip by floor type and payload
- 📈 **Visualizations** (Matplotlib + Seaborn): x-y trajectories, speed trend, heading (polar),
  box plots, heatmaps, correlation matrix, **Pareto** of incidents
- 🔎 **Filters**: time window, robots, mode, floor type, payload
- 💡 **Conclusions & recommendations** generated from the filtered data (e.g. worn motor detection)

## Project structure
```
robot_dashboard/
├── app.py            # Streamlit application
├── requirements.txt  # Python dependencies
└── README.md
```

## Installation & run
```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

## Data
The dataset is **not included**. Two options:
1. Upload `beddiaf_marwa.csv` with the uploader in the sidebar (after login), or
2. Place `beddiaf_marwa.csv` next to `app.py` (or in a `data/` folder) – it is loaded automatically.

## Login
| Username | Password |
|----------|----------|
| marwa    | Marwabdf34 |

## Tech stack
Python · Streamlit · Pandas · NumPy · Matplotlib · Seaborn
