"""Utility module.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/02/2025 (MM/DD/YYYY)
"""
from types import MappingProxyType
from typing import Any, Dict, List, TYPE_CHECKING, Union, Mapping, Tuple

if TYPE_CHECKING:
    import cantera as ct


def parse_composition(comp_str: str) -> List[str]:
    """Parse the composition string into a list of species.

    :param comp_str: Composition string.
    :raises ValueError: If the composition string is invalid.
    :return: List of element names.
    :rtype: List[str]
    """
    if not comp_str:
        raise ValueError("Composition string is empty.")

    species_list = []

    components = comp_str.split(',')
    for component in components:
        component = component.strip()

        if ':' not in component:
            raise ValueError(
                f"Invalid format in component '{component}', missing ':'"
            )

        species, amount_str = component.split(':')

        species = species.strip()

        if not species:
            raise ValueError(
                f"Invalid species '{species}', name cannot be empty."
            )

        species_list.append(species)

    return species_list


def slpm_to_ndot(slpm: float) -> float:
    """Convert a volumetric flow rate (slpm) to a molar flow rate (mol/s).

    This function assumes ideal gas behavior.

    :param slpm: Volumetric flow rate, slpm.
    :return: Molar flow rate, mol/s.
    :rtype: float
    """
    return (slpm * 0.001 * 1.0e+05) / (60.0 * 8.314 * 273.15)


def calculate_composition(flow_rates: Dict[str, float], fuel: str) -> str:
    """Compute the composition string from the volumetric flow rates in slpm."""

    return ",".join(f"{component}: {value / flow_rates[fuel]}" for component, value in flow_rates.items())
