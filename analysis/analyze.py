"""Analyze the results from the Monte Carlo simulation.

Author: Aldo Gargiulo
Email:  bzc6rs@virginia.edu
Date:   05/08/2025 (MM/DD/YYYY)
"""
import h5py
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
from matplotlib.ticker import MultipleLocator
from scipy.interpolate import interp1d


RC_PARAMS = {
    "font.size": 18,
    "font.family": "Avenir",
    "axes.linewidth": 2,
    "axes.labelpad": 10,
    "lines.linewidth": 1,
    "xtick.direction": "in",
    "xtick.major.width": 2,
    "xtick.major.size": 4,
    "xtick.minor.size": 3,
    "xtick.major.pad": 10,
    "ytick.direction": "in",
    "ytick.major.width": 2,
    "ytick.major.size": 4,
    "ytick.minor.size": 3,
    "ytick.major.pad": 10,
}
plt.rcParams.update(RC_PARAMS)



FILE_NAME = "./data/8x100_impinging_jet_MonteCarlo.h5"
E_S = 8
A_S = 100
N_INT = 800

xint = np.linspace(0, 0.02, N_INT)
TT = np.zeros((E_S, A_S, N_INT))
with h5py.File(FILE_NAME, "r") as f:
    for ep in range(E_S):
        for al in range(A_S):
            group = f[f"impinging_jet_ep{ep:02d}_al{al:03d}"]
            x = group["solution"]["flame"]["grid"][...]
            T = group["solution"]["flame"]["T"][...]
            Tfunc = interp1d(x, T, kind='linear')  # or 'cubic', 'quadratic'
            Tint = Tfunc(xint)
            TT[ep, al, :] = Tint

T_sorted = np.zeros((E_S, A_S, N_INT))
cdfs = np.zeros((E_S, A_S, N_INT))
for ep in range(E_S):
    for n in range(N_INT):
        temps = TT[ep, :, n]
        T_sorted[ep, :, n] = np.sort(temps)
        cdfs[ep, :, n] = np.arange(1, len(T_sorted[ep, :, n]) + 1) / len(T_sorted[ep, :, n])

# plot p-box at spatial location
cmap = plt.cm.Blues
colors = cmap(np.linspace(0.3, 0.9, E_S))

n = 500
Ts = T_sorted[:, :, n]  # shape: (E_S, A_S)
Fs = cdfs[:, :, n]      # shape: (E_S, A_S)

# Define a common temperature axis for interpolation
T_min = Ts.min()
T_max = Ts.max()
T_grid = np.linspace(T_min, T_max, 300)

Fs_interp = []
for ep in range(E_S):
    f_interp = interp1d(Ts[ep, :], Fs[ep, :], kind='linear', bounds_error=False, fill_value=(0, 1))
    Fs_interp.append(f_interp(T_grid))
Fs_interp = np.array(Fs_interp)  # shape: (E_S, len(T_grid))

# Compute bounding CDFs
F_lower = np.min(Fs_interp, axis=0)
F_upper = np.max(Fs_interp, axis=0)


# Precompute the means over aleatory samples for each epistemic case at each x
means = np.mean(TT, axis=1)  # shape: (N_epistemic, N_x)

# Compute mean bounds across epistemic cases
lower_mu = np.min(means, axis=0)  # shape: (N_x,)
upper_mu = np.max(means, axis=0)  # shape: (N_x,)

# Midpoint mean for plotting (optional)
mu_mid = (lower_mu + upper_mu) / 2

# Compute min and max temperature values at each x across all samples
T_min = np.min(TT.reshape(-1, N_INT), axis=0)  # shape: (N_x,)
T_max = np.max(TT.reshape(-1, N_INT), axis=0)  # shape: (N_x,)



fig1 = plt.figure(figsize=(3,3))
ax1 = fig1.add_axes((0,0,1,1))

# Plot the P-box bounds
pl1, = ax1.plot(T_grid, F_lower, label="Bounds", color="black", linestyle="--")
ax1.plot(T_grid, F_upper, color="black", linestyle="--")

# Fill the P-box region
pl2 = ax1.fill_between(T_grid, F_lower, F_upper, color="gray", alpha=0.4, label="p-Box")

# Optional: plot individual CDFs
for i, ep in enumerate(range(E_S)):
    if i == 0:
        pl3, = ax1.plot(T_sorted[ep, :, n], cdfs[ep, :, n], color="blue", alpha=0.3, linewidth=0.8, label="CDF")
    ax1.plot(T_sorted[ep, :, n], cdfs[ep, :, n], color="blue", alpha=0.3, linewidth=0.8)

ax1.set_xlabel("Temperature (K)")
ax1.set_ylabel("CDF")
ax1.set_title(f"P-box at HAB = {xint[n]*1000:.1f} mm", fontsize=18)
ax1.grid(True, alpha=0.3)
ax1.legend(handles=[pl2, pl1, pl3], fontsize=14, edgecolor='k', facecolor='white', framealpha=1)
fig1.savefig("cdf.png", dpi=300, bbox_inches='tight')


m2mm = 1000.0
fig = plt.figure(figsize=(3, 3))
ax = fig.add_axes((0, 0, 1, 1))

# Main plot
ax.plot(xint*m2mm, mu_mid, label="Mean Temperature", color="blue")
ppl1 = ax.fill_between(xint*m2mm, lower_mu, upper_mu, alpha=0.3, label="Mean Bounds (Epistemic)", color="blue")
ppl2 = ax.fill_between(xint*m2mm, T_min, T_max, alpha=0.2, label="Total Bounds (Epistemic + Aleatory)", color="red")
ax.xaxis.set_major_locator(MultipleLocator(5.0))
ax.set_ylim(250, 1750)
ax.set_xlabel("HAB (mm)")
ax.set_ylabel("Temperature (K)")
ax.grid(True)
ax.legend(handles=[ppl1, ppl2], fontsize=10, edgecolor="k", facecolor="white", framealpha=1, loc='center', bbox_to_anchor=(0.5, 1.1), bbox_transform=ax.transAxes)

# Zoomed inset 1
zoom_s, zoom_e = 0.0*m2mm, 1e-4*m2mm
axins = inset_axes(ax, width=1.0, height=1.0, loc='center', bbox_to_anchor=(0.3, 0.2), bbox_transform=ax.transAxes, borderpad=0)
zoom_region = (xint*m2mm > zoom_s) & (xint*m2mm < zoom_e)  # adjust to your target area
axins.plot(xint*m2mm, mu_mid, color="blue")
axins.fill_between(xint*m2mm, lower_mu, upper_mu, alpha=0.3, color="blue")
axins.fill_between(xint*m2mm, T_min, lower_mu, alpha=0.2, color="red")
axins.fill_between(xint*m2mm, upper_mu, T_max, alpha=0.2, color="red")
axins.set_xlim(zoom_s, zoom_e)
axins.set_ylim(400, 600)  # match y-axis scale
axins.set_xticks([])
axins.set_yticks([])
pp, pp1, pp2 = mark_inset(ax, axins, loc1=2, loc2=3, fc="none", ec="k", zorder=10)
for line in (pp1, pp2):
    line.set_linestyle("--")

# Zoomed inset 2
zoom_s2, zoom_e2 = 0.008*m2mm, 0.012*m2mm
axins2 = inset_axes(ax, width=1.0, height=1.0, loc='center', bbox_to_anchor=(0.28, 0.58), bbox_transform=ax.transAxes, borderpad=0)
zoom_region = (xint*m2mm > zoom_s2) & (xint*m2mm < zoom_e2)  # adjust to your target area
axins2.plot(xint*m2mm, mu_mid, color="blue")
axins2.fill_between(xint*m2mm, lower_mu, upper_mu, alpha=0.3, color="blue")
axins2.fill_between(xint*m2mm, T_min, lower_mu, alpha=0.2, color="red")
axins2.fill_between(xint*m2mm, upper_mu, T_max, alpha=0.2, color="red")
axins2.set_xlim(zoom_s2, zoom_e2)
axins2.set_ylim(1400, 1600)  # match y-axis scale
axins2.set_xticks([])
axins2.set_yticks([])
pp2, pp21, pp22 = mark_inset(ax, axins2, loc1=2, loc2=4, fc="none", ec="k", zorder=10)
for line in (pp21, pp22):
    line.set_linestyle("--")

# Zoomed inset 3
zoom_s3, zoom_e3 = 0.019*m2mm, 0.02*m2mm
axins3 = inset_axes(ax, width=1.0, height=1.0, loc='center', bbox_to_anchor=(0.68, 0.28), bbox_transform=ax.transAxes, borderpad=0)
zoom_region = (xint*m2mm > zoom_s3) & (xint*m2mm < zoom_e3)  # adjust to your target area
axins3.plot(xint*m2mm, mu_mid, color="blue")
axins3.fill_between(xint*m2mm, lower_mu, upper_mu, alpha=0.3, color="blue")
axins3.fill_between(xint*m2mm, T_min, lower_mu, alpha=0.2, color="red")
axins3.fill_between(xint*m2mm, upper_mu, T_max, alpha=0.2, color="red")
axins3.set_xlim(zoom_s3, zoom_e3)
axins3.set_ylim(500, 700)  # match y-axis scale
axins3.set_xticks([])
axins3.set_yticks([])
pp3, pp31, pp32 = mark_inset(ax, axins3, loc1=1, loc2=4, fc="none", ec="k", zorder=10)
for line in (pp31, pp32):
    line.set_linestyle("--")


fig.savefig("uq.png", dpi=300, bbox_inches='tight')
