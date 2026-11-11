# TOTO Draw Patterns

Window: 2025-11-09 through 2026-11-09 (inclusive). Configured range: 1-49.
Report draws: 105; excluded report rows: 0.
The first six numbers are main numbers; the seventh is the additional number, analyzed separately.
Reports require seven distinct in-range values. Ranking still counts all seven cells, including
duplicates accepted by the parser. Duplicate dates remain separate rows; same-date rows are
ordered by their numbers for reproducibility. Successive-row overlap is not necessarily a
comparison of distinct draw dates. Input CSV, ranking and suggestions are unchanged by reporting.

## Findings

- Expected main-number appearances per number: 12.86.
- Global frequency Monte Carlo p: 0.8194.
- Maximum-pair familywise Monte Carlo p: 0.9348.
- Adjacent consecutive pairs: 56; two-sided Monte Carlo p: 0.2651.
- Mean main-number sum: 150.21; random expectation: 150.
- Mean successive-row overlap: 0.7307692307692307; overlap Monte Carlo p: 0.9484103179364127.
  Overlap is unavailable (null) with fewer than two draws.

## Main-Number Ranking

| Number | Draws | Draw percentage |
| --- | --- | --- |
| 11 | 20 | 19.0% |
| 22 | 18 | 17.1% |
| 39 | 18 | 17.1% |
| 6 | 17 | 16.2% |
| 8 | 17 | 16.2% |
| 30 | 17 | 16.2% |
| 33 | 17 | 16.2% |
| 35 | 17 | 16.2% |
| 23 | 16 | 15.2% |
| 43 | 16 | 15.2% |
| 46 | 16 | 15.2% |
| 48 | 16 | 15.2% |
| 4 | 15 | 14.3% |
| 27 | 15 | 14.3% |
| 7 | 14 | 13.3% |
| 25 | 14 | 13.3% |
| 3 | 13 | 12.4% |
| 5 | 13 | 12.4% |
| 9 | 13 | 12.4% |
| 13 | 13 | 12.4% |
| 16 | 13 | 12.4% |
| 18 | 13 | 12.4% |
| 32 | 13 | 12.4% |
| 34 | 13 | 12.4% |
| 36 | 13 | 12.4% |
| 37 | 13 | 12.4% |
| 49 | 13 | 12.4% |
| 15 | 12 | 11.4% |
| 24 | 12 | 11.4% |
| 26 | 12 | 11.4% |
| 31 | 12 | 11.4% |
| 40 | 12 | 11.4% |
| 12 | 11 | 10.5% |
| 19 | 11 | 10.5% |
| 28 | 11 | 10.5% |
| 44 | 11 | 10.5% |
| 47 | 11 | 10.5% |
| 2 | 10 | 9.5% |
| 14 | 10 | 9.5% |
| 17 | 10 | 9.5% |
| 20 | 10 | 9.5% |
| 41 | 10 | 9.5% |
| 42 | 10 | 9.5% |
| 10 | 9 | 8.6% |
| 21 | 9 | 8.6% |
| 29 | 9 | 8.6% |
| 38 | 9 | 8.6% |
| 1 | 7 | 6.7% |
| 45 | 6 | 5.7% |

## Top Co-Occurring Pairs

| Pair | Shared draws |
| --- | --- |
| 33, 46 | 6 |
| 4, 23 | 5 |
| 4, 46 | 5 |
| 8, 37 | 5 |
| 11, 39 | 5 |
| 13, 22 | 5 |
| 18, 35 | 5 |
| 25, 34 | 5 |
| 25, 43 | 5 |
| 33, 43 | 5 |
| 2, 19 | 4 |
| 3, 27 | 4 |
| 4, 11 | 4 |
| 4, 21 | 4 |
| 4, 22 | 4 |

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

Assumes independent, uniform six-from-49 main-number draws.
These are descriptive checks, not predictions or a comprehensive randomness certification.
No pattern establishes a future advantage. Only the maximum-pair test adjusts for the search
across pairs; tests across different checks are not jointly adjusted. Simulation p-values have
Monte Carlo uncertainty. Small histories provide little evidence.

Automatically refreshed by `python -m src.lotto_analyzer.cli` (also `python -m lotto_analyzer.cli`
after installation). Seed 20261103; 5,000 simulations when data is available.
Full statistics, bonus counts and latest-50 rankings: [statistics.json](statistics.json).
