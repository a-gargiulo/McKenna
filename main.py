import mckenna as mk
from mckenna.mytypes import ConfigDict
from typing import cast
import time



def main():
    config = mk.config.validate_config_file("./config.yaml")
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
    import multiprocessing as mp
    mp.freeze_support()
    main()
