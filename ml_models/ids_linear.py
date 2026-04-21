import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler

_LAMBDAS = ["100ms", "500ms", "1500ms", "10s", "60s"]

def _window_stats(channel, stats):
    return [f"{channel}_L{lam}_{stat}" for lam in _LAMBDAS for stat in stats]

FEATURE_NAMES = (
    _window_stats("MI",       ["weight", "mean", "std"])
    + _window_stats("H",      ["weight", "mean", "std"])
    + _window_stats("HH",     ["weight", "mean", "std",
                                "magnitude", "radius", "covariance", "pcc"])
    + _window_stats("HpHp",   ["weight", "mean", "std",
                                "magnitude", "radius", "covariance", "pcc"])
    + _window_stats("HH_jit", ["weight", "mean", "std"])
)

assert len(FEATURE_NAMES) == 115


def load_kitsune_dataset(dataset_path, labels_path):
    features = pd.read_csv(dataset_path, header=None)

    if features.shape[1] != 115:
        raise ValueError(f"Expected 115 columns, found {features.shape[1]}.")

    features.columns = FEATURE_NAMES

    labels_raw = pd.read_csv(labels_path, header=None, names=["label"], low_memory=False)
    try:
        pd.to_numeric(labels_raw["label"].iloc[0])
        labels = labels_raw
    except (ValueError, TypeError):
        labels = labels_raw.iloc[1:].reset_index(drop=True)
        print("Labels file has a header row, skipped it.")

    if len(features) != len(labels):
        raise ValueError(f"Row mismatch: dataset has {len(features)} rows, labels has {len(labels)} rows.")

    features["label"] = labels["label"].values
    return features


def load_captured_csv(csv_path):
    df = pd.read_csv(csv_path)
    df = df.drop(columns=["packet_id", "label", "x", "Unnamed: 0", "Is_Attack"], errors="ignore")

    if list(df.columns) != FEATURE_NAMES:
        if df.shape[1] == 115:
            print("Old header naming detected, renaming columns.")
            df.columns = FEATURE_NAMES
        else:
            raise ValueError(f"Expected 115 feature columns, found {df.shape[1]}.")

    return df


TRAIN_DATASET = "OS_Scan_dataset.csv"
TRAIN_LABELS  = "OS_Scan_labels.csv"
TEST_CSV      = "Your_own_csv_file.csv"

print("Loading training data")
train_df = load_kitsune_dataset(TRAIN_DATASET, TRAIN_LABELS)
print(f"Rows loaded: {len(train_df):,}")
print(train_df["label"].value_counts().to_string())

X = train_df[FEATURE_NAMES]
y = train_df["label"].astype(int)

print("\nChecking data quality")
nan_count = X.isnull().sum().sum()
inf_count = np.isinf(X.values).sum()
print(f"NaN: {nan_count}  Inf: {inf_count}")

X = X.replace([np.inf, -np.inf], np.nan)
X = X.fillna(X.median())

print("\nScaling and training")
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train.values)
X_val_scaled   = scaler.transform(X_val.values)

print(f"Training rows:   {len(X_train):,}")
print(f"Validation rows: {len(X_val):,}")

model = LogisticRegression(
    max_iter=1000,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)
model.fit(X_train_scaled, y_train.values)
print("Training complete")

print("\nValidation results:")
val_preds = model.predict(X_val_scaled)
print(classification_report(y_val, val_preds, target_names=["Benign (0)", "Attack (1)"]))

cm = confusion_matrix(y_val, val_preds)
tn, fp, fn, tp = cm.ravel()
print(f"True  Negatives: {tn:,}")
print(f"False Positives: {fp:,}")
print(f"False Negatives: {fn:,}")
print(f"True  Positives: {tp:,}")

print(f"\nLoading test file: {TEST_CSV}")
test_df = load_captured_csv(TEST_CSV)
test_df = test_df.replace([np.inf, -np.inf], np.nan)
test_df = test_df.fillna(test_df.median())

test_scaled   = scaler.transform(test_df.values)
predictions   = model.predict(test_scaled)
probabilities = model.predict_proba(test_scaled)[:, 1]

results_df = test_df.copy()
results_df["Is_Attack"]          = predictions
results_df["Attack_Probability"] = probabilities.round(4)

output_file = "detection_results_linear.csv"
results_df.to_csv(output_file, index=False)

attack_count  = int(np.array(predictions, dtype=np.int64).sum())
total_packets = int(len(predictions))
print(f"Results saved to {output_file}")