---

#### `app.py`
```python
"""
Interactive ATC Classroom Presentation & Flight-Path Simulator
Covers: CCO, CDO, CDFA, CNS/ATM Integration, Tactical Trade-offs, and Assessment Quiz.
Grounded strictly in the attached educational reference guide (cco_cdo_cdfa_atc_guide.txt).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ==============================================================================
# 1. PAGE CONFIG & GLOBAL CONSTANTS
# ==============================================================================
st.set_page_config(
    page_title="ATC Vertical Flight Efficiency Console | CCO · CDO · CDFA",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Color Palette: Radar / ATC Console Aesthetic
BG_PRIMARY = "#0b1220"
BG_CARD = "#111b2e"
BG_ELEVATED = "#16233b"
BORDER_SUBTLE = "#233554"
ACCENT_GREEN = "#39ff88"     # Primary Radar Green
ACCENT_CYAN = "#38bdf8"      # Secondary Telemetry Cyan
ACCENT_AMBER = "#fbbf24"     # Caution / Warning Amber
ACCENT_RED = "#ff4d6d"       # Conflict / Hazard Red
TEXT_PRIMARY = "#e6f1ff"
TEXT_MUTED = "#8fa3bf"

AIRCRAFT_PALETTE = [
    "#39ff88",  # Radar Green
    "#38bdf8",  # Sky Cyan
    "#fbbf24",  # Amber
    "#c084fc",  # Violet
    "#fb7185",  # Coral
    "#2dd4bf",  # Teal
]

FOOTER_DISCLAIMER = (
    "This tool is for educational purposes only and must not be used for real ATC "
    "operations or procedure design."
)


# ==============================================================================
# 2. CUSTOM CSS & UI HELPER COMPONENTS
# ==============================================================================
def inject_custom_css(presentation_mode: bool = False) -> None:
    """Injects dark radar/ATC console styling and responsive presentation scaling."""
    base_font = "19px" if presentation_mode else "15px"
    heading_scale = "1.22" if presentation_mode else "1.0"
    card_bg = "#0d1628" if presentation_mode else BG_CARD
    border_col = "#39ff8866" if presentation_mode else BORDER_SUBTLE

    hide_chrome_css = (
        """
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="stToolbar"] {visibility: hidden;}
        """
        if presentation_mode
        else ""
    )

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&display=swap');

        :root {{
            --bg-primary: {BG_PRIMARY};
            --bg-card: {card_bg};
            --bg-elevated: {BG_ELEVATED};
            --border-subtle: {border_col};
            --accent-green: {ACCENT_GREEN};
            --accent-cyan: {ACCENT_CYAN};
            --accent-amber: {ACCENT_AMBER};
            --accent-red: {ACCENT_RED};
            --text-primary: {TEXT_PRIMARY};
            --text-muted: {TEXT_MUTED};
        }}

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: {base_font};
            color: var(--text-primary);
        }}

        .stApp {{
            background-color: var(--bg-primary);
            background-image:
                radial-gradient(circle at 15% 15%, rgba(57, 255, 136, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 85% 20%, rgba(56, 189, 248, 0.06) 0%, transparent 45%);
        }}

        section[data-testid="stSidebar"] {{
            background-color: #080e1a;
            border-right: 1px solid var(--border-subtle);
        }}

        h1 {{
            font-size: calc(2.1rem * {heading_scale}) !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
            color: var(--text-primary) !important;
        }}
        h2 {{
            font-size: calc(1.5rem * {heading_scale}) !important;
            font-weight: 600 !important;
            color: var(--accent-cyan) !important;
            border-bottom: 1px solid var(--border-subtle);
            padding-bottom: 0.35rem;
            margin-top: 1.1rem !important;
        }}
        h3 {{
            font-size: calc(1.18rem * {heading_scale}) !important;
            font-weight: 600 !important;
            color: var(--text-primary) !important;
        }}

        /* Hero Banner with Pure CSS Radar Sweep */
        .atc-hero {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            background: linear-gradient(135deg, #0f1b30 0%, #13233d 60%, #0d192b 100%);
            border: 1px solid rgba(57, 255, 136, 0.35);
            border-radius: 14px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45), inset 0 0 24px rgba(57, 255, 136, 0.06);
        }}
        .atc-hero-badge {{
            display: inline-block;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--accent-green);
            background: rgba(57, 255, 136, 0.12);
            border: 1px solid rgba(57, 255, 136, 0.35);
            padding: 0.22rem 0.65rem;
            border-radius: 999px;
            margin-bottom: 0.6rem;
        }}
        .atc-hero-title {{
            font-size: calc(2.0rem * {heading_scale});
            font-weight: 700;
            line-height: 1.2;
            color: #ffffff;
            margin: 0 0 0.45rem 0;
        }}
        .atc-hero-sub {{
            font-size: calc(1.02rem * {heading_scale});
            color: var(--text-muted);
            margin: 0;
            max-width: 760px;
        }}

        /* Pure CSS Radar Scope */
        .radar-scope {{
            position: relative;
            width: 112px;
            height: 112px;
            min-width: 112px;
            border-radius: 50%;
            background:
                radial-gradient(circle, rgba(57, 255, 136, 0.14) 0%, rgba(11, 18, 32, 0.95) 72%);
            border: 2px solid rgba(57, 255, 136, 0.55);
            box-shadow: 0 0 22px rgba(57, 255, 136, 0.22), inset 0 0 14px rgba(57, 255, 136, 0.15);
            overflow: hidden;
        }}
        .radar-scope::before {{
            content: "";
            position: absolute;
            inset: 18px;
            border-radius: 50%;
            border: 1px dashed rgba(57, 255, 136, 0.35);
        }}
        .radar-scope::after {{
            content: "";
            position: absolute;
            inset: 36px;
            border-radius: 50%;
            border: 1px solid rgba(57, 255, 136, 0.25);
        }}
        .radar-crosshair-h {{
            position: absolute;
            top: 50%;
            left: 0;
            width: 100%;
            height: 1px;
            background: rgba(57, 255, 136, 0.25);
        }}
        .radar-crosshair-v {{
            position: absolute;
            left: 50%;
            top: 0;
            width: 1px;
            height: 100%;
            background: rgba(57, 255, 136, 0.25);
        }}
        .radar-sweep {{
            position: absolute;
            inset: 0;
            border-radius: 50%;
            background: conic-gradient(
                from 0deg,
                rgba(57, 255, 136, 0.42) 0deg,
                rgba(57, 255, 136, 0.08) 45deg,
                transparent 90deg,
                transparent 360deg
            );
            animation: radarSpin 4s linear infinite;
        }}
        .radar-blip {{
            position: absolute;
            top: 28%;
            left: 64%;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #39ff88;
            box-shadow: 0 0 8px #39ff88;
            animation: blipPulse 4s ease-in-out infinite;
        }}
        @keyframes radarSpin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        @keyframes blipPulse {{
            0%, 100% {{ opacity: 0.25; transform: scale(0.85); }}
            22% {{ opacity: 1; transform: scale(1.25); }}
            60% {{ opacity: 0.45; transform: scale(1.0); }}
        }}

        /* Content & Metric Cards */
        .atc-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 1.15rem 1.3rem;
            margin-bottom: 0.9rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
        }}
        .atc-card-title {{
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--accent-cyan);
            margin-bottom: 0.5rem;
        }}

        .metric-card {{
            background: linear-gradient(180deg, var(--bg-elevated) 0%, var(--bg-card) 100%);
            border: 1px solid var(--border-subtle);
            border-radius: 11px;
            padding: 0.9rem 1.05rem;
            margin-bottom: 0.65rem;
            transition: border-color 0.2s ease;
        }}
        .metric-card:hover {{
            border-color: rgba(56, 189, 248, 0.55);
        }}
        .metric-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.4rem;
            margin-bottom: 0.35rem;
        }}
        .metric-label {{
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }}
        .metric-value {{
            font-family: 'JetBrains Mono', monospace;
            font-size: calc(1.38rem * {heading_scale});
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.25;
        }}
        .metric-sub {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.22rem;
        }}

        /* Status Badges */
        .badge {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 0.14rem 0.48rem;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .badge-ok {{
            background: rgba(57, 255, 136, 0.14);
            color: #39ff88;
            border: 1px solid rgba(57, 255, 136, 0.4);
        }}
        .badge-warning {{
            background: rgba(251, 191, 36, 0.16);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.45);
        }}
        .badge-conflict {{
            background: rgba(255, 77, 109, 0.18);
            color: #ff4d6d;
            border: 1px solid rgba(255, 77, 109, 0.5);
        }}
        .badge-info {{
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.4);
        }}

        /* Concept Map Flow Nodes */
        .concept-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 0.9rem;
            margin: 0.75rem 0 1.2rem 0;
        }}
        .concept-node {{
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-top: 3px solid var(--accent-green);
            border-radius: 10px;
            padding: 1rem;
        }}
        .concept-node.cdo {{ border-top-color: var(--accent-cyan); }}
        .concept-node.cdfa {{ border-top-color: var(--accent-amber); }}
        .concept-node.cns {{ border-top-color: #c084fc; }}

        /* Fixed Educational Footer */
        .atc-footer {{
            margin-top: 2.2rem;
            padding: 0.85rem 1.2rem;
            background: #080e1a;
            border: 1px solid rgba(251, 191, 36, 0.35);
            border-radius: 10px;
            text-align: center;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem;
            color: var(--accent-amber);
        }}

        /* Tab styling */
        button[data-baseweb="tab"] {{
            font-weight: 600 !important;
            color: var(--text-muted) !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: var(--accent-green) !important;
        }}

        @media (max-width: 768px) {{
            .atc-hero {{
                flex-direction: column;
                align-items: flex-start;
                padding: 1.15rem;
            }}
            .radar-scope {{
                width: 84px;
                height: 84px;
                min-width: 84px;
            }}
        }}
        {hide_chrome_css}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(
    label: str,
    value: str,
    status: str = "INFO",
    subtitle: str = "",
) -> None:
    """Renders a styled ATC telemetry metric card with status pill."""
    status_upper = status.upper()
    badge_class = {
        "OK": "badge-ok",
        "WARNING": "badge-warning",
        "CONFLICT": "badge-conflict",
        "INFO": "badge-info",
    }.get(status_upper, "badge-info")

    sub_html = f'<div class="metric-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">{label}</span>
                <span class="badge {badge_class}">{status_upper}</span>
            </div>
            <div class="metric-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Renders the mandatory fixed educational disclaimer footer."""
    st.markdown(
        f'<div class="atc-footer">⚠️ {FOOTER_DISCLAIMER}</div>',
        unsafe_allow_html=True,
    )


# ==============================================================================
# 3. PURE-CALCULATION KINEMATICS & SIMULATION FUNCTIONS (NO STREAMLIT DEPENDENCY)
# ==============================================================================
def compute_cco_profiles(
    cruise_fl: int,
    climb_rate_fpm: float,
    ground_speed_kt: float,
    level_offs: list[tuple[float, float]],
    extra_fuel_kg_per_min: float,
) -> dict[str, Any]:
    """
    Computes side-view (Distance NM vs Altitude ft) trajectories for:
      1) Continuous Climb Operations (CCO)
      2) Stepped Climb with intermediate ATC level-offs

    Educational approximation:
    - Constant ground speed (GS in knots -> NM/min = GS / 60).
    - Constant climb rate (ROC in ft/min) during climbing segments.
    - Extra fuel approximated linearly with level-flight duration.
    """
    target_alt_ft = float(cruise_fl * 100)
    gs_nm_per_min = ground_speed_kt / 60.0

    # --- 1. Continuous Climb (CCO) ---
    cco_time_min = target_alt_ft / climb_rate_fpm
    cco_dist_nm = cco_time_min * gs_nm_per_min
    cco_df = pd.DataFrame(
        {
            "time_min": [0.0, cco_time_min],
            "distance_nm": [0.0, cco_dist_nm],
            "altitude_ft": [0.0, target_alt_ft],
            "phase": ["Climb", "Top of Climb (ToC)"],
        }
    )

    # --- 2. Stepped Climb ---
    # Sort valid level-offs below target cruise altitude
    valid_steps = sorted(
        [(alt, dur) for alt, dur in level_offs if 0 < alt < target_alt_ft and dur > 0],
        key=lambda x: x[0],
    )

    t_curr = 0.0
    d_curr = 0.0
    alt_curr = 0.0
    step_points = [(t_curr, d_curr, alt_curr, "Takeoff")]
    total_level_min = 0.0

    for step_alt, hold_min in valid_steps:
        if step_alt <= alt_curr:
            continue
        # Climb to intermediate altitude
        dt_climb = (step_alt - alt_curr) / climb_rate_fpm
        t_curr += dt_climb
        d_curr += dt_climb * gs_nm_per_min
        alt_curr = step_alt
        step_points.append((t_curr, d_curr, alt_curr, f"Level-off Start ({int(alt_curr):,} ft)"))

        # Level hold segment
        t_curr += hold_min
        d_curr += hold_min * gs_nm_per_min
        total_level_min += hold_min
        step_points.append((t_curr, d_curr, alt_curr, f"Resume Climb ({int(alt_curr):,} ft)"))

    # Final climb segment to initial cruise altitude
    if alt_curr < target_alt_ft:
        dt_final = (target_alt_ft - alt_curr) / climb_rate_fpm
        t_curr += dt_final
        d_curr += dt_final * gs_nm_per_min
        alt_curr = target_alt_ft
        step_points.append((t_curr, d_curr, alt_curr, "Top of Climb (ToC)"))

    step_df = pd.DataFrame(
        step_points, columns=["time_min", "distance_nm", "altitude_ft", "phase"]
    )

    time_diff_min = t_curr - cco_time_min
    dist_diff_nm = d_curr - cco_dist_nm
    extra_fuel_kg = total_level_min * extra_fuel_kg_per_min

    return {
        "cco_df": cco_df,
        "step_df": step_df,
        "cco_time_min": cco_time_min,
        "cco_dist_nm": cco_dist_nm,
        "step_time_min": t_curr,
        "step_dist_nm": d_curr,
        "time_diff_min": time_diff_min,
        "dist_diff_nm": dist_diff_nm,
        "total_level_min": total_level_min,
        "extra_fuel_kg": extra_fuel_kg,
    }


def compute_cdo_profiles(
    start_alt_ft: float,
    faf_alt_ft: float,
    descent_angle_deg: float,
    ground_speed_kt: float,
    step_downs: list[tuple[float, float]],
    extra_fuel_kg_per_min: float,
) -> dict[str, Any]:
    """
    Computes side-view (Distance to FAF NM vs Altitude ft) trajectories for:
      1) Continuous Descent Operations (CDO) from Top of Descent (ToD) to FAF
      2) Step-Down Descent with intermediate level segments

    Educational approximation:
    - Geometric descent gradient: tan(angle) * 6076.12 ft/NM.
    - Also computes the standard ATC 3 NM per 1,000 ft rule-of-thumb ToD for comparison.
    """
    alt_to_lose = start_alt_ft - faf_alt_ft
    ft_per_nm = math.tan(math.radians(descent_angle_deg)) * 6076.12
    gs_nm_per_min = ground_speed_kt / 60.0
    rod_fpm = ft_per_nm * gs_nm_per_min

    # Rule of thumb: 3 NM per 1,000 ft
    tod_rule_of_thumb_nm = (alt_to_lose / 1000.0) * 3.0

    # --- 1. Continuous Descent (CDO) ---
    cdo_descent_dist_nm = alt_to_lose / ft_per_nm
    cdo_descent_time_min = cdo_descent_dist_nm / gs_nm_per_min

    # --- 2. Step-Down Profile ---
    # Sort valid step-down altitudes descending from start_alt_ft down to faf_alt_ft
    valid_steps = sorted(
        [(alt, length_nm) for alt, length_nm in step_downs if faf_alt_ft < alt < start_alt_ft and length_nm > 0],
        key=lambda x: x[0],
        reverse=True,
    )

    total_level_nm = sum(length for _, length in valid_steps)
    total_level_min = total_level_nm / gs_nm_per_min
    step_start_dist_nm = cdo_descent_dist_nm + total_level_nm

    # Build trajectory forward from initial point at distance = step_start_dist_nm down to FAF (0 NM)
    max_plot_dist = max(step_start_dist_nm, tod_rule_of_thumb_nm) * 1.08

    # CDO points (cruise segment before ToD, then continuous descent to FAF at 0 NM)
    cdo_points = [
        (0.0, max_plot_dist, start_alt_ft, "Cruise"),
        (
            (max_plot_dist - cdo_descent_dist_nm) / gs_nm_per_min,
            cdo_descent_dist_nm,
            start_alt_ft,
            "Top of Descent (ToD)",
        ),
        (
            (max_plot_dist - cdo_descent_dist_nm) / gs_nm_per_min + cdo_descent_time_min,
            0.0,
            faf_alt_ft,
            "Final Approach Fix (FAF)",
        ),
    ]
    cdo_df = pd.DataFrame(
        cdo_points, columns=["time_min", "dist_to_faf_nm", "altitude_ft", "phase"]
    )

    # Step-down points
    t_curr = 0.0
    d_rem = max_plot_dist
    alt_curr = start_alt_ft
    step_points = [(t_curr, d_rem, alt_curr, "Cruise")]

    # Cruise to step-down ToD
    dt_cruise = (d_rem - step_start_dist_nm) / gs_nm_per_min
    t_curr += dt_cruise
    d_rem = step_start_dist_nm
    step_points.append((t_curr, d_rem, alt_curr, "Step-Down ToD"))

    for step_alt, level_nm in valid_steps:
        if step_alt >= alt_curr:
            continue
        # Descend to intermediate step altitude
        d_desc = (alt_curr - step_alt) / ft_per_nm
        dt_desc = d_desc / gs_nm_per_min
        t_curr += dt_desc
        d_rem -= d_desc
        alt_curr = step_alt
        step_points.append((t_curr, d_rem, alt_curr, f"Step-Down Level ({int(alt_curr):,} ft)"))

        # Fly level segment
        dt_lvl = level_nm / gs_nm_per_min
        t_curr += dt_lvl
        d_rem -= level_nm
        step_points.append((t_curr, d_rem, alt_curr, f"Resume Descent ({int(alt_curr):,} ft)"))

    # Final descent to FAF (0 NM)
    if alt_curr > faf_alt_ft:
        d_final = (alt_curr - faf_alt_ft) / ft_per_nm
        dt_final = d_final / gs_nm_per_min
        t_curr += dt_final
        d_rem = max(0.0, d_rem - d_final)
        alt_curr = faf_alt_ft
        step_points.append((t_curr, 0.0, alt_curr, "Final Approach Fix (FAF)"))

    step_df = pd.DataFrame(
        step_points, columns=["time_min", "dist_to_faf_nm", "altitude_ft", "phase"]
    )

    extra_fuel_kg = total_level_min * extra_fuel_kg_per_min

    return {
        "cdo_df": cdo_df,
        "step_df": step_df,
        "cdo_descent_dist_nm": cdo_descent_dist_nm,
        "tod_rule_of_thumb_nm": tod_rule_of_thumb_nm,
        "rod_fpm": rod_fpm,
        "total_level_nm": total_level_nm,
        "total_level_sec": total_level_min * 60.0,
        "total_level_min": total_level_min,
        "extra_fuel_kg": extra_fuel_kg,
        "max_plot_dist": max_plot_dist,
    }


def compute_cdfa_profiles(
    faf_alt_ft: float,
    thr_elev_ft: float,
    mda_ft: float,
    dda_buffer_ft: float,
    vda_deg: float,
    ground_speed_kt: float,
    dive_rod_fpm: float,
    include_terrain: bool,
) -> dict[str, Any]:
    """
    Computes final approach profiles from FAF to Runway Threshold (0 NM):
      1) CDFA: Constant VDA slope from FAF through DDA to Threshold
      2) Dive and Drive: Rapid initial descent to MDA, level segment near terrain, final descent

    Educational approximation:
    - Rate of descent (fpm) = GS (kt) * tan(VDA) * (6076.12 / 60).
    """
    dda_ft = mda_ft + dda_buffer_ft
    ft_per_nm = math.tan(math.radians(vda_deg)) * 6076.12
    gs_nm_per_min = ground_speed_kt / 60.0
    cdfa_rod_fpm = ft_per_nm * gs_nm_per_min

    # Distance from FAF to Threshold along constant VDA
    alt_drop_total = faf_alt_ft - thr_elev_ft
    faf_dist_nm = alt_drop_total / ft_per_nm
    cdfa_total_min = faf_dist_nm / gs_nm_per_min

    # Distance from Threshold where CDFA crosses DDA
    dda_dist_nm = (dda_ft - thr_elev_ft) / ft_per_nm
    dda_time_min = (faf_dist_nm - dda_dist_nm) / gs_nm_per_min

    cdfa_df = pd.DataFrame(
        [
            (0.0, faf_dist_nm, faf_alt_ft, "Final Approach Fix (FAF)"),
            (dda_time_min, dda_dist_nm, dda_ft, f"DDA ({int(dda_ft):,} ft)"),
            (cdfa_total_min, 0.0, thr_elev_ft, "Runway Threshold"),
        ],
        columns=["time_min", "dist_to_thr_nm", "altitude_ft", "phase"],
    )

    # --- Dive and Drive Profile ---
    # Rapid descent at dive_rod_fpm down to MDA
    dive_ft_per_nm = dive_rod_fpm / gs_nm_per_min
    alt_to_mda = faf_alt_ft - mda_ft
    dive_dist_nm = alt_to_mda / dive_ft_per_nm

    # Visual segment from Missed Approach Point (MAPt) / final descent point to threshold
    visual_drop_ft = mda_ft - thr_elev_ft
    # Final visual descent at ~3.5 deg or steeper if close
    visual_grad_ft_per_nm = math.tan(math.radians(3.5)) * 6076.12
    visual_dist_nm = min(faf_dist_nm * 0.28, visual_drop_ft / visual_grad_ft_per_nm)

    # Ensure dive + visual does not exceed faf_dist_nm
    if dive_dist_nm + visual_dist_nm >= faf_dist_nm * 0.92:
        dive_dist_nm = max(0.5, faf_dist_nm * 0.55)
        visual_dist_nm = max(0.4, faf_dist_nm * 0.18)

    mda_start_dist_nm = faf_dist_nm - dive_dist_nm
    mda_end_dist_nm = visual_dist_nm
    level_mda_dist_nm = max(0.0, mda_start_dist_nm - mda_end_dist_nm)

    t1 = (faf_dist_nm - mda_start_dist_nm) / gs_nm_per_min
    t2 = t1 + (level_mda_dist_nm / gs_nm_per_min)
    t3 = t2 + (mda_end_dist_nm / gs_nm_per_min)

    dive_df = pd.DataFrame(
        [
            (0.0, faf_dist_nm, faf_alt_ft, "Final Approach Fix (FAF)"),
            (t1, mda_start_dist_nm, mda_ft, f"Level-off at MDA ({int(mda_ft):,} ft)"),
            (t2, mda_end_dist_nm, mda_ft, "Visual Descent Point"),
            (t3, 0.0, thr_elev_ft, "Runway Threshold"),
        ],
        columns=["time_min", "dist_to_thr_nm", "altitude_ft", "phase"],
    )

    # Optional schematic terrain profile (always safely below threshold/MDA, rising near mid-final)
    dist_grid = np.linspace(0.0, faf_dist_nm, 80)
    if include_terrain:
        # Smooth rising terrain ridge peaking around 65% of approach distance
        ridge_center = faf_dist_nm * 0.62
        ridge_width = max(0.8, faf_dist_nm * 0.22)
        max_ridge_height = max(0.0, (mda_ft - thr_elev_ft) - 260.0)
        terrain_alt = thr_elev_ft + max_ridge_height * np.exp(
            -0.5 * ((dist_grid - ridge_center) / ridge_width) ** 2
        )
        # Taper smoothly to 0 above threshold at runway end
        taper = np.clip(dist_grid / max(0.8, faf_dist_nm * 0.25), 0.0, 1.0)
        terrain_alt = thr_elev_ft + (terrain_alt - thr_elev_ft) * taper
    else:
        terrain_alt = np.full_like(dist_grid, thr_elev_ft)

    terrain_df = pd.DataFrame({"dist_to_thr_nm": dist_grid, "terrain_ft": terrain_alt})
    min_agl_ft = float(mda_ft - np.max(terrain_alt[(dist_grid >= mda_end_dist_nm) & (dist_grid <= mda_start_dist_nm)])) if level_mda_dist_nm > 0 else float(mda_ft - thr_elev_ft)

    return {
        "cdfa_df": cdfa_df,
        "dive_df": dive_df,
        "terrain_df": terrain_df,
        "dda_ft": dda_ft,
        "faf_dist_nm": faf_dist_nm,
        "cdfa_rod_fpm": cdfa_rod_fpm,
        "level_mda_dist_nm": level_mda_dist_nm,
        "mda_start_dist_nm": mda_start_dist_nm,
        "mda_end_dist_nm": mda_end_dist_nm,
        "min_agl_ft": max(0.0, min_agl_ft),
        "stabilized_ok": cdfa_rod_fpm <= 1000.0,
    }


def interpolate_trajectory_2d_3d(
    waypoints_xy: list[tuple[float, float]],
    start_alt_ft: float,
    target_alt_ft: float,
    vertical_rate_fpm: float,
    speed_kt: float,
    start_offset_min: float,
    time_grid_min: np.ndarray,
    level_off_alt_ft: float | None = None,
    level_off_duration_min: float = 0.0,
) -> pd.DataFrame:
    """
    Simulates 3D aircraft kinematics along a piecewise-linear XY route with optional
    tactical ATC intermediate level-off.
    """
    # Compute cumulative route distances
    pts = np.array(waypoints_xy, dtype=float)
    seg_vecs = np.diff(pts, axis=0)
    seg_lens = np.hypot(seg_vecs[:, 0], seg_vecs[:, 1])
    cum_dist = np.concatenate([[0.0], np.cumsum(seg_lens)])
    total_route_nm = float(cum_dist[-1])

    gs_nm_per_min = speed_kt / 60.0
    is_climbing = target_alt_ft >= start_alt_ft
    rate_signed = abs(vertical_rate_fpm) if is_climbing else -abs(vertical_rate_fpm)

    # Precompute vertical profile as a function of elapsed flight time (tau >= 0)
    use_hold = (
        level_off_alt_ft is not None
        and level_off_duration_min > 0
        and (
            (is_climbing and start_alt_ft < level_off_alt_ft < target_alt_ft)
            or (not is_climbing and target_alt_ft < level_off_alt_ft < start_alt_ft)
        )
    )

    if use_hold:
        t_to_hold = abs(level_off_alt_ft - start_alt_ft) / abs(vertical_rate_fpm)
        t_end_hold = t_to_hold + level_off_duration_min
        t_to_target = t_end_hold + abs(target_alt_ft - level_off_alt_ft) / abs(vertical_rate_fpm)
    else:
        t_to_hold = 0.0
        t_end_hold = 0.0
        t_to_target = abs(target_alt_ft - start_alt_ft) / max(1.0, abs(vertical_rate_fpm))

    rows = []
    for t in time_grid_min:
        tau = max(0.0, float(t) - start_offset_min)
        dist_flown = min(total_route_nm, tau * gs_nm_per_min)

        # Interpolate X, Y along route
        if total_route_nm <= 1e-6 or dist_flown <= 0.0:
            x, y = float(pts[0, 0]), float(pts[0, 1])
        elif dist_flown >= total_route_nm:
            x, y = float(pts[-1, 0]), float(pts[-1, 1])
        else:
            idx = int(np.searchsorted(cum_dist, dist_flown, side="right") - 1)
            idx = min(max(idx, 0), len(seg_lens) - 1)
            frac = (dist_flown - cum_dist[idx]) / max(1e-6, seg_lens[idx])
            x = float(pts[idx, 0] + frac * seg_vecs[idx, 0])
            y = float(pts[idx, 1] + frac * seg_vecs[idx, 1])

        # Interpolate Altitude
        if tau <= 0.0:
            alt = start_alt_ft
        elif use_hold:
            if tau <= t_to_hold:
                alt = start_alt_ft + rate_signed * tau
            elif tau <= t_end_hold:
                alt = float(level_off_alt_ft)
            elif tau <= t_to_target:
                alt = float(level_off_alt_ft) + rate_signed * (tau - t_end_hold)
            else:
                alt = target_alt_ft
        else:
            if tau <= t_to_target:
                alt = start_alt_ft + rate_signed * tau
            else:
                alt = target_alt_ft

        rows.append((float(t), x, y, alt, dist_flown))

    return pd.DataFrame(rows, columns=["time_min", "x_nm", "y_nm", "altitude_ft", "dist_nm"])


def compute_sid_star_scenario(
    sid_start: tuple[float, float],
    sid_end: tuple[float, float],
    star_start: tuple[float, float],
    star_end: tuple[float, float],
    dep_start_alt: float,
    dep_target_alt: float,
    dep_roc_fpm: float,
    dep_gs_kt: float,
    arr_start_alt: float,
    arr_target_alt: float,
    arr_rod_fpm: float,
    arr_gs_kt: float,
    arr_offset_min: float,
    min_horiz_nm: float,
    min_vert_ft: float,
    level_off_target: str = "None",
    level_off_alt_ft: float = 9000.0,
    level_off_dur_min: float = 2.5,
) -> dict[str, Any]:
    """
    Simulates crossing SID (Departure) and STAR (Arrival) trajectories, checks 3D separation
    minima at every time step, and quantifies tactical ATC level-off trade-offs.
    """
    dep_dist = math.hypot(sid_end[0] - sid_start[0], sid_end[1] - sid_start[1])
    arr_dist = math.hypot(star_end[0] - star_start[0], star_end[1] - star_start[1])

    dep_dur = dep_dist / max(1.0, dep_gs_kt / 60.0)
    arr_dur = arr_offset_min + arr_dist / max(1.0, arr_gs_kt / 60.0)
    sim_end_min = max(dep_dur, arr_dur, 8.0)

    time_grid = np.linspace(0.0, sim_end_min, 120)

    dep_hold_alt = level_off_alt_ft if level_off_target == "Departure (Break CCO)" else None
    dep_hold_dur = level_off_dur_min if level_off_target == "Departure (Break CCO)" else 0.0

    arr_hold_alt = level_off_alt_ft if level_off_target == "Arrival (Break CDO)" else None
    arr_hold_dur = level_off_dur_min if level_off_target == "Arrival (Break CDO)" else 0.0

    dep_df = interpolate_trajectory_2d_3d(
        [sid_start, sid_end],
        dep_start_alt,
        dep_target_alt,
        dep_roc_fpm,
        dep_gs_kt,
        0.0,
        time_grid,
        dep_hold_alt,
        dep_hold_dur,
    )
    arr_df = interpolate_trajectory_2d_3d(
        [star_start, star_end],
        arr_start_alt,
        arr_target_alt,
        arr_rod_fpm,
        arr_gs_kt,
        arr_offset_min,
        time_grid,
        arr_hold_alt,
        arr_hold_dur,
    )

    horiz_sep = np.hypot(dep_df["x_nm"] - arr_df["x_nm"], dep_df["y_nm"] - arr_df["y_nm"])
    vert_sep = np.abs(dep_df["altitude_ft"] - arr_df["altitude_ft"])
    conflict_mask = (horiz_sep < min_horiz_nm) & (vert_sep < min_vert_ft)

    sep_df = pd.DataFrame(
        {
            "time_min": time_grid,
            "horiz_sep_nm": horiz_sep,
            "vert_sep_ft": vert_sep,
            "conflict": conflict_mask,
        }
    )

    # Closest point of approach (normalized separation index)
    norm_sep = np.maximum(horiz_sep / max(0.1, min_horiz_nm), vert_sep / max(10.0, min_vert_ft))
    cpa_idx = int(np.argmin(norm_sep))

    # Educational fuel penalty approximation (climb level-off burns ~2.3x more extra fuel than descent)
    if level_off_target == "Departure (Break CCO)":
        extra_fuel_kg = level_off_dur_min * 32.0
    elif level_off_target == "Arrival (Break CDO)":
        extra_fuel_kg = level_off_dur_min * 13.0
    else:
        extra_fuel_kg = 0.0

    return {
        "time_grid": time_grid,
        "dep_df": dep_df,
        "arr_df": arr_df,
        "sep_df": sep_df,
        "has_conflict": bool(conflict_mask.any()),
        "conflict_count": int(conflict_mask.sum()),
        "cpa_time_min": float(time_grid[cpa_idx]),
        "cpa_horiz_nm": float(horiz_sep.iloc[cpa_idx]),
        "cpa_vert_ft": float(vert_sep.iloc[cpa_idx]),
        "extra_fuel_kg": extra_fuel_kg,
    }


def compute_multi_aircraft_tma(
    flights_df: pd.DataFrame,
    min_horiz_nm: float = 3.0,
    min_vert_ft: float = 1000.0,
) -> dict[str, Any]:
    """
    Simulates 3-6 simultaneous departures/arrivals converging on a TMA fixes/runway layout
    and checks pairwise separation across time.
    """
    # Predefined radial sector entry/exit gates around airport center (0, 0)
    dep_gates = [(28.0, 14.0), (26.0, -16.0), (-24.0, 18.0)]
    arr_gates = [(-28.0, -14.0), (14.0, 26.0), (-16.0, -25.0)]

    time_grid = np.linspace(0.0, 12.0, 96)
    trajectories: dict[str, pd.DataFrame] = {}

    dep_idx = 0
    arr_idx = 0
    for i, row in flights_df.iterrows():
        callsign = str(row["Callsign"]).strip() or f"ACFT{i+1}"
        mtype = str(row["Type"]).strip()
        start_alt = float(row["Start Alt (ft)"])
        speed_kt = float(row["Speed (kt)"])
        vrate = abs(float(row["Vert Rate (fpm)"]))

        if mtype == "Departure":
            gate = dep_gates[dep_idx % len(dep_gates)]
            dep_idx += 1
            waypoints = [(0.0, 0.0), gate]
            target_alt = max(start_alt + 14000.0, 24000.0)
        else:
            gate = arr_gates[arr_idx % len(arr_gates)]
            arr_idx += 1
            waypoints = [gate, (0.0, 0.0)]
            target_alt = 2000.0

        traj = interpolate_trajectory_2d_3d(
            waypoints_xy=waypoints,
            start_alt_ft=start_alt,
            target_alt_ft=target_alt,
            vertical_rate_fpm=vrate,
            speed_kt=speed_kt,
            start_offset_min=0.0,
            time_grid_min=time_grid,
        )
        traj["callsign"] = callsign
        traj["type"] = mtype
        trajectories[callsign] = traj

    # Pairwise conflict check across all time steps
    callsigns = list(trajectories.keys())
    conflict_events = []
    conflict_times = set()

    for idx_a in range(len(callsigns)):
        for idx_b in range(idx_a + 1, len(callsigns)):
            cs_a, cs_b = callsigns[idx_a], callsigns[idx_b]
            df_a, df_b = trajectories[cs_a], trajectories[cs_b]
            h_sep = np.hypot(df_a["x_nm"] - df_b["x_nm"], df_a["y_nm"] - df_b["y_nm"])
            v_sep = np.abs(df_a["altitude_ft"] - df_b["altitude_ft"])
            viol = (h_sep < min_horiz_nm) & (v_sep < min_vert_ft)
            if viol.any():
                first_idx = int(np.argmax(viol))
                for t_idx in np.where(viol)[0]:
                    conflict_times.add(float(time_grid[t_idx]))
                conflict_events.append(
                    {
                        "Pair": f"{cs_a} vs {cs_b}",
                        "First Conflict (min)": round(float(time_grid[first_idx]), 2),
                        "Min Horiz (NM)": round(float(h_sep.min()), 2),
                        "Min Vert (ft)": int(round(float(v_sep.min()))),
                    }
                )

    return {
        "time_grid": time_grid,
        "trajectories": trajectories,
        "conflict_events": pd.DataFrame(conflict_events),
        "conflict_times": sorted(conflict_times),
    }


# ==============================================================================
# 4. PLOTLY CHART BUILDERS (CONSISTENT RADAR CONSOLE THEME + ANIMATION)
# ==============================================================================
def apply_radar_layout(
    fig: go.Figure,
    title: str,
    xaxis_title: str,
    yaxis_title: str,
    height: int = 470,
    presentation_mode: bool = False,
) -> go.Figure:
    """Applies unified dark ATC radar console styling and animation controls."""
    font_size = 15 if presentation_mode else 12
    title_size = 20 if presentation_mode else 16

    fig.update_layout(
        title=dict(text=title, font=dict(size=title_size, color=TEXT_PRIMARY, family="Inter")),
        paper_bgcolor=BG_CARD,
        plot_bgcolor="#09101d",
        font=dict(color=TEXT_PRIMARY, family="Inter", size=font_size),
        height=height,
        margin=dict(l=60, r=30, t=65, b=85),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1.0,
            bgcolor="rgba(11,18,32,0.7)",
            bordercolor=BORDER_SUBTLE,
            borderwidth=1,
        ),
        xaxis=dict(
            title=xaxis_title,
            gridcolor="#1b2b47",
            zerolinecolor="#2a4066",
            showline=True,
            linecolor=BORDER_SUBTLE,
        ),
        yaxis=dict(
            title=yaxis_title,
            gridcolor="#1b2b47",
            zerolinecolor="#2a4066",
            showline=True,
            linecolor=BORDER_SUBTLE,
        ),
    )
    return fig


def add_play_pause_controls(
    fig: go.Figure,
    frames: list[go.Frame],
    slider_steps: list[dict[str, Any]],
    frame_duration_ms: int = 90,
) -> go.Figure:
    """Attaches smooth Play/Pause buttons and a scrubbed time slider to a Plotly figure."""
    fig.frames = frames
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.0,
                y=-0.20,
                xanchor="left",
                yanchor="top",
                direction="left",
                pad=dict(r=8, t=4),
                bgcolor=BG_ELEVATED,
                bordercolor=ACCENT_GREEN,
                borderwidth=1,
                font=dict(color=ACCENT_GREEN, size=12),
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=frame_duration_ms, redraw=True),
                                fromcurrent=True,
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                ],
            )
        ],
        sliders=[
            dict(
                active=0,
                yanchor="top",
                xanchor="left",
                y=-0.18,
                x=0.18,
                len=0.82,
                pad=dict(b=6, t=6),
                bgcolor=BG_ELEVATED,
                bordercolor=BORDER_SUBTLE,
                font=dict(color=TEXT_MUTED, size=11),
                currentvalue=dict(
                    prefix="Sim Time: ",
                    suffix=" min",
                    visible=True,
                    xanchor="right",
                    font=dict(color=ACCENT_CYAN, size=12),
                ),
                steps=slider_steps,
            )
        ],
    )
    return fig


def build_cco_chart(res: dict[str, Any], presentation_mode: bool = False) -> go.Figure:
    """Builds animated side-view chart comparing CCO vs Stepped Climb."""
    cco_df = res["cco_df"]
    step_df = res["step_df"]

    fig = go.Figure()

    # Static trajectory lines
    fig.add_trace(
        go.Scatter(
            x=cco_df["distance_nm"],
            y=cco_df["altitude_ft"],
            mode="lines+markers",
            name="Continuous Climb (CCO)",
            line=dict(color=ACCENT_GREEN, width=3.5),
            marker=dict(size=7, color=ACCENT_GREEN),
            hovertemplate="Dist: %{x:.1f} NM<br>Alt: %{y:,.0f} ft<extra>CCO</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=step_df["distance_nm"],
            y=step_df["altitude_ft"],
            mode="lines+markers",
            name="Stepped Climb (ATC Holds)",
            line=dict(color=ACCENT_AMBER, width=3, dash="dash"),
            marker=dict(size=7, color=ACCENT_AMBER),
            hovertemplate="Dist: %{x:.1f} NM<br>Alt: %{y:,.0f} ft<extra>Stepped</extra>",
        )
    )

    # Animated aircraft markers (Trace 2 = CCO aircraft, Trace 3 = Stepped aircraft)
    fig.add_trace(
        go.Scatter(
            x=[0.0],
            y=[0.0],
            mode="markers+text",
            name="CCO Aircraft",
            text=["✈ CCO"],
            textposition="top left",
            textfont=dict(color=ACCENT_GREEN, size=12),
            marker=dict(size=14, color=ACCENT_GREEN, symbol="triangle-right", line=dict(width=1.5, color="#ffffff")),
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[0.0],
            y=[0.0],
            mode="markers+text",
            name="Stepped Aircraft",
            text=["✈ STEP"],
            textposition="bottom right",
            textfont=dict(color=ACCENT_AMBER, size=12),
            marker=dict(size=14, color=ACCENT_AMBER, symbol="triangle-right", line=dict(width=1.5, color="#ffffff")),
            showlegend=False,
        )
    )

    # Build time-sampled animation frames
    max_t = max(res["step_time_min"], res["cco_time_min"], 1.0)
    t_samples = np.linspace(0.0, max_t, 50)
    frames = []
    steps = []

    for idx, t in enumerate(t_samples):
        cco_x = float(np.interp(t, cco_df["time_min"], cco_df["distance_nm"]))
        cco_y = float(np.interp(t, cco_df["time_min"], cco_df["altitude_ft"]))
        stp_x = float(np.interp(t, step_df["time_min"], step_df["distance_nm"]))
        stp_y = float(np.interp(t, step_df["time_min"], step_df["altitude_ft"]))

        frame_name = f"f{idx}"
        frames.append(
            go.Frame(
                name=frame_name,
                data=[
                    go.Scatter(x=[cco_x], y=[cco_y]),
                    go.Scatter(x=[stp_x], y=[stp_y]),
                ],
                traces=[2, 3],
            )
        )
        steps.append(
            dict(
                method="animate",
                label=f"{t:.1f}",
                args=[
                    [frame_name],
                    dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0)),
                ],
            )
        )

    apply_radar_layout(
        fig,
        title="Departure Climb Profile: Continuous Climb (CCO) vs. Stepped Climb",
        xaxis_title="Horizontal Distance from Departure Airport (NM)",
        yaxis_title="Altitude (ft)",
        presentation_mode=presentation_mode,
    )
    add_play_pause_controls(fig, frames, steps)
    return fig


def build_cdo_chart(res: dict[str, Any], presentation_mode: bool = False) -> go.Figure:
    """Builds animated side-view chart comparing CDO vs Step-Down Approach."""
    cdo_df = res["cdo_df"]
    step_df = res["step_df"]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=cdo_df["dist_to_faf_nm"],
            y=cdo_df["altitude_ft"],
            mode="lines+markers",
            name="Continuous Descent (CDO)",
            line=dict(color=ACCENT_CYAN, width=3.5),
            marker=dict(size=7, color=ACCENT_CYAN),
            hovertemplate="Dist to FAF: %{x:.1f} NM<br>Alt: %{y:,.0f} ft<extra>CDO</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=step_df["dist_to_faf_nm"],
            y=step_df["altitude_ft"],
            mode="lines+markers",
            name="Step-Down Arrival",
            line=dict(color=ACCENT_AMBER, width=3, dash="dash"),
            marker=dict(size=7, color=ACCENT_AMBER),
            hovertemplate="Dist to FAF: %{x:.1f} NM<br>Alt: %{y:,.0f} ft<extra>Step-Down</extra>",
        )
    )

    # Vertical reference marker for 3 NM / 1,000 ft Rule-of-Thumb ToD
    fig.add_vline(
        x=res["tod_rule_of_thumb_nm"],
        line_width=1.5,
        line_dash="dot",
        line_color=ACCENT_GREEN,
        annotation_text=f"3:1 Rule ToD ({res['tod_rule_of_thumb_nm']:.1f} NM)",
        annotation_position="top right",
        annotation_font_color=ACCENT_GREEN,
    )

    # Animated aircraft markers (Traces 2 and 3)
    start_x = float(cdo_df["dist_to_faf_nm"].iloc[0])
    start_y = float(cdo_df["altitude_ft"].iloc[0])

    fig.add_trace(
        go.Scatter(
            x=[start_x],
            y=[start_y],
            mode="markers+text",
            text=["✈ CDO"],
            textposition="top right",
            textfont=dict(color=ACCENT_CYAN, size=12),
            marker=dict(size=14, color=ACCENT_CYAN, symbol="triangle-right", line=dict(width=1.5, color="#ffffff")),
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[start_x],
            y=[start_y],
            mode="markers+text",
            text=["✈ STEP"],
            textposition="bottom left",
            textfont=dict(color=ACCENT_AMBER, size=12),
            marker=dict(size=14, color=ACCENT_AMBER, symbol="triangle-right", line=dict(width=1.5, color="#ffffff")),
            showlegend=False,
        )
    )

    max_t = max(float(cdo_df["time_min"].iloc[-1]), float(step_df["time_min"].iloc[-1]), 1.0)
    t_samples = np.linspace(0.0, max_t, 50)
    frames = []
    steps = []

    for idx, t in enumerate(t_samples):
        cdo_x = float(np.interp(t, cdo_df["time_min"], cdo_df["dist_to_faf_nm"]))
        cdo_y = float(np.interp(t, cdo_df["time_min"], cdo_df["altitude_ft"]))
        stp_x = float(np.interp(t, step_df["time_min"], step_df["dist_to_faf_nm"]))
        stp_y = float(np.interp(t, step_df["time_min"], step_df["altitude_ft"]))

        frame_name = f"cdo_{idx}"
        frames.append(
            go.Frame(
                name=frame_name,
                data=[
                    go.Scatter(x=[cdo_x], y=[cdo_y]),
                    go.Scatter(x=[stp_x], y=[stp_y]),
                ],
                traces=[2, 3],
            )
        )
        steps.append(
            dict(
                method="animate",
                label=f"{t:.1f}",
                args=[
                    [frame_name],
                    dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0)),
                ],
            )
        )

    apply_radar_layout(
        fig,
        title="Arrival Descent Profile: CDO vs. Step-Down (Descending Toward FAF at 0 NM)",
        xaxis_title="Distance to Final Approach Fix — FAF (NM) [Left → Right = Inbound]",
        yaxis_title="Altitude (ft)",
        presentation_mode=presentation_mode,
    )
    # Reverse X-axis so aircraft flies visually Left-to-Right toward FAF (0 NM)
    fig.update_xaxes(autorange="reversed")
    add_play_pause_controls(fig, frames, steps)
    return fig


def build_cdfa_chart(res: dict[str, Any], presentation_mode: bool = False) -> go.Figure:
    """Builds animated final approach chart comparing CDFA vs Dive-and-Drive with CFIT zone."""
    cdfa_df = res["cdfa_df"]
    dive_df = res["dive_df"]
    terrain_df = res["terrain_df"]

    fig = go.Figure()

    # Terrain fill
    fig.add_trace(
        go.Scatter(
            x=terrain_df["dist_to_thr_nm"],
            y=terrain_df["terrain_ft"],
            mode="lines",
            name="Terrain / Ground Profile",
            fill="tozeroy",
            fillcolor="rgba(120, 90, 60, 0.32)",
            line=dict(color="#a17c5b", width=2),
            hovertemplate="Dist: %{x:.2f} NM<br>Terrain: %{y:,.0f} ft<extra></extra>",
        )
    )

    # CDFA Constant Slope
    fig.add_trace(
        go.Scatter(
            x=cdfa_df["dist_to_thr_nm"],
            y=cdfa_df["altitude_ft"],
            mode="lines+markers",
            name="CDFA (Constant VDA Slope)",
            line=dict(color=ACCENT_GREEN, width=3.5),
            marker=dict(size=8, color=ACCENT_GREEN),
            hovertemplate="Dist to Thr: %{x:.2f} NM<br>Alt: %{y:,.0f} ft<extra>CDFA</extra>",
        )
    )

    # Dive and Drive Profile
    fig.add_trace(
        go.Scatter(
            x=dive_df["dist_to_thr_nm"],
            y=dive_df["altitude_ft"],
            mode="lines+markers",
            name="Dive & Drive (MDA Level-Off)",
            line=dict(color=ACCENT_RED, width=3, dash="dash"),
            marker=dict(size=8, color=ACCENT_RED),
            hovertemplate="Dist to Thr: %{x:.2f} NM<br>Alt: %{y:,.0f} ft<extra>Dive & Drive</extra>",
        )
    )

    # Highlight CFIT Risk Zone during low-altitude level segment at MDA
    if res["level_mda_dist_nm"] > 0.1:
        fig.add_vrect(
            x0=res["mda_end_dist_nm"],
            x1=res["mda_start_dist_nm"],
            fillcolor="rgba(255, 77, 109, 0.14)",
            layer="below",
            line_width=1,
            line_dash="dot",
            line_color=ACCENT_RED,
            annotation_text="⚠️ CFIT Risk Zone (Low Level Flight at MDA)",
            annotation_position="top left",
            annotation_font_color=ACCENT_RED,
        )

    # Animated aircraft markers (Traces 3 and 4)
    start_x = float(cdfa_df["dist_to_thr_nm"].iloc[0])
    start_y = float(cdfa_df["altitude_ft"].iloc[0])

    fig.add_trace(
        go.Scatter(
            x=[start_x],
            y=[start_y],
            mode="markers+text",
            text=["✈ CDFA"],
            textposition="top right",
            textfont=dict(color=ACCENT_GREEN, size=12),
            marker=dict(size=14, color=ACCENT_GREEN, symbol="triangle-right", line=dict(width=1.5, color="#ffffff")),
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[start_x],
            y=[start_y],
            mode="markers+text",
            text=["✈ DIVE"],
            textposition="bottom left",
            textfont=dict(color=ACCENT_RED, size=12),
            marker=dict(size=14, color=ACCENT_RED, symbol="triangle-right", line=dict(width=1.5, color="#ffffff")),
            showlegend=False,
        )
    )

    max_t = max(float(cdfa_df["time_min"].iloc[-1]), float(dive_df["time_min"].iloc[-1]), 1.0)
    t_samples = np.linspace(0.0, max_t, 45)
    frames = []
    steps = []

    for idx, t in enumerate(t_samples):
        c_x = float(np.interp(t, cdfa_df["time_min"], cdfa_df["dist_to_thr_nm"]))
        c_y = float(np.interp(t, cdfa_df["time_min"], cdfa_df["altitude_ft"]))
        d_x = float(np.interp(t, dive_df["time_min"], dive_df["dist_to_thr_nm"]))
        d_y = float(np.interp(t, dive_df["time_min"], dive_df["altitude_ft"]))

        frame_name = f"cdfa_{idx}"
        frames.append(
            go.Frame(
                name=frame_name,
                data=[
                    go.Scatter(x=[c_x], y=[c_y]),
                    go.Scatter(x=[d_x], y=[d_y]),
                ],
                traces=[3, 4],
            )
        )
        steps.append(
            dict(
                method="animate",
                label=f"{t:.1f}",
                args=[
                    [frame_name],
                    dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0)),
                ],
            )
        )

    apply_radar_layout(
        fig,
        title="Final Approach Profile: CDFA vs. Traditional 'Dive and Drive'",
        xaxis_title="Distance to Runway Threshold (NM) [Left → Right = Inbound to Runway]",
        yaxis_title="Altitude (ft MSL)",
        presentation_mode=presentation_mode,
    )
    fig.update_xaxes(autorange="reversed")
    add_play_pause_controls(fig, frames, steps)
    return fig


def build_comparison_bar_chart(presentation_mode: bool = False) -> go.Figure:
    """Builds a visual multi-dimensional comparison chart for CCO, CDO, and CDFA."""
    categories = [
        "Fuel & CO₂ Savings Impact",
        "Community Noise Reduction",
        "CFIT / Terrain Safety Margin",
        "ATC R/T Workload Relief",
        "PBN / VNAV Dependency",
    ]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="CCO (Departure Climb)",
            x=categories,
            y=[9.5, 7.5, 6.0, 8.0, 7.5],
            marker_color=ACCENT_GREEN,
        )
    )
    fig.add_trace(
        go.Bar(
            name="CDO (Arrival Descent)",
            x=categories,
            y=[9.0, 9.5, 6.5, 8.5, 8.5],
            marker_color=ACCENT_CYAN,
        )
    )
    fig.add_trace(
        go.Bar(
            name="CDFA (Final Approach)",
            x=categories,
            y=[5.0, 6.5, 10.0, 7.5, 8.0],
            marker_color=ACCENT_AMBER,
        )
    )

    apply_radar_layout(
        fig,
        title="Relative Operational Focus & Benefit Profile (Illustrative Pedagogical Scale)",
        xaxis_title="Operational Dimension",
        yaxis_title="Relative Emphasis (1–10 Scale)",
        height=410,
        presentation_mode=presentation_mode,
    )
    fig.update_layout(barmode="group", hovermode="x unified")
    return fig


def build_sid_star_dual_chart(res: dict[str, Any], presentation_mode: bool = False) -> go.Figure:
    """
    Builds synchronized dual-subplot animation:
      Left: Plan View (X vs Y in NM) with 3 NM separation halo
      Right: Vertical Side View (Time vs Altitude ft)
    """
    dep_df = res["dep_df"]
    arr_df = res["arr_df"]
    sep_df = res["sep_df"]
    time_grid = res["time_grid"]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "Plan View (Lateral X / Y in NM)",
            "Vertical Profile (Time vs. Altitude ft)",
        ),
        horizontal_spacing=0.10,
    )

    # --- Left Subplot: Static Routes ---
    fig.add_trace(
        go.Scatter(
            x=dep_df["x_nm"],
            y=dep_df["y_nm"],
            mode="lines",
            name="SID Departure Route",
            line=dict(color=ACCENT_GREEN, width=2.5),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=arr_df["x_nm"],
            y=arr_df["y_nm"],
            mode="lines",
            name="STAR Arrival Route",
            line=dict(color=ACCENT_CYAN, width=2.5),
        ),
        row=1,
        col=1,
    )

    # --- Right Subplot: Static Altitude Profiles ---
    fig.add_trace(
        go.Scatter(
            x=dep_df["time_min"],
            y=dep_df["altitude_ft"],
            mode="lines",
            name="Departure Climb",
            line=dict(color=ACCENT_GREEN, width=2.5, dash="dot"),
            showlegend=False,
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=arr_df["time_min"],
            y=arr_df["altitude_ft"],
            mode="lines",
            name="Arrival Descent",
            line=dict(color=ACCENT_CYAN, width=2.5, dash="dot"),
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    # --- Dynamic Animated Markers (Traces 4, 5, 6, 7) ---
    fig.add_trace(
        go.Scatter(
            x=[dep_df["x_nm"].iloc[0]],
            y=[dep_df["y_nm"].iloc[0]],
            mode="markers+text",
            text=["DEP (SID)"],
            textposition="top center",
            textfont=dict(color=ACCENT_GREEN, size=11),
            marker=dict(size=13, color=ACCENT_GREEN, line=dict(width=1.5, color="#ffffff")),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[arr_df["x_nm"].iloc[0]],
            y=[arr_df["y_nm"].iloc[0]],
            mode="markers+text",
            text=["ARR (STAR)"],
            textposition="bottom center",
            textfont=dict(color=ACCENT_CYAN, size=11),
            marker=dict(size=13, color=ACCENT_CYAN, line=dict(width=1.5, color="#ffffff")),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=[dep_df["time_min"].iloc[0]],
            y=[dep_df["altitude_ft"].iloc[0]],
            mode="markers",
            marker=dict(size=12, color=ACCENT_GREEN, line=dict(width=1.5, color="#ffffff")),
            showlegend=False,
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=[arr_df["time_min"].iloc[0]],
            y=[arr_df["altitude_ft"].iloc[0]],
            mode="markers",
            marker=dict(size=12, color=ACCENT_CYAN, line=dict(width=1.5, color="#ffffff")),
            showlegend=False,
        ),
        row=1,
        col=2,
    )

    # Sample every 2nd step for smooth 60-frame animation
    sample_indices = list(range(0, len(time_grid), 2))
    frames = []
    steps = []

    for idx in sample_indices:
        t = float(time_grid[idx])
        is_viol = bool(sep_df["conflict"].iloc[idx])
        marker_col_dep = ACCENT_RED if is_viol else ACCENT_GREEN
        marker_col_arr = ACCENT_RED if is_viol else ACCENT_CYAN
        dep_lbl = "⚠️ CONFLICT" if is_viol else "DEP (SID)"

        frame_name = f"ss_{idx}"
        frames.append(
            go.Frame(
                name=frame_name,
                data=[
                    go.Scatter(
                        x=[dep_df["x_nm"].iloc[idx]],
                        y=[dep_df["y_nm"].iloc[idx]],
                        text=[dep_lbl],
                        marker=dict(size=15 if is_viol else 13, color=marker_col_dep),
                    ),
                    go.Scatter(
                        x=[arr_df["x_nm"].iloc[idx]],
                        y=[arr_df["y_nm"].iloc[idx]],
                        marker=dict(size=15 if is_viol else 13, color=marker_col_arr),
                    ),
                    go.Scatter(
                        x=[dep_df["time_min"].iloc[idx]],
                        y=[dep_df["altitude_ft"].iloc[idx]],
                        marker=dict(size=14 if is_viol else 12, color=marker_col_dep),
                    ),
                    go.Scatter(
                        x=[arr_df["time_min"].iloc[idx]],
                        y=[arr_df["altitude_ft"].iloc[idx]],
                        marker=dict(size=14 if is_viol else 12, color=marker_col_arr),
                    ),
                ],
                traces=[4, 5, 6, 7],
            )
        )
        steps.append(
            dict(
                method="animate",
                label=f"{t:.1f}",
                args=[
                    [frame_name],
                    dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0)),
                ],
            )
        )

    apply_radar_layout(
        fig,
        title="TMA Crossing Conflict Simulation: SID Departure vs. STAR Arrival",
        xaxis_title="East–West Position X (NM)",
        yaxis_title="North–South Position Y (NM)",
        height=500,
        presentation_mode=presentation_mode,
    )
    fig.update_xaxes(title_text="Simulation Time (min)", gridcolor="#1b2b47", row=1, col=2)
    fig.update_yaxes(title_text="Altitude (ft)", gridcolor="#1b2b47", row=1, col=2)
    add_play_pause_controls(fig, frames, steps)
    return fig


def build_multi_aircraft_chart(res: dict[str, Any], presentation_mode: bool = False) -> go.Figure:
    """Builds animated radar Plan View + Altitude view for 3–6 TMA aircraft."""
    trajectories = res["trajectories"]
    time_grid = res["time_grid"]
    conflict_times = set(res["conflict_times"])

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("TMA Radar Scope (X / Y in NM)", "Vertical Separation View (Time vs. Altitude ft)"),
        horizontal_spacing=0.10,
    )

    # Airport / TMA center beacon
    fig.add_trace(
        go.Scatter(
            x=[0.0],
            y=[0.0],
            mode="markers+text",
            name="Aerodrome / TMA ARP",
            text=["ARP"],
            textposition="bottom center",
            marker=dict(size=11, color="#ffffff", symbol="cross"),
        ),
        row=1,
        col=1,
    )

    callsigns = list(trajectories.keys())
    # Add static paths first
    for idx, cs in enumerate(callsigns):
        df = trajectories[cs]
        col = AIRCRAFT_PALETTE[idx % len(AIRCRAFT_PALETTE)]
        fig.add_trace(
            go.Scatter(
                x=df["x_nm"],
                y=df["y_nm"],
                mode="lines",
                name=f"{cs} ({df['type'].iloc[0][:3].upper()})",
                line=dict(color=col, width=2, dash="solid" if df["type"].iloc[0] == "Departure" else "dash"),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df["time_min"],
                y=df["altitude_ft"],
                mode="lines",
                line=dict(color=col, width=2),
                showlegend=False,
            ),
            row=1,
            col=2,
        )

    # Add animated markers (2 per aircraft: plan marker & altitude marker)
    base_dynamic_trace = 1 + 2 * len(callsigns)
    dynamic_indices = []
    for idx, cs in enumerate(callsigns):
        df = trajectories[cs]
        col = AIRCRAFT_PALETTE[idx % len(AIRCRAFT_PALETTE)]
        fig.add_trace(
            go.Scatter(
                x=[df["x_nm"].iloc[0]],
                y=[df["y_nm"].iloc[0]],
                mode="markers+text",
                text=[f"{cs} FL{int(df['altitude_ft'].iloc[0]//100):03d}"],
                textposition="top right",
                textfont=dict(color=col, size=11),
                marker=dict(size=12, color=col, line=dict(width=1.2, color="#ffffff")),
                showlegend=False,
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=[df["time_min"].iloc[0]],
                y=[df["altitude_ft"].iloc[0]],
                mode="markers",
                marker=dict(size=11, color=col, line=dict(width=1.2, color="#ffffff")),
                showlegend=False,
            ),
            row=1,
            col=2,
        )
        dynamic_indices.extend([base_dynamic_trace + 2 * idx, base_dynamic_trace + 2 * idx + 1])

    frames = []
    steps = []
    for t_idx in range(0, len(time_grid), 2):
        t = float(time_grid[t_idx])
        is_alert = t in conflict_times
        frame_data = []
        for idx, cs in enumerate(callsigns):
            df = trajectories[cs]
            col = ACCENT_RED if is_alert else AIRCRAFT_PALETTE[idx % len(AIRCRAFT_PALETTE)]
            fl_str = f"FL{int(round(df['altitude_ft'].iloc[t_idx] / 100.0)):03d}"
            frame_data.append(
                go.Scatter(
                    x=[df["x_nm"].iloc[t_idx]],
                    y=[df["y_nm"].iloc[t_idx]],
                    text=[f"{cs} {fl_str}"],
                    marker=dict(size=14 if is_alert else 12, color=col),
                )
            )
            frame_data.append(
                go.Scatter(
                    x=[df["time_min"].iloc[t_idx]],
                    y=[df["altitude_ft"].iloc[t_idx]],
                    marker=dict(size=13 if is_alert else 11, color=col),
                )
            )
        fname = f"ma_{t_idx}"
        frames.append(go.Frame(name=fname, data=frame_data, traces=dynamic_indices))
        steps.append(
            dict(
                method="animate",
                label=f"{t:.1f}",
                args=[
                    [fname],
                    dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0)),
                ],
            )
        )

    apply_radar_layout(
        fig,
        title="Multi-Aircraft TMA Sector Simulation (Plan View & Vertical Profiles)",
        xaxis_title="East–West Position X (NM)",
        yaxis_title="North–South Position Y (NM)",
        height=500,
        presentation_mode=presentation_mode,
    )
    fig.update_xaxes(title_text="Simulation Time (min)", gridcolor="#1b2b47", row=1, col=2)
    fig.update_yaxes(title_text="Altitude (ft)", gridcolor="#1b2b47", row=1, col=2)
    add_play_pause_controls(fig, frames, steps)
    return fig


# ==============================================================================
# 5. EDUCATIONAL CONTENT DATA (STRICTLY FROM cco_cdo_cdfa_atc_guide.txt)
# ==============================================================================
COMPARISON_MATRIX_DF = pd.DataFrame(
    [
        {
            "Feature / Dimension": "Primary Flight Phase",
            "CCO": "Takeoff to Top of Climb (ToC)",
            "CDO": "Top of Descent (ToD) to FAF",
            "CDFA": "FAF to Runway Threshold / DDA",
        },
        {
            "Feature / Dimension": "Primary Goal",
            "CCO": "Fuel efficiency & climb optimization",
            "CDO": "Fuel savings & community noise reduction",
            "CDFA": "Flight safety & CFIT elimination",
        },
        {
            "Feature / Dimension": "Engine Thrust",
            "CCO": "Optimum Climb Thrust",
            "CDO": "Minimum / Idle Thrust",
            "CDFA": "Stabilized approach thrust",
        },
        {
            "Feature / Dimension": "Method Replaced",
            "CCO": "Step-up intermediate altitude holds",
            "CDO": "Step-down intermediate level-offs",
            "CDFA": '"Dive and Drive" at MDA',
        },
        {
            "Feature / Dimension": "ATC Facilitation",
            "CCO": "Altitude windows on SIDs; timely climb clearances",
            "CDO": "Altitude windows on STARs, speed control, DTG, AMAN",
            "CDFA": "Vectoring smoothly prior to FAF",
        },
        {
            "Feature / Dimension": "Critical Reference",
            "CCO": "Initial Cruise Flight Level",
            "CDO": "Top of Descent (ToD)",
            "CDFA": "Derived Decision Altitude (DDA)",
        },
    ]
)

QUIZ_QUESTIONS = [
    {
        "q": "1. During which phase of flight does an aircraft consume fuel at the highest rate, making intermediate level-offs especially costly?",
        "options": [
            "Final approach segment below the FAF",
            "The departure climb phase from takeoff toward initial cruise level",
            "En-route cruise at optimum flight level",
            "Taxi-out prior to takeoff clearance",
        ],
        "answer": 1,
        "explanation": "Section 1.2 & 8.2: The climb phase consumes fuel at the highest rate during flight, and leveling off during climb burns significantly more fuel than an equivalent level segment during descent.",
    },
    {
        "q": "2. How should airspace procedure designers structure altitude constraints on SIDs and STARs to facilitate CCO and CDO across diverse aircraft types?",
        "options": [
            "Use rigid 'at' altitude constraints (e.g., 'at 7,000 ft') at every waypoint",
            "Provide flexible altitude windows (e.g., 'at or above 7,000 ft') rather than hard altitudes",
            "Require pilots to level off at every 3,000 ft increment",
            "Eliminate all published vertical profiles on RNAV procedures",
        ],
        "answer": 1,
        "explanation": "Section 1.3 & 2.3: Minimizing rigid altitude constraints in favor of altitude windows ('at or above') allows onboard FMS computers to compute optimum continuous climb and descent trajectories.",
    },
    {
        "q": "3. According to the reference guide, which ATC technique is far more effective for maintaining CDO profiles than tactical radar vectoring?",
        "options": [
            "Issuing frequent low-altitude step-down clearances",
            "Early speed control (especially above 10,000 ft, keeping speeds around 280 kts)",
            "Holding aircraft at 4,000 ft prior to localizer intercept",
            "Delaying descent clearance until 15 NM from the FAF",
        ],
        "answer": 1,
        "explanation": "Section 2.3: Early speed adjustments above 10,000 ft (around 280 kts) allow smooth energy management and are far more effective for preserving CDO than tactical radar vectoring.",
    },
    {
        "q": "4. When radar vectoring is unavoidable during an arrival, what information should controllers provide to help the flight crew manage energy for CDO?",
        "options": [
            "Runway surface wind every 30 seconds",
            "Accurate Distance-to-Go (DTG) information",
            "Outside air temperature at the departure airport",
            "Minimum fuel reserve estimates",
        ],
        "answer": 1,
        "explanation": "Section 2.3 & 5.3: Providing accurate Distance-to-Go (DTG) during radar vectoring allows the crew and FMS to manage kinetic and potential energy effectively.",
    },
    {
        "q": "5. According to the guide's economic and operational benchmarks, how much time and extra fuel does an average non-CDO arrival waste in low-altitude level flight?",
        "options": [
            "45 seconds and 12 kg of extra fuel",
            "120 seconds and 25 kg of extra fuel",
            "217 seconds and 46 kg of extra fuel per arrival",
            "600 seconds and 180 kg of extra fuel per arrival",
        ],
        "answer": 2,
        "explanation": "Section 7.2: Flights flying non-CDO profiles lose an average of 217 seconds in low-altitude level flight, wasting 46 kg of extra fuel per arrival.",
    },
    {
        "q": "6. What traditional Non-Precision Approach (NPA) technique does CDFA replace to reduce Controlled Flight Into Terrain (CFIT) risk?",
        "options": [
            "Point Merge sequencing",
            "The 'Dive and Drive' method (rapid descent and level flight at MDA)",
            "ILS CAT III autoland",
            "Step-up departure climbs",
        ],
        "answer": 1,
        "explanation": "Section 3.2: CDFA eliminates extended low-altitude level flight at Minimum Descent Altitude (MDA) associated with 'Dive and Drive,' converting NPAs into precision-like continuous descents.",
    },
    {
        "q": "7. Why do operators add a small safety buffer above the published MDA to establish a Derived Decision Altitude (DDA) on a CDFA?",
        "options": [
            "To allow pilots to fly level at MDA for 2 minutes before landing",
            "So the pilot can decide to land or execute a missed approach without dipping below the published MDA",
            "To increase engine thrust during cruise",
            "To eliminate the need for a Final Approach Fix (FAF)",
        ],
        "answer": 1,
        "explanation": "Section 3.3: At DDA, the pilot initiates a missed approach if visual references are not acquired, ensuring the aircraft does not dip below the published MDA during the transition.",
    },
    {
        "q": "8. What is the normal published range for a Vertical Descent Angle (VDA) on a CDFA, and what is the optimum value?",
        "options": [
            "1.50° to 2.50°, with 2.0° optimum",
            "2.75° to 3.77°, with 3.0° optimum",
            "4.00° to 5.50°, with 4.5° optimum",
            "0.50° to 1.25°, with 1.0° optimum",
        ],
        "answer": 1,
        "explanation": "Section 3.3: Published VDAs normally range between 2.75° and 3.77°, with 3.0° as the optimum angle.",
    },
    {
        "q": "9. Which CNS/ATM technologies supply geometric vertical guidance during Non-Precision Approaches without requiring ground ILS infrastructure?",
        "options": [
            "Primary Surveillance Radar (PSR) and NDB",
            "Baro-VNAV and SBAS/LPV",
            "CPDLC and DMAN",
            "VHF voice radio and VOR",
        ],
        "answer": 1,
        "explanation": "Section 5.2: Advanced navigation tools such as Baro-VNAV and SBAS/LPV supply geometric vertical guidance during Non-Precision Approaches without requiring ILS ground infrastructure.",
    },
    {
        "q": "10. In a congested TMA where a SID and STAR cross and an intermediate level-off is unavoidable, which trade-off principle should guide the controller?",
        "options": [
            "Always level off the climbing departure because climb burns less fuel",
            "A level flight segment during climb burns significantly more fuel than an equivalent level segment during descent",
            "Fuel burn is identical whether leveling off in climb or descent",
            "Never use speed control or altitude windows in a TMA",
        ],
        "answer": 1,
        "explanation": "Section 1.3 & 8.2: When trade-offs between CCO and CDO are unavoidable, controllers must note that an aircraft forced into an intermediate level segment during climb burns significantly more fuel than an equivalent level segment during descent.",
    },
]


# ==============================================================================
# 6. SESSION STATE INITIALIZATION & RESET HELPERS
# ==============================================================================
DEFAULTS: dict[str, Any] = {
    # CCO Defaults
    "cco_cruise_fl": 330,
    "cco_roc": 2200,
    "cco_gs": 320,
    "cco_num_holds": 2,
    "cco_hold1_alt": 7000,
    "cco_hold1_dur": 2.5,
    "cco_hold2_alt": 14000,
    "cco_hold2_dur": 2.0,
    "cco_hold3_alt": 21000,
    "cco_hold3_dur": 1.5,
    "cco_fuel_factor": 32.0,
    # CDO Defaults
    "cdo_start_alt": 31000,
    "cdo_faf_alt": 3000,
    "cdo_angle": 3.0,
    "cdo_gs": 280,
    "cdo_num_steps": 2,
    "cdo_step1_alt": 11000,
    "cdo_step1_len": 9.0,
    "cdo_step2_alt": 6000,
    "cdo_step2_len": 8.0,
    "cdo_step3_alt": 4000,
    "cdo_step3_len": 5.0,
    "cdo_fuel_factor": 13.0,
    "cdo_dtg_query": 42.0,
    # CDFA Defaults
    "cdfa_faf_alt": 3000,
    "cdfa_thr_elev": 100,
    "cdfa_mda": 620,
    "cdfa_dda_buf": 50,
    "cdfa_vda": 3.0,
    "cdfa_gs": 140,
    "cdfa_dive_rod": 1450,
    "cdfa_terrain": True,
    # SID/STAR Crossing Defaults
    "ss_sid_x0": 0.0,
    "ss_sid_y0": 0.0,
    "ss_sid_x1": 30.0,
    "ss_sid_y1": 24.0,
    "ss_star_x0": 32.0,
    "ss_star_y0": 0.0,
    "ss_star_x1": 0.0,
    "ss_star_y1": 22.0,
    "ss_dep_roc": 2000,
    "ss_dep_gs": 260,
    "ss_arr_rod": 1800,
    "ss_arr_gs": 250,
    "ss_arr_offset": 0.5,
    "ss_min_horiz": 3.0,
    "ss_min_vert": 1000,
    "ss_hold_target": "None",
    "ss_hold_alt": 9000,
    "ss_hold_dur": 2.5,
}


def init_session_state() -> None:
    """Ensures all widget keys exist in st.session_state."""
    for key, val in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = val


def reset_keys(prefix: str) -> None:
    """Resets all session_state keys matching a simulator prefix."""
    for key, val in DEFAULTS.items():
        if key.startswith(prefix):
            st.session_state[key] = val


# ==============================================================================
# 7. MAIN APPLICATION RENDERING
# ==============================================================================
def main() -> None:
    init_session_state()

    # --- Sidebar Controls ---
    with st.sidebar:
        st.markdown("### 🎛️ ATC Classroom Console")
        presentation_mode = st.toggle(
            "🖥️ Presentation Mode",
            value=False,
            help="Enlarges fonts, boosts contrast, and hides secondary UI chrome for classroom projectors.",
        )
        st.markdown("---")
        st.markdown("**Quick Classroom Navigation**")
        st.caption(
            "Use the top navigation tabs to walk students through concepts, live flight-path "
            "simulators, CNS/ATM integration, and the 10-question assessment quiz."
        )
        st.markdown(
            """
            <div class="atc-card" style="padding:0.85rem;">
                <div class="atc-card-title">Key Reference Benchmarks</div>
                <ul style="margin:0; padding-left:1.1rem; font-size:0.86rem; color:#cbd5e1;">
                    <li><strong>EUROCONTROL Network:</strong> Up to 340,000 t fuel & 1.1M t CO₂ saved/yr</li>
                    <li><strong>Noise Footprint:</strong> Up to 40% reduction (1–5 dB)</li>
                    <li><strong>Non-CDO Penalty:</strong> Avg 217 s level flight & 46 kg extra fuel/arrival</li>
                    <li><strong>CDFA VDA Range:</strong> 2.75°–3.77° (3.0° optimum)</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    inject_custom_css(presentation_mode=presentation_mode)

    # --- Top Navigation Tabs ---
    tabs = st.tabs(
        [
            "1. Home",
            "2. CCO",
            "3. CDO",
            "4. CDFA",
            "5. Comparison",
            "6. CNS & ATM",
            "7. Challenges & Trade-offs",
            "8. Class Quiz",
        ]
    )

    # ==========================================================================
    # TAB 1: HOME
    # ==========================================================================
    with tabs[0]:
        st.markdown(
            """
            <div class="atc-hero">
                <div>
                    <div class="atc-hero-badge">ATC STUDENT PRESENTATION &amp; TRAJECTORY LAB</div>
                    <h1 class="atc-hero-title">CCO, CDO, CDFA &amp; CNS/ATM Integration</h1>
                    <p class="atc-hero-sub">
                        Interactive classroom guide to vertical flight efficiency, stabilized non-precision
                        approaches, and integrated Air Traffic Management operations.
                    </p>
                </div>
                <div class="radar-scope" aria-hidden="true">
                    <div class="radar-crosshair-h"></div>
                    <div class="radar-crosshair-v"></div>
                    <div class="radar-sweep"></div>
                    <div class="radar-blip"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_obj, col_ben = st.columns([1.15, 1.0])
        with col_obj:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">Lesson Objectives</div>
                    <ul style="margin-bottom:0;">
                        <li><strong>Understand Vertical Flight Efficiency:</strong> Distinguish Continuous Climb Operations (CCO), Continuous Descent Operations (CDO), and Continuous Descent Final Approach (CDFA).</li>
                        <li><strong>Apply Tactical ATC Techniques:</strong> Use altitude windows, early speed control, Distance-to-Go (DTG), and timely clearances instead of restrictive step altitudes.</li>
                        <li><strong>Mitigate Approach Hazards:</strong> Explain how CDFA, Vertical Descent Angles (VDA), and Derived Decision Altitude (DDA) eliminate "Dive and Drive" CFIT risks.</li>
                        <li><strong>Connect CNS/ATM Enablers:</strong> Link CPDLC, PBN/VNAV, ADS-B, AMAN/DMAN, and Trajectory-Based Operations (TBO) to uninterrupted trajectories.</li>
                        <li><strong>Evaluate TMA Trade-Offs:</strong> Analyze crossing SID/STAR separation conflicts and apply the climb-vs-descent fuel trade-off principle.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_ben:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">Comprehensive Guide Impact Highlights</div>
                    <ul style="margin-bottom:0;">
                        <li><strong>Network Fuel &amp; CO₂:</strong> EUROCONTROL studies indicate annual network savings up to <strong>340,000 tonnes of fuel</strong> and <strong>1.1 million tonnes of CO₂</strong>.</li>
                        <li><strong>Community Noise:</strong> Keeping aircraft higher longer and descending at idle thrust cuts noise footprints by up to <strong>40% (1–5 dB)</strong>.</li>
                        <li><strong>Per-Flight CDO Impact:</strong> Non-CDO arrivals lose an average of <strong>217 seconds</strong> in low-altitude level flight, wasting <strong>46 kg of extra fuel</strong>.</li>
                        <li><strong>Safety &amp; Workload:</strong> Reduces R/T chatter, readback/hearback errors, and Controlled Flight Into Terrain (CFIT) exposure.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### End-to-End Flight Phase Concept Map")
        st.markdown(
            """
            <div class="concept-grid">
                <div class="concept-node">
                    <span class="badge badge-ok">1 · DEPARTURE</span>
                    <h4 style="margin:0.45rem 0 0.3rem 0; color:#39ff88;">CCO (Continuous Climb)</h4>
                    <p style="font-size:0.9rem; margin:0; color:#cbd5e1;">
                        <strong>Takeoff → Top of Climb (ToC)</strong><br/>
                        Optimum climb thrust without step-up level-offs. Enabled by SID altitude windows ("at or above") and proactive climb clearances.
                    </p>
                </div>
                <div class="concept-node cdo">
                    <span class="badge badge-info">2 · ARRIVAL</span>
                    <h4 style="margin:0.45rem 0 0.3rem 0; color:#38bdf8;">CDO (Continuous Descent)</h4>
                    <p style="font-size:0.9rem; margin:0; color:#cbd5e1;">
                        <strong>Top of Descent (ToD) → FAF</strong><br/>
                        Minimum/idle thrust &amp; low drag. Enabled by STAR altitude windows, early speed control, DTG updates, and AMAN / Point Merge.
                    </p>
                </div>
                <div class="concept-node cdfa">
                    <span class="badge badge-warning">3 · FINAL APPROACH</span>
                    <h4 style="margin:0.45rem 0 0.3rem 0; color:#fbbf24;">CDFA (Final Approach)</h4>
                    <p style="font-size:0.9rem; margin:0; color:#cbd5e1;">
                        <strong>FAF → Runway Threshold / DDA</strong><br/>
                        Constant VDA slope (~3.0°) on Non-Precision Approaches, eliminating low-altitude "Dive and Drive" level segments at MDA.
                    </p>
                </div>
                <div class="concept-node cns">
                    <span class="badge badge-info">4 · SYSTEM ENABLERS</span>
                    <h4 style="margin:0.45rem 0 0.3rem 0; color:#c084fc;">CNS &amp; ATM Integration</h4>
                    <p style="font-size:0.9rem; margin:0; color:#cbd5e1;">
                        <strong>Cross-Sector Trajectory (TBO)</strong><br/>
                        CPDLC, PBN/Baro-VNAV/SBAS, ADS-B, and integrated AMAN/DMAN synchronize departure and arrival flows across ACC, APP, and TWR.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Feature Comparison Matrix Summary")
        st.dataframe(COMPARISON_MATRIX_DF, use_container_width=True, hide_index=True)

    # ==========================================================================
    # TAB 2: CCO (CONTINUOUS CLIMB OPERATIONS)
    # ==========================================================================
    with tabs[1]:
        st.header("Continuous Climb Operations (CCO)")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">Definition &amp; Core Concept</div>
                    <p style="margin-bottom:0;">
                        CCO is an aircraft operating technique enabled by integrated airspace design,
                        procedure design, and tactical ATC clearances. Rather than holding aircraft at
                        intermediate step-up altitudes during departure, CCO allows a continuous climb
                        from takeoff toward initial cruising flight level using optimum climb thrust and speeds.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">Fuel &amp; Environmental Impact</div>
                    <ul style="margin-bottom:0; padding-left:1.1rem;">
                        <li><strong>Highest-Fuel Phase:</strong> Climb consumes fuel at the highest rate; leveling off at lower altitudes drops fuel efficiency per km flown.</li>
                        <li><strong>Eliminating Step Climbs:</strong> Reduces total fuel burn and CO₂ emissions across the entire flight.</li>
                        <li><strong>Noise Mitigation:</strong> Optimum climb gradients gain altitude faster, shifting noise footprints away from communities.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">ATC Perspective &amp; Key Takeaways</div>
                    <ul style="margin-bottom:0; padding-left:1.1rem;">
                        <li><strong>Workload Reduction:</strong> Fewer intermediate R/T clearances and altitude readbacks.</li>
                        <li><strong>SID Altitude Windows:</strong> Prefer "at or above 7,000 ft" over rigid "at 7,000 ft" restrictions.</li>
                        <li><strong>TMA Trade-off Rule:</strong> A level segment in climb burns significantly more fuel than an equivalent level segment in descent.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.subheader("Interactive CCO Flight-Path Simulator")
        ctrl_col, chart_col = st.columns([1.05, 2.15])

        with ctrl_col:
            st.number_input("Initial Cruise Level (FL)", min_value=100, max_value=430, step=10, key="cco_cruise_fl")
            st.slider("Average Climb Rate (ft/min)", min_value=800, max_value=4000, step=100, key="cco_roc")
            st.slider("Average Ground Speed (kt)", min_value=180, max_value=460, step=10, key="cco_gs")
            st.selectbox("Number of Forced ATC Level-Offs", options=[0, 1, 2, 3], key="cco_num_holds")

            holds: list[tuple[float, float]] = []
            num_holds = int(st.session_state["cco_num_holds"])
            for i in range(1, num_holds + 1):
                st.markdown(f"**ATC Level-Off #{i}**")
                h_col1, h_col2 = st.columns(2)
                with h_col1:
                    alt_val = st.number_input(
                        f"Altitude #{i} (ft)",
                        min_value=2000,
                        max_value=38000,
                        step=1000,
                        key=f"cco_hold{i}_alt",
                    )
                with h_col2:
                    dur_val = st.number_input(
                        f"Hold #{i} (min)",
                        min_value=0.5,
                        max_value=15.0,
                        step=0.5,
                        key=f"cco_hold{i}_dur",
                    )
                holds.append((float(alt_val), float(dur_val)))

            st.number_input(
                "Extra Fuel Factor (kg/min level — Educational approx.)",
                min_value=5.0,
                max_value=100.0,
                step=1.0,
                key="cco_fuel_factor",
            )
            st.button("↺ Reset CCO to Defaults", on_click=reset_keys, args=("cco_",), use_container_width=True)

        # Input validation
        cruise_alt_ft = st.session_state["cco_cruise_fl"] * 100
        invalid_hold = any(alt >= cruise_alt_ft for alt, _ in holds)
        if invalid_hold:
            st.warning(
                f"One or more intermediate level-off altitudes are at or above the initial cruise altitude "
                f"({cruise_alt_ft:,} ft). Those level-offs are ignored until lowered below cruise altitude."
            )

        cco_res = compute_cco_profiles(
            cruise_fl=int(st.session_state["cco_cruise_fl"]),
            climb_rate_fpm=float(st.session_state["cco_roc"]),
            ground_speed_kt=float(st.session_state["cco_gs"]),
            level_offs=holds,
            extra_fuel_kg_per_min=float(st.session_state["cco_fuel_factor"]),
        )

        with chart_col:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                render_metric_card(
                    "CCO Time to ToC",
                    f"{cco_res['cco_time_min']:.1f} min",
                    "OK",
                    f"Stepped: {cco_res['step_time_min']:.1f} min",
                )
            with m2:
                render_metric_card(
                    "CCO Distance to ToC",
                    f"{cco_res['cco_dist_nm']:.1f} NM",
                    "INFO",
                    f"Stepped: {cco_res['step_dist_nm']:.1f} NM",
                )
            with m3:
                tdiff = cco_res["time_diff_min"]
                render_metric_card(
                    "Level-Off Delay",
                    f"+{tdiff:.1f} min",
                    "WARNING" if tdiff > 0 else "OK",
                    f"+{cco_res['dist_diff_nm']:.1f} NM extra track",
                )
            with m4:
                xfuel = cco_res["extra_fuel_kg"]
                render_metric_card(
                    "Est. Extra Fuel*",
                    f"+{xfuel:.0f} kg",
                    "WARNING" if xfuel > 0 else "OK",
                    "Educational approximation",
                )

            cco_fig = build_cco_chart(cco_res, presentation_mode=presentation_mode)
            st.plotly_chart(cco_fig, use_container_width=True)

            # Export buttons
            exp1, exp2 = st.columns(2)
            cco_export = pd.concat(
                [cco_res["cco_df"].assign(profile="CCO"), cco_res["step_df"].assign(profile="Stepped")],
                ignore_index=True,
            )
            with exp1:
                st.download_button(
                    "📥 Download CCO Profile Data (CSV)",
                    data=cco_export.to_csv(index=False).encode("utf-8"),
                    file_name="cco_simulation_profile.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with exp2:
                st.download_button(
                    "🖼️ Download Interactive Chart (HTML)",
                    data=cco_fig.to_html(include_plotlyjs="cdn").encode("utf-8"),
                    file_name="cco_flight_path_chart.html",
                    mime="text/html",
                    use_container_width=True,
                )

        with st.expander("📐 Formulas & Assumptions (Educational Approximation)"):
            st.markdown(
                """
                - **Kinematic Model:** Constant ground speed ($GS$ in knots $\\rightarrow GS / 60$ NM/min) and constant rate of climb ($ROC$ in ft/min) during climbing segments.
                - **Top of Climb (ToC):** $t_{\\text{CCO}} = \\frac{\\text{FL} \\times 100}{ROC}$, and horizontal distance $d_{\\text{CCO}} = t_{\\text{CCO}} \\times \\frac{GS}{60}$.
                - **Stepped Climb Penalty:** During ATC level holds, altitude remains constant while horizontal distance increases by $\\Delta d = t_{\\text{hold}} \\times \\frac{GS}{60}$.
                - **Extra Fuel (Educational Approximation):** Estimated as $\\Delta \\text{Fuel} = t_{\\text{level}} \\times k_{\\text{fuel}}$, reflecting higher fuel burn per kilometer at lower, denser altitudes.
                """
            )

    # ==========================================================================
    # TAB 3: CDO (CONTINUOUS DESCENT OPERATIONS)
    # ==========================================================================
    with tabs[2]:
        st.header("Continuous Descent Operations (CDO)")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">Definition &amp; Core Concept</div>
                    <p style="margin-bottom:0;">
                        CDO enables arriving aircraft to descend continuously from Top of Descent (ToD)
                        down to the Final Approach Fix (FAF) or ILS intercept using minimum engine thrust
                        (idle settings) and low-drag configurations, avoiding traditional low-altitude
                        step-down level-offs.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">Operational &amp; Environmental Benefits</div>
                    <ul style="margin-bottom:0; padding-left:1.1rem;">
                        <li><strong>Fuel &amp; CO₂ Savings:</strong> Eliminates high-thrust level segments at low altitudes.</li>
                        <li><strong>Noise Footprint Reduction:</strong> Keeps aircraft higher longer, cutting noise footprints by up to <strong>40% (1–5 dB)</strong>.</li>
                        <li><strong>Safety &amp; Workload:</strong> Replaces multiple step-down clearances with "Descend via STAR," reducing R/T chatter and readback errors.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">ATC Facilitation &amp; Benchmarks</div>
                    <ul style="margin-bottom:0; padding-left:1.1rem;">
                        <li><strong>Speed Control vs. Vectoring:</strong> Early speed adjustments above 10,000 ft (~280 kts) outperform radar vectoring.</li>
                        <li><strong>Distance-to-Go (DTG):</strong> Essential when vectoring so crews/FMS can manage energy.</li>
                        <li><strong>Guide Benchmark:</strong> Non-CDO arrivals average <strong>217 s</strong> of level flight and <strong>46 kg</strong> extra fuel per arrival.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.subheader("Interactive CDO Flight-Path Simulator & Distance-to-Go (DTG) Advisor")
        ctrl_col, chart_col = st.columns([1.05, 2.15])

        with ctrl_col:
            st.number_input("Cruise / Start Altitude (ft)", min_value=8000, max_value=41000, step=1000, key="cdo_start_alt")
            st.number_input("FAF Altitude (ft)", min_value=1500, max_value=8000, step=500, key="cdo_faf_alt")
            st.slider("Descent Angle (degrees)", min_value=2.0, max_value=4.5, step=0.1, key="cdo_angle")
            st.slider("Average Descent Ground Speed (kt)", min_value=180, max_value=380, step=10, key="cdo_gs")
            st.selectbox("Number of Step-Down Level-Offs", options=[0, 1, 2, 3], key="cdo_num_steps")

            step_downs: list[tuple[float, float]] = []
            num_steps = int(st.session_state["cdo_num_steps"])
            for i in range(1, num_steps + 1):
                st.markdown(f"**Step-Down Segment #{i}**")
                s_col1, s_col2 = st.columns(2)
                with s_col1:
                    s_alt = st.number_input(
                        f"Level Alt #{i} (ft)",
                        min_value=2000,
                        max_value=35000,
                        step=1000,
                        key=f"cdo_step{i}_alt",
                    )
                with s_col2:
                    s_len = st.number_input(
                        f"Length #{i} (NM)",
                        min_value=1.0,
                        max_value=30.0,
                        step=1.0,
                        key=f"cdo_step{i}_len",
                    )
                step_downs.append((float(s_alt), float(s_len)))

            st.number_input(
                "Extra Fuel Factor (kg/min level — Educational approx.)",
                min_value=3.0,
                max_value=50.0,
                step=1.0,
                key="cdo_fuel_factor",
            )

            st.markdown("---")
            st.markdown("**Distance-to-Go (DTG) 3° Path Advisor**")
            st.number_input(
                "Current Distance-to-Go to Airport/FAF (NM)",
                min_value=0.0,
                max_value=150.0,
                step=2.0,
                key="cdo_dtg_query",
            )
            dtg_nm = float(st.session_state["cdo_dtg_query"])
            # 3-degree geometric path above FAF altitude (approx 318 ft/NM)
            suggested_alt_3deg = float(st.session_state["cdo_faf_alt"]) + dtg_nm * math.tan(math.radians(3.0)) * 6076.12
            suggested_alt_3to1 = float(st.session_state["cdo_faf_alt"]) + (dtg_nm / 3.0) * 1000.0
            st.info(
                f"At **{dtg_nm:.1f} NM** DTG: Suggested 3.0° geometric altitude is **{suggested_alt_3deg:,.0f} ft** "
                f"(3:1 rule of thumb: **{suggested_alt_3to1:,.0f} ft**)."
            )

            st.button("↺ Reset CDO to Defaults", on_click=reset_keys, args=("cdo_",), use_container_width=True)

        # Validation
        if st.session_state["cdo_start_alt"] <= st.session_state["cdo_faf_alt"]:
            st.error("Cruise/Start Altitude must be strictly greater than FAF Altitude.")
            st.stop()

        cdo_res = compute_cdo_profiles(
            start_alt_ft=float(st.session_state["cdo_start_alt"]),
            faf_alt_ft=float(st.session_state["cdo_faf_alt"]),
            descent_angle_deg=float(st.session_state["cdo_angle"]),
            ground_speed_kt=float(st.session_state["cdo_gs"]),
            step_downs=step_downs,
            extra_fuel_kg_per_min=float(st.session_state["cdo_fuel_factor"]),
        )

        with chart_col:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                render_metric_card(
                    "ToD (3:1 Rule of Thumb)",
                    f"{cdo_res['tod_rule_of_thumb_nm']:.1f} NM",
                    "OK",
                    f"Exact {st.session_state['cdo_angle']:.1f}°: {cdo_res['cdo_descent_dist_nm']:.1f} NM",
                )
            with m2:
                render_metric_card(
                    "CDO Descent Rate",
                    f"{cdo_res['rod_fpm']:.0f} fpm",
                    "INFO",
                    f"At {st.session_state['cdo_gs']} kt GS",
                )
            with m3:
                lvl_sec = cdo_res["total_level_sec"]
                render_metric_card(
                    "Step-Down Level Time",
                    f"{lvl_sec:.0f} s ({cdo_res['total_level_nm']:.1f} NM)",
                    "WARNING" if lvl_sec > 0 else "OK",
                    "Guide avg non-CDO: 217 s",
                )
            with m4:
                xfuel = cdo_res["extra_fuel_kg"]
                render_metric_card(
                    "Est. Extra Fuel*",
                    f"+{xfuel:.0f} kg",
                    "WARNING" if xfuel > 0 else "OK",
                    "Guide avg non-CDO: 46 kg",
                )

            cdo_fig = build_cdo_chart(cdo_res, presentation_mode=presentation_mode)
            st.plotly_chart(cdo_fig, use_container_width=True)

            exp1, exp2 = st.columns(2)
            cdo_export = pd.concat(
                [cdo_res["cdo_df"].assign(profile="CDO"), cdo_res["step_df"].assign(profile="Step-Down")],
                ignore_index=True,
            )
            with exp1:
                st.download_button(
                    "📥 Download CDO Profile Data (CSV)",
                    data=cdo_export.to_csv(index=False).encode("utf-8"),
                    file_name="cdo_simulation_profile.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with exp2:
                st.download_button(
                    "🖼️ Download Interactive Chart (HTML)",
                    data=cdo_fig.to_html(include_plotlyjs="cdn").encode("utf-8"),
                    file_name="cdo_flight_path_chart.html",
                    mime="text/html",
                    use_container_width=True,
                )

        with st.expander("📐 Formulas & Assumptions (Educational Approximation)"):
            st.markdown(
                """
                - **3:1 Rule of Thumb ToD:** $\\text{ToD}_{\\text{3:1}} = \\frac{\\Delta h}{1,000} \\times 3\\text{ NM}$.
                - **Geometric Descent Gradient:** $\\text{Gradient (ft/NM)} = \\tan(\\theta) \\times 6,076.12$, and Rate of Descent $ROD = \\text{Gradient} \\times \\frac{GS}{60}$.
                - **Reference Benchmark:** The educational guide reports that non-CDO arrivals average **217 seconds** of low-altitude level flight and **46 kg** of extra fuel per arrival.
                - **Extra Fuel (Educational Approximation):** $\\Delta \\text{Fuel} = t_{\\text{level, min}} \\times k_{\\text{fuel}}$.
                """
            )

    # ==========================================================================
    # TAB 4: CDFA (CONTINUOUS DESCENT FINAL APPROACH)
    # ==========================================================================
    with tabs[3]:
        st.header("Continuous Descent Final Approach (CDFA)")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">Definition &amp; Core Concept</div>
                    <p style="margin-bottom:0;">
                        CDFA is a flying technique used during the final approach segment of a
                        <strong>Non-Precision Approach (NPA)</strong>. Instead of descending in steps,
                        the aircraft flies a continuous, stabilized descent along a published
                        <strong>Vertical Descent Angle (VDA)</strong>—typically 3°—from the FAF to the
                        runway threshold or Derived Decision Altitude (DDA).
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">CDFA vs. "Dive and Drive" Hazard</div>
                    <ul style="margin-bottom:0; padding-left:1.1rem;">
                        <li><strong>Dive &amp; Drive Risk:</strong> Rapid descent to step altitudes and level flight at MDA (sometimes ~250 ft AGL in cloud) demands multiple power/pitch changes near the ground, sharply increasing <strong>CFIT</strong> risk.</li>
                        <li><strong>CDFA Solution:</strong> Eliminates level flight at MDA, keeping the aircraft higher longer on a stabilized slope.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                """
                <div class="atc-card">
                    <div class="atc-card-title">VDA, DDA &amp; Stabilized Criteria</div>
                    <ul style="margin-bottom:0; padding-left:1.1rem;">
                        <li><strong>VDA Range:</strong> Normally <strong>2.75° to 3.77°</strong> (3.0° optimum).</li>
                        <li><strong>Derived Decision Altitude (DDA):</strong> MDA + small safety buffer so a missed approach is executed without dipping below MDA.</li>
                        <li><strong>Stabilized Criterion:</strong> Constant descent rate typically <strong>under 1,000 fpm</strong>, stable airspeed, and landing configuration.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.subheader("Interactive CDFA vs. 'Dive and Drive' Simulator")
        ctrl_col, chart_col = st.columns([1.05, 2.15])

        with ctrl_col:
            st.number_input("FAF Altitude (ft MSL)", min_value=1500, max_value=6000, step=100, key="cdfa_faf_alt")
            st.number_input("Runway Threshold Elevation (ft MSL)", min_value=0, max_value=4000, step=50, key="cdfa_thr_elev")
            st.number_input("Minimum Descent Altitude — MDA (ft MSL)", min_value=200, max_value=4500, step=20, key="cdfa_mda")
            st.number_input("DDA Safety Buffer above MDA (ft)", min_value=20, max_value=150, step=10, key="cdfa_dda_buf")
            st.slider(
                "Vertical Descent Angle — VDA (deg)",
                min_value=2.75,
                max_value=3.77,
                step=0.05,
                key="cdfa_vda",
            )
            st.slider("Final Approach Ground Speed (kt)", min_value=90, max_value=200, step=5, key="cdfa_gs")
            st.slider(
                "Dive & Drive Initial Descent Rate (fpm)",
                min_value=1000,
                max_value=2200,
                step=50,
                key="cdfa_dive_rod",
            )
            st.checkbox("Show Schematic Rising Approach Terrain", key="cdfa_terrain")
            st.button("↺ Reset CDFA to Defaults", on_click=reset_keys, args=("cdfa_",), use_container_width=True)

        # Input validation
        faf_val = float(st.session_state["cdfa_faf_alt"])
        thr_val = float(st.session_state["cdfa_thr_elev"])
        mda_val = float(st.session_state["cdfa_mda"])

        if faf_val <= thr_val + 400:
            st.error("FAF Altitude must be at least 400 ft above Runway Threshold Elevation.")
            st.stop()
        if not (thr_val + 150 <= mda_val < faf_val - 200):
            st.error("MDA must be at least 150 ft above Runway Threshold Elevation and below FAF Altitude.")
            st.stop()

        cdfa_res = compute_cdfa_profiles(
            faf_alt_ft=faf_val,
            thr_elev_ft=thr_val,
            mda_ft=mda_val,
            dda_buffer_ft=float(st.session_state["cdfa_dda_buf"]),
            vda_deg=float(st.session_state["cdfa_vda"]),
            ground_speed_kt=float(st.session_state["cdfa_gs"]),
            dive_rod_fpm=float(st.session_state["cdfa_dive_rod"]),
            include_terrain=bool(st.session_state["cdfa_terrain"]),
        )

        with chart_col:
            rod_ok = cdfa_res["stabilized_ok"]
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                render_metric_card(
                    "CDFA Descent Rate*",
                    f"{cdfa_res['cdfa_rod_fpm']:.0f} fpm",
                    "OK" if rod_ok else "WARNING",
                    "Criterion: ≤ 1,000 fpm" if rod_ok else "Exceeds 1,000 fpm limit!",
                )
            with m2:
                render_metric_card(
                    "Derived Decision Alt (DDA)",
                    f"{cdfa_res['dda_ft']:,.0f} ft",
                    "OK",
                    f"MDA {mda_val:,.0f} + {st.session_state['cdfa_dda_buf']} ft buffer",
                )
            with m3:
                render_metric_card(
                    "FAF to Threshold Dist",
                    f"{cdfa_res['faf_dist_nm']:.1f} NM",
                    "INFO",
                    f"Constant {st.session_state['cdfa_vda']:.2f}° VDA",
                )
            with m4:
                min_agl = cdfa_res["min_agl_ft"]
                render_metric_card(
                    "Dive & Drive Level Seg",
                    f"{cdfa_res['level_mda_dist_nm']:.1f} NM",
                    "CONFLICT" if min_agl < 350 else "WARNING",
                    f"Min clearance: ~{min_agl:.0f} ft AGL",
                )

            if not rod_ok:
                st.warning(
                    f"⚠️ **Stabilized Approach Alert:** Computed CDFA descent rate is **{cdfa_res['cdfa_rod_fpm']:.0f} fpm**, "
                    f"exceeding the **1,000 fpm** stabilized approach criterion cited in the guide. Reduce ground speed or VDA."
                )

            cdfa_fig = build_cdfa_chart(cdfa_res, presentation_mode=presentation_mode)
            st.plotly_chart(cdfa_fig, use_container_width=True)

            exp1, exp2 = st.columns(2)
            cdfa_export = pd.concat(
                [cdfa_res["cdfa_df"].assign(profile="CDFA"), cdfa_res["dive_df"].assign(profile="Dive_and_Drive")],
                ignore_index=True,
            )
            with exp1:
                st.download_button(
                    "📥 Download CDFA Profile Data (CSV)",
                    data=cdfa_export.to_csv(index=False).encode("utf-8"),
                    file_name="cdfa_simulation_profile.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with exp2:
                st.download_button(
                    "🖼️ Download Interactive Chart (HTML)",
                    data=cdfa_fig.to_html(include_plotlyjs="cdn").encode("utf-8"),
                    file_name="cdfa_approach_chart.html",
                    mime="text/html",
                    use_container_width=True,
                )

        with st.expander("📐 Formulas & Assumptions (Educational Approximation)"):
            st.markdown(
                """
                - **CDFA Descent Rate (Educational Approximation):**
                  $$ROD_{\\text{CDFA}} = GS \\times \\tan(\\text{VDA}) \\times \\frac{6,076.12}{60}$$
                  (A common cockpit rule of thumb for 3.0° is $ROD \\approx 5 \\times GS$).
                - **Derived Decision Altitude (DDA):** $\\text{DDA} = \\text{MDA} + \\text{Buffer}$, preventing altitude loss below MDA during missed approach initiation.
                - **CFIT Risk Zone:** Shaded interval where the "Dive and Drive" profile levels off at MDA close to underlying approach terrain.
                """
            )

    # ==========================================================================
    # TAB 5: COMPARISON (CCO VS CDO VS CDFA)
    # ==========================================================================
    with tabs[4]:
        st.header("Comparative Analysis: CCO vs. CDO vs. CDFA")
        st.markdown(
            """
            <div class="atc-card">
                <div class="atc-card-title">Phase-by-Phase Operational Synthesis</div>
                <ul style="margin-bottom:0;">
                    <li><strong>CCO (Continuous Climb Operations):</strong> Focuses on the <em>DEPARTURE</em> phase from takeoff to Top of Climb (ToC), using optimum climb thrust to save fuel and reduce CO₂.</li>
                    <li><strong>CDO (Continuous Descent Operations):</strong> Covers the <em>ARRIVAL</em> phase from Top of Descent (ToD) to the Final Approach Fix (FAF), keeping engines at low thrust/idle to reduce fuel burn and community noise.</li>
                    <li><strong>CDFA (Continuous Descent Final Approach):</strong> Focuses specifically on the <em>FINAL APPROACH</em> segment of Non-Precision Approaches (NPA), replacing dangerous step-downs ("Dive and Drive") with a continuous VDA to eliminate CFIT.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Complete Feature Comparison Matrix")
        st.dataframe(COMPARISON_MATRIX_DF, use_container_width=True, hide_index=True)

        st.subheader("Visual Operational Emphasis Comparison")
        comp_fig = build_comparison_bar_chart(presentation_mode=presentation_mode)
        st.plotly_chart(comp_fig, use_container_width=True)

    # ==========================================================================
    # TAB 6: CNS & ATM INTEGRATION
    # ==========================================================================
    with tabs[5]:
        st.header("CNS & ATM Integration")
        st.markdown(
            "Seamless CCO, CDO, and CDFA execution relies on modernized **Communication, Navigation, and Surveillance (CNS)** "
            "infrastructure coupled with **Trajectory-Based Operations (TBO)**."
        )

        col_cns, col_atm = st.columns(2)
        with col_cns:
            st.subheader("CNS Enablers")
            with st.expander("📡 Communication (C): CPDLC & Standardized Phraseology", expanded=True):
                st.markdown(
                    """
                    - **CPDLC & R/T Workload Reduction:** Controller-Pilot Data Link Communications (CPDLC) and automated messaging reduce voice frequency congestion and readback/hearback errors when issuing complex vertical clearances.
                    - **Standardized Phraseology:** Clear tactical instructions—such as **"Descend via STAR"** or explicit speed/altitude constraint cancellations—allow flight crews and FMS computers to maintain uninterrupted vertical profiles while respecting procedure limits.
                    """
                )
            with st.expander("🧭 Navigation (N): PBN, Baro-VNAV, SBAS/LPV & Point Merge", expanded=True):
                st.markdown(
                    """
                    - **Performance-Based Navigation (PBN):** RNAV and RNP specifications enable closed-path SIDs and STARs with published altitude windows (e.g., *"at or above"*), allowing onboard FMS to compute exact continuous trajectories.
                    - **Vertical Guidance for CDFA:** **Baro-VNAV** and **SBAS/LPV** supply geometric vertical guidance during Non-Precision Approaches, establishing a constant VDA without requiring ground ILS infrastructure.
                    - **Point Merge Systems:** Standardized PBN route architectures allow controllers to sequence arriving traffic smoothly on equidistant arcs without sacrificing continuous descent profiles.
                    """
                )
            with st.expander("🎯 Surveillance (S): ADS-B, Radar & Distance-to-Go (DTG)", expanded=True):
                st.markdown(
                    """
                    - **High-Precision Tracking (ADS-B & Radar):** Provides controllers with accurate 3D position and altitude telemetry to monitor vertical profile adherence in real time.
                    - **Distance-to-Go (DTG) Delivery:** Enables controllers to pass accurate DTG updates during tactical radar vectoring so crews can manage kinetic and potential energy.
                    - **Arrival Management Feed:** Feeds automated sequencing tools early in the cruise/ToD phase.
                    """
                )

        with col_atm:
            st.subheader("ATM Integration & Sequencing")
            with st.expander("🌐 Trajectory-Based Operations (TBO)", expanded=True):
                st.markdown(
                    """
                    - **Gate-to-Gate Collaboration:** Integrated ATM transitions control operations toward **Trajectory-Based Operations (TBO)**, where En-Route (ACC), Terminal/Approach (APP), and Tower (TWR) units collaborate with aircraft operators to facilitate uninterrupted climb and descent trajectories across multiple airspace sectors.
                    """
                )
            with st.expander("⏱️ AMAN / DMAN Integration", expanded=True):
                st.markdown(
                    """
                    - **Early Sequencing at Cruise:** Integrated Arrival Managers (**AMAN**) and Departure Managers (**DMAN**) process real-time surveillance data to sequence arrivals and departures early.
                    - **Speed Adjustments Over Level-Offs:** Establishing arrival sequences while aircraft are still at cruising altitude enables subtle early speed adjustments rather than fuel-wasting low-altitude level-offs or holding stacks.
                    """
                )
            with st.expander("🤝 Cross-Sector Coordination (ACC ↔ APP)", expanded=True):
                st.markdown(
                    """
                    - **Seamless Sector Hand-Offs:** Standardized Letters of Agreement (LoAs) and hand-off procedures between En-Route Area Control Centers (**ACC**) and Approach Control (**APP**) prevent forcing aircraft to level off artificially at sector boundaries.
                    """
                )

    # ==========================================================================
    # TAB 7: CHALLENGES & TRADE-OFFS (SID/STAR CROSSING + MULTI-AIRCRAFT TMA)
    # ==========================================================================
    with tabs[6]:
        st.header("Operational Challenges & Tactical ATC Trade-offs")
        st.markdown(
            """
            <div class="atc-card">
                <div class="atc-card-title">Capacity vs. Vertical Efficiency &amp; The Fuel Trade-Off Principle</div>
                <ul style="margin-bottom:0;">
                    <li><strong>TMA Route Intersections:</strong> In congested Terminal Control Areas (TMAs), departure (SID) and arrival (STAR) routes frequently cross, requiring tactical intervention to preserve separation minima.</li>
                    <li><strong>Fuel Trade-Off Principle:</strong> When an intermediate level-off is unavoidable, <strong>a level flight segment during climb burns significantly more fuel than an equivalent level segment during descent</strong>.</li>
                    <li><strong>Fleet Heterogeneity:</strong> Diverse aircraft climb/descent rates make flexible altitude windows ("at or above") superior to rigid altitude restrictions.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Scenario D: Crossing SID (Departure) vs. STAR (Arrival) Conflict Lab")
        s_ctrl, s_viz = st.columns([1.05, 2.15])

        with s_ctrl:
            st.markdown("**1. Route Coordinates (NM)**")
            r1, r2 = st.columns(2)
            with r1:
                st.number_input("SID Start X", step=2.0, key="ss_sid_x0")
                st.number_input("SID End X", step=2.0, key="ss_sid_x1")
                st.number_input("STAR Start X", step=2.0, key="ss_star_x0")
                st.number_input("STAR End X", step=2.0, key="ss_star_x1")
            with r2:
                st.number_input("SID Start Y", step=2.0, key="ss_sid_y0")
                st.number_input("SID End Y", step=2.0, key="ss_sid_y1")
                st.number_input("STAR Start Y", step=2.0, key="ss_star_y0")
                st.number_input("STAR End Y", step=2.0, key="ss_star_y1")

            st.markdown("**2. Aircraft Performance & Timing**")
            p1, p2 = st.columns(2)
            with p1:
                st.slider("DEP Climb (fpm)", 1000, 3500, step=100, key="ss_dep_roc")
                st.slider("DEP Speed (kt)", 180, 350, step=10, key="ss_dep_gs")
            with p2:
                st.slider("ARR Descent (fpm)", 1000, 3200, step=100, key="ss_arr_rod")
                st.slider("ARR Speed (kt)", 180, 340, step=10, key="ss_arr_gs")
            st.slider("Arrival Entry Time Offset (min)", 0.0, 5.0, step=0.25, key="ss_arr_offset")

            st.markdown("**3. Separation Minima & Tactical ATC Resolution**")
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.number_input("Min Horiz (NM)", min_value=1.0, max_value=10.0, step=0.5, key="ss_min_horiz")
            with m_col2:
                st.number_input("Min Vert (ft)", min_value=500, max_value=2000, step=500, key="ss_min_vert")

            st.selectbox(
                "Apply Controller Level-Off Resolution",
                options=["None", "Arrival (Break CDO)", "Departure (Break CCO)"],
                key="ss_hold_target",
                help="Compare the fuel and profile trade-off of leveling off the Arrival vs. the Departure.",
            )
            if st.session_state["ss_hold_target"] != "None":
                h1, h2 = st.columns(2)
                with h1:
                    st.number_input("Hold Alt (ft)", min_value=3000, max_value=16000, step=1000, key="ss_hold_alt")
                with h2:
                    st.number_input("Hold Dur (min)", min_value=0.5, max_value=6.0, step=0.5, key="ss_hold_dur")

            st.button("↺ Reset SID/STAR Scenario", on_click=reset_keys, args=("ss_",), use_container_width=True)

        ss_res = compute_sid_star_scenario(
            sid_start=(float(st.session_state["ss_sid_x0"]), float(st.session_state["ss_sid_y0"])),
            sid_end=(float(st.session_state["ss_sid_x1"]), float(st.session_state["ss_sid_y1"])),
            star_start=(float(st.session_state["ss_star_x0"]), float(st.session_state["ss_star_y0"])),
            star_end=(float(st.session_state["ss_star_x1"]), float(st.session_state["ss_star_y1"])),
            dep_start_alt=2000.0,
            dep_target_alt=18000.0,
            dep_roc_fpm=float(st.session_state["ss_dep_roc"]),
            dep_gs_kt=float(st.session_state["ss_dep_gs"]),
            arr_start_alt=16000.0,
            arr_target_alt=3000.0,
            arr_rod_fpm=float(st.session_state["ss_arr_rod"]),
            arr_gs_kt=float(st.session_state["ss_arr_gs"]),
            arr_offset_min=float(st.session_state["ss_arr_offset"]),
            min_horiz_nm=float(st.session_state["ss_min_horiz"]),
            min_vert_ft=float(st.session_state["ss_min_vert"]),
            level_off_target=str(st.session_state["ss_hold_target"]),
            level_off_alt_ft=float(st.session_state["ss_hold_alt"]),
            level_off_dur_min=float(st.session_state["ss_hold_dur"]),
        )

        with s_viz:
            conflict = ss_res["has_conflict"]
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                render_metric_card(
                    "Separation Status",
                    "LOSS OF SEP" if conflict else "SEPARATED",
                    "CONFLICT" if conflict else "OK",
                    f"Minima: {st.session_state['ss_min_horiz']} NM / {st.session_state['ss_min_vert']} ft",
                )
            with c2:
                render_metric_card(
                    "CPA Horizontal",
                    f"{ss_res['cpa_horiz_nm']:.2f} NM",
                    "CONFLICT" if ss_res["cpa_horiz_nm"] < st.session_state["ss_min_horiz"] and conflict else "INFO",
                    f"At t = {ss_res['cpa_time_min']:.1f} min",
                )
            with c3:
                render_metric_card(
                    "CPA Vertical",
                    f"{ss_res['cpa_vert_ft']:.0f} ft",
                    "CONFLICT" if ss_res["cpa_vert_ft"] < st.session_state["ss_min_vert"] and conflict else "INFO",
                    f"At t = {ss_res['cpa_time_min']:.1f} min",
                )
            with c4:
                xf = ss_res["extra_fuel_kg"]
                target_lbl = st.session_state["ss_hold_target"]
                render_metric_card(
                    "Trade-Off Extra Fuel*",
                    f"+{xf:.0f} kg",
                    "WARNING" if "Departure" in target_lbl else ("INFO" if xf > 0 else "OK"),
                    "Climb hold burns ~2.3x descent hold" if xf > 0 else "No tactical hold applied",
                )

            if conflict:
                st.error(
                    f"🚨 **Separation Minima Violated!** At **t = {ss_res['cpa_time_min']:.1f} min**, horizontal separation "
                    f"drops to **{ss_res['cpa_horiz_nm']:.2f} NM** and vertical separation to **{ss_res['cpa_vert_ft']:.0f} ft**. "
                    f"Try selecting **'Apply Controller Level-Off Resolution'** on the left and compare the fuel penalty of "
                    f"leveling off the Arrival (CDO) vs. the Departure (CCO)."
                )
            elif st.session_state["ss_hold_target"] != "None":
                st.success(
                    f"✅ **Conflict Resolved** using **{st.session_state['ss_hold_target']}** at "
                    f"**{st.session_state['ss_hold_alt']:,} ft** for **{st.session_state['ss_hold_dur']:.1f} min** "
                    f"(Estimated extra fuel penalty: **+{ss_res['extra_fuel_kg']:.0f} kg** — Educational approximation)."
                )

            ss_fig = build_sid_star_dual_chart(ss_res, presentation_mode=presentation_mode)
            st.plotly_chart(ss_fig, use_container_width=True)

            exp1, exp2 = st.columns(2)
            with exp1:
                st.download_button(
                    "📥 Download Separation Telemetry (CSV)",
                    data=ss_res["sep_df"].to_csv(index=False).encode("utf-8"),
                    file_name="sid_star_separation_log.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with exp2:
                st.download_button(
                    "🖼️ Download Dual Radar Chart (HTML)",
                    data=ss_fig.to_html(include_plotlyjs="cdn").encode("utf-8"),
                    file_name="sid_star_crossing_chart.html",
                    mime="text/html",
                    use_container_width=True,
                )

        with st.expander("📐 Formulas & Assumptions (Educational Approximation)"):
            st.markdown(
                """
                - **3D Separation Check:** A conflict is flagged whenever **both** horizontal distance $d_{xy} < d_{\\min}$ (default 3.0 NM) **and** vertical separation $\\Delta h < h_{\\min}$ (default 1,000 ft) occur simultaneously.
                - **Tactical Fuel Trade-Off (Educational Approximation):** Reflects Section 1.3 and Section 8.2 of the guide: holding a climbing departure level burns significantly more extra fuel (~32 kg/min illustrative factor) than holding a descending arrival level (~13 kg/min illustrative factor).
                """
            )

        # --- Bonus Section E: Multi-Aircraft TMA Mode ---
        st.markdown("---")
        st.subheader("Scenario E (Bonus): Multi-Aircraft TMA Sector Mode (3–6 Aircraft)")
        st.caption(
            "Edit callsigns, movement types (Departure/Arrival), starting altitudes, speeds, and vertical rates below "
            "to observe multi-traffic TMA interactions and separation alerts."
        )

        default_flights = pd.DataFrame(
            [
                {"Callsign": "KLM101", "Type": "Departure", "Start Alt (ft)": 2000, "Speed (kt)": 260, "Vert Rate (fpm)": 2200},
                {"Callsign": "DLH402", "Type": "Arrival", "Start Alt (ft)": 15000, "Speed (kt)": 250, "Vert Rate (fpm)": 1800},
                {"Callsign": "BAW718", "Type": "Departure", "Start Alt (ft)": 3000, "Speed (kt)": 280, "Vert Rate (fpm)": 2000},
                {"Callsign": "AFR912", "Type": "Arrival", "Start Alt (ft)": 13000, "Speed (kt)": 240, "Vert Rate (fpm)": 1600},
            ]
        )

        edited_flights = st.data_editor(
            default_flights,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Callsign": st.column_config.TextColumn("Callsign", max_chars=10, required=True),
                "Type": st.column_config.SelectboxColumn("Movement Type", options=["Departure", "Arrival"], required=True),
                "Start Alt (ft)": st.column_config.NumberColumn("Start Alt (ft)", min_value=1000, max_value=35000, step=500, required=True),
                "Speed (kt)": st.column_config.NumberColumn("Ground Speed (kt)", min_value=140, max_value=420, step=10, required=True),
                "Vert Rate (fpm)": st.column_config.NumberColumn("Climb/Descent Rate (fpm)", min_value=500, max_value=4000, step=100, required=True),
            },
            key="multi_acft_editor",
        )

        clean_flights = edited_flights.dropna().head(6)
        if len(clean_flights) < 3:
            st.warning("Please keep between 3 and 6 valid aircraft rows in the table to run the multi-aircraft simulation.")
        else:
            ma_res = compute_multi_aircraft_tma(clean_flights, min_horiz_nm=3.0, min_vert_ft=1000.0)
            if not ma_res["conflict_events"].empty:
                st.error(
                    f"🚨 **TMA Separation Alert:** {len(ma_res['conflict_events'])} aircraft pair(s) breached "
                    f"3.0 NM / 1,000 ft separation minima!"
                )
                st.dataframe(ma_res["conflict_events"], use_container_width=True, hide_index=True)
            else:
                st.success("✅ All simulated TMA trajectories remain separated by at least 3.0 NM horizontally or 1,000 ft vertically.")

            ma_fig = build_multi_aircraft_chart(ma_res, presentation_mode=presentation_mode)
            st.plotly_chart(ma_fig, use_container_width=True)

    # ==========================================================================
    # TAB 8: CLASS QUIZ
    # ==========================================================================
    with tabs[7]:
        st.header("Class Knowledge Check: CCO, CDO, CDFA & CNS/ATM")
        st.markdown(
            "Select one answer for each of the **10 questions** below. Immediate feedback and references to the "
            "ATC presentation guide appear after selection."
        )

        score = 0
        answered_count = 0

        for idx, item in enumerate(QUIZ_QUESTIONS):
            st.markdown(f"#### {item['q']}")
            choice = st.radio(
                label=f"Select answer for Q{idx+1}",
                options=item["options"],
                index=None,
                key=f"quiz_q_{idx}",
                label_visibility="collapsed",
            )
            if choice is not None:
                answered_count += 1
                chosen_idx = item["options"].index(choice)
                if chosen_idx == item["answer"]:
                    score += 1
                    st.success(f"✅ **Correct!** {item['explanation']}")
                else:
                    correct_text = item["options"][item["answer"]]
                    st.error(f"❌ **Incorrect.** Correct answer: **{correct_text}**. {item['explanation']}")
            st.markdown("---")

        q_col1, q_col2 = st.columns([2, 1])
        with q_col1:
            pct = (score / len(QUIZ_QUESTIONS)) * 100.0
            badge_status = "OK" if score >= 8 else ("WARNING" if score >= 5 else "CONFLICT")
            render_metric_card(
                "Final Classroom Quiz Score",
                f"{score} / {len(QUIZ_QUESTIONS)} ({pct:.0f}%)",
                badge_status,
                f"Answered {answered_count} of {len(QUIZ_QUESTIONS)} questions",
            )
        with q_col2:
            if st.button("🔄 Reset All Quiz Answers", use_container_width=True):
                for idx in range(len(QUIZ_QUESTIONS)):
                    st.session_state[f"quiz_q_{idx}"] = None
                st.rerun()

    # Fixed Educational Footer
    render_footer()


if __name__ == "__main__":
    main()
