# Overview
This project is an add-on for nmap that implements a new switch that demonstrates adversarial feature manipulation in network traffic. It includes a custom patch for NMaps OS fingerprinting engine designed to inflate volumetric , variance and weight metrics to bypass machine learning intrusion detection systems , specifically targeting Random Forest , Neural Network and Linear architectures trained on the Kitsune OS scan dataset.

## Repository Structure
* `feature_extractor`: The files containing the code needed to run the pcap2csv script.
* `nmap_source`: Contains the full modified NMap source code.
* `ml_models/`: The scripts used for testing against different ml models.

## Part 1 : The evasion scanner

### Installation
1. Clone the repository
   ```bash
   git clone https://github.com/Papagenaa/Nmap_Ids_Bypass.git
   ```
2. Navigate into the source directory
   ```bash
   cd Nmap_Ids_Bypass
   ```
3. Configure the environment
   ```bash
   ./configure
   ```
4. Compile the source code
   ```bash
   make
   ```

### Usage
You can run normal scans using the -O flag. To execute the payload add the --evade-mlids flag. Warning , in order for it to work you need to add specific ports to avoid unnecassary traffic.
```bash
cd nmap_source
sudo ./nmap -O --evade-mlids -p <x,x) <target_ip>
```

## Part 2 : The IDS detection models

## Usage
1. ```python
   pip install requirements.txt
   ```
2. Place 'OS_Scan_dataset.csv' and 'OS_Scan_labels.csv' in the root folder.
3. Capture your own traffic , convert it to a CSV with the pcap2csv script and place it in the root.
4. Run your chosen model e.g
   ```python
   python ml_models/ids_neural_network.py
   ```
5. The script will produce a CSV file with a column appended to it about the model's decision.


# DISCLAIMER
**This project is provided for authorized security research and educational purposes only. Unauthorized access to computer systems is illegal. The author assumes no liability for misuse of this software. Users are solely responsible for ensuring they have proper authorization before testing any systems. By using this tool, you agree to use it only on systems you own or have explicit written permission to test.**
