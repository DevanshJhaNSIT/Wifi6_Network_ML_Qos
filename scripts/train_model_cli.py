from wifi6_qos.config import DATA_FILE
from wifi6_qos.modeling import train_and_save_model


if __name__ == "__main__":
    train_and_save_model(str(DATA_FILE))
