import os
from typing import Any, Dict, List, cast
from mckenna.mytypes import ConfigDict, NormalDistr, UniformDistr, Samples
import numpy as np
from mckenna.model import McKenna
import asyncio
import concurrent.futures
from mckenna import utility
import multiprocessing as mp
import time
from multiprocessing import current_process, Manager
import mckenna.logging as logger
from colorama import init, Fore, Style


class MonteCarlo:
    """Class for Monte Carlo simulation."""

    def __init__(self, config: ConfigDict):
        """Insert here."""
        self._config = config  # Read only

    # TODO: Handle more distributions if needed
    def sample_epistemic_inputs(self, ep_idx: int) -> Dict[str, Any]:
        """Sample from the epistemic uncertainty space.

        :param bc: Boundary conditions.
        :return: Samples.
        :rtype: Dict[str, float]
        """
        Tb = cast(UniformDistr, self._config["boundary_conditions"]["burner_temperature"])

        samples = {"boundary_conditions": {}}

        ep_samples = np.linspace(Tb["min"], Tb["max"], cast(dict, self._config["settings"]["uq"])["epistemic_samples"])
        samples["boundary_conditions"]["burner_temperature"] = ep_samples[ep_idx]
        # samples["boundary_conditions"]["burner_temperature"] = np.random.uniform(Tb["min"], Tb["max"])

        return samples

    # TODO: Handle more distributions if needed
    def sample_aleatory_inputs(self) -> Dict[str, Any]:
        """Sample from the aleatory uncertainty space.

        :param bc: Boundary conditions.
        :return: Samples.
        :rtype: Dict[str, float]
        """
        Ts = cast(
            NormalDistr, self._config["boundary_conditions"]["stagnation_temperature"]
        )
        rates = self._config["boundary_conditions"]["flow_rates"]

        samples = {"boundary_conditions": {}}
        samples["boundary_conditions"]["stagnation_temperature"] = np.random.normal(Ts["mean"], Ts["stdev"])
        samples["boundary_conditions"]["flow_rates"] = {}

        for key in rates.keys():
            samples["boundary_conditions"]["flow_rates"][key] = np.random.normal(
                cast(NormalDistr, rates[key])["mean"],
                cast(NormalDistr, rates[key])["stdev"]
            )

        return samples

    def run_aleatory_batch(self, epistemic_inputs: Dict[str, Any], n_samples: int, ep_idx) -> List[None]:
        results = []
        for al_idx in range(n_samples):
            start_time = time.time()  # Start time for aleatory sample
            aleatory_inputs = self.sample_aleatory_inputs()
            overrides = utility.deep_merge(epistemic_inputs, aleatory_inputs)
            model = McKenna(self._config, overrides)
            logger.log_info(f"[{Fore.MAGENTA}{Style.BRIGHT}PID {os.getpid()}{Style.RESET_ALL}] Epistemic {ep_idx}, Aleatory {al_idx} started.")
            result = model.run_simulation(ep_idx, al_idx)
            end_time = time.time()  # End time for aleatory sample
            logger.log_info(f"[{Fore.MAGENTA}{Style.BRIGHT}PID {os.getpid()}{Style.RESET_ALL}] Epistemic {ep_idx}, Aleatory {al_idx} done."
                  f" (Duration: {end_time - start_time:.2f} seconds)")
            results.append(result)
        return results

    def process_epistemic_samples(self, ep_idx, n_aleatory) -> List[None]:
        logger.log_info(f"[{Fore.MAGENTA}{Style.BRIGHT}PID {os.getpid()}{Style.RESET_ALL}] Starting epistemic sample {ep_idx}.")
        epistemic_inputs = self.sample_epistemic_inputs(ep_idx)
        result = self.run_aleatory_batch(epistemic_inputs, n_aleatory, ep_idx)
        logger.log_info(f"[{Fore.MAGENTA}{Style.BRIGHT}PID {os.getpid()}{Style.RESET_ALL}] Finished epistemic sample {ep_idx}.")
        return result


    def run(self):
        n_epistemic = cast(Samples, self._config["settings"]["uq"])["epistemic_samples"]
        n_aleatory = cast(Samples, self._config["settings"]["uq"])["aleatory_samples"]

        with mp.Pool(mp.cpu_count()) as pool:
            pool.starmap(
                self.process_epistemic_samples,
                [(ep_idx, n_aleatory) for ep_idx in range(n_epistemic)]
            )
