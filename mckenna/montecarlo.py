from typing import Any, Dict
import numpy as np


# TODO: Handle more distributions if needed
def sample_epistemic_inputs(bc: Dict[str, Any]) -> Dict[str, float]:
    """Sample from the epistemic uncertainty space.

    :param bc: Boundary conditions.
    :return: Samples.
    :rtype: Dict[str, float]
    """
    Tb = bc["burner_temperature"]
    return {
        "burner_temperature": np.random.uniform(Tb["min"], Tb["max"])
    }


# TODO: Handle more distributions if needed
def sample_aleatory_inputs(bc: Dict[str, Any]) -> Dict[str, float]:
    """Sample from the aleatory uncertainty space.

    :param bc: Boundary conditions.
    :return: Samples.
    :rtype: Dict[str, float]
    """
    Ts = bc["stagnation_temperature"]
    rates = bc["flow_rates"]

    samples = {
        "stagnation_temperature": np.random.normal(Ts["mean"], Ts["stdev"])
    }

    for key in rates.keys():
        samples[key] = np.random.normal(
            rates[key]["mean"], rates[key]["stdev"]
        )

    return samples
