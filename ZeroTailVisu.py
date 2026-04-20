from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


RAW_PATH = Path(r"Knacksat2_13753740_replayed_iq_out\Knacksat2_13753740_replayed_cf32.raw")
SAMPLE_RATE = 78125.0
VIEW_LAST_SEC = 0.15
ZERO_THRESHOLD = 1e-12


iq = np.fromfile(RAW_PATH, dtype=np.complex64)
mag = np.abs(iq)

nonzero_idx = np.where(mag > ZERO_THRESHOLD)[0]
last_nonzero = nonzero_idx[-1]
zero_tail_start = last_nonzero + 1

zero_tail_len_samples = len(iq) - zero_tail_start
zero_tail_len_sec = zero_tail_len_samples / SAMPLE_RATE

n_view = int(VIEW_LAST_SEC * SAMPLE_RATE)
start_idx = max(0, len(iq) - n_view)
end_idx = len(iq)

t = np.arange(start_idx, end_idx) / SAMPLE_RATE
mag_view = mag[start_idx:end_idx]

zero_tail_start_t = zero_tail_start / SAMPLE_RATE
file_end_t = len(iq) / SAMPLE_RATE

fig, ax = plt.subplots(figsize=(6.5, 6.5))
ax.plot(t, mag_view, linewidth=1.2, color="black")
ax.axvline(
    zero_tail_start_t,
    linestyle="--",
    linewidth=1.2,
    color="red",
    label="Start of zero tail"
)
ax.axvspan(
    zero_tail_start_t,
    file_end_t,
    alpha=0.15,
    color="gray",
    label="Zero tail"
)

ax.set_xlabel("Time (s)")
ax.set_ylabel("Magnitude |IQ|")

ax.grid(True, which="both", linestyle=":", linewidth=0.7, alpha=0.8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.margins(x=0.01)

annotation_text = (
    f"Zero tail length = {zero_tail_len_sec:.3f} s\n"
    f"({zero_tail_len_samples} samples)"
)
ax.text(
    0.98, 0.95,
    annotation_text,
    transform=ax.transAxes,
    ha="right",
    va="top",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9, edgecolor="black")
)

ax.legend(loc="lower left")

plt.tight_layout()
plt.show()