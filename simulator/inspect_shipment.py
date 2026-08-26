"""
Quick sanity-check visualization for generated shipment data.
Run this after generate_shipment.py to visually confirm the temperature profile looks correct.
"""

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("simulator/sample_shipment.csv")

plt.figure(figsize=(10, 5))
plt.plot(df.index, df["temperature"], marker="o", label="Temperature (°C)")
plt.axhline(y=8.0, color="red", linestyle="--", label="Safe max (8°C)")
plt.axhline(y=2.0, color="blue", linestyle="--", label="Safe min (2°C)")
plt.xlabel("Reading index (time progression)")
plt.ylabel("Temperature (°C)")
plt.title("Simulated Shipment Temperature Profile")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("simulator/temperature_profile.png")
print("Saved plot to simulator/temperature_profile.png")
plt.show()