"""Estimate numerical error.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/08/2025 (MM/DD/YYYY)
"""
import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

ROOT = "./data"
BASE = "impinging_jet"
LVL = ["coarse2", "coarse", "medium", "fine"]
HAB = 0.02

X = {}
T = {}
h = {}
dx = {}
lmbda = {}
lmbda2 = {}
plt.figure()
for level in LVL:
    file_name = ROOT + "/" + "_".join((BASE, level)) + ".h5"
    with h5py.File(file_name, "r") as f:
        X[level] = f["solution"]["flame"]["grid"][...]
        dx[level] = np.diff(X[level])
        lmbda[level] = np.mean(dx[level])
        lmbda2[level] = np.sqrt(np.mean(dx[level]**2))
        T[level] = f["solution"]["flame"]["T"][...]
        h[level] = HAB / len(X[level])
        # print(f"h_{level} = {h[level]}")
        plt.plot(X[level], T[level])


# print(f"r1,coarse = {lmbda['coarse'] / lmbda['fine']}")
# print(f"r2,coarse = {lmbda2['coarse'] / lmbda2['fine']}")
# print(f"r1,medium = {lmbda['medium'] / lmbda['fine']}")
# print(f"r2,medium = {lmbda2['medium'] / lmbda2['fine']}")



T2intrp = interp1d(X["coarse"], T["coarse"], kind='linear')
T2 = T2intrp(X["fine"])
T3intrp = interp1d(X["coarse2"], T["coarse2"], kind='linear')
T3 = T3intrp(X["fine"])
# xx = np.where(T2 < T3)
# pdb.set_trace()
# # OOA = np.log((np.linalg.norm(T2) - np.linalg.norm(T3)) / (np.linalg.norm(T["fine"]) - np.linalg.norm(T2))) / np.log(2.0)
OOA = np.log((T2 - T3) / (T["fine"] - T2)) / np.log(2.0)
# # print(OOA)
plt.figure()
# # plt.plot(X["fine"], T3)
# # plt.plot(X["fine"], T2)
# # plt.plot(X["fine"], T["fine"])
plt.plot(X["fine"], OOA)

plt.show()
# print(len(X["coarse"]))
# print(len(X["medium"]))
# print(len(X["fine"]))
# # print(f"r1 = {h['coarse']/h['medium']}")
# # print(f"r2 = {h['medium']/h['fine']}")
