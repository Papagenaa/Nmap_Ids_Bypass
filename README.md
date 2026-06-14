# Evading Detection During Reconnaissance: AI Explainability as Inside Information

Research implementation accompanying the paper submitted to the **Workshop on Secure and Trustworthy AI (STAI 2026)**

---

## What This Is

This project demonstrates a structural vulnerability in machine learning-based intrusion detection systems (ML-IDS) that use the **AfterImage** feature extractor (as found in Kitsune). The core finding is that ML-IDS classifiers never observe raw network traffic; they only receive a 115-column statistical feature vector produced by the feature extractor. This creates a layer that can be manipulated independently of the classifier itself.

The framework does not try to hide the scan by slowing it down or fragmenting packets. Instead, it poisons the statistical accumulators inside AfterImage before and during the scan, so that the feature vectors produced by Nmap traffic fall within the benign range. The evasion was validated against three tree-based classifiers of increasing difficulty:

| Classifier | Baseline Recall | Post-Evasion Recall |
|---|---|---|
| Decision Tree | 99.61% | 0% |
| Random Forest | 98.52% | 0% |
| Gradient Boosting | 99.16% | 0% |

AI explainability tools (LIME, feature importance) were used both to identify which features drive classification and to debug evasion failures, demonstrating that defensive tooling can be repurposed as an attack calibrator.

---

## How It Works

### The Vulnerability

AfterImage tracks network statistics using **exponentially decaying time windows**. Each window maintains a running mean, variance, and covariance of packet characteristics (size, inter-arrival time, etc.) for a given connection. Nmap OS scans produce near-zero packet-size variance within these windows, which is the primary feature classifiers learn to flag as malicious.

Since the classifier only sees the output of the feature extractor, an attacker who can manipulate the feature vector controls the classification outcome.

### Identifying the Target Feature

A decision tree trained on the Kitsune OS scan dataset was used to extract feature importance scores. The analysis identified **packet-size variance in short decay windows**, particularly the 10-second and 1500ms radius features, as the primary classification signals. These are the features the evasion framework targets.

### The Two-Part Evasion

**1. Nmap Source Modification**

Standard Nmap OS scan probes are sent one at a time at fixed sizes, producing zero variance. The modification turns each single probe into a flood of 5 packets: the first is the original unmodified probe (preserving scan accuracy), and the remaining 4 carry random-sized payloads. This inflates the variance in active connection windows above the detection threshold.

**2. The Evasion Script**

The evasion script runs in two stages: one before the scan and one concurrently with it. The pre-scan stage initializes the relevant AfterImage accumulators with high-variance traffic so they do not appear uninitialized when the scan starts. Uninitialized accumulators produce zero variance and would immediately reveal the scan. The concurrent stage keeps those accumulators in a poisoned state for the full duration of the scan, counteracting the natural decay of AfterImage's time windows.

Together, the two components ensure that the feature vectors produced during the scan consistently fall within the benign range.

---

## Requirements

- Linux (tested on Kali Linux)
- Python 3.8+
- Nmap source (for patching)
- [Kitsune](https://github.com/ymirsky/Kitsune-py) (AfterImage feature extractor)
- Python packages:

```bash
pip install scikit-learn lime numpy pandas matplotlib scapy
```

---

## Setup

### 1. Dataset

Download the OS scan dataset from the [Kitsune Network Attack Dataset](https://github.com/ymirsky/KitNET-py):

```bash
# Place the pcap and its AfterImage-extracted feature CSV in data/
```

### 2. Train the Classifiers

```bash
python classifiers/train_decision_tree.py
python classifiers/train_random_forest.py
python classifiers/train_gradient_boosting.py
```

### 3. Build the Patched Nmap

```bash
# Clone Nmap source
git clone https://github.com/nmap/nmap.git
cd nmap

# Install dependencies

# Build
./configure && make
```

---

## Usage

> **For authorized testing environments only.**

Run the evasion script and patched Nmap against a target on your lab network:

```bash
# Terminal 1 — start the evasion script
sudo python blindfold.py // you can change the ip within the script

# Terminal 2 — run the patched Nmap scan right after phase 1
sudo ./nmap_source/nmap -sU -Pn --evade-mlids -p 22,80 -O <TARGET_IP>
```

Capture the traffic with tcpdump or Wireshark, then extract features with AfterImage and run through the trained classifiers to validate evasion.

---

## Results

All three classifiers achieved near-perfect detection on unmodified Nmap scans (>=98.5% recall). With evasion active, recall dropped to 0% across all three, meaning every attack packet was classified as benign. The vulnerability is in the shared feature extraction layer, not in any individual classifier.

The gradient boosting classifier required additional calibration. LIME analysis revealed the 1500ms radius window (not the 10-second window) was its primary signal. Phase 1 timing was adjusted to keep the 1500ms bucket above threshold at scan start.

---

## Limitations

Timing parameters in the evasion script are calibrated for the lab environment used in the paper. Background traffic volume, CPU load, and network conditions affect AfterImage's accumulator behavior. Recalibration may be needed in different environments.

---

## Disclaimer

This framework is intended for security research and authorized penetration testing only. The authors are not responsible for misuse. All experiments were conducted in isolated lab environments.
