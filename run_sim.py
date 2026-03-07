import numpy as np
import json
from math import gcd, lcm

# ─── DESIGN PARAMETERS (YASA Dual-Rotor, 8-pole, 12-slot) ───────────────────
n_poles   = 8
n_slots   = 12
Br        = 1.32        # T  (NdFeB N42 remanence)
r_out     = 0.100       # m  outer radius
r_in      = 0.050       # m  inner radius
g         = 0.001       # m  air-gap
lm        = 0.005       # m  magnet thickness
kc        = 1.1         # Carter coefficient
n_phases  = 3
N_turns   = 20          # turns per coil (concentrated)
rpm       = 1500
omega     = rpm * 2 * np.pi / 60

# 1. FLUX DENSITY IN AIR GAP
g_eff = kc * (g + lm)
B_gap = Br * lm / g_eff
print(f"Air-gap flux density B_gap = {B_gap:.4f} T")

# 2. EMF PER PHASE
r_avg      = (r_out + r_in) / 2
tau_p      = np.pi * r_avg / (n_poles / 2)
A_coil     = tau_p * (r_out - r_in)
n_coils_ph = n_slots // n_phases
kw         = 0.866

E_single = n_coils_ph * N_turns * kw * B_gap * A_coil * omega * (n_poles / 2)
E_dual   = 2 * E_single
print(f"Phase EMF (RMS): single={E_single/np.sqrt(2):.2f} V, dual={E_dual/np.sqrt(2):.2f} V")

# 3. CURRENT & POWER
d_wire    = 1.5e-3
A_wire    = np.pi*(d_wire/2)**2
J         = 6e6
I_ph      = J * A_wire
R_coil    = (1.72e-8 * n_coils_ph * N_turns * 2 * tau_p) / A_wire
P_single  = n_phases * E_single/np.sqrt(2) * I_ph * np.cos(np.deg2rad(20))
P_dual    = n_phases * E_dual/np.sqrt(2)   * I_ph * np.cos(np.deg2rad(20))
print(f"Power: single={P_single:.1f} W, dual={P_dual:.1f} W")

# 4. COGGING TORQUE
N_cog = lcm(n_poles, n_slots)
theta = np.linspace(0, 2*np.pi, 3600)
T_peak_base = 0.015 * B_gap**2 * r_avg * (r_out - r_in) * lm

def cogging_torque(th, geom_lcm, alpha_m=0.8, skew_deg=0.0):
    skew = np.deg2rad(skew_deg) * geom_lcm
    T = np.zeros_like(th)
    for n in range(1, 5):
        coeff = T_peak_base * np.sin(n * np.pi * alpha_m) / (n * np.pi * alpha_m)
        T += coeff * np.sin(n * geom_lcm * th + skew)
    return T

T_no_skew  = cogging_torque(theta, N_cog, 0.80, 0.0)
T_skew15   = cogging_torque(theta, N_cog, 0.80, 15.0)
T_pp_no_skew = T_no_skew.max() - T_no_skew.min()
T_pp_skew15  = T_skew15.max() - T_skew15.min()
T_rated = P_dual / omega
cog_pct_no_skew = T_pp_no_skew / T_rated * 100
cog_pct_skew    = T_pp_skew15 / T_rated * 100
print(f"Cogging (no skew): {cog_pct_no_skew:.2f}%")
print(f"Cogging (15 skew): {cog_pct_skew:.2f}%")

# 5. EFFICIENCY
Cu_loss  = n_phases * I_ph**2 * R_coil
fe_freq  = omega * n_poles / (4 * np.pi)
Fe_loss  = 2.5 * (fe_freq/50)**1.5 * 0.3
mech_loss = 0.01 * P_dual
eta = P_dual / (P_dual + Cu_loss + Fe_loss + mech_loss)
print(f"Efficiency: {eta*100:.2f}%")

# 6. MASS & COST
tau_m    = 0.8 * tau_p
w_m      = r_out - r_in
m_mag    = 2 * n_poles * tau_m * w_m * lm * 7500
c_mag    = m_mag * 50
l_coil   = n_coils_ph * N_turns * 2 * (w_m + 1.5*tau_p) * n_phases
m_cu     = l_coil * A_wire * 8960
c_cu     = m_cu * 15
A_rotor  = np.pi*(r_out**2 - r_in**2)
m_fe     = 2 * A_rotor * 0.005 * 7800
c_fe     = m_fe * 3
total_mass = m_mag + m_cu + m_fe
total_cost = c_mag + c_cu + c_fe + 120
PD = P_dual / 1000 / total_mass
mass_ref  = total_mass * 2.8
cost_ref  = total_cost * 1.92
PD_ref    = P_single / 1000 / mass_ref

print(f"\n{'─'*55}")
print(f"{'Parameter':<30} {'Radial Flux':>12} {'Dual-Rotor YASA':>12}")
print(f"{'─'*55}")
print(f"{'Power output (W)':<30} {P_single:>12.1f} {P_dual:>12.1f}")
print(f"{'Phase RMS voltage (V)':<30} {E_single/np.sqrt(2):>12.2f} {E_dual/np.sqrt(2):>12.2f}")
print(f"{'Current (A)':<30} {I_ph:>12.2f} {I_ph:>12.2f}")
print(f"{'Total mass (kg)':<30} {mass_ref:>12.3f} {total_mass:>12.3f}")
print(f"{'Power density (kW/kg)':<30} {PD_ref:>12.3f} {PD:>12.3f}")
print(f"{'PD improvement':<30} {'—':>12} {PD/PD_ref:>11.2f}x")
print(f"{'Total cost ($)':<30} {cost_ref:>12.1f} {total_cost:>12.1f}")
print(f"{'Cost reduction (%)':<30} {'—':>12} {(1-total_cost/cost_ref)*100:>11.1f}%")
print(f"{'Efficiency (%)':<30} {'—':>12} {eta*100:>12.2f}")
print(f"{'Cogging % (no skew)':<30} {'—':>12} {cog_pct_no_skew:>12.2f}")
print(f"{'Cogging % (15 skew)':<30} {'—':>12} {cog_pct_skew:>12.2f}")
print(f"{'─'*55}")

results = {
    "B_gap": round(B_gap,4),
    "E_single_rms": round(E_single/np.sqrt(2),2),
    "E_dual_rms": round(E_dual/np.sqrt(2),2),
    "I_A": round(I_ph,2),
    "P_single": round(P_single,1),
    "P_dual": round(P_dual,1),
    "eta_pct": round(eta*100,2),
    "mass_kg": round(total_mass,3),
    "cost_usd": round(total_cost,1),
    "PD_kWkg": round(PD,3),
    "cog_no_skew_pct": round(cog_pct_no_skew,2),
    "cog_skew_pct": round(cog_pct_skew,2),
    "mass_ref": round(mass_ref,3),
    "cost_ref": round(cost_ref,1),
    "PD_ref": round(PD_ref,3),
    "N_cog": N_cog,
    "Cu_loss": round(Cu_loss,2),
    "Fe_loss": round(Fe_loss,2),
    "mech_loss": round(mech_loss,2)
}
with open("sim_results.json","w") as f:
    json.dump(results, f, indent=2)
print("\nSaved to sim_results.json")
