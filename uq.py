"""McKenna burner simulation uncertainty quantification."""
import numpy as np

P = 101325
RXN = "./FFCM-2/FFCM-2.yaml"
PHI = 1.0
X_B = "C2H4:1.0, O2:3.0, N2:11.14, AR:0.14"
V_DOT_SLPM = {
    "C2H4": 0.652,
    "O2": 1.9635,
    "N2": 7.2930,
    "AR": 0.0935
}
M_KG_MOL = {
    "C2H4": 28.05336e-03,
    "O2": 31.99800e-03,
    "N2": 28.013400e-03,
    "AR": 39.94800e-03
}

if __name__ == "__main__":
    T_b = np.linspace(300, 350, 10)

    mu_T_s = 345.15
    sigma_T_s = 2
