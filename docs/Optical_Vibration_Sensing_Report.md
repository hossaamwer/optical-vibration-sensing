# Non-Contact Optical Vibration Sensing

**Frequency Analysis Using Reflected Laser Light, Embedded Data Acquisition and FFT**  
Experimental Project Report  
**Hossam Ahmed — GIU Berlin — October 2026**

---

## Abstract

This project investigates a low-cost, non-contact optical method for measuring mechanical vibration frequencies from reflected laser light. A continuous laser beam is directed onto a vibrating target and the reflected beam is received by a light-sensitive detector. Small mechanical motion produces measurable variations in received optical intensity. The detector signal is amplified using an NPN transistor stage, sampled by an Arduino Uno at a nominal 1 kHz rate, buffered locally to avoid serial-timing disturbances, transferred to Python, and transformed from the time domain into the frequency domain using the Fast Fourier Transform (FFT).

With 550 stored samples and the first 50 discarded during analysis, 500 samples remain for the FFT. At a nominal 1 kHz sampling rate, this gives a 2 Hz FFT bin spacing and a theoretical Nyquist frequency of 500 Hz. The 2 Hz value is a spectral-bin spacing, not a calibrated ±2 Hz absolute accuracy specification.

The prototype was evaluated using four experimental cases: a cantilevered ruler, the same ruler with an added €2 coin, a DC motor, and a piezo/buzzer excitation source. The ruler produced a dominant component at 16 Hz, the loaded-ruler experiment produced a dominant component at 14 Hz, the motor produced a dominant component around 52 Hz with higher-order components near 104 Hz and 156 Hz, and a 125 Hz commanded piezo/buzzer excitation was recovered at the nearest 124 Hz FFT bin.

The development process also exposed real measurement challenges including limited ADC headroom, a small useful optical signal swing, alignment sensitivity, startup transients, high-value loading effects, and a strong 50 Hz mains-related component. Grounded conductive shielding reduced the observed 50 Hz interference by approximately 70% in the tested configuration.

The project is intentionally presented as an experimental optical frequency-sensing demonstrator rather than a calibrated laser vibrometer.

---

## 1. Motivation and Objectives

Mechanical vibration contains useful information about the dynamic behavior of structures and machines. Resonant frequencies can change when mass, stiffness, boundary conditions, or operating conditions change. Conventional measurements often use contact sensors such as accelerometers. Optical sensing provides another approach: motion can be inferred from changes in light without attaching an electrical sensor directly to the measured object.

The objective of this project was to investigate how far a simple optical system could be pushed using inexpensive components and software-based analysis. The project focused on:

- converting small mechanical vibration into measurable optical-intensity variation,
- acquiring the detector signal at a controlled and repeatable sample rate,
- extracting dominant vibration frequencies using frequency-domain analysis,
- testing the same measurement chain on multiple physical systems,
- investigating interference, detector limitations, transient behavior, and alignment,
- documenting both successful measurements and engineering limitations.

The system was developed iteratively: observe a problem, form a hypothesis, modify the hardware or software, and retest.

---

## 2. Measurement Principle

The system uses a reflected-light / optical-lever style principle.

```mermaid
flowchart LR
    A[Mechanical vibration] --> B[Reflected beam position / coupling changes]
    B --> C[Received optical intensity changes]
    C --> D[Photodiode + NPN amplification]
    D --> E[Arduino ADC sampling]
    E --> F[Buffered sample block]
    F --> G[Python]
    G --> H[DC removal + FFT]
    H --> I[Dominant mechanical frequency]
```

### 2.1 Knife-edge alignment

A key practical improvement was to avoid placing the reflected laser spot fully inside the detector's sensitive area. If the entire spot stays on the detector, a small beam displacement may produce very little change in total received optical power.

Instead, the beam was positioned close to the edge of the detector's active region. In this knife-edge arrangement, a small displacement causes a larger change in the fraction of optical power reaching the detector, increasing sensitivity to vibration.

### 2.2 What the prototype measures

The prototype primarily measures **frequency**, not absolute displacement. The ADC amplitude depends on detector responsivity, optical alignment, reflectivity, distance, ambient light, transistor operating point, and the electrical front end.

For this reason, ADC amplitude is treated as a relative optical signal. The most reliable extracted quantity is the frequency of repeatable signal variation.

---

## 3. Hardware and Electrical Connections

### 3.1 Main components

| Component | Role |
|---|---|
| Three-pin laser module | Continuous optical source |
| Photodiode / optical receiver | Detects reflected optical intensity |
| NPN transistor stage | Amplifies the weak detector signal |
| Arduino Uno | ADC acquisition, timing, buffering and serial transfer |
| Breadboard and jumper wiring | Prototype interconnection |
| Grounded aluminum shield | Experimental EMI shielding |
| Metal ruler | Cantilever resonance test object |
| €2 coin | Added tip mass for qualitative loading test |
| DC motor | Periodic rotating / vibrating test source |
| Piezo / buzzer | Controlled excitation reference |
| Laptop with Python | Data capture, FFT analysis and plotting |

### 3.2 Arduino connections

| Function | Arduino connection | Notes |
|---|---|---|
| Laser signal/control | D9 | Held HIGH for a continuous beam |
| Laser supply | 5 V | Three-pin laser module supply |
| Laser ground | GND | Common reference |
| Detector / amplifier output | A0 | Analog vibration signal |
| Piezo / buzzer | D8 | Used only for controlled validation |
| Shield reference | GND | Grounded aluminum shielding |

The implemented optical detector branch uses the photodiode together with an NPN transistor amplification stage before the Arduino analog input.

See [`hardware/electrical_schematic.svg`](../hardware/electrical_schematic.svg) for the repository schematic.

### 3.3 Usable signal swing and ADC headroom

In many measurements, vibration-related changes were only about 10–20 ADC counts while the operating point could sit close to the upper end of the Arduino's 0–1023 ADC range. This limited available headroom and made the measurement sensitive to noise, clipping, and optical alignment.

Because of this limitation, the project relies more strongly on repeatable frequency-domain behavior than on absolute amplitude accuracy.

---

## 4. Embedded Data Acquisition

The acquisition firmware was designed so serial communication does not disturb the time-critical sampling loop.

Instead of printing each ADC sample immediately, the Arduino first stores a complete block in RAM and transmits the block only after acquisition is complete.

### 4.1 Sampling strategy

- nominal sampling interval: **1000 µs**
- nominal sampling frequency: **1 kHz**
- stored samples: **550**
- analyzed samples: **500**
- serial baud rate: **115200**

The timing loop uses an accumulated target time:

```cpp
unsigned long nextSampleTime = micros();

for (int i = 0; i < numSamples; i++) {
    while (micros() - nextSampleTime < sampleInterval) {}
    nextSampleTime += sampleInterval;
    samples[i] = analogRead(analogPin);
}
```

Using `nextSampleTime += sampleInterval` is preferable to adding a simple `delay(1)` after each conversion because the intended schedule does not deliberately accumulate ADC execution time into every interval.

The rate is described as **nominally 1 kHz**, not perfectly calibrated 1 kHz, because `micros()` timing and `analogRead()` execution were not independently verified using laboratory timing equipment.

### 4.2 Transient rejection

Before the stored acquisition begins, the firmware performs 50 dummy ADC reads to allow the detector / ADC input to settle.

The Python script then discards the first 50 stored samples. This leaves 500 samples for analysis and reduces startup / settling artifacts.

### 4.3 Nyquist limit

For a nominal sampling frequency of 1000 Hz:

\[
f_N = \frac{F_s}{2} = \frac{1000}{2} = 500\ \text{Hz}
\]

This 500 Hz value is the theoretical Nyquist boundary. It does **not** mean that every vibration up to 500 Hz is measured with equal quality. Detector bandwidth, analog response, aliasing, signal-to-noise ratio, timing uncertainty and behavior close to Nyquist all matter.

---

## 5. Signal Processing and FFT Analysis

Python is used to trigger a capture, receive the 550 ADC samples, discard the initial transient region, remove the DC component, compute the FFT, select the strongest component above 5 Hz, and save a plot.

### 5.1 DC removal

The average optical level is removed before the FFT:

```python
signal = np.array(valid_data, dtype=float)
signal = signal - np.mean(signal)
```

This suppresses the large DC component associated with average received optical power and leaves the changing part of the signal for frequency analysis.

### 5.2 Frequency resolution

For 500 analyzed samples at 1000 Hz:

\[
\Delta f = \frac{F_s}{N} = \frac{1000}{500} = 2\ \text{Hz}
\]

Therefore, FFT bins are separated by 2 Hz. This is a property of the chosen acquisition window, not an independently calibrated ±2 Hz absolute measurement accuracy.

### 5.3 Peak selection

The Python analysis ignores frequencies at or below 5 Hz when choosing the dominant peak. This reduces the chance that slow drift or residual startup behavior is reported as the vibration frequency.

The selected FFT peak is still interpreted together with repeated measurements and the time-domain waveform.

---

## 6. Experimental Results

### 6.1 Summary

| Experiment | Dominant measured component | Interpretation |
|---|---:|---|
| Cantilever ruler | **16 Hz** | Dominant mechanical vibration component |
| Ruler + €2 coin | **14 Hz** | Qualitative added-mass shift; noisier test |
| DC motor | **52 Hz** | Dominant periodic component |
| Piezo / buzzer | **124 Hz** | Nearest 2 Hz FFT bin to commanded 125 Hz |

### 6.2 Cantilevered ruler

A metal ruler was clamped so a free section could oscillate as a cantilever. The ruler was displaced and released, creating a decaying vibration. The reflected laser beam was aligned near the detector edge and the resulting optical signal was processed using the same acquisition and FFT pipeline.

**Final reported dominant component: 16 Hz.**

### 6.3 Added-mass test

A €2 coin was attached near the free end of the ruler. For a simplified oscillator, increasing effective mass is expected to reduce natural frequency if stiffness and boundary conditions remain approximately unchanged.

The dominant FFT bin shifted from **16 Hz to 14 Hz**. The loaded test was less clean than the unloaded case, and the observed shift corresponds to only one 2 Hz FFT bin. Therefore, this result is treated as a qualitative structural-loading experiment rather than a precision measurement of the resonance shift.

### 6.4 DC motor

The same optical measurement chain was used on a DC motor. A dominant spectral component around **52 Hz** was detected together with higher-order components near **104 Hz** and **156 Hz**.

If one optical modulation cycle corresponds to one complete revolution, 52 Hz would correspond to:

\[
RPM \approx 52 \times 60 = 3120\ \text{RPM}
\]

However, that RPM interpretation is valid only if the optical geometry creates exactly one bright/dark modulation cycle per revolution. The directly measured result is the 52 Hz optical modulation component.

### 6.5 Piezo / buzzer validation

A controlled piezo/buzzer excitation was commanded at **125 Hz**.

The analysis reported **124 Hz**. This is consistent with the 2 Hz FFT bin spacing because 125 Hz lies between available 124 Hz and 126 Hz bins.

The buzzer line is commented out by default in the repository firmware and should be enabled only when reproducing this controlled validation test.

---

## 7. Engineering Challenges and Troubleshooting

### 7.1 Limited usable signal swing

**Observation:** vibration-related signal changes were often only around 10–20 ADC counts and the baseline could approach the top of the 10-bit ADC range.

**Response:** improve optical sensitivity using knife-edge alignment and focus interpretation on repeatable frequency-domain behavior rather than absolute amplitude.

**Remaining limitation:** amplitude calibration remains poor and the detector front end needs redesign for quantitative measurement.

### 7.2 50 Hz mains-related component

A strong component at 50 Hz repeatedly appeared in the measurement environment. Higher-frequency components were also sometimes visible.

Possible coupling paths include electrical pickup in high-impedance wiring and optical modulation from room lighting. Grounded conductive shielding around the receiver and sensitive wiring reduced the observed 50 Hz component by approximately 70% in the tested configuration.

The shielding result supports the presence of electrical coupling, but does not prove that electrical pickup was the only source.

### 7.3 Higher-order spectral components

The detector signal was amplified using an NPN transistor. During interference tests, higher-order spectral components were observed.

Possible contributors include:

- nonlinear transistor operation,
- clipping,
- non-sinusoidal electrical pickup,
- lighting modulation,
- interaction between several interference paths.

Because these mechanisms were not independently isolated, the report does not assign the observed harmonics to a single cause.

### 7.4 High-value loading experiments

Several resistor / loading configurations were tested around the detector stage. Higher resistance values increased sensitivity to noise and parasitic effects and degraded the useful vibration signal.

The problematic loading arrangement was removed in the working configuration.

### 7.5 Startup / low-frequency artifacts

Early samples could contain settling behavior that created misleading low-frequency FFT energy.

The implemented solution combined:

- 50 dummy ADC reads before acquisition,
- capturing 550 samples,
- discarding the first 50 stored samples in Python.

### 7.6 Optical alignment sensitivity

Small movements of the laser, target or detector could strongly change signal amplitude. The knife-edge arrangement improved sensitivity but also made mechanical stability important.

### 7.7 Serial timing risk

Printing every sample during acquisition would introduce timing disturbances. The final firmware buffers the sample block first and transmits it only after acquisition.

---

## 8. Limitations and Measurement Uncertainty

The current prototype successfully recovers useful frequency information, but it is not a calibrated vibration instrument.

Main limitations are:

- no absolute displacement calibration,
- small usable optical signal swing and limited ADC headroom,
- no dedicated low-noise transimpedance amplifier,
- no analog anti-aliasing filter,
- nominal `micros()`-based sampling rather than externally validated hardware-timer sampling,
- finite FFT record length,
- strong sensitivity to alignment and ambient illumination,
- unresolved optical-vs-electrical contributions to the 50 Hz interference,
- motor RPM interpretation dependent on optical events per revolution.

---

## 9. Future Improvements

The prototype can be upgraded significantly while keeping the same basic optical measurement principle.

### Dedicated photodiode transimpedance amplifier

A designed TIA would provide predictable current-to-voltage conversion, controlled bandwidth, better sensitivity and improved noise performance.

### Improved ADC headroom

Biasing the analog signal near mid-supply would reduce clipping risk and make better use of the ADC range.

### Differential / split photodetection

Using two photodiodes, a quadrant detector, or a position-sensitive detector would allow differential measurement of beam motion and improve rejection of common-mode optical intensity variation.

### Analog anti-aliasing

A low-pass filter before the ADC would suppress out-of-band components that could alias into the measured spectrum.

### Hardware-timed acquisition

Timer-triggered ADC acquisition would provide a more accurately defined sampling frequency and reduce timing jitter.

### Higher-resolution ADC

A 12- or 16-bit ADC could resolve smaller optical changes once the analog front end is properly designed.

### Longer acquisition windows

Increasing the number of analyzed samples would improve FFT bin spacing for the same sampling frequency.

### Windowing and peak interpolation

A Hann window and sub-bin peak estimation could improve spectral interpretation when a vibration lies between FFT bins.

### Controlled interference experiments

Future tests could independently vary room lighting, shielding geometry, cable length, power source and grounding to isolate 50 Hz coupling mechanisms.

### Absolute calibration

A reference displacement source or calibrated accelerometer / vibrometer could be used to map optical signal amplitude to physical displacement and quantify measurement error.

---

## 10. Relevance to Photonic Sensing and Structural Monitoring

This project is much simpler than professional fiber-optic sensing systems, but it demonstrates a related measurement workflow:

**mechanical quantity → optical modulation → photodetection → electrical acquisition → signal evaluation → physical interpretation**

This workflow is relevant to optical sensing, vibration monitoring, rotating machinery analysis and structural monitoring.

A professional system may use specialized photonic devices, fiber Bragg gratings, multiplexed interrogation, calibrated analog front ends and much more advanced instrumentation. The connection of this project to those systems is conceptual and methodological rather than a claim of equivalent performance.

---

## 11. Conclusion

A low-cost non-contact optical vibration-sensing prototype was designed, built, debugged and tested on several mechanical systems. Reflected laser light was used to convert motion into optical-intensity variation, a photodetector with an NPN amplification stage produced an electrical signal, an Arduino Uno performed nominal 1 kHz block acquisition, and Python/FFT processing extracted dominant frequency components.

The system identified a dominant 16 Hz component from a cantilevered ruler, a 14 Hz component in an exploratory added-mass test, a 52 Hz dominant component from a DC motor, and a 124 Hz FFT bin from a commanded 125 Hz piezo/buzzer validation test.

The project also provided practical experience with optical alignment, photodetection, transistor amplification, ADC acquisition, sampling theory, FFT analysis, interference, grounding, shielding, startup transients and measurement limitations.

The main result is therefore not only the measured frequencies, but the complete experimental engineering workflow: build, observe, analyze, isolate problems, modify hardware/software, retest, and state the remaining limitations.

---

## Repository Files

- Arduino firmware: [`../firmware/optical_vibration_acquisition.ino`](../firmware/optical_vibration_acquisition.ino)
- Python analysis: [`../analysis/capture_and_fft.py`](../analysis/capture_and_fft.py)
- Electrical schematic: [`../hardware/electrical_schematic.svg`](../hardware/electrical_schematic.svg)
