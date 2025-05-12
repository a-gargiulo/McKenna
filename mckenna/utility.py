"""Utility module.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/02/2025 (MM/DD/YYYY)
"""
import h5py
import os
import re
import glob
from typing import Any, Dict, List, TYPE_CHECKING
import mckenna.logging as logger

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


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge dict2 into dict1 without modifying the originals."""
    result = dict1.copy()  # Create a shallow copy of dict1

    for key, value in dict2.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)  # Recursively merge nested dictionaries
        else:
            result[key] = value  # Otherwise, just overwrite the value from dict2

    return result


def merge_and_cleanup_hdf5_auto(
    directory: str, output_file: str, pattern="*_ep*_al*.h5"
) -> None:
    """Merge and cleanup UQ output HDF5 files from Monte Carlo simulation.

    Find HDF5 files matching a filename pattern in a directory, merge them
    into a single file, and delete the originals.

    :param directory: Directory to scan for files.
    :param output_file: Path to the final merged HDF5 file.
    :param pattern: Glob pattern to match input files.
    :raises FileNotFoundError: If no input files are found,
        or the output file already exists.
    :raises RuntimeError: If a file could not be deleted.
    """
    input_files = glob.glob(os.path.join(directory, pattern))

    if not input_files:
        raise FileNotFoundError(
            f"No matching files found in {directory} with pattern '{pattern}'."
        )

    if os.path.exists(output_file):
        raise FileExistsError(
            f"{output_file} already exists. Please delete it first."
        )

    with h5py.File(output_file, "w") as out_f:
        for file_path in input_files:
            base = os.path.basename(file_path)

            # Expect filenames like: geometry_ep01_al005.h5
            match = re.match(
                r"(?P<geometry>\w+)_ep(?P<ep>\d+)_al(?P<al>\d+)", base
            )
            if not match:
                logger.log_warning(f"Skipping file (pattern mismatch): {base}")
                continue

            geometry = match.group("geometry")
            ep = int(match.group("ep"))
            al = int(match.group("al"))
            group_name = f"{geometry}_ep{ep:02d}_al{al:03d}"

            with h5py.File(file_path, "r") as in_f:
                grp = out_f.create_group(group_name)
                for dset_name in in_f:
                    in_f.copy(dset_name, grp)
                grp.attrs['source_filename'] = base
                grp.attrs['epistemic_index'] = ep
                grp.attrs['aleatory_index'] = al

            logger.log_info(f"Merged: {file_path} -> {group_name}")

    # After merging, delete original files
    for file_path in input_files:
        try:
            os.remove(file_path)
            logger.log_info(f"Deleted: {file_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete {file_path}: {e}")

    logger.log_info(
        f"All files merged into '{output_file}' and originals deleted."
    )
