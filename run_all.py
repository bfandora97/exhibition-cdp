"""Jalankan semua: generate data dummy -> ETL -> data quality report."""
import subprocess
import sys

for script in ["src/generate_data.py", "src/etl.py", "src/data_quality.py"]:
    print(f"\n=== {script} ===")
    subprocess.run([sys.executable, script], check=True)
print("\nSelesai. Cek folder output/ dan data/clean/")
