# This module owns the training and evaluation pipeline.
# It is the bridge that turns the raw ns-3 CSV into a saved, reusable ML model.

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

# Import configuration constants and the artifact-saving helper.
from .config import DATA_FILE, FEATURE_COLS, TARGET_COLS, RESULTS_DIR
from .data_utils import save_model_artifacts
from .features import prepare_training_frame


def train_model(data_file: str = str(DATA_FILE)) -> tuple[RandomForestRegressor, pd.DataFrame]:
    """Train the Random Forest model and return the fitted model plus evaluation data.

    The returned tuple contains the trained model and a pair of test splits.
    """
    # Load the dataset using pandas.
    df = pd.read_csv(data_file)

    # Clean, encode, and engineer features before fitting the model.
    clean_df, label_encoder = prepare_training_frame(df)

    # Slice the cleaned dataset into feature matrix and target matrix.
    X = clean_df[FEATURE_COLS]
    y = clean_df[TARGET_COLS]

    # Split the data into train and test sets.
    # Stratification keeps the traffic type balance similar in both subsets.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=clean_df["traffic_type_enc"],
    )

    # Create the forest regressor with a fixed random seed for reproducibility.
    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=20,
        min_samples_split=3,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1,
    )

    # Fit the model on the training split.
    model.fit(X_train, y_train)

    # Save the trained model and the associated companion files.
    save_model_artifacts(model, FEATURE_COLS, label_encoder)

    # Return the fitted model and the held-out test data for evaluation.
    return model, (X_test, y_test)


def evaluate_model(model, y_test, y_pred) -> None:
    """Print metrics and save evaluation plots for the trained model.

    This function turns the numeric test results into human-readable evidence.
    """
    # Print a clear heading before the metric results.
    print("\n" + "=" * 50)
    print("  Evaluation on ns-3 test data")
    print("=" * 50)

    # Compute a metric per output column and print the values.
    for i, col in enumerate(TARGET_COLS):
        mae = mean_absolute_error(y_test[col], y_pred[:, i])
        r2 = r2_score(y_test[col], y_pred[:, i])
        print(f"  {col:12s}  MAE = {mae:6.3f}   R² = {r2:.3f}")

    # Create a 2x2 scatter plot grid, one subplot per target variable.
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle("Predicted vs Actual — ns-3 Trained Model", fontsize=13, fontweight="bold")

    # Plot actual vs predicted values for each target column.
    for ax, col, idx in zip(axes.flatten(), TARGET_COLS, range(4)):
        act = y_test[col].values
        pred = y_pred[:, idx]
        ax.scatter(act, pred, alpha=0.35, s=8, color="#339af0")
        mn, mx = min(act.min(), pred.min()), max(act.max(), pred.max())
        ax.plot([mn, mx], [mn, mx], "r--", lw=1.2, label="Perfect")
        ax.set_xlabel(f"Actual {col}")
        ax.set_ylabel(f"Predicted {col}")
        ax.set_title(f"{col}   R²={r2_score(act, pred):.3f}")
        ax.legend(fontsize=8)

    # Ensure the results folder exists before writing any plot files.
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save the prediction-vs-actual evaluation figure.
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "model_evaluation.png", dpi=150)

    # Build a feature importance table from the trained model.
    feature_importance = pd.DataFrame(
        {"feature": FEATURE_COLS, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)

    # Plot the feature importance ranking in a horizontal bar chart.
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    feature_importance.plot(kind="barh", x="feature", y="importance", ax=ax2, color="#51cf66", legend=False)
    ax2.set_title("Feature Importance")
    ax2.set_xlabel("Importance")

    # Save the feature importance figure.
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "feature_importance.png", dpi=150)

    # Print the locations of the saved result images.
    print("✅  results/model_evaluation.png saved")
    print("✅  results/feature_importance.png saved")


def train_and_save_model(data_file: str = str(DATA_FILE)) -> None:
    """End-to-end training pipeline for the CLI wrapper.

    This is the public function used by the training command-line entrypoint.
    """
    # Train the model on the dataset file passed in.
    model, (X_test, y_test) = train_model(data_file)

    # Use the held-out test set to create predictions for evaluation.
    y_pred = model.predict(X_test)

    # Print the metrics and save the plots.
    evaluate_model(model, y_test, y_pred)

    # Finish with a helpful message for the ns-3 integration step.
    print("\n🎉  Model trained on ns-3 data and ready!")
    print("    Copy models/model.pkl + models/feature_cols.pkl + models/label_encoder.pkl")
    print("    to ~/ns-3-dev/ then run 4_wifi_qos_validate.cc")
