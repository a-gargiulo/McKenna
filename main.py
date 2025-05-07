"""Main entry point for UVA McKenna burner simulation.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/02/2025 (MM/DD/YYYY)
"""

import multiprocessing as mp
import sys
from typing import cast

import mckenna as mk
from mckenna.mytypes import ConfigDict

CONFIG_FILE = "./config.yaml"


def main():
    """Provide program main entry point."""
    mk.logger.log_todo(
        "Handle unexpected/superfluous keys when "
        "loading/validating config.yaml."
    )

    config = mk.config.load_yaml_config(CONFIG_FILE)
    if not config:
        sys.exit(1)

    config = mk.config.validate_config_file(config)
    if not config:
        sys.exit(1)
    config = cast(ConfigDict, config)

    if config["mode"] == "uq":
        mp.freeze_support()
        uq_sim = mk.montecarlo.MonteCarlo(config)
        uq_sim.run()
    elif config["mode"] == "single":
        model = mk.model.McKenna(config, None)
        model.run_simulation()


if __name__ == "__main__":
    main()
