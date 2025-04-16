"""Analyze and plot the McKenna burner simulation and experimental data."""
import platform
import os
import argparse
import yaml
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
import numpy as np

sys_name = platform.system()

M_TO_MM = 1000.0

RC_PARAMS = {
    "font.size": 18 if sys_name == "Darwin" else 16,
    "font.family": "Avenir" if sys_name == "Darwin" else "Montserrat",
    "axes.linewidth": 2,
    "lines.linewidth": 2,
    "xtick.direction": "in",
    "xtick.major.width": 2,
    "xtick.major.size": 4,
    "xtick.minor.size": 3,
    "ytick.direction": "in",
    "ytick.major.width": 2,
    "ytick.major.size": 4,
    "ytick.minor.size": 3,
}
plt.rcParams.update(RC_PARAMS)


def load_cantera_csv(file_path: str) -> tuple[list[str], np.ndarray]:
    """Load Cantera .csv data.

    :param file_path: The data file's system path.

    :return: The Cantera simulation meta and numerical data stored in the .csv file.
    :rtype: tuple[list[str], np.ndarray]
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r") as f:
        meta = f.readline().strip().split(",")

    data = np.genfromtxt(file_path, delimiter=",", skip_header=1)

    return meta, data


def plot_data(datasets: dict, plot_config: dict):
    """Plot the numerical and experimental McKenna burner data.

    :param datasets: The Cantera datasets to be plotted.
    :param plot_config: Plot configurations.
    """
    fig = plt.figure(figsize=(3, 3))
    ax1 = fig.add_axes((0, 0, 1, 1))

    handles = []
    labels = []
    for dataset in datasets:
        meta, data = load_cantera_csv(dataset["file_path"])
        idxx = meta.index("grid")
        idyy = meta.index("T")
        x, y = data[:, idxx], data[:, idyy]

        handles.append(
            ax1.plot(
                x * M_TO_MM,
                y,
                label=dataset.get("label", "Dataset"),
                color=dataset.get("color", 'k'),
                linestyle=dataset.get("linestyle", "-"),
                marker=dataset.get("marker", None),
                markevery=dataset.get("markevery", None),
            )[0]
        )
        labels.append(dataset.get("label", "data"))

    ax1.xaxis.set_major_locator(MultipleLocator(5))
    ax1.yaxis.set_major_locator(MultipleLocator(250))
    ax1.tick_params(axis="x", pad=10)
    ax1.tick_params(axis="y", pad=10)
    ax1.set_xlim(plot_config.get("x_lim", [0, 20]))
    ax1.set_ylim(plot_config.get("y_lim", [300, 1750]))
    ax1.set_xlabel(plot_config.get("x_label", "X-Axis"), labelpad=10)
    ax1.set_ylabel(plot_config.get("y_label", "Y-Axis"), labelpad=10)

    if plot_config.get("grid", True):
        ax1.grid(True, color=plot_config.get("grid_color", "gray"), alpha=plot_config.get("grid_alpha", 1))

    ax1.legend(
        handles,
        labels,
        loc=plot_config.get("legend_loc", "lower center"),
        fontsize=plot_config.get("legend_fontsize", 18 if sys_name == "Darwin" else 16),
        edgecolor="k",
        facecolor="white",
        framealpha=1
    )

    output_file = plot_config.get("output_file", "output_plot.png")
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Plot saved to {output_file}")


def main(config_file: str):
    """Provide an alternative main entry point.

    :param config_file: The configuration file's system path.
    """
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    plot_data(config["datasets"], config["plot_config"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="McKenna burner data plotter")
    parser.add_argument(
        "--config", type=str, required=True, help="Path to the YAML configuration file"
    )
    args = parser.parse_args()

    main(args.config)
