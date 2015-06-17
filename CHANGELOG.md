# Changelog

All notable changes to EnvelopeSeal are documented here. The format follows
Keep a Changelog, and the project uses semantic versioning.

## [Unreleased]

### Changed

- Rotation planner wording is under review for the next patch.

## [1.0.1] - 2026-07-01

### Fixed

- A manifest with a wrapped key listed before its KEK is now ordered
  topologically instead of reported as broken.

## [1.0.0] - 2025-11-11

### Added

- Stable CLI contract for audit, graph, rotation, and version, exit codes 0/1/2.
- Tests pin the hierarchy edges: cycles, missing KEKs, and depth.

## [0.9.5] - 2024-04-23

### Changed

- Maintenance release: documentation pass and sample refresh.

## [0.9.0] - 2023-06-13

### Added

- Rotation planner checks: blast radius per KEK and safe order.
- Architecture note for the hierarchy model.

## [0.8.0] - 2022-12-06

### Added

- JSON output for the audit and rotation commands.
- Strength view per key in the hierarchy.

## [0.7.0] - 2021-05-04

### Added

- Bundled manifest samples: healthy and broken.
- README walkthrough captured from a real audit run.

## [0.6.0] - 2020-09-15

### Added
