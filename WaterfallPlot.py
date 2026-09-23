from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

OUTPUT_DIR = Path("Waterfalls")
OUTPUT_DIR.mkdir(exist_ok=True)

FILES = [
    {
        "path": Path(r"Decoded\Authentic\waterfall.dat"),
        "title": "Authentic replay",
        "fmin": -8.0,
        "fmax": 8.0,
        "full": {
            "tmin": 0.0,
            "tmax": 704.0,
            "out": OUTPUT_DIR / "AuthenticWaterfallFull.png",
        },
        "cropped": {
            "tmin": 100.0,
            "tmax": 300.0,
            "out": OUTPUT_DIR / "AuthenticWaterfallCropped.png",
        },
    },
    {
        "path": Path(r"Decoded\Reconstructed\waterfall.dat"),
        "title": "Reconstructed replay",
        "fmin": -8.0,
        "fmax": 8.0,
        "full": {
            "tmin": 0.0,
            "tmax": 31.0,
            "out": OUTPUT_DIR / "ReconstructedWaterfallFull.png",
        },
        "cropped": {
            "tmin": 6.0,
            "tmax": 12.0,
            "out": OUTPUT_DIR / "ReconstructedWaterfallCropped.png",
        },
    },
]

def read_waterfall(path):

    with open(path, mode="rb") as datafile:

        metadata = {
            "timestamp": np.fromfile(
                datafile, dtype="|S32", count=1
            )[0].decode("utf-8"),

            "nchan": np.fromfile(
                datafile, dtype=">i4", count=1
            )[0],

            "samp_rate": np.fromfile(
                datafile, dtype=">i4", count=1
            )[0],

            "nfft_per_row": np.fromfile(
                datafile, dtype=">i4", count=1
            )[0],

            "center_freq": np.fromfile(
                datafile, dtype=">f4", count=1
            )[0],

            "endianness": np.fromfile(
                datafile, dtype="<i4", count=1
            )[0],
        }

        dtype_prefix = "<" if metadata["endianness"] else ">"

        data_dtypes = np.dtype([
            ("tabs", dtype_prefix + "i8"),
            ("spec", dtype_prefix + "f4", (metadata["nchan"],))
        ])

        waterfall = np.fromfile(
            datafile,
            dtype=data_dtypes
        )

    spec = waterfall["spec"]

    tabs = (
        waterfall["tabs"].astype(np.float64)
        / 1_000_000.0
    )

    tabs = tabs - tabs[0]

    freq = np.linspace(
        -0.5 * metadata["samp_rate"],
        0.5 * metadata["samp_rate"],
        metadata["nchan"],
        endpoint=False
    ) / 1000.0

    return tabs, freq, spec, metadata


plots = []

for item in FILES:

    tabs, freq, spec, metadata = read_waterfall(
        item["path"]
    )

    fmask = (
        (freq >= item["fmin"])
        & (freq <= item["fmax"])
    )

    freq_plot = freq[fmask]

    for version in ["full", "cropped"]:

        config = item[version]

        tmask = (
            (tabs >= config["tmin"])
            & (tabs <= config["tmax"])
        )

        tabs_plot = tabs[tmask]

        spec_plot = spec[np.ix_(tmask, fmask)]

        valid = (
            np.isfinite(spec_plot)
            & (spec_plot > -200.0)
        )

        values = spec_plot[valid]

        low = np.percentile(values, 1.0)
        high = np.percentile(values, 99.9)

        plots.append({
            "title": item["title"],
            "version": version,
            "tabs": tabs_plot,
            "freq": freq_plot,
            "spec": spec_plot,
            "out": config["out"],
            "fmin": item["fmin"],
            "fmax": item["fmax"],
            "low": low,
            "high": high,
        })


vmin = min(plot["low"] for plot in plots)
vmax = max(plot["high"] for plot in plots)

vmin = np.floor(vmin)
vmax = np.ceil(vmax)


for plot in plots:

    fig, ax = plt.subplots(
        figsize=(12, 5.4),
        dpi=200
    )

    im = ax.imshow(
        plot["spec"].T,
        origin="lower",
        aspect="auto",
        interpolation="none",
        extent=[
            plot["tabs"][0],
            plot["tabs"][-1],
            plot["freq"][0],
            plot["freq"][-1]
        ],
        vmin=vmin,
        vmax=vmax,
        cmap="viridis"
    )

    ax.set_title(
        plot["title"],
        fontsize=16
    )

    ax.set_xlabel(
        "Relative time (s)",
        fontsize=13
    )

    ax.set_ylabel(
        "Relative frequency (kHz)",
        fontsize=13
    )

    ax.tick_params(
        axis="both",
        labelsize=11
    )

    ax.set_ylim(
        plot["fmin"],
        plot["fmax"]
    )

    cbar = fig.colorbar(
        im,
        ax=ax
    )

    cbar.set_label(
        "Power (dB)",
        fontsize=13
    )

    cbar.ax.tick_params(
        labelsize=11
    )

    plt.tight_layout()

    fig.savefig(
        plot["out"],
        dpi=1200,
        bbox_inches="tight",
        pad_inches=0.05,
        facecolor="white"
    )

    print(f"Saved: {plot['out']}")

    plt.show()

    plt.close(fig)