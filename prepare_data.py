# prepare_data.py — Run this locally, then commit the /data folder to GitHub

import os
import fastf1 as ff1
import pandas as pd

os.makedirs('data', exist_ok=True)
os.makedirs('ff1_cache', exist_ok=True)
ff1.Cache.enable_cache('ff1_cache')

DRIVERS = ['RUS', 'ANT', 'LEC', 'HAM']

print("Loading session...")
race = ff1.get_session(2026, 'Australia', 'R')
race.load(laps=True, telemetry=True, weather=True)

# ── LAPS ──────────────────────────────────────────────────────────────────────
laps = race.laps.copy()

# Convert timedelta columns to float seconds for parquet compatibility
for col in laps.select_dtypes(include=['timedelta64[ns]']).columns:
    laps[col] = laps[col].dt.total_seconds()

laps.to_parquet('data/laps.parquet', index=False)
print("✅ data/laps.parquet saved")

# ── TELEMETRY per driver ───────────────────────────────────────────────────────
def save_tel(tel, path):
    df = tel.copy()
    # Convert timedelta to seconds
    for col in df.select_dtypes(include=['timedelta64[ns]']).columns:
        df[col] = df[col].dt.total_seconds()
    df.to_parquet(path, index=False)

for d in DRIVERS:
    dl = race.laps.pick_drivers(d)
    print(f"  Processing {d}...")

    # Best lap
    try:
        lap = dl.pick_accurate().pick_fastest()
        tel = lap.get_telemetry().add_distance()
        save_tel(tel, f'data/tel_{d}_best.parquet')
    except Exception as e:
        print(f"    ⚠️ Best lap {d}: {e}")

    # Lap 1
    try:
        lap1 = dl[dl['LapNumber'] == 1].iloc[0]
        tel  = lap1.get_telemetry()
        save_tel(tel, f'data/tel_{d}_lap1.parquet')
    except Exception as e:
        print(f"    ⚠️ Lap 1 {d}: {e}")

    # Fresh tyre (Lap 2) and Degraded tyre (lap before pit)
    try:
        pits    = dl[dl['PitOutTime'].notna()]
        pit_lap = int(pits['LapNumber'].min()) if not pits.empty else 20

        lap_fresh = dl[dl['LapNumber'] == 2].iloc[0]
        lap_deg   = dl[dl['LapNumber'] == max(2, pit_lap - 1)].iloc[0]

        save_tel(lap_fresh.get_telemetry().add_distance(), f'data/tel_{d}_fresh.parquet')
        save_tel(lap_deg.get_telemetry().add_distance(),   f'data/tel_{d}_deg.parquet')
    except Exception as e:
        print(f"    ⚠️ Fresh/deg {d}: {e}")

    # Pit info (store pit_lap number)
    try:
        pits = dl[dl['PitOutTime'].notna()][['LapNumber', 'TyreLife', 'Compound', 'Position']].copy()
        pits['Driver'] = d
        pits.to_parquet(f'data/pits_{d}.parquet', index=False)
    except Exception as e:
        print(f"    ⚠️ Pits {d}: {e}")

print("\n✅ All done! Commit the /data folder to GitHub.")
print("Files created:")
for f in sorted(os.listdir('data')):
    size = os.path.getsize(f'data/{f}') / 1024
    print(f"  data/{f}  ({size:.1f} KB)")
