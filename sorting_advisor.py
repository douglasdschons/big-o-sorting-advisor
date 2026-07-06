"""
Big-O Sorting Advisor - Core Decision Engine

Core principles:
1. Best algorithm = lowest cost among compatible algorithms.
2. This tool does not sort the data; it explains which sorting strategy
   makes the most sense for the described scenario.

This module is intentionally independent from Streamlit.
You can run it directly in Spyder, VS Code, PyCharm, or terminal.

Author: Douglas Schons
Project: Engineering-to-Software Portfolio
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np


# ==========================================================
# 1. Default scenario for local Spyder testing
# ==========================================================
# Edit this section and run this file directly to test the engine.

DEFAULT_N = 10_000
DEFAULT_DATA_TYPE = "integer"
DEFAULT_DATA_ORDER = "random"
DEFAULT_INTEGER_RANGE_K = 500
DEFAULT_REQUIRES_STABILITY = True
DEFAULT_AVAILABLE_RAM_GB = 8.0
DEFAULT_SHOW_EDUCATIONAL_ALGORITHMS = True
DEFAULT_ZOOM_DELTA = 1000
DEFAULT_MAX_COST_RATIO_FOR_ZOOM = 2.5
DEFAULT_RADIX_BASE = 256


# ==========================================================
# 2. Visual model
# ==========================================================

CURVE_COLORS = {
    "O(n)": "tab:blue",
    "O(n log n)": "tab:orange",
    "O(n²)": "tab:red",
    "O(n + k)": "tab:green",
    "O(d n)": "tab:purple",
}

ALGORITHM_MARKERS = {
    "Timsort": "o",
    "Counting Sort": "s",
    "Radix Sort": "^",
    "Merge Sort": "D",
    "Quick Sort": "X",
    "Heap Sort": "P",
    "Bubble Sort": "v",
}


def get_algorithm_marker(algorithm_name: str) -> str:
    return ALGORITHM_MARKERS.get(algorithm_name, "o")


def get_algorithm_color(result: Dict) -> str:
    return CURVE_COLORS[result["complexity_family"]]


# ==========================================================
# 3. Basic models
# ==========================================================

BYTES_PER_ELEMENT = {
    "integer": 8,
    "float": 8,
    "string": 50,   # rough educational estimate
    "object": 64,   # rough educational estimate
}

VALID_DATA_TYPES = ["integer", "float", "string", "object"]
VALID_DATA_ORDERS = ["random", "nearly_sorted", "reversed", "many_duplicates"]


def validate_inputs(
    n: int,
    data_type: str,
    data_order: str,
    integer_range_k: Optional[int],
    available_ram_gb: float,
) -> None:
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer.")

    if data_type not in VALID_DATA_TYPES:
        raise ValueError(f"data_type must be one of: {VALID_DATA_TYPES}")

    if data_order not in VALID_DATA_ORDERS:
        raise ValueError(f"data_order must be one of: {VALID_DATA_ORDERS}")

    if data_type == "integer":
        if integer_range_k is None:
            raise ValueError("integer_range_k is required when data_type = 'integer'.")
        if not isinstance(integer_range_k, int) or integer_range_k <= 0:
            raise ValueError("integer_range_k must be a positive integer.")

    if available_ram_gb <= 0:
        raise ValueError("available_ram_gb must be greater than zero.")


def gb_to_bytes(value_gb: float) -> float:
    return value_gb * 1024**3


def bytes_to_mb(value_bytes: float) -> float:
    return value_bytes / 1024**2


def estimate_data_memory_bytes(n: int, data_type: str) -> float:
    return n * BYTES_PER_ELEMENT[data_type]


# ==========================================================
# 4. Complexity functions
# ==========================================================

def cost_n(n: int, k: Optional[int] = None) -> float:
    return float(n)


def cost_n_log_n(n: int, k: Optional[int] = None) -> float:
    if n <= 1:
        return float(n)
    return float(n * math.log2(n))


def cost_n_squared(n: int, k: Optional[int] = None) -> float:
    return float(n**2)


def cost_n_plus_k(n: int, k: Optional[int]) -> float:
    if k is None:
        raise ValueError("k is required for O(n + k).")
    return float(n + k)


def estimate_radix_passes(k: Optional[int], radix_base: int = DEFAULT_RADIX_BASE) -> int:
    """Estimates Radix Sort passes using d = ceil(log_base(k))."""
    if k is None or k <= 1:
        return 1
    return max(1, math.ceil(math.log(k, radix_base)))


def cost_radix(n: int, k: Optional[int], radix_base: int = DEFAULT_RADIX_BASE) -> float:
    """Simplified Radix Sort cost model: O(d * n)."""
    passes = estimate_radix_passes(k, radix_base)
    return float(passes * n)


def get_complexity_family(algorithm_name: str, data_order: str) -> str:
    """Returns the effective complexity family for the current scenario."""
    if algorithm_name == "Timsort":
        return "O(n)" if data_order == "nearly_sorted" else "O(n log n)"
    if algorithm_name == "Counting Sort":
        return "O(n + k)"
    if algorithm_name == "Radix Sort":
        return "O(d n)"
    if algorithm_name == "Merge Sort":
        return "O(n log n)"
    if algorithm_name == "Quick Sort":
        return "O(n²)" if data_order == "reversed" else "O(n log n)"
    if algorithm_name == "Heap Sort":
        return "O(n log n)"
    if algorithm_name == "Bubble Sort":
        return "O(n)" if data_order == "nearly_sorted" else "O(n²)"
    raise ValueError(f"Unknown algorithm: {algorithm_name}")


# ==========================================================
# 5. Algorithm database
# ==========================================================

ALGORITHMS = [
    {
        "name": "Timsort",
        "category": "practical",
        "allowed_types": ["integer", "float", "string", "object"],
        "stable": True,
        "extra_memory_model": "n",
        "notes": "Python's built-in sorting strategy. Stable and strong for partially ordered data.",
    },
    {
        "name": "Counting Sort",
        "category": "practical",
        "allowed_types": ["integer"],
        "stable": True,
        "extra_memory_model": "k",
        "notes": "Very efficient for integer data when the value range is small.",
    },
    {
        "name": "Radix Sort",
        "category": "practical",
        "allowed_types": ["integer"],
        "stable": True,
        "extra_memory_model": "n",
        "notes": "Useful for integer data when digit-based processing is suitable.",
    },
    {
        "name": "Merge Sort",
        "category": "practical",
        "allowed_types": ["integer", "float", "string", "object"],
        "stable": True,
        "extra_memory_model": "n",
        "notes": "Stable comparison sort with predictable O(n log n) behavior.",
    },
    {
        "name": "Quick Sort",
        "category": "practical",
        "allowed_types": ["integer", "float", "string", "object"],
        "stable": False,
        "extra_memory_model": "log_n",
        "notes": "Fast average-case comparison sort, but not stable in its standard form.",
    },
    {
        "name": "Heap Sort",
        "category": "practical",
        "allowed_types": ["integer", "float", "string", "object"],
        "stable": False,
        "extra_memory_model": "constant",
        "notes": "Memory-efficient comparison sort with O(n log n) behavior, but not stable.",
    },
    {
        "name": "Bubble Sort",
        "category": "educational",
        "allowed_types": ["integer", "float", "string", "object"],
        "stable": True,
        "extra_memory_model": "constant",
        "notes": "Educational reference only. Not recommended for practical use.",
    },
]


# ==========================================================
# 6. Cost model
# ==========================================================

def estimate_theoretical_cost(
    algorithm_name: str,
    n: int,
    k: Optional[int],
    data_order: str,
    radix_base: int = DEFAULT_RADIX_BASE,
) -> float:
    """Returns a simplified theoretical cost value, not runtime in seconds."""
    if algorithm_name == "Timsort":
        return cost_n(n) if data_order == "nearly_sorted" else cost_n_log_n(n)
    if algorithm_name == "Counting Sort":
        return cost_n_plus_k(n, k)
    if algorithm_name == "Radix Sort":
        return cost_radix(n, k, radix_base)
    if algorithm_name == "Merge Sort":
        return cost_n_log_n(n)
    if algorithm_name == "Quick Sort":
        return cost_n_squared(n) if data_order == "reversed" else cost_n_log_n(n)
    if algorithm_name == "Heap Sort":
        return cost_n_log_n(n)
    if algorithm_name == "Bubble Sort":
        return cost_n(n) if data_order == "nearly_sorted" else cost_n_squared(n)
    raise ValueError(f"Unknown algorithm: {algorithm_name}")


# ==========================================================
# 7. Memory model
# ==========================================================

def estimate_extra_memory_bytes(algorithm: Dict, n: int, k: Optional[int], data_type: str) -> float:
    element_size = BYTES_PER_ELEMENT[data_type]
    model = algorithm["extra_memory_model"]

    if model == "constant":
        return 0.0
    if model == "log_n":
        return float(int(math.log2(max(n, 2))) * element_size)
    if model == "n":
        return float(n * element_size)
    if model == "k":
        return 0.0 if k is None else float(k * element_size)

    raise ValueError(f"Unknown memory model: {model}")


# ==========================================================
# 8. Compatibility check
# ==========================================================

def check_algorithm_compatibility(
    algorithm: Dict,
    n: int,
    data_type: str,
    k: Optional[int],
    requires_stability: bool,
    available_ram_gb: float,
) -> Tuple[List[str], float, float, float]:
    rejection_reasons = []

    if algorithm["category"] == "educational":
        rejection_reasons.append(
            "Educational algorithm only. It is not considered for practical recommendation."
        )

    if data_type not in algorithm["allowed_types"]:
        rejection_reasons.append(f"Data type '{data_type}' is not supported by {algorithm['name']}.")

    if requires_stability and not algorithm["stable"]:
        rejection_reasons.append("Stable sorting is required, but this algorithm is not stable.")

    if algorithm["name"] == "Counting Sort":
        if data_type != "integer":
            rejection_reasons.append("Counting Sort requires integer data.")
        if k is None:
            rejection_reasons.append("Counting Sort requires a known integer range k.")
        if k is not None and k > 10 * n:
            rejection_reasons.append(
                "Integer range k is too large compared with n. "
                "Counting Sort loses efficiency and memory advantage."
            )

    if algorithm["name"] == "Radix Sort" and data_type != "integer":
        rejection_reasons.append("Radix Sort requires integer data.")

    data_memory = estimate_data_memory_bytes(n, data_type)
    extra_memory = estimate_extra_memory_bytes(algorithm, n, k, data_type)
    total_memory = data_memory + extra_memory
    available_memory = gb_to_bytes(available_ram_gb)

    if total_memory > available_memory:
        rejection_reasons.append("Estimated memory requirement exceeds available RAM.")

    return rejection_reasons, data_memory, extra_memory, total_memory


# ==========================================================
# 9. Advisor engine
# ==========================================================

def evaluate_algorithms(
    n: int,
    data_type: str,
    data_order: str,
    k: Optional[int],
    requires_stability: bool,
    available_ram_gb: float,
    radix_base: int = DEFAULT_RADIX_BASE,
) -> Tuple[List[Dict], Optional[Dict]]:
    validate_inputs(n, data_type, data_order, k, available_ram_gb)

    results = []

    for algorithm in ALGORITHMS:
        rejection_reasons, data_memory, extra_memory, total_memory = check_algorithm_compatibility(
            algorithm=algorithm,
            n=n,
            data_type=data_type,
            k=k,
            requires_stability=requires_stability,
            available_ram_gb=available_ram_gb,
        )

        theoretical_cost = estimate_theoretical_cost(
            algorithm_name=algorithm["name"],
            n=n,
            k=k,
            data_order=data_order,
            radix_base=radix_base,
        )

        complexity_family = get_complexity_family(algorithm["name"], data_order)

        results.append({
            "name": algorithm["name"],
            "category": algorithm["category"],
            "compatible": len(rejection_reasons) == 0,
            "stable": algorithm["stable"],
            "complexity_family": complexity_family,
            "rejection_reasons": rejection_reasons,
            "theoretical_cost": theoretical_cost,
            "data_memory_mb": bytes_to_mb(data_memory),
            "extra_memory_mb": bytes_to_mb(extra_memory),
            "total_memory_mb": bytes_to_mb(total_memory),
            "notes": algorithm["notes"],
        })

    compatible_results = [result for result in results if result["compatible"]]
    compatible_results.sort(key=lambda item: item["theoretical_cost"])

    recommendation = compatible_results[0] if compatible_results else None
    return results, recommendation


# ==========================================================
# 10. Explanations and report
# ==========================================================

def get_decision_flow_lines(n: int, data_type: str, data_order: str, recommendation: Optional[Dict]) -> List[str]:
    lines = [
        "[Start]",
        "  ↓",
        f"[Read input scenario: n={n}, type={data_type}, order={data_order}]",
        "  ↓",
        "[Build candidate algorithm list]",
        "  ↓",
        "[Reject educational algorithms from practical recommendation]",
        "  ↓",
        "[Reject algorithms incompatible with data type]",
        "  ↓",
        "[Reject algorithms that violate stability requirement]",
        "  ↓",
        "[Reject algorithms exceeding estimated available RAM]",
        "  ↓",
        "[Estimate theoretical cost for remaining algorithms]",
        "  ↓",
        "[Rank compatible algorithms by theoretical cost]",
        "  ↓",
    ]
    lines.append("[No compatible algorithm found]" if recommendation is None else f"[Recommend: {recommendation['name']}]")
    return lines


def explain_recommendation(recommendation: Optional[Dict], results: List[Dict]) -> str:
    if recommendation is None:
        return "No compatible practical algorithm was found for this scenario. Relax one or more constraints and try again."

    compatible_not_chosen = [
        result for result in results
        if result["compatible"] and result["name"] != recommendation["name"]
    ]
    rejected = [result for result in results if not result["compatible"]]

    explanation = [
        f"{recommendation['name']} was recommended because it has the lowest theoretical cost among the compatible practical algorithms.",
        "",
        f"Estimated cost: {recommendation['theoretical_cost']:.2f}",
        f"Effective complexity family: {recommendation['complexity_family']}",
    ]

    if compatible_not_chosen:
        explanation.append("")
        explanation.append("Compatible alternatives were available, but their estimated costs were higher:")
        for result in sorted(compatible_not_chosen, key=lambda item: item["theoretical_cost"]):
            explanation.append(f"- {result['name']}: {result['theoretical_cost']:.2f} ({result['complexity_family']})")

    if rejected:
        explanation.append("")
        explanation.append("Some algorithms were rejected because they violated scenario constraints:")
        for result in rejected:
            reasons = "; ".join(result["rejection_reasons"])
            explanation.append(f"- {result['name']}: {reasons}")

    return "\n".join(explanation)


def build_results_table(results: List[Dict]) -> List[Dict]:
    return [
        {
            "Algorithm": result["name"],
            "Category": result["category"],
            "Status": "Compatible" if result["compatible"] else "Rejected",
            "Complexity": result["complexity_family"],
            "Stable": result["stable"],
            "Theoretical cost": result["theoretical_cost"],
            "Data memory (MB)": result["data_memory_mb"],
            "Extra memory (MB)": result["extra_memory_mb"],
            "Total memory (MB)": result["total_memory_mb"],
            "Notes": result["notes"],
            "Rejection reasons": "; ".join(result["rejection_reasons"]),
        }
        for result in results
    ]


def print_console_report(
    n: int,
    data_type: str,
    data_order: str,
    k: Optional[int],
    requires_stability: bool,
    available_ram_gb: float,
    results: List[Dict],
    recommendation: Optional[Dict],
    radix_base: int = DEFAULT_RADIX_BASE,
) -> None:
    print("\n" + "=" * 78)
    print("BIG-O SORTING ADVISOR")
    print("=" * 78)

    print("\nCore principles:")
    print("1. Best algorithm = lowest cost among compatible algorithms.")
    print("2. This tool does not sort the data; it explains which sorting strategy makes the most sense for the described scenario.")

    print("\nInput scenario:")
    print(f"- Number of elements n: {n}")
    print(f"- Data type: {data_type}")
    print(f"- Data order: {data_order}")
    print(f"- Integer range k: {k}")
    print(f"- Requires stability: {requires_stability}")
    print(f"- Available RAM: {available_ram_gb} GB")

    if data_type == "integer":
        print(f"- Estimated Radix Sort passes: {estimate_radix_passes(k, radix_base)}")
        print(f"- Radix base used in model: {radix_base}")

    print("\nDecision flow:")
    for line in get_decision_flow_lines(n, data_type, data_order, recommendation):
        print(line)

    print("\nAlgorithm evaluation:")
    sorted_results = sorted(results, key=lambda item: (not item["compatible"], item["theoretical_cost"]))
    for result in sorted_results:
        print("\n" + "-" * 78)
        print(f"Algorithm: {result['name']}")
        print(f"Category: {result['category']}")
        print(f"Effective complexity family: {result['complexity_family']}")
        print(f"Stable: {result['stable']}")
        print(f"Status: {'COMPATIBLE' if result['compatible'] else 'REJECTED'}")
        print(f"Theoretical cost at n={n}: {result['theoretical_cost']:.2f}")
        print(f"Data memory: {result['data_memory_mb']:.4f} MB")
        print(f"Extra memory: {result['extra_memory_mb']:.4f} MB")
        print(f"Total estimated memory: {result['total_memory_mb']:.4f} MB")
        print(f"Notes: {result['notes']}")
        if result["rejection_reasons"]:
            print("Rejection reasons:")
            for reason in result["rejection_reasons"]:
                print(f"- {reason}")

    print("\n" + "=" * 78)
    if recommendation is None:
        print("Final recommendation: no compatible practical algorithm found.")
    else:
        print("Final recommendation:")
        print(f"- Best algorithm: {recommendation['name']}")
        print("- Criterion: lowest theoretical cost among compatible practical algorithms.")
        print(f"- Estimated theoretical cost: {recommendation['theoretical_cost']:.2f}")
        print(f"- Effective complexity family: {recommendation['complexity_family']}")
    print("=" * 78)


# ==========================================================
# 11. Complexity curves and plots
# ==========================================================

def get_curve_values(x_values: np.ndarray, k: Optional[int], radix_base: int = DEFAULT_RADIX_BASE) -> Dict[str, Dict]:
    if k is None:
        k = 0
    radix_passes = estimate_radix_passes(k, radix_base)
    return {
        "O(n)": {"y": x_values, "label": "O(n)", "color": CURVE_COLORS["O(n)"]},
        "O(n log n)": {"y": x_values * np.log2(x_values), "label": "O(n log n)", "color": CURVE_COLORS["O(n log n)"]},
        "O(n²)": {"y": x_values**2, "label": "O(n²)", "color": CURVE_COLORS["O(n²)"]},
        "O(n + k)": {"y": x_values + k, "label": "O(n + k)", "color": CURVE_COLORS["O(n + k)"]},
        "O(d n)": {"y": radix_passes * x_values, "label": f"O(d n), d={radix_passes}", "color": CURVE_COLORS["O(d n)"]},
    }


def create_global_complexity_figure(
    n: int,
    k: Optional[int],
    results: List[Dict],
    recommendation: Optional[Dict],
    show_educational_algorithms: bool = DEFAULT_SHOW_EDUCATIONAL_ALGORITHMS,
    radix_base: int = DEFAULT_RADIX_BASE,
):
    x_max = max(10, int(n * 1.2))
    x_values = np.linspace(1, x_max, 500)
    curves = get_curve_values(x_values, k, radix_base)
    fig, ax = plt.subplots(figsize=(12, 7))

    for _, curve_data in curves.items():
        ax.plot(x_values, curve_data["y"], label=curve_data["label"], color=curve_data["color"])

    for result in results:
        if result["category"] == "educational" and not show_educational_algorithms:
            continue
        color = get_algorithm_color(result)
        marker = get_algorithm_marker(result["name"])
        y = result["theoretical_cost"]
        if result["compatible"]:
            ax.scatter(n, y, s=90, color=color, edgecolors="black", linewidths=1.2, marker=marker, label=f"{result['name']} point", zorder=5)
        else:
            ax.scatter(n, y, s=80, color=color, marker="x", linewidths=2, label=f"{result['name']} rejected", zorder=5)

    if recommendation is not None:
        ax.scatter(n, recommendation["theoretical_cost"], s=260, marker="o", linewidths=2.5, facecolors="none", edgecolors="black", label=f"Recommendation: {recommendation['name']}", zorder=6)

    ax.axvline(x=n, linestyle="--", linewidth=1, label=f"Input size n = {n}")
    ax.set_title("Global View - Theoretical Complexity Curves")
    ax.set_xlabel("Number of elements (n)")
    ax.set_ylabel("Estimated theoretical cost f(n)")
    ax.set_yscale("log")
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig


def get_auto_y_limits_for_relevant_points(
    results: List[Dict],
    recommendation: Optional[Dict],
    max_cost_ratio: float = DEFAULT_MAX_COST_RATIO_FOR_ZOOM,
    margin_ratio: float = 0.15,
) -> Tuple[Optional[float], Optional[float], List[Dict]]:
    if recommendation is None:
        return None, None, []

    reference_cost = recommendation["theoretical_cost"]
    max_allowed_cost = reference_cost * max_cost_ratio
    relevant_results = []
    omitted_results = []

    for result in results:
        if result["category"] == "educational":
            omitted_results.append(result)
            continue
        cost = result["theoretical_cost"]
        if cost <= max_allowed_cost:
            relevant_results.append(result)
        else:
            omitted_results.append(result)

    y_values = [result["theoretical_cost"] for result in relevant_results]
    if not y_values:
        return None, None, omitted_results

    y_min = min(y_values)
    y_max = max(y_values)
    padding = max(1.0, y_min * margin_ratio) if y_min == y_max else (y_max - y_min) * margin_ratio
    return max(0.0, y_min - padding), y_max + padding, omitted_results


def get_visible_results_for_zoom(results: List[Dict], y_lower: Optional[float], y_upper: Optional[float]) -> List[Dict]:
    visible_results = []
    for result in results:
        if result["category"] == "educational":
            continue
        y = result["theoretical_cost"]
        if y_lower is not None and y_upper is not None and (y < y_lower or y > y_upper):
            continue
        visible_results.append(result)
    return visible_results


def create_zoom_complexity_figure(
    n: int,
    k: Optional[int],
    results: List[Dict],
    recommendation: Optional[Dict],
    delta: int = DEFAULT_ZOOM_DELTA,
    max_cost_ratio: float = DEFAULT_MAX_COST_RATIO_FOR_ZOOM,
    radix_base: int = DEFAULT_RADIX_BASE,
):
    x_min = max(1, n - delta)
    x_max = n + delta
    x_values = np.linspace(x_min, x_max, 500)
    curves = get_curve_values(x_values, k, radix_base)

    y_lower, y_upper, omitted_results = get_auto_y_limits_for_relevant_points(results, recommendation, max_cost_ratio, margin_ratio=0.15)
    visible_results = get_visible_results_for_zoom(results, y_lower, y_upper)
    families_to_plot = sorted({result["complexity_family"] for result in visible_results})

    fig, ax = plt.subplots(figsize=(12, 7))

    for family in families_to_plot:
        curve_data = curves[family]
        ax.plot(x_values, curve_data["y"], label=curve_data["label"], color=curve_data["color"])

    for result in visible_results:
        color = get_algorithm_color(result)
        marker = get_algorithm_marker(result["name"])
        if result["compatible"]:
            ax.scatter(n, result["theoretical_cost"], s=110, color=color, edgecolors="black", linewidths=1.2, marker=marker, label=f"{result['name']} point", zorder=5)
        else:
            ax.scatter(n, result["theoretical_cost"], s=90, color=color, marker="x", linewidths=2, label=f"{result['name']} rejected", zorder=5)

    if recommendation is not None:
        ax.scatter(n, recommendation["theoretical_cost"], s=290, marker="o", linewidths=2.5, facecolors="none", edgecolors="black", label=f"Recommendation: {recommendation['name']}", zorder=6)

    ax.axvline(x=n, linestyle="--", linewidth=1, label=f"Input size n = {n}")
    ax.set_title(f"Auto Zoom View - Relevant Complexity Region Around n = {n}")
    ax.set_xlabel("Number of elements (n)")
    ax.set_ylabel("Estimated theoretical cost f(n)")
    ax.set_xlim(x_min, x_max)
    if y_lower is not None and y_upper is not None:
        ax.set_ylim(y_lower, y_upper)
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig, omitted_results


# ==========================================================
# 12. Direct local run for Spyder
# ==========================================================

def run_demo() -> None:
    results, recommendation = evaluate_algorithms(
        n=DEFAULT_N,
        data_type=DEFAULT_DATA_TYPE,
        data_order=DEFAULT_DATA_ORDER,
        k=DEFAULT_INTEGER_RANGE_K,
        requires_stability=DEFAULT_REQUIRES_STABILITY,
        available_ram_gb=DEFAULT_AVAILABLE_RAM_GB,
        radix_base=DEFAULT_RADIX_BASE,
    )

    print_console_report(
        n=DEFAULT_N,
        data_type=DEFAULT_DATA_TYPE,
        data_order=DEFAULT_DATA_ORDER,
        k=DEFAULT_INTEGER_RANGE_K,
        requires_stability=DEFAULT_REQUIRES_STABILITY,
        available_ram_gb=DEFAULT_AVAILABLE_RAM_GB,
        results=results,
        recommendation=recommendation,
        radix_base=DEFAULT_RADIX_BASE,
    )

    create_global_complexity_figure(DEFAULT_N, DEFAULT_INTEGER_RANGE_K, results, recommendation)
    _, omitted_results = create_zoom_complexity_figure(DEFAULT_N, DEFAULT_INTEGER_RANGE_K, results, recommendation)

    if omitted_results:
        print("\nAlgorithms omitted from zoom view due to scale:")
        for result in omitted_results:
            print(f"- {result['name']}: cost = {result['theoretical_cost']:.2f}, family = {result['complexity_family']}")

    plt.show()


if __name__ == "__main__":
    run_demo()
