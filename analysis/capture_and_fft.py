"""Capture optical vibration data from Arduino and perform FFT analysis.

This script matches the measurement workflow used in the project report:
- Trigger acquisition over serial.
- Receive 550 ADC samples.
- Discard the first 50 stored samples to reduce startup transients.
- Remove the DC component.
- Compute the FFT and report the strongest component above 5 Hz.
- Save a timestamped time/frequency-domain figure.
"""

import time
import serial
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

SERIAL_PORT = "COM9"  # Change to match your system
BAUD_RATE = 115200
TOTAL_SAMPLES = 550
FS = 1000.0  # Nominal sampling frequency [Hz]


def capture_and_analyze():
    print(f"Connecting to {SERIAL_PORT}...")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)
        ser.reset_input_buffer()

        print("Triggering data capture...")
        ser.write(b"s")

        raw_data = []
        for _ in range(TOTAL_SAMPLES):
            line = ser.readline().decode("utf-8").strip()
            if line.isdigit():
                raw_data.append(int(line))

        ser.close()

        if len(raw_data) != TOTAL_SAMPLES:
            print(f"Error: Received {len(raw_data)} samples instead of {TOTAL_SAMPLES}.")
            return

        print("Data acquired successfully. Computing FFT...")

        # Discard the first 50 stored samples to reduce startup/settling artifacts.
        valid_data = raw_data[50:]
        analyzed_samples = len(valid_data)

        signal = np.array(valid_data, dtype=float)
        signal = signal - np.mean(signal)
        t = np.arange(analyzed_samples) / FS

        yf = fft(signal)
        xf = fftfreq(analyzed_samples, 1 / FS)[: analyzed_samples // 2]
        amplitude = (2.0 / analyzed_samples) * np.abs(yf[: analyzed_samples // 2])

        valid_indices = np.where(xf > 5)[0]
        peak_idx = valid_indices[np.argmax(amplitude[valid_indices])]
        dominant_freq = xf[peak_idx]

        print(f"Dominant frequency: {dominant_freq:.1f} Hz")

        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        plt.plot(t, valid_data, linewidth=1)
        plt.title("Time Domain: Optical Signal")
        plt.xlabel("Time [s]")
        plt.ylabel("ADC Value (0-1023)")
        plt.grid(True)

        plt.subplot(1, 2, 2)
        plt.plot(xf, amplitude, linewidth=1.5)
        plt.axvline(dominant_freq, linestyle="--", label=f"Peak: {dominant_freq:.1f} Hz")
        plt.title("Frequency Domain: FFT Spectrum")
        plt.xlabel("Frequency [Hz]")
        plt.ylabel("Amplitude")
        plt.legend()
        plt.grid(True)

        plt.tight_layout()

        filename = f"fft_result_{time.strftime('%H%M%S')}.png"
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        print(f"Graph saved as: {filename}")
        plt.show()

    except Exception as exc:
        print(f"Connection failed: {exc}")


if __name__ == "__main__":
    capture_and_analyze()
