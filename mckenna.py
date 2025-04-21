"""UVA McKenna Burner Simulation."""

import argparse
import os
import platform
from pathlib import Path
from typing import Dict, Union, cast

import cantera as ct
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.ticker import MultipleLocator

sys_name = platform.system()

BoundaryConditions = Dict[str, Union[int, float, str, Dict[str, float]]]
Models = Dict[str, Union[bool, str]]
Settings = Dict[str, Dict[str, Union[int, float]]]

# Constants
D_CORE_M = 60.452e-03
A_CORE_M2 = D_CORE_M**2.0 * np.pi / 4.0
HAB_STAGNATION_M = 0.020
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


def slpm_to_ndot(slpm: float) -> float:
    """Convert a volumetric flow rate (slpm) to a molar flow rate (mol/s).

    This function assumes ideal gas behavior.

    :param slpm: Volumetric flow rate, slpm.

    :return: Molar flow rate, mol/s.
    :rtype: float
    """
    return (slpm * 0.001 * 1.0e+05) / (60.0 * 8.314 * 273.15)


def check_models(md: Models) -> bool:
    """Check the compliance of the models section in config.yaml.

    :param md: Models dictionary.

    :return: True if successful, False otherwise.
    :rtype: bool
    """
    if not isinstance(md, dict):
        print(
            "[ERROR]: The 'models' section in 'config.yaml' should be "
            "structured as a dictionary.")
        return False

    required_fields = {
        "radiation": bool,
        "transport": str,
        "soret": bool,
    }
    for field, expected_type in required_fields.items():
        if field not in md:
            print(f"[ERROR]: '{field}' is missing in the 'models' section.")
            return False
        if not isinstance(md[field], expected_type):
            print(
                f"[ERROR]: '{field}' in the 'models' section of 'config.yaml' "
                f"should be of type {expected_type}, but "
                f"got {type(md[field])}."
            )
            return False

    return True


def check_simulation_settings(simsets: Settings) -> bool:
    """Check the compliance of the settings section in config.yaml.

    :param simsets: Simulation settings.

    :return: True if successful, False otherwise.
    :rtype: bool
    """
    if not isinstance(simsets, dict):
        print(
            "[ERROR]: The 'settings' section in 'config.yaml' should be "
            "structured as a dictionary."
        )
        return False

    for field in ["general", "meshing"]:
        if field not in simsets:
            print(
                f"[ERROR]: '{field}' is missing in the 'settings' section "
                f"of 'config.yaml'."
            )
            return False
        if not isinstance(simsets[field], dict):
            print(
                f"[ERROR]: '{field}' in the 'settings' section of "
                f"'config.yaml' should be of type dict, "
                f"but got {type(simsets[field])}."
            )
            return False

    general_fields = ["grid_min", "max_grid_points"]
    mesh_fields = ["ratio", "slope", "curve", "prune"]

    for field in general_fields:
        if field not in simsets["general"]:
            print(
                f"[ERROR]: '{field}' is missing in the 'general' section "
                f"of the 'settings' section in 'config.yaml'."
            )
            return False
        if not isinstance(simsets["general"][field], (int, float)):
            print(
                f"[ERROR]: '{field}' in the 'general' section of "
                f"the 'settings' section in 'config.yaml' should be of type "
                f"int or float, but got {type(simsets['general'][field])}."
            )
            return False

    for field in mesh_fields:
        if field not in simsets["meshing"]:
            print(
                f"[ERROR]: '{field}' is missing in the 'meshing' section "
                f"of the 'settings' section in 'config.yaml'."
            )
            return False
        if not isinstance(simsets["meshing"][field], (int, float)):
            print(
                f"[ERROR]: '{field}' in the 'meshing' section of "
                f"the 'settings' section in 'config.yaml' should be of type "
                f"int or float, but got {type(simsets['meshing'][field])}."
            )
            return False

    return True


def check_boundary_conditions(bc: BoundaryConditions) -> bool:
    """Check the compliance of the boundary_conditions section in config.yaml.

    :param bc: Boundary conditions.

    :return: True if successful, False otherwise.
    :rtype: bool
    """
    if not isinstance(bc, dict):
        print(
            "[ERROR]: The 'boundary_conditions' section should be a "
            "dictionary."
        )
        return False

    required_fields = {
        "p_pa": (int, float),
        "T_burner_K": (int, float),
        "X_burner": str,
        "phi": float,
        "Vdot_burner_slpm": dict,
        "M_kg_mol": dict,
        "T_stagnation_K": (int, float),
    }
    for field, expected_type in required_fields.items():
        if field not in bc:
            print(
                f"[ERROR]: '{field}' is missing in the 'boundary_conditions' "
                f"section of 'config.yaml'."
            )
            return False
        if not isinstance(bc[field], expected_type):
            print(
                f"[ERROR]: '{field}' in the 'boundary_conditions' section "
                f"in 'config.yaml' should be of type {expected_type}, but "
                f"got {type(bc[field])}."
            )
            return False

    for key, value in cast(dict, bc["Vdot_burner_slpm"]).items():
        if not isinstance(value, (int, float)):
            print(
                f"[ERROR]: Value for '{key}' in the 'Vdot_burner_slpm' "
                f"section of the 'boundary_conditions' section in "
                f"'config.yaml' should be int or float, but got {type(value)}."
            )
            return False

    if (
        cast(dict, bc["Vdot_burner_slpm"]).keys()
        != cast(dict, bc["M_kg_mol"]).keys()
    ):
        print(
            "[ERROR]: Vdot_burner_slpm and M_kg_mol must contain the"
            "same elements."
        )
        return False

    for key in cast(dict, bc["Vdot_burner_slpm"]):
        if type(cast(dict, bc["Vdot_burner_slpm"])[key]) is not type(
            cast(dict, bc["M_kg_mol"])[key]
        ):
            print(
                "[ERROR]: Vdot_burner_slpm and M_kg_mol must have the"
                "same element types."
            )
            return False

    return True


def run_sim(
    mode: str,
    rxnmech: str,
    bc: BoundaryConditions,
    models: Models,
    simsets: Settings,
) -> bool:
    """Run a 1D premixed impinging jet or free flame Cantera simulation.

    :param mode: Calculation mode (impinging jet / free flame).
    :param rxnmech: Path to reaction mechanism file.
    :param bc: Boundary conditions.
    :param models: Models.
    :param simset: Simulation settings.

    :return: True if successful, False otherwise.
    :rtype: bool
    """
    if not isinstance(mode, str):
        print(f"[ERROR]: 'mode' should be of type str, but got {type(mode)}.")
        return False

    if not isinstance(rxnmech, str):
        print(
            f"[ERROR]: 'rxnmech' should be of type str, "
            f"but got {type(rxnmech)}."
        )
        return False

    if not check_boundary_conditions(bc):
        return False

    if not check_models(models):
        return False

    if not check_simulation_settings(simsets):
        return False

    ndot_mol_s = []
    for component, Vdot in cast(dict, bc["Vdot_burner_slpm"]).items():
        ndot_mol_s.append(slpm_to_ndot(Vdot))

    M_kg_mol = []
    for component, M in cast(dict, bc["M_kg_mol"]).items():
        M_kg_mol.append(M)

    mdot_kg_s = []
    for ndot, mw in zip(ndot_mol_s, M_kg_mol):
        mdot_kg_s.append(ndot * mw)

    mass_flux_kg_m2_s = sum(mdot_kg_s) / A_CORE_M2

    gas = ct.composite.Solution(rxnmech)
    gas.TPX = bc["T_burner_K"], bc["p_pa"], bc["X_burner"]

    if mode == "jet":
        sim = ct.ImpingingJet(gas=gas, width=HAB_STAGNATION_M)
        sim.radiation_enabled = models["radiation"]
        sim.transport_model = models["transport"]
        sim.soret_enabled = models["soret"]

        sim.inlet.mdot = mass_flux_kg_m2_s
        sim.inlet.T = bc["T_burner_K"]
        sim.surface.T = bc["T_stagnation_K"]
        sim.set_initial_guess(products="equil")
    elif mode == "free":
        sim = ct.BurnerFlame(gas=gas, width=HAB_STAGNATION_M)
        sim.radiation_enabled = models["radiation"]
        sim.transport_model = models["transport"]
        sim.soret_enabled = models["soret"]

        sim.burner.mdot = mass_flux_kg_m2_s
        sim.burner.T = bc["T_burner_K"]
    else:
        print(f"[ERROR]: The selected simulation mode {mode} is invalid.")
        return False

    loglevel = 1
    sim.set_grid_min(simsets["general"]["grid_min"])
    sim.set_max_grid_points(
        sim.domains[sim.domain_index("flame")],
        simsets["general"]["max_grid_points"],
    )
    sim.set_refine_criteria(
        ratio=simsets["meshing"]["ratio"],
        slope=simsets["meshing"]["slope"],
        curve=simsets["meshing"]["curve"],
        prune=simsets["meshing"]["prune"],
    )

    sim.show()
    sim.solve(loglevel, auto=True)

    output_path = Path() / "data"
    output_path.mkdir(parents=True, exist_ok=True)

    output_file_name = f"{mode}_Tb{bc['T_burner_K']}"
    if mode == "jet":
        output_file_name = output_file_name + f"_Tplate{bc['T_stagnation_K']}"

    if sim.radiation_enabled:
        output_file_name = output_file_name + "_Radiation"
    else:
        output_file_name = output_file_name + "_NoRadiation"

    if sim.transport_model == "multicomponent":
        output_file_name = output_file_name + "_Multicomponent"
    else:
        output_file_name = output_file_name + "_MixtureAveraged"

    if sim.soret_enabled:
        output_file_name = output_file_name + "_Soret"
    else:
        output_file_name = output_file_name + "_NoSoret"

    output_file_name = output_file_name + f"_phi{bc['phi']}.csv"
    output_file_name = (
        "_".join(output_file_name.rsplit(".", 1)[0].split(".")) +
        "." +
        output_file_name.rsplit(".", 1)[1]
    )

    sim.save(output_path / output_file_name, basis="mole", overwrite=True)

    sim.show_stats()

    return True


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
                color=dataset.get("color", "k"),
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
        ax1.grid(
            True,
            color=plot_config.get("grid_color", "gray"),
            alpha=plot_config.get("grid_alpha", 1),
        )

    ax1.legend(
        handles,
        labels,
        loc=plot_config.get("legend_loc", "lower center"),
        fontsize=plot_config.get(
            "legend_fontsize", 18 if sys_name == "Darwin" else 16
        ),
        edgecolor="k",
        facecolor="white",
        framealpha=1,
    )

    output_file = plot_config.get("output_file", "output_plot.png")
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"Plot saved to {output_file}")


def load_cantera_csv(file_path: str) -> tuple[list[str], np.ndarray]:
    """Load Cantera .csv data.

    :param file_path: The data file's system path.

    :return: The Cantera simulation meta and numerical data stored in the .csv
        file.
    :rtype: tuple[list[str], np.ndarray]
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r") as f:
        meta = f.readline().strip().split(",")

    data = np.genfromtxt(file_path, delimiter=",", skip_header=1)

    return meta, data


def main(config_file: str):
    """Provide an alternative main entry point.

    :param config_file: The configuration file's system path.
    """
    with open(config_file, "r") as file:
        config = yaml.safe_load(file)
    if config["simulation"]["active"]:
        run_sim(
            config["simulation"]["mode"],
            config["simulation"]["rxnmech"],
            config["simulation"]["boundary_conditions"],
            config["simulation"]["models"],
            config["simulation"]["settings"],
        )
    if config["plot"]["active"]:
        plot_data(config["plot"]["datasets"], config["plot"]["config"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="McKenna burner simulator")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the YAML configuration file",
    )
    args = parser.parse_args()
    main(args.config)
