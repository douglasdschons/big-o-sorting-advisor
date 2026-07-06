"""
Big-O Sorting Advisor - Streamlit App

Run locally:
    streamlit run app.py

Alternative:
    python -m streamlit run app.py
"""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from sorting_advisor import (
    DEFAULT_MAX_COST_RATIO_FOR_ZOOM,
    DEFAULT_RADIX_BASE,
    DEFAULT_ZOOM_DELTA,
    VALID_DATA_ORDERS,
    VALID_DATA_TYPES,
    build_results_table,
    create_global_complexity_figure,
    create_zoom_complexity_figure,
    evaluate_algorithms,
    explain_recommendation,
    get_decision_flow_lines,
    estimate_radix_passes,
)


# ==========================================================
# Page configuration
# ==========================================================

st.set_page_config(
    page_title="Big-O Sorting Advisor",
    page_icon="📊",
    layout="wide",
)


# ==========================================================
# Session state
# ==========================================================

DEFAULTS = {
    "n": 10_000,
    "data_type": "integer",
    "data_order": "random",
    "integer_range_k": 500,
    "requires_stability": True,
    "ram_option": "8 GB",
    "available_ram_custom": 8.0,
    "show_educational_algorithms": True,
    "zoom_delta": DEFAULT_ZOOM_DELTA,
    "max_cost_ratio_for_zoom": float(DEFAULT_MAX_COST_RATIO_FOR_ZOOM),
    "radix_base": DEFAULT_RADIX_BASE,
    "calculated": False,
}


def initialize_state() -> None:
    """
    Initializes state only for missing keys.

    This function is safe to run before widgets are created.
    """
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_defaults() -> None:
    """
    Resets the app state.

    Important:
    This function is used as a Streamlit callback. Widget-related session_state
    keys must be changed inside callbacks or before the widgets are created.
    Modifying them after widgets are instantiated raises a StreamlitAPIException.
    """
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


initialize_state()


# ==========================================================
# Sidebar controls
# ==========================================================

st.sidebar.title("Input scenario")

# The reset button is registered before the form widgets are created.
# This avoids Streamlit's "cannot modify widget state after instantiation" error.
st.sidebar.button(
    "Reset default scenario",
    on_click=reset_defaults,
    help="Restore the default scenario and clear the previous calculation.",
)

with st.sidebar.form("input_form"):
    n = st.number_input(
        "Number of elements (n)",
        min_value=1,
        step=1_000,
        key="n",
        help="Size of the dataset to be sorted.",
    )

    data_type = st.selectbox(
        "Data type",
        VALID_DATA_TYPES,
        key="data_type",
        help="Counting Sort and Radix Sort require integer-like data.",
    )

    data_order = st.selectbox(
        "Initial data order",
        VALID_DATA_ORDERS,
        key="data_order",
        help="Some algorithms behave differently when data is nearly sorted or reversed.",
    )

    if data_type == "integer":
        integer_range_k = st.number_input(
            "Integer range (k)",
            min_value=1,
            step=100,
            key="integer_range_k",
            help=(
                "Approximate number of possible integer values. "
                "For values from 0 to 500, k is approximately 501."
            ),
        )
        integer_range_k = int(integer_range_k)
    else:
        integer_range_k = None
        st.info("Integer range (k) is not used for non-integer data.")

    requires_stability = st.checkbox(
        "Requires stable sorting",
        key="requires_stability",
        help="Stable sorting preserves the relative order of elements with equal keys.",
    )

    ram_option = st.selectbox(
        "Available RAM",
        ["8 GB", "16 GB", "32 GB", "64 GB", "Custom"],
        key="ram_option",
    )

    if ram_option == "Custom":
        available_ram_gb = st.number_input(
            "Custom RAM (GB)",
            min_value=0.1,
            step=1.0,
            key="available_ram_custom",
        )
    else:
        available_ram_gb = float(ram_option.replace(" GB", ""))

    with st.expander("Advanced settings"):
        show_educational_algorithms = st.checkbox(
            "Show educational algorithms in global chart",
            key="show_educational_algorithms",
        )

        zoom_delta = st.number_input(
            "Zoom delta around n",
            min_value=1,
            step=100,
            key="zoom_delta",
        )

        max_cost_ratio_for_zoom = st.number_input(
            "Max cost ratio for zoom",
            min_value=1.0,
            step=0.5,
            key="max_cost_ratio_for_zoom",
        )

        radix_base = st.number_input(
            "Radix base",
            min_value=2,
            step=2,
            key="radix_base",
        )

    calculate_clicked = st.form_submit_button(
        "Calculate recommendation",
        type="primary",
    )

if calculate_clicked:
    st.session_state["calculated"] = True


# ==========================================================
# Main header
# ==========================================================

st.title("Big-O Sorting Advisor")

st.markdown(
    """
A visual and educational decision tool that explains which sorting strategy
makes the most sense for a described data scenario.

**Core principle:** the best algorithm is the lowest-cost option among the
compatible algorithms.
"""
)

st.info(
    "This app does not sort the data. It explains which sorting strategy makes "
    "the most sense for the described scenario, and why."
)

if not st.session_state["calculated"]:
    st.warning("Set the scenario in the sidebar and click **Calculate recommendation**.")
    st.stop()


# ==========================================================
# Clean evaluation
# ==========================================================
# Streamlit reruns this script from top to bottom after every submitted form.
# No result object is reused from previous calculations.

current_scenario = {
    "n": int(n),
    "data_type": data_type,
    "data_order": data_order,
    "k": integer_range_k,
    "requires_stability": bool(requires_stability),
    "available_ram_gb": float(available_ram_gb),
    "radix_base": int(radix_base),
    "show_educational_algorithms": bool(show_educational_algorithms),
    "zoom_delta": int(zoom_delta),
    "max_cost_ratio_for_zoom": float(max_cost_ratio_for_zoom),
}

try:
    results, recommendation = evaluate_algorithms(
        n=current_scenario["n"],
        data_type=current_scenario["data_type"],
        data_order=current_scenario["data_order"],
        k=current_scenario["k"],
        requires_stability=current_scenario["requires_stability"],
        available_ram_gb=current_scenario["available_ram_gb"],
        radix_base=current_scenario["radix_base"],
    )
except ValueError as error:
    st.error(str(error))
    st.stop()


# ==========================================================
# Scenario summary and recommendation
# ==========================================================

left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("Scenario")

    scenario_rows = [
        ("Number of elements", f"{current_scenario['n']:,}"),
        ("Data type", current_scenario["data_type"]),
        ("Initial data order", current_scenario["data_order"]),
        ("Requires stability", str(current_scenario["requires_stability"])),
        ("Available RAM", f"{current_scenario['available_ram_gb']:g} GB"),
    ]

    if current_scenario["data_type"] == "integer":
        scenario_rows.append(("Integer range k", f"{current_scenario['k']:,}"))
        scenario_rows.append(
            (
                "Estimated Radix passes",
                str(
                    estimate_radix_passes(
                        current_scenario["k"],
                        current_scenario["radix_base"],
                    )
                ),
            )
        )

    st.table(pd.DataFrame(scenario_rows, columns=["Parameter", "Value"]))

with right_col:
    st.subheader("Recommendation")

    if recommendation is None:
        st.error("No compatible practical algorithm was found.")
    else:
        st.success(f"Recommended algorithm: {recommendation['name']}")

        metric_col_1, metric_col_2 = st.columns(2)
        metric_col_1.metric(
            "Theoretical cost",
            f"{recommendation['theoretical_cost']:,.0f}",
        )
        metric_col_2.metric(
            "Complexity family",
            recommendation["complexity_family"],
        )

        st.markdown(
            f"""
**Why this recommendation?**

{recommendation['name']} has the lowest theoretical cost among the compatible
practical algorithms for the described scenario.
"""
        )


# ==========================================================
# Explanation
# ==========================================================

st.subheader("Technical explanation")

st.text(
    explain_recommendation(
        recommendation=recommendation,
        results=results,
    )
)


# ==========================================================
# Results table
# ==========================================================

st.subheader("Algorithm evaluation table")

results_df = pd.DataFrame(build_results_table(results))
display_df = results_df.copy()


def format_numeric_value(value):
    if isinstance(value, float) and math.isnan(value):
        return "Not applicable"
    return f"{value:,.4f}"


for column in [
    "Theoretical cost",
    "Data memory (MB)",
    "Extra memory (MB)",
    "Total memory (MB)",
]:
    display_df[column] = display_df[column].map(format_numeric_value)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# ==========================================================
# Charts
# ==========================================================

st.subheader("Visual analysis")

chart_tab_1, chart_tab_2 = st.tabs(
    ["Global Big-O view", "Decision zoom"]
)

with chart_tab_1:
    st.markdown(
        """
The global chart shows the complexity families that are actually represented
by evaluated algorithms in the current scenario.
"""
    )

    global_fig = create_global_complexity_figure(
        n=current_scenario["n"],
        k=current_scenario["k"],
        results=results,
        recommendation=recommendation,
        show_educational_algorithms=current_scenario["show_educational_algorithms"],
        radix_base=current_scenario["radix_base"],
    )

    st.pyplot(global_fig, clear_figure=True)
    plt.close(global_fig)

with chart_tab_2:
    st.markdown(
        """
The zoom chart is decision-oriented. It only shows complexity families that
are represented by visible algorithm points in the relevant region.
"""
    )

    zoom_fig, omitted_results = create_zoom_complexity_figure(
        n=current_scenario["n"],
        k=current_scenario["k"],
        results=results,
        recommendation=recommendation,
        delta=current_scenario["zoom_delta"],
        max_cost_ratio=current_scenario["max_cost_ratio_for_zoom"],
        radix_base=current_scenario["radix_base"],
    )

    st.pyplot(zoom_fig, clear_figure=True)
    plt.close(zoom_fig)

    if omitted_results:
        with st.expander("Algorithms omitted from zoom due to scale"):
            omitted_table = pd.DataFrame(
                [
                    {
                        "Algorithm": result["name"],
                        "Cost": (
                            f"{result['theoretical_cost']:,.2f}"
                            if not math.isnan(result["theoretical_cost"])
                            else "Not applicable"
                        ),
                        "Family": result["complexity_family"],
                        "Reason": "Too far from the recommended cost, not applicable, or educational only.",
                    }
                    for result in omitted_results
                ]
            )
            st.dataframe(omitted_table, use_container_width=True, hide_index=True)


# ==========================================================
# Decision flow
# ==========================================================

st.subheader("Decision flow")

flow_text = "\n".join(
    get_decision_flow_lines(
        n=current_scenario["n"],
        data_type=current_scenario["data_type"],
        data_order=current_scenario["data_order"],
        recommendation=recommendation,
    )
)

st.code(flow_text, language="text")


# ==========================================================
# Footer
# ==========================================================

st.markdown("---")

st.markdown(
    """
### Why this project exists

Calling `sort()` is easy. Understanding why a sorting strategy is appropriate
requires looking at data type, input size, stability, memory, value range, and
theoretical cost.

This app was built as an educational tool to make that reasoning visible.
"""
)
