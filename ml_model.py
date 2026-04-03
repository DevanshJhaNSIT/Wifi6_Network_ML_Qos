import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import numpy as np

# 🔹 Simulated training data
data = {
    "packet_size": [200, 1400, 1500, 800, 300],
    "interval": [20, 40, 10, 200, 1000],
    "traffic_type": [0, 1, 2, 3, 4],  # encoded
    "priority": [3, 2, 1, 1, 0]       # HIGH=3 → LOW=0
}

df = pd.DataFrame(data)

X = df[["packet_size", "interval", "traffic_type"]]
y = df["priority"]

model = RandomForestClassifier()
model.fit(X, y)

joblib.dump(model, "model.pkl")

print("Model trained and saved!")



