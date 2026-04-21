#!/bin/bash
# setup.sh

echo "Installing system dependencies for Nmap compilation"
sudo apt-get update
sudo apt-get install -y liblinear-dev liblua5.4-dev libpcap-dev libssl-dev

echo "Installing Python dependencies for packet conversion"
pip install -r requirements.txt

echo "Environment setup complete!"
