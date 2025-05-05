"""Uncertainty quantification of the McKenna burner Cantera simulations.

This code utilizes mutliprocessing and multithreading to optimized performance.

Author: Aldo Gargiulo
Date: 05/02/25
"""
import asyncio
import concurrent.futures
import multiprocessing as mp
import os
from typing import Dict, List

import cantera as ct
import h5py
import numpy as np


# ---------- CONFIGURATION ----------
NUM_EPISTEMIC_SAMPLES = 10
NUM_ALEATORY_SAMPLES = 100
OUTPUT_DIR = "./results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# # Define ranges or distributions for inputs
# def sample_epistemic_input() -> Dict:
#     """Sample from the epistemic uncertainty space."""
#     # Example: equivalence ratio
#     return {"phi": np.random.uniform(0.8, 1.2)}

# def sample_aleatory_inputs() -> Dict:
#     """Sample from the aleatory uncertainty space."""
#     # Example: initial temperature and pressure
#     return {
#         "T0": np.random.normal(300, 10),    # Temperature in K
#         "P0": np.random.normal(101325, 1000)  # Pressure in Pa
#     }


# # ---------- Asynchronous Inner Loop ----------
# async def run_aleatory_batch(epistemic_input: Dict, n_samples: int, thread_id: int) -> List[float]:
#     """Run the inner aleatory loop asynchronously."""
#     loop = asyncio.get_running_loop()
#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         tasks = [
#             loop.run_in_executor(
#                 executor,
#                 run_flame_simulation,
#                 epistemic_input,
#                 sample_aleatory_inputs()
#             )
#             for _ in range(n_samples)
#         ]
#         results = await asyncio.gather(*tasks)
    
#     # Save the results in an HDF5 file for each thread
#     output_file = os.path.join(OUTPUT_DIR, f"simulation_results_thread_{thread_id}.h5")
#     with h5py.File(output_file, 'w') as f:
#         f.create_dataset("output_samples", data=results)
    
#     return results

# # ---------- Outer Loop Worker ----------
# def process_epistemic_sample(epistemic_sample_index: int) -> Dict:
#     """Handles one epistemic sample and runs the inner loop."""
#     epistemic_input = sample_epistemic_input()
#     results = asyncio.run(run_aleatory_batch(epistemic_input, NUM_ALEATORY_SAMPLES, epistemic_sample_index))
#     return {
#         "epistemic_input": epistemic_input,
#         "output_samples": results,
#     }

# # ---------- Main Entry ----------
# def main():
    # pass
#     with mp.Pool(processes=mp.cpu_count()) as pool:
#         all_results = pool.map(process_epistemic_sample, range(NUM_EPISTEMIC_SAMPLES))

#     # Example post-processing: compute mean flame temperature for each epistemic sample
#     for i, res in enumerate(all_results):
#         mean_temp = np.nanmean(res["output_samples"])
#         print(f"[{i}] φ={res['epistemic_input']['phi']:.3f}, Mean T = {mean_temp:.1f} K")

#     # Example: Merging HDF5 results for post-processing
#     all_data = []
#     files = [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.endswith('.h5')]
#     for file in files:
#         with h5py.File(file, 'r') as f:
#             output_samples = f["output_samples"][:]
#             all_data.append(output_samples)

#     # Combine all output samples into a single numpy array (or pandas DataFrame)
#     combined_data = np.concatenate(all_data, axis=0)

#     # Save the merged data (if needed)
#     np.savetxt("merged_output_samples.csv", combined_data, delimiter=",")

# if __name__ == "__main__":
    # main()
