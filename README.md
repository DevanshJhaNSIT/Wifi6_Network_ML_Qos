# Wi-Fi 6 QoS ML Project

This project combines an ns-3 Wi-Fi 6 simulation with a Python machine-learning pipeline.

The aim is to:

1. collect Wi-Fi QoS data from an ns-3 simulation,
2. train a regression model on that data,
3. use the trained model inside the ns-3 validator to assign better QoS values,
4. compare the baseline and ML-assisted results,
5. generate plots that show the difference.

---

## Project structure

- `data/` — dataset and ns-3 data collector source
- `models/` — training script and saved ML artifacts
- `results/` — graph-generation code and output figures
- `wifi6_qos/` — reusable Python package for config, feature engineering, training, and prediction
- `scripts/` — simple command-line wrappers for training and inference

---

## What each piece does

### 1. Data collection

- [data/1_data_collector.cc](data/1_data_collector.cc) is the ns-3 program that generates training data.
- It writes a CSV file named `ns3_training_data.csv` into the `data/` folder.

### 2. Model training

- [models/train_model.py](models/train_model.py) is the training script.
- [scripts/train_model_cli.py](scripts/train_model_cli.py) is the recommended entrypoint for normal use.
- After training, the model artifacts are saved into `models/`.

### 3. Inference inside ns-3

- [3_predict.py](3_predict.py) loads the trained model and returns four QoS values:
  - priority
  - ru
  - twt_ms
  - mcs

### 4. Validation simulation

- [4_wifi_qos_validate_modified3t.cc](4_wifi_qos_validate_modified3t.cc) is the ns-3 simulation file that validates the ML-driven QoS behavior.
- It creates a Wi-Fi 6 topology, runs traffic, and compares the baseline vs ML-assisted behavior.

### 5. Graph generation

- [results/generate_graphs.py](results/generate_graphs.py) reads the CSV outputs from the validation runs and produces graphs.

---

## Prerequisites

Before running anything, make sure you have:

- Python 3.10+ installed
- `pip` available
- A working ns-3 installation, such as `~/ns-3-dev`
- A C++ compiler and the usual build tools for ns-3
- Internet access only if you want to install dependencies from PyPI

---

## Step 1: Clone and set up the repo

Clone the repository into a folder on your machine.

Then create and activate a Python virtual environment:

```bash
cd /path/to/Wifi6_Network_ML_Qos-3
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

If you prefer not to use a virtual environment, you may just install the packages directly with `pip`.

---

## Step 2: Prepare the dataset

The project expects the dataset file at:

```text
data/ns3_training_data.csv
```

If you do not already have that file, generate it using ns-3.

### Option A — If you already have the CSV

Place it inside the `data/` folder.

### Option B — If you need to generate it

First make sure your ns-3 source tree exists. A common location is:

```bash
~/ns-3-dev
```

Copy the data collector into the ns-3 `scratch` directory:

```bash
mkdir -p ~/ns-3-dev/scratch
cp data/1_data_collector.cc ~/ns-3-dev/scratch/
```

Then build and run it:

```bash
cd ~/ns-3-dev
./ns3 build
./ns3 run scratch/1_data_collector
```

The collector writes `ns3_training_data.csv` in the ns-3 working directory. Copy that file into the project’s `data/` folder:

```bash
cp ~/ns-3-dev/ns3_training_data.csv data/ns3_training_data.csv
```

---

## Step 3: Train the model

From the project root, run:

```bash
python3 scripts/train_model_cli.py
```

This will:

- read `data/ns3_training_data.csv`,
- engineer the required features,
- train the model,
- save the resulting artifacts into `models/`.

Expected saved files:

- `models/model.pkl`
- `models/feature_cols.pkl`
- `models/label_encoder.pkl`

---

## Step 4: Prepare the ns-3 validation run

The ns-3 validator needs the Python prediction script and the trained model files available inside the ns-3 environment.

Copy them into the ns-3 workspace:

```bash
cp 3_predict.py ~/ns-3-dev/
cp models/model.pkl ~/ns-3-dev/
cp models/feature_cols.pkl ~/ns-3-dev/
cp models/label_encoder.pkl ~/ns-3-dev/
```

Copy the validator source into the ns-3 `scratch` folder:

```bash
cp 4_wifi_qos_validate_modified3t.cc ~/ns-3-dev/scratch/4_wifi_qos_validate.cc
```

Now build ns-3:

```bash
cd ~/ns-3-dev
./ns3 build
```

---

## Step 5: Run the validation simulation

There are two modes:

- baseline mode: `--useML=false`
- ML-assisted mode: `--useML=true`

### Baseline run

```bash
cd ~/ns-3-dev
./ns3 run "scratch/4_wifi_qos_validate --useML=false"
```

### ML-assisted run

```bash
cd ~/ns-3-dev
./ns3 run "scratch/4_wifi_qos_validate --useML=true"
```

These commands produce CSV files such as:

- `results_without_ml.csv`
- `results_with_ml.csv`
- `stats_without_ml.csv`
- `stats_with_ml.csv`

---

## Step 6: Generate graphs

Copy the output CSVs into the `results/` folder of this repository, then run:

```bash
cd results
python3 generate_graphs.py
```

This creates the graph images in the same `results/` folder.

---

## Using the automation script

A small helper script is included at [run.sh](run.sh). It is intended for macOS/Linux users and wraps the common workflow into one place.

You can run:

```bash
./run.sh train
./run.sh validate
./run.sh graphs
./run.sh all
```

What each command does:

- `train` — trains the ML model from the dataset in `data/`
- `validate` — copies the inference assets into the ns-3 environment and runs the baseline and ML validation simulations
- `graphs` — copies the result CSVs into `results/` and generates the plots
- `all` — runs the full sequence in order

If you want the full manual workflow instead, use the commands in the sections above.

---

## Quick end-to-end summary

If you want the shortest path from a clean machine:

```bash
cd /path/to/Wifi6_Network_ML_Qos-3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

mkdir -p ~/ns-3-dev/scratch
cp data/1_data_collector.cc ~/ns-3-dev/scratch/
cd ~/ns-3-dev
./ns3 build
./ns3 run scratch/1_data_collector
cp ~/ns-3-dev/ns3_training_data.csv /path/to/Wifi6_Network_ML_Qos-3/data/ns3_training_data.csv

cd /path/to/Wifi6_Network_ML_Qos-3
python3 scripts/train_model_cli.py
cp 3_predict.py ~/ns-3-dev/
cp models/model.pkl ~/ns-3-dev/
cp models/feature_cols.pkl ~/ns-3-dev/
cp models/label_encoder.pkl ~/ns-3-dev/
cp 4_wifi_qos_validate_modified3t.cc ~/ns-3-dev/scratch/4_wifi_qos_validate.cc
cd ~/ns-3-dev
./ns3 build
./ns3 run "scratch/4_wifi_qos_validate --useML=true"
./ns3 run "scratch/4_wifi_qos_validate --useML=false"

cd /path/to/Wifi6_Network_ML_Qos-3/results
python3 generate_graphs.py
```

---

## Troubleshooting

### `scratch` not found

This usually means your ns-3 install is not in `~/ns-3-dev` or it has not been created yet.

Create the folder manually:

```bash
mkdir -p ~/ns-3-dev/scratch
```

### `python3` cannot find the project package

Make sure your virtual environment is active and that you are running the scripts from the project root.

### The model files are missing

Re-run:

```bash
python3 scripts/train_model_cli.py
```

### Graph generation fails

Make sure the four required CSV files are present in the `results/` directory before running:

- `results_without_ml.csv`
- `results_with_ml.csv`
- `stats_without_ml.csv`
- `stats_with_ml.csv`

---

## Final note

This project is a hybrid workflow:

- ns-3 handles the network simulation,
- Python handles feature engineering and ML,
- CSV files connect the two halves,
- plotting turns the simulation results into figures.

If you follow the steps above in order, a beginner should be able to reproduce the full workflow on a clean system.
