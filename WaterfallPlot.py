from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


FILES = [
    {
        "path": Path(r"Decoded\Authentic\waterfall.dat"),
        "title": "Authentic replay",
        "tmin": 100.0,  
        "tmax": 300.0,
        "fmin": -8.0,
        "fmax": 8.0,
        "out": Path("AuthenticWaterfall.png"),
    },
    {
        "path": Path(r"Decoded\Reconstructed\waterfall.dat"),
        "title": "Reconstructed replay",
        "tmin": 0,
        "tmax": 15.0,
        "fmin": -8.0,
        "fmax": 8.0,
        "out": Path("ReconstructedWaterfall.png"),
    },
]


def read_waterfall_official_style(path):
    with open(path, mode="rb") as datafile:
        metadata = {
            "timestamp": np.fromfile(datafile, dtype="|S32", count=1)[0].decode("utf-8"),
            "nchan": np.fromfile(datafile, dtype=">i4", count=1)[0],
            "samp_rate": np.fromfile(datafile, dtype=">i4", count=1)[0],
            "nfft_per_row": np.fromfile(datafile, dtype=">i4", count=1)[0],
            "center_freq": np.fromfile(datafile, dtype=">f4", count=1)[0],
            "endianness": np.fromfile(datafile, dtype="<i4", count=1)[0],
        }

        dtype_prefix = "<" if metadata["endianness"] else ">"
        data_dtypes = np.dtype([
            ("tabs", dtype_prefix + "i8"),
            ("spec", dtype_prefix + "f4", (metadata["nchan"],))
        ])

        waterfall = np.fromfile(datafile, dtype=data_dtypes)

    spec = waterfall["spec"]
    tabs = waterfall["tabs"].astype(np.float64) / 1_000_000.0
    tabs = tabs - tabs[0]

    freq = np.linspace(
        -0.5 * metadata["samp_rate"],
        0.5 * metadata["samp_rate"],
        metadata["nchan"],
        endpoint=False
    ) / 1000.0

    return tabs, freq, spec, metadata


for item in FILES:
    tabs, freq, spec, metadata = read_waterfall_official_style(item["path"])

    tmask = np.ones_like(tabs, dtype=bool)
    if item["tmin"] is not None:
        tmask &= tabs >= item["tmin"]
    if item["tmax"] is not None:
        tmask &= tabs <= item["tmax"]

    tabs_plot = tabs[tmask]
    spec_plot = spec[tmask]

    valid = spec_plot > -200.0
    if np.sum(valid) > 100:
        data_mean = np.mean(spec_plot[valid])
        data_std = np.std(spec_plot[valid])
        vmin = data_mean - 2.0 * data_std
        vmax = data_mean + 6.0 * data_std
    else:
        vmin = np.percentile(spec_plot, 5)
        vmax = np.percentile(spec_plot, 99.5)

    fig, ax = plt.subplots(figsize=(10, 4.5))

    im = ax.imshow(
        spec_plot.T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        extent=[tabs_plot[0], tabs_plot[-1], freq[0], freq[-1]],
        vmin=vmin,
        vmax=vmax,
        cmap="viridis"
    )

    ax.set_title(item["title"])
    ax.set_xlabel("Relative time (s)")
    ax.set_ylabel("Relative frequency (kHz)")
    ax.set_ylim(item["fmin"], item["fmax"])

    fig.colorbar(im, ax=ax, label="Power (dB)")
    plt.tight_layout()

    fig.savefig(item["out"], dpi=1200, bbox_inches="tight")
    plt.show()
    plt.close(fig)