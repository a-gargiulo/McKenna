"""Main entry point for UVA McKenna burner simulation.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/02/2025 (MM/DD/YYYY)
"""

import sys
import multiprocessing as mp
import time
from typing import cast

import mckenna as mk
from mckenna.mytypes import ConfigDict


CONFIG_FILE = "./config.yaml"


def main():
    """Provide program main entry point."""
    mk.logger.log_todo(
        "Handle superfluous keys when loading/validating config.yaml."
    )

    config = mk.config.load_yaml_config(CONFIG_FILE)
    if not config:
        sys.exit(1)

    config = mk.config.validate_config_file(config)
    if not config:
        sys.exit(1)
    config = cast(ConfigDict, config)

    if config["mode"] == "uq":
        uq_sim = mk.montecarlo.MonteCarlo(config)
        uq_sim.run()
    elif config["mode"] == "single":
        model = mk.model.McKenna(config, None)
        start_time = time.time()
        model.run_simulation()
        end_time = time.time()
        print(f"Simulation Duration: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    mp.freeze_support()
    main()
