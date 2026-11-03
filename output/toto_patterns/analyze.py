"""Create descriptive charts; requires numpy, scipy, and matplotlib."""

import csv
import json
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform
from scipy.stats import binom, hypergeom


def main():
    folder = Path(__file__).resolve().parent
    source = folder.parent / "toto_results.csv"
    with source.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.reader(stream))
    records = []
    for row in rows:
        if len(row) != 8:
            raise ValueError(f"Expected date plus seven numbers: {row}")
        draw_date = date.fromisoformat(row[0])
        values = [int(value) for value in row[1:]]
        if len(set(values)) != 7 or not all(1 <= value <= 49 for value in values):
            raise ValueError(f"Invalid draw: {row}")
        records.append((draw_date, values))
    records.sort()
    dates = [record[0] for record in records]
    if len(set(dates)) != len(dates):
        raise ValueError("Duplicate draw dates")
    draws = np.array([record[1][:6] for record in records])
    bonuses = np.array([record[1][6] for record in records])
    count = len(draws)
    numbers = np.arange(1, 50)
    presence = np.zeros((count, 49), dtype=np.int16)
    presence[np.arange(count)[:, None], draws - 1] = 1
    frequencies = presence.sum(axis=0)
    bonus_frequencies = np.bincount(bonuses, minlength=50)[1:]
    pair_counts = presence.T @ presence
    upper = np.triu_indices(49, 1)
    probability = 6 / 49
    expected = count * probability
    pair_probability = 6 * 5 / (49 * 48)
    expected_pair = count * pair_probability
    score = np.sum((frequencies - expected) ** 2 / expected)
    maximum_pair = int(pair_counts[upper].max())
    overlaps = (presence[1:] * presence[:-1]).sum(axis=1)
    adjacent_per_draw = (np.diff(np.sort(draws, axis=1), axis=1) == 1).sum(axis=1)
    sums = draws.sum(axis=1)
    odd_counts = (draws % 2).sum(axis=1)
    rng = np.random.default_rng(20261103)
    simulations = 5000
    null_scores = np.empty(simulations)
    null_pair_maxima = np.empty(simulations)
    null_adjacent = np.empty(simulations)
    null_overlap = np.empty(simulations)
    null_sums = []
    for trial in range(simulations):
        selected = np.argpartition(rng.random((count, 49)), 6, axis=1)[:, :6]
        simulated = np.zeros_like(presence)
        simulated[np.arange(count)[:, None], selected] = 1
        simulated_counts = simulated.sum(axis=0)
        null_scores[trial] = np.sum((simulated_counts - expected) ** 2 / expected)
        null_pair_maxima[trial] = (simulated.T @ simulated)[upper].max()
        null_adjacent[trial] = (np.diff(np.sort(selected, axis=1), axis=1) == 1).sum()
        null_overlap[trial] = (simulated[1:] * simulated[:-1]).sum()
        if trial < 100:
            null_sums.extend((selected + 1).sum(axis=1).tolist())
    frequency_p = (1 + np.count_nonzero(null_scores >= score)) / (simulations + 1)
    pair_p = (1 + np.count_nonzero(null_pair_maxima >= maximum_pair)) / (simulations + 1)

    def central_p(samples, observed):
        center = samples.mean()
        return (1 + np.count_nonzero(abs(samples - center) >= abs(observed - center))) / (simulations + 1)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "#fafafa", "axes.facecolor": "#fafafa"})
    figure, axes = plt.subplots(2, 1, figsize=(15, 9), layout="constrained")
    for axis, counts, chance, title, color in [
        (axes[0], frequencies, probability, "Six main numbers", "#16817a"),
        (axes[1], bonus_frequencies, 1 / 49, "Additional number (separate)", "#b55b45"),
    ]:
        low, high = binom.ppf([0.025, 0.975], count, chance)
        axis.axhspan(low, high, color="#d9dde1", alpha=0.7, label="95% range for ONE number under random draws")
        axis.bar(numbers, counts, color=color, width=0.8, zorder=2)
        axis.axhline(count * chance, color="#252525", linestyle="--", label=f"Expected: {count * chance:.1f}")
        axis.set(title=title, ylabel="Draws containing number", xticks=numbers, xlim=(0, 50))
        axis.legend(loc="upper right", fontsize=8)
    figure.suptitle(f"Number frequencies | {count} draws | {dates[0]} to {dates[-1]}", fontsize=17)
    figure.savefig(folder / "frequency.png", dpi=160)
    plt.close(figure)

    months = sorted({draw_date.strftime("%Y-%m") for draw_date in dates})
    monthly = np.zeros((49, len(months)))
    month_sizes = []
    for column, month in enumerate(months):
        selected = np.array([draw_date.strftime("%Y-%m") == month for draw_date in dates])
        month_sizes.append(int(selected.sum()))
        monthly[:, column] = presence[selected].mean(axis=0) * 100
    figure, axis = plt.subplots(figsize=(15, 12), layout="constrained")
    image = axis.imshow(monthly, aspect="auto", origin="lower", cmap="YlGnBu", vmin=0)
    axis.set(yticks=np.arange(49), yticklabels=numbers, ylabel="Main number",
             xticks=np.arange(len(months)),
             xticklabels=[f"{month} ({size})" for month, size in zip(months, month_sizes)],
             title="Main-number appearances by month | label includes number of draws")
    axis.tick_params(axis="x", rotation=70)
    figure.colorbar(image, ax=axis, label="Percentage of that month's draws")
    figure.savefig(folder / "timeline.png", dpi=160)
    plt.close(figure)

    correlation = np.nan_to_num(np.corrcoef(presence, rowvar=False))
    distance = np.clip(1 - correlation, 0, 2)
    np.fill_diagonal(distance, 0)
    order = leaves_list(linkage(squareform(distance, checks=False), method="average"))
    residuals = (pair_counts - expected_pair) / np.sqrt(count * pair_probability * (1 - pair_probability))
    np.fill_diagonal(residuals, np.nan)
    figure, axis = plt.subplots(figsize=(14, 12), layout="constrained")
    limit = float(np.nanmax(abs(residuals)))
    image = axis.imshow(residuals[np.ix_(order, order)], cmap="RdBu_r", vmin=-limit, vmax=limit)
    axis.set(xticks=np.arange(49), xticklabels=numbers[order],
             yticks=np.arange(49), yticklabels=numbers[order], xlabel="Main number", ylabel="Main number",
             title="Pair co-occurrence | hierarchical ordering of appearance correlations\n"
                   "Red: more shared draws than expected; blue: fewer. Clusters are exploratory.")
    axis.tick_params(labelsize=8)
    figure.colorbar(image, ax=axis, label="Deviation from random-pair expectation (standard deviations)")
    figure.savefig(folder / "clusters.png", dpi=160)
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(16, 5), layout="constrained")
    bins = np.arange(20, 286, 10)
    axes[0].hist(null_sums, bins=bins, density=True, color="#d9dde1", label="Random reference")
    axes[0].hist(sums, bins=bins, density=True, histtype="step", linewidth=2, color="#16817a", label="Observed")
    axes[0].set(title="Sum of six main numbers", xlabel="Sum", ylabel="Probability density")
    axes[0].legend()
    for axis, observed, theoretical, title in [
        (axes[1], odd_counts, hypergeom.pmf(np.arange(7), 49, 25, 6), "Odd numbers per draw"),
        (axes[2], overlaps, hypergeom.pmf(np.arange(7), 49, 6, 6), "Numbers repeated from prior draw"),
    ]:
        positions = np.arange(7)
        axis.bar(positions - 0.18, np.bincount(observed, minlength=7) / len(observed), width=0.36, color="#16817a", label="Observed")
        axis.bar(positions + 0.18, theoretical, width=0.36, color="#b9bfc4", label="Random expectation")
        axis.set(title=title, xlabel="Count", ylabel="Fraction of draws", xticks=positions)
        axis.legend(fontsize=8)
    figure.savefig(folder / "draw_structure.png", dpi=160)
    plt.close(figure)

    ranked = sorted(zip(numbers.tolist(), frequencies.tolist()), key=lambda item: (-item[1], item[0]))
    pairs = sorted([(int(first + 1), int(second + 1), int(pair_counts[first, second]))
                    for first, second in zip(*upper)], key=lambda item: (-item[2], item[0], item[1]))
    recent = presence[-50:].sum(axis=0)
    recent_ranked = sorted(zip(numbers.tolist(), recent.tolist()), key=lambda item: (-item[1], item[0]))
    frequency_table = "\n".join(f"| {number} | {hits} | {hits / count:.1%} |" for number, hits in ranked)
    pair_table = "\n".join(f"| {first}, {second} | {hits} |" for first, second, hits in pairs[:15])
    statistics = {
        "draws": count, "first_date": str(dates[0]), "last_date": str(dates[-1]),
        "expected_main_frequency": expected, "main_frequency_ranking": ranked,
        "expected_pair_frequency": expected_pair, "top_pairs": pairs[:15],
        "global_frequency_monte_carlo_p": frequency_p,
        "maximum_pair_familywise_monte_carlo_p": pair_p,
        "consecutive_pair_count": int(adjacent_per_draw.sum()),
        "draws_with_consecutive_numbers": int((adjacent_per_draw > 0).sum()),
        "consecutive_pairs_monte_carlo_p": central_p(null_adjacent, adjacent_per_draw.sum()),
        "mean_overlap_between_draws": float(overlaps.mean()),
        "overlap_monte_carlo_p": central_p(null_overlap, overlaps.sum()),
        "mean_sum": float(sums.mean()), "expected_sum": 150,
        "recent_50_frequency_ranking": recent_ranked,
        "simulations": simulations,
    }
    (folder / "statistics.json").write_text(json.dumps(statistics, indent=2), encoding="utf-8")
    conclusion = ("The overall main-number frequency variation is not unusual under the random model."
                  if frequency_p >= 0.05 else
                  "The overall frequency variation is unusual under the random model; this does not establish predictability.")
    report = f"""# TOTO Draw Patterns

{count} unique draw dates, {dates[0]} through {dates[-1]}. All rows contain six distinct main numbers and a distinct additional number, each in 1-49. Main numbers and additional numbers are analyzed separately. The input CSV is unchanged.

## Findings

- Expected main-number appearances per number: **{expected:.2f}** ({probability:.2%} of draws).
- Most frequent main numbers: **{', '.join(f'{number} ({hits})' for number, hits in ranked[:8])}**.
- Least frequent main numbers: **{', '.join(f'{number} ({hits})' for number, hits in sorted(ranked, key=lambda item: (item[1], item[0]))[:8])}**.
- Overall frequency test, calibrated against {simulations:,} simulated independent six-from-49 histories: **p = {frequency_p:.4f}**. {conclusion}
- Most frequent pair: **{pairs[0][0]}, {pairs[0][1]}**, together in **{pairs[0][2]}** draws; expectation for a preselected pair is **{expected_pair:.2f}**. Comparing the maximum across all 1,176 pairs gives **p = {pair_p:.4f}**. This adjustment matters because the pair was chosen after inspecting the data.
- **{int((adjacent_per_draw > 0).sum())} / {count}** draws contain consecutive main numbers. Total adjacent pairs: **{int(adjacent_per_draw.sum())}**, random expectation **{count * 30 / 49:.2f}**; two-sided simulation **p = {statistics['consecutive_pairs_monte_carlo_p']:.4f}**.
- Successive draws share **{overlaps.mean():.3f}** main numbers on average; random expectation **{36 / 49:.3f}**; two-sided simulation **p = {statistics['overlap_monte_carlo_p']:.4f}**.
- Mean main-number sum: **{sums.mean():.2f}**; random expectation **150**.
- In the latest 50 draws, the leading numbers are **{', '.join(f'{number} ({hits})' for number, hits in recent_ranked[:8])}**. This window is descriptive, not a forecast.

## Charts

![Main and additional number frequencies](frequency.png)

The dashed line is the random expectation. Shading is a 95% range for one preselected number, not a simultaneous limit across all 49; a few bars outside it are expected by chance.

![Monthly main-number appearances](timeline.png)

Each column is normalized by its actual draw count, shown in parentheses; partial months have less evidence. Read left to right chronologically.

![Clustered pair co-occurrence](clusters.png)

Hierarchical average-linkage clustering groups numbers with similar binary draw histories (distance = 1 minus Pearson correlation). Cell color compares pair counts with the random expectation. Any dataset, including random draws, produces apparent clusters. Cell colors are not multiple-comparison-adjusted significance tests; the maximum-pair test above handles the search for the strongest pair.

![Draw structures compared with randomness](draw_structure.png)

Middle sums, balanced odd/even counts, and occasional repeats or consecutive numbers arise naturally from random sampling. The sum reference is simulated; odd-count and repeat distributions are exact hypergeometric probabilities.

## Limits

Assumes independent, uniformly random six-from-49 draws throughout this period and accurate source data. These are exploratory checks, not a comprehensive randomness certification. Individual p-values across different checks are not jointly adjusted; the maximum-pair test alone accounts for all pairs. Simulation p-values have Monte Carlo uncertainty. No detected pattern establishes a future advantage; under the model, every number still has a 6/49 main-number chance each draw.

## Main-Number Ranking

| Number | Draws | Draw percentage |
| --- | --- | --- |
{frequency_table}

## Top Co-Occurring Pairs

| Pair | Shared draws |
| --- | --- |
{pair_table}

## Reproduce

Run `python output/toto_patterns/analyze.py` with numpy, matplotlib, and scipy installed. Uses seed 20261103 and {simulations:,} simulations. Raw summary: [statistics.json](statistics.json).
"""
    (folder / "report.md").write_text(report, encoding="utf-8")
    assert frequencies.sum() == count * 6
    assert bonus_frequencies.sum() == count
    assert pair_counts[upper].sum() == count * 15
    assert np.all(np.diag(pair_counts) == frequencies)
    assert sum(month_sizes) == count
    print(json.dumps(statistics, indent=2))
    print(f"Charts and report written to {folder}; all accounting checks passed.")


if __name__ == "__main__":
    main()