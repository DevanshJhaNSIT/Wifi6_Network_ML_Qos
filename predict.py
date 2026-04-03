import joblib
import sys
import numpy as np

model = joblib.load("model.pkl")

packet_size = int(sys.argv[1])
interval = int(sys.argv[2])
traffic_type = int(sys.argv[3])

X = np.array([[packet_size, interval, traffic_type]])
prediction = model.predict(X)

print(prediction[0])


