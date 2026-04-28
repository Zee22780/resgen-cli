# TUI Architecture Decision

## Decision

Use **Textual** as the primary TUI framework and **Rich** as the terminal rendering foundation.

## Why Textual

- It matches the project language and keeps the TUI in Python beside the existing Typer CLI.
- It already provides the screen, widget, layout, key binding, worker, and testing primitives needed for a multi-screen app.
- It is a better fit than a lower-level toolkit for this project because the next phases need panels, dashboards, validation views, and export flows more than bespoke terminal drawing code.

## Why Not a Lower-Level Stack

- **prompt_toolkit** is strong for prompts and full-screen terminal apps, but it exposes more application plumbing directly.
- For this repo, that would push layout, widget composition, and screen-state management closer to custom code than necessary.

## Boundary Rules

The TUI should be a thin interface over shared services. It must not duplicate resume-loading, schema-validation, export, or stats logic.

- `resgen.core`
  - Owns low-level data access and template environment setup.
  - Examples: load resume JSON, inject env-backed secrets, load schema, locate themes.
- `resgen.services`
  - Owns reusable application workflows for both CLI and TUI.
  - Examples: validate resume, render templates, export artifacts, collect dashboard stats.
- `resgen.main`
  - Owns Typer commands and shell-oriented messaging only.
  - It should call `resgen.services` and translate exceptions into CLI output.
- `resgen.tui` (future)
  - Will own Textual screens, widgets, key bindings, and app state.
  - It should call `resgen.services` for all business operations and only format results for terminal interaction.

## Initial Module Plan

- `src/resgen/services.py`
  - Shared workflow entry points for CLI and TUI.
- `src/resgen/tui/app.py`
  - Textual app bootstrap.
- `src/resgen/tui/screens/`
  - Dashboard, validation, export, and settings screens.
- `src/resgen/tui/widgets/`
  - Reusable panels such as status cards and results tables.

## Design References

- See `docs/tui_screen_map.md` for the initial screen set, navigation model, and service-to-screen mapping.

## Operational Guidance

- Keep business results structured so both CLI and TUI can present them differently.
- Keep file writes and dependency-specific logic in services, not in UI code.
- Let the TUI show state and progress, but keep resume transformation rules in one place.
