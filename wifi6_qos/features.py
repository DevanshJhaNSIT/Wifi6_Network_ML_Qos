# This module holds the feature-engineering logic.
# Feature engineering is the step where raw simulation metrics are converted into
# the numerical inputs the machine-learning model can understand.

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Import the schema that defines how the model input should be shaped.
from .config import FEATURE_COLS, TARGET_COLS


def prepare_training_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, LabelEncoder]:
    """Encode traffic type and derive the engineered features used by the model.

    The returned DataFrame is ready to be split into training and test sets.
    """
    # Create a label encoder to convert categorical traffic types into integers.
    le = LabelEncoder()

    # Work on a copy so the original dataset is not modified accidentally.
    df = df.copy()

    # Replace the text labels with numeric indices.
    df["traffic_type_enc"] = le.fit_transform(df["traffic_type"])

    # Throughput efficiency measures how effectively the selected RU is used.
    # It is clipped to [0, 1] so it stays numerically stable for the model.
    df["throughput_efficiency"] = (
        df["throughput_mbps"] / (df["ru"] / 37.0 * 143.4 + 1e-9)
    ).clip(0, 1)

    # Estimate the total channel load created by multiple stations sending data.
    df["channel_load_mbps"] = (
        df["num_stations"] * df["packet_size"] * 8.0
        / (df["interval_ms"] / 1000.0) / 1e6
    )

    # Drop rows that do not have all required features or target values.
    df = df.dropna(subset=FEATURE_COLS + TARGET_COLS)

    # Return both the cleaned dataset and the encoder object for later reuse.
    return df, le


def build_feature_vector(values: dict, feature_cols: list[str]) -> np.ndarray:
    """Create the ordered NumPy matrix expected by the trained model.

    The model expects a 2D array, even for a single sample.
    """
    # Create a row in the same column order that was used for training.
    return np.array([[values[col] for col in feature_cols]])


def derive_inference_features(packet_size: int, interval_ms: int, num_stations: int) -> dict:
    """Generate the derived feature values used at prediction time.

    During training, the model learned from already-engineered features.
    At prediction time, the inference script must rebuild the same shape.
    """
    # Use neutral defaults for the QoS values that the model will predict.
    # These are only placeholders to construct a valid feature vector.
    ru_est = 10
    mcs_est = 6

    # Convert packet size and interval into an approximate throughput value.
    throughput_mbps = round((packet_size * 8.0) / max(interval_ms, 1) * 1000.0 / 1e6, 6)

    # Provide representative latency-related placeholders.
    mean_delay_ms = 0.30
    mean_jitter_ms = 0.20
    packet_loss_rate = 0.00

    # Map packet size ranges to the traffic type code learned during training.
    # The encoding order follows LabelEncoder sorting.
    if packet_size <= 100:
        traffic_type_enc = 1   # IoT
    elif packet_size <= 300:
        traffic_type_enc = 4   # VoIP
    elif packet_size <= 850:
        traffic_type_enc = 0   # HTTP
    elif packet_size <= 950:
        traffic_type_enc = 2   # VPN
    else:
        traffic_type_enc = 3   # Video

    # Compute throughput efficiency from the estimated RU and throughput.
    throughput_efficiency = min(1.0, throughput_mbps / (ru_est / 37.0 * 143.4 + 1e-9))

    # Estimate aggregate channel load from the station count and packet size.
    channel_load_mbps = num_stations * packet_size * 8.0 / (interval_ms / 1000.0) / 1e6

    # Return a dictionary with exactly the same field names the model was trained on.
    return {
        "packet_size": packet_size,
        "interval_ms": interval_ms,
        "num_stations": num_stations,
        "ru": ru_est,
        "mcs": mcs_est,
        "throughput_mbps": throughput_mbps,
        "mean_delay_ms": mean_delay_ms,
        "mean_jitter_ms": mean_jitter_ms,
        "packet_loss_rate": packet_loss_rate,
        "traffic_type_enc": traffic_type_enc,
        "throughput_efficiency": throughput_efficiency,
        "channel_load_mbps": channel_load_mbps,
    }
