"""Top-level package entry for the Wi-Fi 6 QoS ML workflow.

This package groups the reusable Python logic used by the project:
- configuration and file paths,
- dataset loading and artifact persistence,
- feature engineering,
- model training/evaluation,
- runtime inference for ns-3.
"""

# Re-export the most useful public functions so callers can import them from
# the package root instead of hunting through submodules.
from .config import *
from .data_utils import load_training_data, save_artifact
from .features import prepare_training_frame
from .modeling import train_model, evaluate_model
from .predict import predict_qos

# Define the package's public API in a single place.
__all__ = [
    "load_training_data",
    "prepare_training_frame",
    "train_model",
    "evaluate_model",
    "predict_qos",
]
