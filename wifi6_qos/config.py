# This module centralizes the project-wide paths and schema information.
# Keeping these constants in one place avoids hard-coding file locations in
# multiple scripts and makes the whole workflow easier to explain and maintain.

from pathlib import Path

# Resolve the repository root from this file's location so the package can work
# regardless of which directory the user runs the script from.
ROOT_DIR = Path(__file__).resolve().parent.parent

# Dedicated workspace folders for source artifacts.
DATA_DIR = ROOT_DIR / "data"
MODELS_DIR = ROOT_DIR / "models"
RESULTS_DIR = ROOT_DIR / "results"

# The main dataset and the saved model artifacts used by training and inference.
DATA_FILE = DATA_DIR / "ns3_training_data.csv"
MODEL_PATH = MODELS_DIR / "model.pkl"
FEATURES_PATH = MODELS_DIR / "feature_cols.pkl"
LABEL_ENCODER_PATH = MODELS_DIR / "label_encoder.pkl"

# These are the input columns used to build the feature matrix for training.
# The order matters because the model expects the same ordering during training
# and inference.
FEATURE_COLS = [
    "packet_size",
    "interval_ms",
    "num_stations",
    "ru",
    "mcs",
    "throughput_mbps",
    "mean_delay_ms",
    "mean_jitter_ms",
    "packet_loss_rate",
    "traffic_type_enc",
    "throughput_efficiency",
    "channel_load_mbps",
]

# These are the output variables predicted by the regression model.
TARGET_COLS = [
    "priority",
    "ru",
    "twt_ms",
    "mcs",
]
