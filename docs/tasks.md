# Tasks (Gate 3)

## Metadata
- Task Plan Version: 1.6.0
- Status: Completed (v1.6.0 delta implementation for T-005 through T-007)
- Linked Requirement Version: 1.6.0
- Linked Design Version: 1.6.0

## Task Backlog

- T-001: Build and update data models for records, summaries, and per-number outputs.
  - Depends on: none
  - Maps to: RQ-001, RQ-012
  - Done when: dataclasses exist and are used by parser/analyzer.
  - Current state: Completed on 2026-07-19.

- T-002: Implement config loader for numeric range bounds.
  - Depends on: T-001
  - Maps to: RQ-004, RQ-004a, NFR-004
  - Done when: config file is parsed and invalid bounds trigger clear errors.
  - Current state: Completed on 2026-07-19.

- T-003: Implement CSV parser and validators with config-based numeric range checks.
  - Depends on: T-001, T-002
  - Maps to: RQ-001..RQ-005
  - Done when: valid rows parsed, malformed rows counted, and out-of-range values rejected by config bounds.
  - Current state: Completed on 2026-07-19.

- T-004: Implement date window resolution and date-range filter.
  - Depends on: T-001
  - Maps to: RQ-006
  - Done when: 3m/1y/2y/custom date filtering passes tests.
  - Current state: Completed on 2026-07-19.

- T-005: Implement per-number frequency, percentage, configured-range candidate expansion (including zero-frequency numbers), 6-number combo ranking, and bottom-count tie-inclusive cutoff selection.
  - Depends on: T-003, T-004
  - Maps to: RQ-007, RQ-007a, RQ-008, RQ-009, RQ-010
  - Done when: ranking candidate set always includes full `[min_value,max_value]`, never-seen numbers are counted as zero, combination ranking is deterministic, and tie-inclusive cutoff returns at least `bottom-count` rows.
  - Current state: Completed on 2026-07-19.

- T-006: Implement CLI orchestration and CSV export for 6-number combo results.
  - Depends on: T-002, T-003, T-004, T-005
  - Maps to: RQ-011, RQ-012, NFR-002, NFR-004
  - Done when: command runs end-to-end, accepts config path, and writes combo output CSV derived from v1.6.0 bottom-count tie-inclusive behavior.
  - Current state: Completed on 2026-07-19.

- T-007: Implement unit tests and sample fixtures for config, candidate-set selection, and combo generation behavior.
  - Depends on: T-002, T-003, T-004, T-005, T-006
  - Maps to: NFR-001, NFR-003
  - Done when: tests cover config bounds, parsing, date filter, zero-frequency candidate inclusion, bottom-count cutoff, tie-inclusive expansion, and output determinism.
  - Current state: Completed on 2026-07-19.

- T-008: Remove legacy assumptions from older requirement baselines.
  - Depends on: T-003, T-005, T-006
  - Maps to: RQ-001..RQ-012, RQ-007a, NFR-001
  - Done when: no fixed `1..99` assumption remains in parser/analyzer/tests and no stale combination-row output schema remains.
  - Current state: Completed on 2026-07-19.

- T-009: Keep historical cleanup record from v1.1.0 migration.
  - Depends on: none
  - Maps to: NFR-001
  - Done when: documentation records that T-007 priority-removal migration was completed.
  - Current state: Completed on 2026-07-19.

## Gate Checklist
- Requirement mappings complete.
- Dependencies acyclic.
- Each task has clear done criteria.
- Task execution evidence is recorded in docs/task-results.md.
