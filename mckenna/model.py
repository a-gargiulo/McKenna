"""UVA McKenna burner Cantera model.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/02/2025 (MM/DD/YYYY)
"""
import pdb
import copy
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, cast

import cantera as ct
import numpy as np

from mckenna import utility
from mckenna.mytypes import ConfigDict



class McKenna:
    """UVA McKenna burner model."""

    def __init__(
        self, config: ConfigDict, overrides: Optional[Dict[str, Any]] = None
    ):
        """Construct a McKenna burner model.

        :param config: Configuration data.
        :param overrides: Override values.
        :raise RuntimeError: If something goes wrong during model instantiation.
        """
        self._config = config

        if self._config["mode"] == "uq":
            if overrides is None:
                raise RuntimeError(
                    "In 'uq' mode, the overrides cannot be zero."
                )
            self.inputs = self.extract_model_inputs(overrides)
        elif self._config["mode"] == "single":
            self.inputs = self.extract_model_inputs()
        else:
            raise RuntimeError("No matching caluclation mode provided.")

    def extract_model_inputs(
        self, overrides: Optional[Dict[str, Any]] = None
    ) -> ConfigDict:
        """Extract inputs, optionally overriding with UQ sample values."""
        inputs = copy.deepcopy(self._config)

        if inputs["mode"] == "uq":
            if not overrides:
                raise ValueError("In 'uq' mode, overrides must be provided.")

            for key, override_value in overrides.items():
                base_value = inputs.get(key)

                if isinstance(base_value, dict) and isinstance(
                    override_value, dict
                ):
                    base_value.update(override_value)
                else:
                    inputs[key] = override_value

        return inputs

    def run_simulation(self):
        """Run a 1D premixed impinging jet or free flame Cantera simulation.

        :return: True if successful, False otherwise.
        :rtype: bool
        """
        gas = ct.composite.Solution(self.inputs["mechanism"])

        mdot_total = sum(
            utility.slpm_to_ndot(Vdot)
            * gas.molecular_weights[gas.species_index(species)] * 1e-3
            for species, Vdot in cast(
                Dict[str, float],
                self.inputs["boundary_conditions"]["flow_rates"],
            ).items()
        )
        A_core_m2 = (
            self.inputs["geometry"]["burner_diameter"] ** 2.0 * np.pi / 4.0
        )
        mass_flux_kg_m2_s = mdot_total / A_core_m2

        if self.inputs["mode"] == "uq":
            composition = utility.calculate_composition(
                cast(
                    Dict[str, float],
                    self.inputs["boundary_conditions"]["flow_rates"],
                ),
                cast(str, self.inputs["boundary_conditions"]["fuel"]),
            )
        else:
            composition = self.inputs["boundary_conditions"]["composition"]

        gas.TPX = (
            self.inputs["boundary_conditions"]["burner_temperature"],
            self.inputs["boundary_conditions"]["pressure"],
            composition,
        )

        if self.inputs["geometry"]["type"] == "impinging_jet":
            sim = ct.ImpingingJet(
                gas=gas, width=self.inputs["geometry"]["domain_width"]
            )
            sim.radiation_enabled = self.inputs["submodels"]["radiation"]
            sim.transport_model = self.inputs["submodels"]["transport"]
            sim.soret_enabled = self.inputs["submodels"]["soret"]

            sim.inlet.mdot = mass_flux_kg_m2_s
            sim.inlet.T = self.inputs["boundary_conditions"][
                "burner_temperature"
            ]
            sim.surface.T = self.inputs["boundary_conditions"][
                "stagnation_temperature"
            ]
            sim.set_initial_guess(products="equil")
        elif self.inputs["geometry"]["type"] == "free_flame":
            sim = ct.BurnerFlame(
                gas=gas, width=self.inputs["geometry"]["domain_width"]
            )
            sim.radiation_enabled = self.inputs["submodels"]["radiation"]
            sim.transport_model = self.inputs["submodels"]["transport"]
            sim.soret_enabled = self.inputs["submodels"]["soret"]

            sim.burner.mdot = mass_flux_kg_m2_s
            sim.burner.T = self.inputs["boundary_conditions"][
                "burner_temperature"
            ]
        else:
            raise ValueError(
                "The selected simulation calculation mode is invalid."
            )

        sim.set_grid_min(self.inputs["settings"]["meshing"]["grid_min_size"])
        sim.set_max_grid_points(
            sim.domains[sim.domain_index("flame")],
            self.inputs["settings"]["meshing"]["max_grid_points"],
        )
        sim.set_refine_criteria(
            ratio=self.inputs["settings"]["meshing"]["ratio"],
            slope=self.inputs["settings"]["meshing"]["slope"],
            curve=self.inputs["settings"]["meshing"]["curve"],
            prune=self.inputs["settings"]["meshing"]["prune"],
        )

        if self.inputs["mode"] == "single":
            sim.show()
        if self.inputs["mode"] == 'uq':
            loglvl = 0
        else:
            loglvl = 1

        sim.solve(loglevel=loglvl, auto=True)

        output_path = Path() / "data"
        # output_path.mkdir(parents=True, exist_ok=True)

        output_file_name = f"{self.inputs['geometry']['type']}"
        if self.inputs["mode"] == "uq":
            output_file_name += f"_{uuid.uuid4()}.h5"
        elif self.inputs["mode"] == "single":
            output_file_name += ".h5"

        sim.save(output_path / output_file_name, overwrite=True)

        if self.inputs["mode"] == "single":
            sim.show_stats()
