"""Deterministic, descriptive six-main-plus-bonus draw reports (not forecasts)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform
from scipy.stats import binom, hypergeom

from .analyzer import resolve_date_range
from .models import DrawRecord


SIMULATIONS = 5000
SEED = 20261103
CHARTS = ("frequency.png", "timeline.png", "clusters.png", "draw_structure.png")


def _save(figure, folder: Path, filename: str) -> None:
    try:
        figure.savefig(folder / filename, dpi=120)
    finally:
        plt.close(figure)


def _unavailable_charts(folder: Path, reason: str) -> None:
    for filename in CHARTS:
        figure, axis = plt.subplots(figsize=(10, 4), layout="constrained")
        axis.set_axis_off()
        axis.text(0.5, 0.5, reason, ha="center", va="center", wrap=True)
        _save(figure, folder, filename)


def _central_p(samples, observed) -> float:
    center = samples.mean()
    return float((1 + np.count_nonzero(abs(samples - center) >= abs(observed - center)))
                 / (len(samples) + 1))


def _calculate(records, min_value: int, max_value: int, simulations: int):
    numbers = np.arange(min_value, max_value + 1)
    size = len(numbers)
    count = len(records)
    draws = np.array([record.numbers[:6] for record in records], dtype=np.int64)
    bonuses = np.array([record.numbers[6] for record in records], dtype=np.int64)
    presence = np.zeros((count, size), dtype=np.int64)
    presence[np.arange(count)[:, None], draws - min_value] = 1
    frequencies = presence.sum(axis=0)
    bonus_frequencies = np.bincount(bonuses - min_value, minlength=size)
    pair_counts = presence.T @ presence
    upper = np.triu_indices(size, 1)
    probability = 6 / size
    expected = count * probability
    pair_probability = 30 / (size * (size - 1))
    expected_pair = count * pair_probability
    score = np.sum((frequencies - expected) ** 2 / expected)
    maximum_pair = int(pair_counts[upper].max())
    overlaps = (presence[1:] * presence[:-1]).sum(axis=1)
    adjacent = (np.diff(np.sort(draws, axis=1), axis=1) == 1).sum(axis=1)
    sums = draws.sum(axis=1)
    odd_counts = (draws % 2).sum(axis=1)
    rng = np.random.default_rng(SEED)
    null_scores = np.empty(simulations)
    null_pair_maxima = np.empty(simulations)
    null_adjacent = np.empty(simulations)
    null_overlap = np.empty(simulations)
    null_sums = []
    for trial in range(simulations):
        selected = np.argpartition(rng.random((count, size)), 6, axis=1)[:, :6]
        simulated = np.zeros_like(presence)
        simulated[np.arange(count)[:, None], selected] = 1
        simulated_counts = simulated.sum(axis=0)
        null_scores[trial] = np.sum((simulated_counts - expected) ** 2 / expected)
        null_pair_maxima[trial] = (simulated.T @ simulated)[upper].max()
        null_adjacent[trial] = (np.diff(np.sort(selected, axis=1), axis=1) == 1).sum()
        null_overlap[trial] = (simulated[1:] * simulated[:-1]).sum()
        if trial < 100:
            null_sums.extend((selected + min_value).sum(axis=1).tolist())

    ranked = sorted(zip(numbers.tolist(), frequencies.tolist()), key=lambda item: (-item[1], item[0]))
    pairs = sorted(
        [(int(numbers[first]), int(numbers[second]), int(pair_counts[first, second]))
         for first, second in zip(*upper)],
        key=lambda item: (-item[2], item[0], item[1]),
    )
    recent = presence[-50:].sum(axis=0)
    statistics = {
        "draws": count,
        "first_date": str(records[0].draw_date),
        "last_date": str(records[-1].draw_date),
        "expected_main_frequency": expected,
        "main_frequency_ranking": ranked,
        "bonus_frequency_ranking": sorted(zip(numbers.tolist(), bonus_frequencies.tolist()),
                                          key=lambda item: (-item[1], item[0])),
        "expected_pair_frequency": expected_pair,
        "top_pairs": pairs[:15],
        "global_frequency_monte_carlo_p": float((1 + np.count_nonzero(null_scores >= score)) / (simulations + 1)),
        "maximum_pair_familywise_monte_carlo_p": float((1 + np.count_nonzero(null_pair_maxima >= maximum_pair)) / (simulations + 1)),
        "consecutive_pair_count": int(adjacent.sum()),
        "draws_with_consecutive_numbers": int((adjacent > 0).sum()),
        "consecutive_pairs_monte_carlo_p": _central_p(null_adjacent, adjacent.sum()),
        "mean_overlap_between_draws": float(overlaps.mean()) if count > 1 else None,
        "overlap_monte_carlo_p": _central_p(null_overlap, overlaps.sum()) if count > 1 else None,
        "mean_sum": float(sums.mean()),
        "expected_sum": 3 * (min_value + max_value),
        "recent_50_frequency_ranking": sorted(zip(numbers.tolist(), recent.tolist()),
                                              key=lambda item: (-item[1], item[0])),
        "simulations": simulations,
        "seed": SEED,
    }
    data = (numbers, presence, frequencies, bonus_frequencies, pair_counts,
            sums, odd_counts, overlaps, null_sums)
    return statistics, data


def _render_charts(folder: Path, records, data) -> None:
    numbers, presence, frequencies, bonuses, pairs, sums, odd_counts, overlaps, null_sums = data
    count, size = presence.shape
    figure, axes = plt.subplots(2, 1, figsize=(15, 9), layout="constrained")
    for axis, counts, chance, title, color in [
        (axes[0], frequencies, 6 / size, "Six main numbers", "#16817a"),
        (axes[1], bonuses, 1 / size, "Additional number (separate)", "#b55b45"),
    ]:
        low, high = binom.ppf([0.025, 0.975], count, chance)
        axis.axhspan(low, high, color="#d9dde1", alpha=0.7, label="95% range for ONE random number")
        axis.bar(numbers, counts, color=color, zorder=2)
        axis.axhline(count * chance, color="#252525", linestyle="--", label="Random expectation")
        axis.set(title=title, ylabel="Draws containing number", xticks=numbers,
                 xlim=(numbers[0] - 1, numbers[-1] + 1))
        axis.legend(fontsize=8)
    figure.suptitle(f"Number frequencies | {count} draws | {records[0].draw_date} to {records[-1].draw_date}")
    _save(figure, folder, "frequency.png")

    months = sorted({record.draw_date.strftime("%Y-%m") for record in records})
    monthly = np.zeros((size, len(months)))
    labels = []
    for column, month in enumerate(months):
        selected = np.array([record.draw_date.strftime("%Y-%m") == month for record in records])
        labels.append(f"{month} ({int(selected.sum())})")
        monthly[:, column] = presence[selected].mean(axis=0) * 100
    figure, axis = plt.subplots(figsize=(15, 12), layout="constrained")
    image = axis.imshow(monthly, aspect="auto", origin="lower", cmap="YlGnBu", vmin=0)
    axis.set(yticks=np.arange(size), yticklabels=numbers, ylabel="Main number",
             xticks=np.arange(len(months)), xticklabels=labels,
             title="Monthly main-number appearances | draw counts in parentheses")
    axis.tick_params(axis="x", rotation=70)
    figure.colorbar(image, ax=axis, label="Percentage of month's draws")
    _save(figure, folder, "timeline.png")

    centered = presence - presence.mean(axis=0)
    norms = np.sqrt((centered * centered).sum(axis=0))
    denominator = norms[:, None] * norms[None, :]
    correlation = np.divide(centered.T @ centered, denominator,
                            out=np.zeros((size, size)), where=denominator > 0)
    distance = np.clip(1 - correlation, 0, 2)
    np.fill_diagonal(distance, 0)
    order = leaves_list(linkage(squareform(distance, checks=False), method="average"))
    pair_probability = 30 / (size * (size - 1))
    residuals = (pairs - count * pair_probability) / np.sqrt(count * pair_probability * (1 - pair_probability))
    np.fill_diagonal(residuals, np.nan)
    limit = max(float(np.nanmax(abs(residuals))), 1e-12)
    figure, axis = plt.subplots(figsize=(14, 12), layout="constrained")
    image = axis.imshow(residuals[np.ix_(order, order)], cmap="RdBu_r", vmin=-limit, vmax=limit)
    axis.set(xticks=np.arange(size), xticklabels=numbers[order],
             yticks=np.arange(size), yticklabels=numbers[order],
             xlabel="Main number", ylabel="Main number",
             title="Pair co-occurrence | exploratory hierarchical ordering\n"
                   "Red: more shared draws than expected; blue: fewer")
    axis.tick_params(labelsize=8)
    figure.colorbar(image, ax=axis, label="Deviation from random-pair expectation (standard deviations)")
    _save(figure, folder, "clusters.png")

    figure, axes = plt.subplots(1, 3, figsize=(16, 5), layout="constrained")
    lowest_sum = sum(numbers[:6])
    highest_sum = sum(numbers[-6:])
    bins = np.linspace(lowest_sum - 0.5, highest_sum + 0.5, 28)
    axes[0].hist(null_sums, bins=bins, density=True, color="#d9dde1", label="Random reference")
    axes[0].hist(sums, bins=bins, density=True, histtype="step", linewidth=2,
                 color="#16817a", label="Observed")
    axes[0].set(title="Sum of six main numbers", xlabel="Sum", ylabel="Probability density")
    axes[0].legend()
    positions = np.arange(7)
    for axis, observed, theoretical, title in [
        (axes[1], odd_counts, hypergeom.pmf(positions, size, int((numbers % 2).sum()), 6), "Odd numbers per draw"),
        (axes[2], overlaps, hypergeom.pmf(positions, size, 6, 6), "Numbers repeated from prior draw"),
    ]:
        if len(observed):
            axis.bar(positions - 0.18, np.bincount(observed, minlength=7) / len(observed),
                     width=0.36, color="#16817a", label="Observed")
        else:
            axis.text(0.5, 0.9, "At least two draws required", transform=axis.transAxes, ha="center")
        axis.bar(positions + 0.18, theoretical, width=0.36, color="#b9bfc4", label="Random expectation")
        axis.set(title=title, xlabel="Count", ylabel="Fraction of draws", xticks=positions)
        axis.legend(fontsize=8)
    _save(figure, folder, "draw_structure.png")


def write_report(
    records: Sequence[DrawRecord],
    folder: str | Path,
    min_value: int,
    max_value: int,
    window: str | None = None,
    custom_start: date | None = None,
    custom_end: date | None = None,
    *,
    simulations: int = SIMULATIONS,
) -> dict:
    """Refresh six artifacts without mutating records; duplicate values are report-only exclusions."""
    if min_value > max_value or simulations < 1:
        raise ValueError("Report requires ordered range bounds and positive simulations")
    start, end = resolve_date_range(records, window, custom_start, custom_end)
    filtered = [record for record in records if start <= record.draw_date <= end]
    usable = sorted(
        [record for record in filtered if len(record.numbers) == 7
         and len(set(record.numbers)) == 7
         and all(min_value <= number <= max_value for number in record.numbers)],
        key=lambda record: (record.draw_date, record.numbers),
    )
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    statistics = {
        "status": "ok" if usable else "unavailable",
        "draws": len(usable),
        "filtered_rows": len(filtered),
        "excluded_report_rows": len(filtered) - len(usable),
        "min_value": min_value,
        "max_value": max_value,
        "window_start": str(start),
        "window_end": str(end),
    }
    reason = "No valid report draws: seven distinct in-range numbers are required."
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "#fafafa", "axes.facecolor": "#fafafa"}):
        if usable:
            calculated, data = _calculate(usable, min_value, max_value, simulations)
            statistics.update(calculated)
            _render_charts(folder, usable, data)
        else:
            statistics["reason"] = reason
            _unavailable_charts(folder, reason)

    text = f"""# TOTO Draw Patterns

Window: {start} through {end} (inclusive). Configured range: {min_value}-{max_value}.
Report draws: {len(usable)}; excluded report rows: {statistics['excluded_report_rows']}.
The first six numbers are main numbers; the seventh is the additional number, analyzed separately.
Reports require seven distinct in-range values. Ranking still counts all seven cells, including
duplicates accepted by the parser. Duplicate dates remain separate rows; same-date rows are
ordered by their numbers for reproducibility. Successive-row overlap is not necessarily a
comparison of distinct draw dates. Input CSV, ranking and suggestions are unchanged by reporting.

"""
    if usable:
        text += f"""## Findings

- Expected main-number appearances per number: {statistics['expected_main_frequency']:.2f}.
- Global frequency Monte Carlo p: {statistics['global_frequency_monte_carlo_p']:.4f}.
- Maximum-pair familywise Monte Carlo p: {statistics['maximum_pair_familywise_monte_carlo_p']:.4f}.
- Adjacent consecutive pairs: {statistics['consecutive_pair_count']}; two-sided Monte Carlo p: {statistics['consecutive_pairs_monte_carlo_p']:.4f}.
- Mean main-number sum: {statistics['mean_sum']:.2f}; random expectation: {statistics['expected_sum']}.
- Mean successive-row overlap: {statistics['mean_overlap_between_draws']}; overlap Monte Carlo p: {statistics['overlap_monte_carlo_p']}.
  Overlap is unavailable (null) with fewer than two draws.

## Main-Number Ranking

| Number | Draws | Draw percentage |
| --- | --- | --- |
"""
        text += "\n".join(f"| {number} | {hits} | {hits / len(usable):.1%} |"
                          for number, hits in statistics["main_frequency_ranking"])
        text += "\n\n## Top Co-Occurring Pairs\n\n| Pair | Shared draws |\n| --- | --- |\n"
        text += "\n".join(f"| {first}, {second} | {hits} |"
                          for first, second, hits in statistics["top_pairs"])
    else:
        text += f"## Unavailable\n\n{reason}\n"
    text += f"""

## Charts

![Main and additional number frequencies](frequency.png)

Shading is a 95% range for one preselected number, not a simultaneous limit for all numbers.

![Monthly main-number appearances](timeline.png)

Each month is normalized by its actual draw count, shown in parentheses.

![Clustered pair co-occurrence](clusters.png)

Average-linkage ordering uses 1 minus Pearson correlation of binary main-number histories.
Constant columns have undefined correlations and use neutral zero correlation for ordering.
Colors show pair deviations, not adjusted significance tests. Clusters are exploratory.

![Draw structures compared with randomness](draw_structure.png)

Sum references are simulated; odd-count and repeat distributions are exact hypergeometric probabilities.

## Limits and Reproduction

Assumes independent, uniform six-from-{max_value - min_value + 1} main-number draws.
These are descriptive checks, not predictions or a comprehensive randomness certification.
No pattern establishes a future advantage. Only the maximum-pair test adjusts for the search
across pairs; tests across different checks are not jointly adjusted. Simulation p-values have
Monte Carlo uncertainty. Small histories provide little evidence.

Automatically refreshed by `python -m src.lotto_analyzer.cli` (also `python -m lotto_analyzer.cli`
after installation). Seed {SEED}; {simulations:,} simulations when data is available.
Full statistics, bonus counts and latest-50 rankings: [statistics.json](statistics.json).
"""
    (folder / "statistics.json").write_text(json.dumps(statistics, indent=2, allow_nan=False), encoding="utf-8")
    (folder / "report.md").write_text(text, encoding="utf-8")
    return statistics