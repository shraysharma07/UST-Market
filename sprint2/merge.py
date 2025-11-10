from pathlib import Path
from datetime import datetime
import pandas as pd

# always resolve paths relative to where this script lives
BASE_DIR = Path(__file__).resolve().parent

#load the three csv files
oc = pd.read_csv(BASE_DIR / "OC_2_20180108.csv")
t  = pd.read_csv(BASE_DIR / "T_2_20180108.csv")
wu = pd.read_csv(BASE_DIR / "WU_2_20180108.csv")

oc["Source"] = "OC"
t["Source"]  = "T"
wu["Source"] = "WU"

#stack them into one table (row-wise)
combined = pd.concat([oc, t, wu], ignore_index=True, sort=False)

#parse timestamps into real datetimes (format in these files is 'HH:MM:SS:ffffff YYYYMMDD')
def parse_ts(s):
    if pd.isna(s):
        return pd.NaT
    s = str(s).strip()
    parts = s.split()
    if len(parts) == 2 and ":" in parts[0] and parts[1].isdigit():
        try:
            return datetime.strptime(f"{parts[1]} {parts[0]}", "%Y%m%d %H:%M:%S:%f")
        except Exception:
            return pd.NaT
    return pd.to_datetime(s, errors="coerce")

ts_col = "Timestamp"  # my time column
combined["__ts"] = combined[ts_col].apply(parse_ts)

#tie-break rule 
priority = {"OC": 1, "WU": 2, "T": 3}
combined["__prio"] = combined["Source"].map(priority)

#sanity checks
if combined["__prio"].isna().any():
    missing = combined.loc[combined["__prio"].isna(), "Source"].unique()
    raise ValueError(f"Missing priority mappings for sources: {missing}")

#sort by time, then by my tie-break priority (stable keeps order within perfect ties)
combined = combined.sort_values(by=["__ts", "__prio"], kind="stable")

#write out a clean file (drop my helper columns)
final = combined.drop(columns=["__ts", "__prio"])
out_path = BASE_DIR / "2_20180108_merged.csv"
final.to_csv(out_path, index=False)

#confirmation printout
print("done ->", out_path)
print(final["Source"].value_counts().to_dict())


#Analysis section (for practice)
#which minutes were busiest?
#event type distribution

combined["minute"] = combined["__ts"].dt.floor("min") 
activity_per_min = combined.groupby("minute").size()

print("\nTop 5 busiest minutes:")
print(activity_per_min.sort_values(ascending=False).head(5))

activity_per_min.to_csv(BASE_DIR / "activity_per_minute.csv", header=["event_count"])

event_counts = combined["Source"].value_counts()
print("\nEvent type distribution:")
print(event_counts)

event_counts.to_csv(BASE_DIR / "event_type_distribution.csv", header=["count"])
