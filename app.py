"""
Big-O Sorting Advisor - Streamlit App

Run locally:
    streamlit run app.py
"""

from __future__ import annotations

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

st.set_page_config(
    page_title="Big-O Sorting Advisor",
    page_icon="📊",
    layout="wide",
)

st.sidebar.title("Input scenario")

n = st.sidebar.number_input(
    "Number of elements (n)",
    min_value=1,
    value=10_000,
    step=1_000,
    help="Size of the dataset to be sorted.",
)

data_type = st.sidebar.selectbox(
    "Data type",
    VALID_DATA_TYPES,
    index=0,
    help="Counting Sort and Radix Sort require integer-like data.",
)

data_order = st.sidebar.selectbox(
    "Initial data order",
    VALID_DATA_ORDERS,
    index=0,
    help="Some algorithms behave differently when data is nearly sorted or reversed.",
)

if data_type == "integer":
    integer_range_k = st.sidebar.number_input(
        "Integer range (k)",
        min_value=1,
        value=500,
        step=100,
        help=(
            "Approximate number of possible integer values. "
            "For values from 0 to 500, k is approximately 501."
        ),
    )
    integer_range_k = int(integer_range_k)
else:
    integer_range_k = None
    st.sidebar.info("Integer range (k) is only used for integer data.")

requires_stability = st.sidebar.checkbox(
    "Requires stable sorting",
    value=True,
    help="Stable sorting preserves the relative order of elements with equal keys.",
)

ram_option = st.sidebar.selectbox(
    "Available RAM",
    ["8 GB", "16 GB", "32 GB", "64 GB", "Custom"],
    index=0,
)

if ram_option == "Custom":
    available_ram_gb = st.sidebar.number_input(
        "Custom RAM (GB)",
        min_value=0.1,
        value=8.0,
        step=1.0,
    )
else:
    available_ram_gb = float(ram_option.replace(" GB", ""))

with st.sidebar.expander("Advanced settings"):
    show_educational_algorithms = st.checkbox(
        "Show educational algorithms in global chart",
        value=True,
    )

    zoom_delta = st.number_input(
        "Zoom delta around n",
        min_value=1,
        value=DEFAULT_ZOOM_DELTA,
        step=100,
    )

    max_cost_ratio_for_zoom = st.number_input(
        "Max cost ratio for zoom",
        min_value=1.0,
        value=float(DEFAULT_MAX_COST_RATIO_FOR_ZOOM),
        step=0.5,
    )

    radix_base = st.number_input(
        "Radix base",
        min_value=2,
        value=DEFAULT_RADIX_BASE,
        step=2,
    )

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

try:
    results, recommendation = evaluate_algorithms(
        n=int(n),
        data_type=data_type,
        data_order=data_order,
        k=integer_range_k,
        requires_stability=requires_stability,
        available_ram_gb=float(available_ram_gb),
        radix_base=int(radix_base),
    )
except ValueError as error:
    st.error(str(error))
    st.stop()

left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("Scenario")
    scenario_rows = [
        ("Number of elements", f"{int(n):,}"),
        ("Data type", data_type),
        ("Initial data order", data_order),
        ("Requires stability", str(requires_stability)),
        ("Available RAM", f"{available_ram_gb:g} GB"),
    ]
    if data_type == "integer":
        scenario_rows.append(("Integer range k", f"{integer_range_k:,}"))
        scenario_rows.append(("Estimated Radix passes", str(estimate_radix_passes(integer_range_k, int(radix_base)))))
    st.table(pd.DataFrame(scenario_rows, columns=["Parameter", "Value"]))

with right_col:
    st.subheader("Recommendation")
    if recommendation is None:
        st.error("No compatible practical algorithm was found.")
    else:
        st.success(f"Recommended algorithm: {recommendation['name']}")
        metric_col_1, metric_col_2 = st.columns(2)
        metric_col_1.metric("Theoretical cost", f"{recommendation['theoretical_cost']:,.0f}")
        metric_col_2.metric("Complexity family", recommendation["complexity_family"])
        st.markdown(
            f"""
**Why this recommendation?**

{recommendation['name']} has the lowest theoretical cost among the compatible
practical algorithms for the described scenario.
"""
        )

st.subheader("Technical explanation")
st.text(explain_recommendation(recommendation=recommendation, results=results))

st.subheader("Algorithm evaluation table")
results_df = pd.DataFrame(build_results_table(results))
display_df = results_df.copy()
for column in ["Theoretical cost", "Data memory (MB)", "Extra memory (MB)", "Total memory (MB)"]:
    display_df[column] = display_df[column].map(lambda value: f"{value:,.4f}")
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.subheader("Visual analysis")
chart_tab_1, chart_tab_2 = st.tabs(["Global Big-O view", "Decision zoom"])

with chart_tab_1:
    st.markdown(
        """
The global chart is educational. It shows the general growth behavior of the
main complexity families.
"""
    )
    global_fig = create_global_complexity_figure(
        n=int(n),
        k=integer_range_k,
        results=results,
        recommendation=recommendation,
        show_educational_algorithms=show_educational_algorithms,
        radix_base=int(radix_base),
    )
    st.pyplot(global_fig, clear_figure=True)

with chart_tab_2:
    st.markdown(
        """
The zoom chart is decision-oriented. It only shows complexity families that
are represented by visible algorithm points in the relevant region.
"""
    )
    zoom_fig, omitted_results = create_zoom_complexity_figure(
        n=int(n),
        k=integer_range_k,
        results=results,
        recommendation=recommendation,
        delta=int(zoom_delta),
        max_cost_ratio=float(max_cost_ratio_for_zoom),
        radix_base=int(radix_base),
    )
    st.pyplot(zoom_fig, clear_figure=True)

    if omitted_results:
        with st.expander("Algorithms omitted from zoom due to scale"):
            omitted_table = pd.DataFrame(
                [
                    {
                        "Algorithm": result["name"],
                        "Cost": f"{result['theoretical_cost']:,.2f}",
                        "Family": result["complexity_family"],
                        "Reason": "Too far from the recommended cost or educational only.",
                    }
                    for result in omitted_results
                ]
            )
            st.dataframe(omitted_table, use_container_width=True, hide_index=True)

st.subheader("Decision flow")
flow_text = "\n".join(
    get_decision_flow_lines(
        n=int(n),
        data_type=data_type,
        data_order=data_order,
        recommendation=recommendation,
    )
)
st.code(flow_text, language="text")

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
