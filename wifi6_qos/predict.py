# This module executes the trained ML model at runtime.
# It is the inference layer called by the ns-3 validator to produce QoS values.

import joblib
import numpy as np
import sys

# Import the saved artifact paths and the feature-construction helpers.
from .config import FEATURE_COLS, MODEL_PATH, FEATURES_PATH, LABEL_ENCODER_PATH
from .features import build_feature_vector, derive_inference_features


def predict_qos(packet_size: int, interval_ms: int, num_stations: int = 8) -> tuple[int, int, int, int]:
    """Load the saved model and return QoS decisions for one input sample.

    Returns a tuple of:
    (priority, ru, twt_ms, mcs)
    """
    # Try to load the saved model artifacts. If they are missing, fall back to a
    # safe default schedule so the validator can keep running gracefully.
    try:
        model = joblib.load(MODEL_PATH)
        feat_cols = joblib.load(FEATURES_PATH)
        label_encoder = joblib.load(LABEL_ENCODER_PATH)
    except FileNotFoundError:
        return 1, 10, 50, 6

    # Build the exact feature dictionary expected by the model.
    feature_values = derive_inference_features(packet_size, interval_ms, num_stations)

    # Convert the feature dictionary into a 2D row matrix in the same order used for training.
    X = build_feature_vector(feature_values, feat_cols)

    # Ask the loaded model to predict the QoS outputs.
    pred = model.predict(X)[0]

    # Clamp the results into valid Wi-Fi 6-friendly ranges before returning them.
    priority = int(np.clip(round(pred[0]), 0, 3))
    ru = int(np.clip(round(pred[1]), 1, 37))
    twt = int(np.clip(round(pred[2]), 5, 500))
    mcs = int(np.clip(round(pred[3]), 0, 11))

    # Return the final deterministic, bounded QoS values.
    return priority, ru, twt, mcs


def main() -> None:
    """Command-line entrypoint for direct inference from the shell.

    Expected input:
        python3 predict.py <packet_size> <interval_ms> <num_stations>
    """
    # Parse the first two required arguments.
    packet_size = int(sys.argv[1])
    interval_ms = int(sys.argv[2])

    # The third argument defaults to 8 if the caller does not provide it.
    num_stations = int(sys.argv[3]) if len(sys.argv) > 3 else 8

    # Obtain the predicted QoS tuple.
    priority, ru, twt, mcs = predict_qos(packet_size, interval_ms, num_stations)

    # Print the result on one line so ns-3 can read it using `popen()`.
    print(priority, ru, twt, mcs)


if __name__ == "__main__":
    main()
