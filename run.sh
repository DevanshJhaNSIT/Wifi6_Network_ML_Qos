#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$PROJECT_ROOT/data"
MODELS_DIR="$PROJECT_ROOT/models"
RESULTS_DIR="$PROJECT_ROOT/results"

usage() {
    echo "Usage: ./run.sh [train|validate|graphs|all]"
    echo ""
    echo "Commands:"
    echo "  train     Train the ML model from data/ns3_training_data.csv"
    echo "  validate  Run the baseline and ML ns-3 validation modes"
    echo "  graphs    Generate plots from the validation CSV outputs"
    echo "  all       Run train, validate, and graphs"
}

detect_ns3_dir() {
    if [[ -n "${NS3_DIR:-}" && -x "$NS3_DIR/ns3" ]]; then
        return
    fi

    local candidates=(
        "$HOME/ns-3-dev"
        "$HOME/ns-3"
        "/opt/ns-3-dev"
    )

    for candidate in "${candidates[@]}"; do
        if [[ -x "$candidate/ns3" ]]; then
            NS3_DIR="$candidate"
            return
        fi
    done

    echo "Error: no ns-3 installation was found." >&2
    echo "Expected one of: ~/ns-3-dev, ~/ns-3, /opt/ns-3-dev" >&2
    echo "Set NS3_DIR to the correct location and try again." >&2
    exit 1
}

require_file() {
    local path="$1"
    local label="$2"
    if [[ ! -f "$path" ]]; then
        echo "Error: missing $label at $path" >&2
        echo "Please prepare that file before running this step." >&2
        exit 1
    fi
}

train_model() {
    echo "[1/3] Checking inputs..."
    require_file "$DATA_DIR/ns3_training_data.csv" "training dataset"

    echo "[1/3] Training model..."
    python3 "$PROJECT_ROOT/scripts/train_model_cli.py"
}

validate_model() {
    detect_ns3_dir

    require_file "$MODELS_DIR/model.pkl" "trained model"
    require_file "$MODELS_DIR/feature_cols.pkl" "feature column file"
    require_file "$MODELS_DIR/label_encoder.pkl" "label encoder"
    require_file "$PROJECT_ROOT/3_predict.py" "prediction script"
    require_file "$PROJECT_ROOT/4_wifi_qos_validate_modified3t.cc" "validation source"

    echo "[2/3] Preparing ns-3 validation artifacts in $NS3_DIR..."
    mkdir -p "$NS3_DIR/scratch"
    cp "$PROJECT_ROOT/3_predict.py" "$NS3_DIR/"
    cp "$MODELS_DIR/model.pkl" "$NS3_DIR/"
    cp "$MODELS_DIR/feature_cols.pkl" "$NS3_DIR/"
    cp "$MODELS_DIR/label_encoder.pkl" "$NS3_DIR/"
    cp "$PROJECT_ROOT/4_wifi_qos_validate_modified3t.cc" "$NS3_DIR/scratch/4_wifi_qos_validate.cc"

    echo "[2/3] Building ns-3..."
    (cd "$NS3_DIR" && ./ns3 build)

    echo "[2/3] Running baseline validation (--useML=false)..."
    (cd "$NS3_DIR" && ./ns3 run "scratch/4_wifi_qos_validate --useML=false")

    echo "[2/3] Running ML validation (--useML=true)..."
    (cd "$NS3_DIR" && ./ns3 run "scratch/4_wifi_qos_validate --useML=true")
}

generate_graphs() {
    echo "[3/3] Generating graphs..."
    local required_files=(
        "$NS3_DIR/results_without_ml.csv"
        "$NS3_DIR/results_with_ml.csv"
        "$NS3_DIR/stats_without_ml.csv"
        "$NS3_DIR/stats_with_ml.csv"
    )

    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            cp "$file" "$RESULTS_DIR/"
        fi
    done

    for file in \
        "$RESULTS_DIR/results_without_ml.csv" \
        "$RESULTS_DIR/results_with_ml.csv" \
        "$RESULTS_DIR/stats_without_ml.csv" \
        "$RESULTS_DIR/stats_with_ml.csv"; do
        require_file "$file" "result CSV"
    done

    python3 "$PROJECT_ROOT/results/generate_graphs.py"
}

case "${1:-}" in
    train)
        train_model
        ;;
    validate)
        validate_model
        ;;
    graphs)
        detect_ns3_dir
        generate_graphs
        ;;
    all)
        train_model
        validate_model
        generate_graphs
        ;;
    -h|--help|help|"")
        usage
        ;;
    *)
        usage
        exit 1
        ;;
 esac
