import csv
import numpy as np
from FeatureExtractor import FE
import sys
import os

_LAMBDAS = ["100ms", "500ms", "1500ms", "10s", "60s"]

def _window_stats(channel, stats):
    names = []
    for lam in _LAMBDAS:
        for stat in stats:
            names.append(f"{channel}_L{lam}_{stat}")
    return names

FEATURE_NAMES = (
    _window_stats("MI",       ["weight", "mean", "std"])
    + _window_stats("H",      ["weight", "mean", "std"])
    + _window_stats("HH",     ["weight", "mean", "std",
                                "magnitude", "radius", "covariance", "pcc"])
    + _window_stats("HpHp",   ["weight", "mean", "std",
                                "magnitude", "radius", "covariance", "pcc"])
    + _window_stats("HH_jit", ["weight", "mean", "std"])
)

assert len(FEATURE_NAMES) == 115, f"Expected 115 features, got {len(FEATURE_NAMES)}"


def pcap_to_csv(pcap_file, output_csv, packet_limit=np.inf):
    if not os.path.isfile(pcap_file):
        print(f"Error: File '{pcap_file}' not found.")
        return 0

    print(f"Input:  {pcap_file}")
    print(f"Output: {output_csv}")
    print(f"Limit:  {packet_limit if packet_limit != np.inf else 'All packets'}")

    try:
        fe = FE(pcap_file, limit=packet_limit)
    except Exception as e:
        print(f"Error initializing Feature Extractor: {e}")
        return 0

    num_features = len(FEATURE_NAMES)

    try:
        with open(output_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(FEATURE_NAMES)

            packet_count = 0
            failed_count = 0

            while True:
                feature_vector = fe.get_next_vector()

                if len(feature_vector) == 0:
                    break

                packet_count += 1

                if len(feature_vector) != num_features:
                    failed_count += 1
                    print(f"Skipping packet {packet_count}: expected {num_features} features, got {len(feature_vector)}")
                    continue

                writer.writerow(list(feature_vector))

                if packet_count % 1000 == 0:
                    print(f"Processed {packet_count} packets...", end='\r')

            written = packet_count - failed_count
            print(f"\nDone.")
            print(f"Total seen:   {packet_count}")
            print(f"Written:      {written}")
            print(f"Skipped:      {failed_count}")
            if packet_count > 0:
                print(f"Success rate: {(written / packet_count * 100):.2f}%")
            print(f"Output size:  {os.path.getsize(output_csv) / (1024*1024):.2f} MB")

    except Exception as e:
        print(f"Error writing to CSV: {e}")
        return 0

    return packet_count


def main():
    if len(sys.argv) < 2:
        print("Usage: python pcap_to_csv.py <input.pcap> [output.csv] [packet_limit]")
        sys.exit(1)

    pcap_file = sys.argv[1]

    if len(sys.argv) >= 3:
        output_csv = sys.argv[2]
    else:
        base_name = os.path.splitext(os.path.basename(pcap_file))[0]
        output_csv = f"{base_name}_features.csv"

    if len(sys.argv) >= 4:
        try:
            packet_limit = int(sys.argv[3])
        except ValueError:
            print("Error: packet_limit must be an integer")
            sys.exit(1)
    else:
        packet_limit = np.inf

    packets_processed = pcap_to_csv(pcap_file, output_csv, packet_limit)

    if packets_processed == 0:
        print("Conversion failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
