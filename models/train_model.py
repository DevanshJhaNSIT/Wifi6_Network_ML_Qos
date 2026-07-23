"""Compatibility wrapper for the legacy training entrypoint."""

from wifi6_qos.modeling import train_and_save_model


if __name__ == "__main__":
    train_and_save_model("ns3_training_data.csv")
