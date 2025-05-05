"""UVA McKenna burner Cantera model.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/02/2025 (MM/DD/YYYY)
"""
from typing import Any, Dict, Union
from mckenna import utility
import numpy as np
import cantera as ct


class McKenna()


def run_flame_simulation(inputs: Dict[str, Any]) -> bool:
    """Run a 1D premixed impinging jet or free flame Cantera simulation.

    :param mode: Simulation mode (uq, single)
    :param rxn: Path to reaction mechanism file.
    :param geometry: Model geometry.
    :param bc: Boundary conditions.
    :param submodels: Submodels.
    :param settings: Simulation settings.
    :return: True if successful, False otherwise.
    :rtype: bool
    """
    gas = ct.composite.Solution(inputs[])
    A_core_m2 = inputs["burner_diameter"]**2.0 * np.pi / 4.0
    mass_flux_kg_m2_s = utility.calculate_mass_flux(inputs["flow_rates"], gas, A_core_m2)

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
# # ---------- Flame Simulation Function ----------
# def run_flame_simulation(epistemic_input: Dict, aleatory_input: Dict) -> float:
#     """Runs a 1D premixed flame simulation with given inputs and returns a metric."""
#     phi = epistemic_input["phi"]
#     T0 = aleatory_input["T0"]
#     P0 = aleatory_input["P0"]

#     try:
#         gas = ct.Solution("gri30.yaml")
#         gas.set_equivalence_ratio(phi, "CH4", "O2:1, N2:3.76")
#         gas.TP = T0, P0

#         width = 0.03  # meters
#         flame = ct.FreeFlame(gas, width=width)
#         flame.set_refine_criteria(ratio=3, slope=0.06, curve=0.12)
#         flame.solve(loglevel=0, auto=True)

#         # Return peak temperature as a sample output metric
#         return flame.T[-1]
#     except Exception as e:
#         print(f"Simulation failed: {e}")
#         return np.nan

