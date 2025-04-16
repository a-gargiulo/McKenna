"""UVA McKenna Burner Simulation."""
from pathlib import Path
from typing import Dict, Union, cast

import cantera as ct
import numpy as np

BoundaryConditions = Dict[str, Union[int, float, str, Dict[str, float]]]
Models = Dict[str, Union[bool, str]]
Settings = Dict[str, Dict[str, Union[int, float]]]

# McKenna Burner Geometry
D_CORE_M = 60.452e-03
A_CORE_M2 = D_CORE_M**2 * np.pi / 4
HAB_STAGNATION_M = 0.020


def slpm_to_ndot(slpm: float) -> float:
    """Convert volumetric flow rate to molar flow rate.

    The function converts from slpm to mol/s, assuming ideal gas behavior.

    :param slpm: Volumetric flow rate in slpm.

    :return: Molar flow rate in mol/s.
    :rtype: float
    """
    return (slpm * 0.001 * 1e5) / (60 * 8.314 * 273.15)


def check_models(md: Models) -> bool:
    """Check if the models dictionary is structured correctly.

    :param md: Models dictionary.

    :return: Boolean 'False' in case of an error or 'True' otherwise.
    :rtype: bool
    """
    if not isinstance(md, dict):
        print("[ERROR]: Models should be a dictionary.")
        return False

    required_fields = {
        "radiation": bool,
        "transport": str,
        "soret": bool,
    }
    for field, expected_type in required_fields.items():
        if field not in md:
            print(f"[ERROR]: '{field}' is missing in the models.")
            return False
        if not isinstance(md[field], expected_type):
            print(
                f"[ERROR]: '{field}' should be of type {expected_type}, but got {type(md[field])}."
            )
            return False

    return True


def check_simulation_settings(simsets: Settings) -> bool:
    """Check if the simulation settings dictionary is structured correctly.

    :param simsets: Simulation settings.

    :return: Boolean 'False' in case of an error or 'True' otherwise.
    :rtype: bool
    """
    if not isinstance(simsets, dict):
        print("[ERROR]: Simulation settings should be a dictionary.")
        return False

    for field in ["general", "meshing"]:
        if field not in simsets:
            print(f"[ERROR]: '{field}' is missing in the simulation settings.")
            return False
        if not isinstance(simsets[field], dict):
            print(
                f"[ERROR]: '{field}' should be of type dict, but got {type(simsets[field])}."
            )
            return False

    general_fields = ["grid_min", "max_grid_points"]
    mesh_fields = ["ratio", "slope", "curve", "prune"]

    for field in general_fields:
        if field not in simsets["general"]:
            print(f"[ERROR]: '{field}' is missing in general settings.")
            return False
        if not isinstance(simsets["general"][field], (int, float)):
            print(
                f"[ERROR]: '{field}' should be of type int or float, but got {type(simsets['general'][field])}."
            )
            return False

    for field in mesh_fields:
        if field not in simsets["meshing"]:
            print(f"[ERROR]: '{field}' is missing in meshing settings.")
            return False
        if not isinstance(simsets["meshing"][field], (int, float)):
            print(
                f"[ERROR]: '{field}' should be of type int or float, but got {type(simsets['meshing'][field])}."
            )
            return False

    return True


def check_boundary_conditions(bc: BoundaryConditions) -> bool:
    """Check if the boundary conditions dictionary is structured correctly.

    :param bc: Boundary conditions.

    :return: Boolean 'False' in case of an error or 'True' otherwise.
    :rtype: bool
    """
    if not isinstance(bc, dict):
        print("[ERROR]: Boundary conditions should be a dictionary.")
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
            print(f"[ERROR]: '{field}' is missing in the boundary conditions.")
            return False
        if not isinstance(bc[field], expected_type):
            print(
                f"[ERROR]: '{field}' should be of type {expected_type}, but got {type(bc[field])}."
            )
            return False

    for key, value in cast(dict, bc["Vdot_burner_slpm"]).items():
        if not isinstance(value, (int, float)):
            print(
                f"[ERROR]: Value for '{key}' in 'Vdot_burner_slpm' should be int or float, but got {type(value)}."
            )
            return False

    for key, value in cast(dict, bc["M_kg_mol"]).items():
        if not isinstance(value, (int, float)):
            print(
                f"[ERROR]: Value for '{key}' in 'M_kg_mol' should be int or float, but got {type(value)}."
            )
            return False

    if cast(dict, bc["Vdot_burner_slpm"]).keys() != cast(dict, bc["M_kg_mol"]).keys():
        print("[ERROR]: The elements of 'Vdot_burner_slpm' and 'M_kg_mol' must match.")
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

    :return: Boolean 'False' in case of an error or 'True' otherwise.
    :rtype: bool
    """
    if not isinstance(mode, str):
        print(f"[ERROR]: 'mode' should be of type str, but got {type(mode)}.")
        return False

    if not isinstance(rxnmech, str):
        print(f"[ERROR]: 'rxnmech' should be of type str, but got {type(rxnmech)}.")
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

    gas = ct.Solution(rxnmech)
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
        sim.domains[sim.domain_index("flame")], simsets["general"]["max_grid_points"]
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

    sim.save(output_path / output_file_name, basis="mole", overwrite=True)

    sim.show_stats()

    return True


if __name__ == "__main__":
    mode = "free"  # "free" / "jet"

    rxnmech = "./FFCM-2/FFCM-2.yaml"  # reaction mechanism file

    # bc = {
    #     "p_pa": 101325,
    #     "T_burner_K": 350,
    #     "X_burner": "C2H4:1, O2:3, N2:11.29",
    #     "phi": 1.0,
    #     "Vdot_burner_slpm": {"C2H4": 0.652, "Air": 9.35},
    #     "M_kg_mol": {"C2H4": 28.05336e-03, "Air": 28.97e-03},
    #     "T_stagnation_K": 345.15,
    # }

    bc = {
        "p_pa": 101325,
        "T_burner_K": 350,
        "X_burner": "C2H4:1, O2:1.5, N2:5.64",
        "phi": 2.0,
        "Vdot_burner_slpm": {"C2H4": 1.22, "Air": 8.78},
        "M_kg_mol": {"C2H4": 28.05336e-03, "Air": 28.97e-03},
        "T_stagnation_K": 393.15,
    }

    models = {
        "radiation": True,
        "transport": "multicomponent",  # 'multicomponent', 'mixture-averaged'
        "soret": True,
    }

    simsets = {
        "general": {
            "grid_min": 1e-7,
            "max_grid_points": 1e4,
        },
        "meshing": {"ratio": 2, "slope": 0.015, "curve": 0.022, "prune": 0.0},
    }

    run_sim(mode, rxnmech, bc, models, simsets)
