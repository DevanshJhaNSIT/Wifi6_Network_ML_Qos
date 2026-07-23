"""Compatibility wrapper for the legacy prediction entrypoint."""

import sys

from wifi6_qos.predict import predict_qos


if __name__ == "__main__":
    packet_size = int(sys.argv[1])
    interval_ms = int(sys.argv[2])
    num_stations = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    priority, ru, twt, mcs = predict_qos(packet_size, interval_ms, num_stations)
    print(priority, ru, twt, mcs)
