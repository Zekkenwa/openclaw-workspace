"""mep_calc — reusable MEP engineering calculations.

Covers:
  - Colebrook-White friction factor (implicit, solved by iteration)
  - Huebscher equivalent diameter (circular equivalent of rectangular duct)
  - Darcy-Weisbach pressure drop
  - Hazen-Williams head loss / velocity / flow (water piping)

Units: SI throughout (m, m/s, Pa, m of water column) unless noted.
Run: py -3.12 mep_calc.py  for the self-test suite.

Standards referenced:
  - Colebrook-White: C.F. Colebrook (1939), used by ASHRAE/SMACNA duct calcs
  - Huebscher: R. Huebscher (1947), Heating/Piping/Air Conditioning — the
    equivalent-diameter formula adopted by SMACNA and most duct-sizing charts
  - Hazen-Williams: standard water-pipe formula (SNI 8153:2015 drainage context
    uses DFU sizing; H-W applies to pressure lines: chilled water, sprinkler,
    hydrant, domestic cold water)
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# Colebrook-White friction factor
# ---------------------------------------------------------------------------

def colebrook_white(Re: float, rel_roughness: float, tol: float = 1e-10,
                    max_iter: int = 100) -> float:
    """Darcy friction factor f from the implicit Colebrook-White equation.

        1/sqrt(f) = -2*log10( eps/(3.7*D) + 2.51/(Re*sqrt(f)) )

    Args:
        Re: Reynolds number (dimensionless).
        rel_roughness: eps/D, absolute roughness over diameter (dimensionless).
            Typical: galvanized steel 0.15 mm / duct diameter in mm.

    Returns:
        Darcy friction factor (dimensionless).

    Raises:
        ValueError: for laminar-range misuse (Re <= 0) — see `friction_factor`.
    """
    if Re <= 0:
        raise ValueError("Reynolds number must be positive")
    if Re < 2300:
        raise ValueError(
            f"Re={Re:.0f} is laminar; Colebrook-White applies to turbulent "
            "flow (Re > ~4000). Use friction_factor() which handles laminar."
        )
    if rel_roughness < 0:
        raise ValueError("Relative roughness must be non-negative")

    # Swamee-Jain explicit formula as initial guess (fast convergence)
    f = 0.25 / (math.log10(rel_roughness / 3.7 + 5.74 / Re**0.9)) ** 2

    for _ in range(max_iter):
        sqrt_f = math.sqrt(f)
        rhs = -2.0 * math.log10(rel_roughness / 3.7 + 2.51 / (Re * sqrt_f))
        f_new = 1.0 / rhs**2
        if abs(f_new - f) < tol:
            return f_new
        f = f_new
    return f


def friction_factor(Re: float, rel_roughness: float = 0.0) -> float:
    """Darcy friction factor covering laminar and turbulent regimes.

    Laminar (Re < 2300): f = 64/Re (exact, Hagen-Poiseuille).
    Turbulent: Colebrook-White iteration.
    Transition band (2300-4000): conservative — uses turbulent result at Re.
    """
    if Re < 2300:
        return 64.0 / Re
    return colebrook_white(Re, rel_roughness)


# ---------------------------------------------------------------------------
# Duct flow (Darcy-Weisbach + Huebscher)
# ---------------------------------------------------------------------------

def reynolds(v: float, d: float, nu: float = 1.5e-5) -> float:
    """Reynolds number. v [m/s], d [m], nu [m2/s] (air at 20C ≈ 1.5e-5)."""
    return v * d / nu


def huebscher_equivalent_diameter(a: float, b: float) -> float:
    """Circular equivalent diameter of a rectangular duct (equal flow,
    equal velocity), Huebscher 1947:

        De = 1.30 * (a*b)^0.625 / (a+b)^0.25

    Args:
        a, b: duct sides [m] (or mm — result is same unit).

    Returns:
        Equivalent diameter, same unit as inputs.

    NOTE: This is the *equal-velocity* equivalent used by SMACNA charts.
    For equal-friction-per-length sizing some charts use De = 1.26*(a³b³/(a+b))^(1/5);
    see huebscher_equal_friction().
    """
    if a <= 0 or b <= 0:
        raise ValueError("Duct dimensions must be positive")
    return 1.30 * (a * b) ** 0.625 / (a + b) ** 0.25


def huebscher_equal_friction(a: float, b: float) -> float:
    """Equal-friction circular equivalent: De = 1.26 * (a³·b³/(a+b))^(1/5).

    Used by some duct-sizing charts where friction loss per unit length is
    held constant rather than velocity.
    """
    if a <= 0 or b <= 0:
        raise ValueError("Duct dimensions must be positive")
    return 1.26 * ((a**3 * b**3) / (a + b)) ** 0.2


def darcy_weisbach_dp(f: float, L: float, d: float, v: float,
                      rho: float = 1.2) -> float:
    """Pressure drop over straight length: dp = f * (L/D) * (rho*v²/2).

    Args:
        f: Darcy friction factor.
        L: length [m]. d: diameter [m]. v: velocity [m/s].
        rho: fluid density [kg/m3] (air ≈ 1.2, water ≈ 1000).

    Returns:
        Pressure drop [Pa] for air-density default; consistent units if rho
        is overridden (e.g. water → result in Pa directly too).
    """
    return f * (L / d) * rho * v**2 / 2.0


def duct_pressure_drop(q: float, a: float = 0.0, b: float = 0.0, d: float = 0.0,
                       L: float = 1.0, roughness_mm: float = 0.15,
                       rho: float = 1.2, nu: float = 1.5e-5) -> dict:
    """One-shot duct pressure-drop calc for round or rectangular duct.

    Args:
        q: volumetric flow [m3/s].
        a, b: rectangular sides [m] (supply both) OR
        d: round diameter [m] (supply instead).
        L: duct length [m].
        roughness_mm: absolute roughness [mm] (galvanized ≈ 0.15).
        rho: density [kg/m3], nu: kinematic viscosity [m2/s].

    Returns:
        dict with velocity, Re, friction factor, equivalent diameter,
        pressure drop [Pa], and loss per meter [Pa/m].
    """
    if d > 0:
        de = d
        area = math.pi * d**2 / 4.0
    elif a > 0 and b > 0:
        de = huebscher_equivalent_diameter(a, b)
        area = a * b
    else:
        raise ValueError("Supply either d (round) or a and b (rectangular)")

    v = q / area
    Re = reynolds(v, de, nu)
    f = friction_factor(Re, (roughness_mm / 1000.0) / de)
    dp = darcy_weisbach_dp(f, L, de, v, rho)
    return {
        "velocity_m_s": v,
        "Re": Re,
        "friction_factor": f,
        "equiv_diameter_m": de,
        "area_m2": area,
        "dp_Pa": dp,
        "dp_Pa_per_m": dp / L,
    }


# ---------------------------------------------------------------------------
# Hazen-Williams (water piping)
# ---------------------------------------------------------------------------

def hazen_williams_head_loss(q: float, d: float, C: float = 130.0,
                             L: float = 1.0) -> float:
    """Hazen-Williams head loss, SI form:

        hf = 10.67 * L * Q^1.852 / (C^1.852 * D^4.87)

    Args:
        q: flow [m3/s]. d: internal diameter [m]. C: roughness coefficient
           (PVC/PE 140-150, new steel 130-140, aged CI 100, GIP used ~120).
        L: length [m].

    Returns:
        Head loss [m of water] over length L.
    """
    if q <= 0 or d <= 0 or C <= 0:
        raise ValueError("q, d, C must be positive")
    return 10.67 * L * q**1.852 / (C**1.852 * d**4.87)


def hazen_williams_velocity_from_head_loss(hf: float, d: float, C: float = 130.0,
                                           L: float = 1.0) -> float:
    """Invert H-W for flow given allowable head loss. Returns Q [m3/s]."""
    # q = (hf * C^1.852 * d^4.87 / (10.67 * L))^(1/1.852)
    inner = hf * C**1.852 * d**4.87 / (10.67 * L)
    return inner ** (1.0 / 1.852)


def hazen_williams_pressure_drop(q: float, d: float, C: float = 130.0,
                                 L: float = 1.0, rho: float = 1000.0,
                                 g: float = 9.80665) -> dict:
    """Convenience wrapper: returns head loss [m] and pressure drop [Pa],
    plus velocity and hydraulic gradient (per meter)."""
    area = math.pi * d**2 / 4.0
    v = q / area
    hf = hazen_williams_head_loss(q, d, C, L)
    return {
        "velocity_m_s": v,
        "head_loss_m": hf,
        "dp_Pa": hf * rho * g,
        "gradient_m_per_m": hf / L,
    }


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _selftest():
    print("mep_calc self-test")
    print("-" * 60)

    # 1. Colebrook-White: classic check — Re=1e5, eps/D=0.001 → f≈0.0222 (Moody chart)
    f = colebrook_white(1e5, 0.001)
    print(f"Colebrook  Re=1e5, eps/D=0.001  f = {f:.5f}  (expect ~0.0222)")
    assert abs(f - 0.0222) < 2e-4, f

    # Laminar check
    f_lam = friction_factor(1000)
    print(f"Laminar    Re=1000              f = {f_lam:.5f}  (expect 0.064)")
    assert abs(f_lam - 0.064) < 1e-6

    # 2. Huebscher: 600x300 mm duct → formula value ≈ 457 mm (matches SMACNA charts)
    de = huebscher_equivalent_diameter(0.6, 0.3) * 1000
    print(f"Huebscher  600x300 mm           De = {de:.1f} mm  (expect ~457)")
    assert 450 < de < 465, de

    de_ef = huebscher_equal_friction(0.6, 0.3) * 1000
    print(f"Equal-fric 600x300 mm           De = {de_ef:.1f} mm")

    # 3. Duct pressure drop: 1.0 m3/s in 600x300 galvanized, 10 m
    r = duct_pressure_drop(1.0, a=0.6, b=0.3, L=10.0)
    print(f"Duct 1.0 m3/s in 600x300, 10 m: v={r['velocity_m_s']:.2f} m/s, "
          f"Re={r['Re']:.2e}, dp={r['dp_Pa']:.1f} Pa "
          f"({r['dp_Pa_per_m']:.2f} Pa/m)")
    assert 3 < r["velocity_m_s"] < 7 and 0.3 < r["dp_Pa_per_m"] < 3.0

    # 4. Hazen-Williams: 10 L/s in DN100 (ID 102.3 mm), C=130, 100 m
    #    Standard charts: v≈1.2 m/s, gradient ≈1.7 m/100m
    hw = hazen_williams_pressure_drop(0.010, 0.1023, C=130.0, L=100.0)
    print(f"H-W 10 L/s DN100 C=130 100 m:  v={hw['velocity_m_s']:.2f} m/s, "
          f"hf={hw['head_loss_m']:.2f} m ({hw['gradient_m_per_m']*100:.2f} m/100m), "
          f"dp={hw['dp_Pa']/1000:.1f} kPa")
    assert 0.8 < hw["velocity_m_s"] < 1.5
    assert 1.0 < hw["head_loss_m"] < 2.5

    # 5. H-W inversion round-trip
    q = hazen_williams_velocity_from_head_loss(hw["head_loss_m"], 0.1023, 130.0, 100.0)
    print(f"H-W inversion round-trip:      Q = {q*1000:.3f} L/s (expect 10.000)")
    assert abs(q - 0.010) < 1e-9

    print("-" * 60)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    _selftest()
