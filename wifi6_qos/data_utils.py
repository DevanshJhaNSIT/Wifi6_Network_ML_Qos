# This module handles file I/O for the ML workflow.
# Its job is simple: load the training CSV and persist model artifacts to disk.

import joblib
import pandas as pd
from pathlib import Path

# Import the known artifact paths from the shared configuration module.
from .config import DATA_FILE, MODEL_PATH, FEATURES_PATH, LABEL_ENCODER_PATH


def load_training_data(data_file: str | Path = DATA_FILE) -> pd.DataFrame:
    """Load the ns-3 training dataset into a pandas DataFrame.

    Parameters
    ----------
    data_file:
        The CSV file to read. By default it points to `data/ns3_training_data.csv`.
    """
    # Read the CSV and return it as a DataFrame for the rest of the pipeline.
    df = pd.read_csv(data_file)
    return df


def save_artifact(obj, path: str | Path) -> None:
    """Persist any Python object to disk with joblib.

    This is used for model files, feature lists, and label encoders.
    """
    # Convert the incoming path to a Path object so the code is portable.
    path = Path(path)

    # Ensure the destination folder exists before saving.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write the object using joblib, which is more convenient for scikit-learn
    # models and other Python objects than plain pickle.
    joblib.dump(obj, path)


def save_model_artifacts(model, feature_cols, label_encoder) -> None:
    """Save all three persistent artifacts required by the inference pipeline."""
    # Store the trained model.
    save_artifact(model, MODEL_PATH)

    # Store the feature column order used during training.
    save_artifact(feature_cols, FEATURES_PATH)

    # Store the encoder so traffic-type labels can be reproduced consistently.
    save_artifact(label_encoder, LABEL_ENCODER_PATH)
