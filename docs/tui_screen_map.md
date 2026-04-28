# TUI Screen Map

## Goal

Define the first screen set for the Textual app around the existing resume workflows:

- view current resume state
- validate schema health
- export artifacts
- inspect runtime configuration

This document is intentionally scoped to the current service layer in `resgen.services`.

## App Shell

The TUI should launch into a single app shell with:

- a header showing app name and active screen
- a footer showing global key bindings
- a left navigation rail or top tab bar for screen switching
- a main content region that swaps full screens
- a transient status/toast area for success and failure messages

## Global Navigation

- `d`: Dashboard
- `r`: Resume Summary
- `v`: Validation
- `e`: Export
- `s`: Settings
- `q`: Quit
- `?`: Toggle help overlay

## Screen 1: Dashboard

### Purpose

Give a fast, read-only snapshot of the active resume and system health.

### Primary Content

- identity card from `basics.name`, `basics.label`, `basics.summary`
- stat cards for experience, skills, projects, and education
- validation status badge
- export status area showing the most recent successful artifact path if available
- section counts for work, volunteer, education, awards, certificates, publications, languages, interests, references, and projects

### Data Dependencies

- `resgen.services.validate_resume()`
- `resgen.services.collect_resume_stats()`

### Layout

- top row: profile summary plus health/status card
- middle row: four stat cards
- bottom row: section inventory table or list

### Empty/Error States

- config error: show missing resume path or unreadable file
- schema failure: show dashboard counts only if the load succeeds, with a warning badge pointing to Validation
- unexpected failure: show a dismissible error panel

## Screen 2: Resume Summary

### Purpose

Browse the actual resume content without opening the source JSON.

### Primary Content

- basics panel with contact and location summary
- selectable section list for:
  - work
  - projects
  - education
  - skills
  - volunteer
  - awards
  - certificates
  - publications
  - languages
  - interests
  - references
- detail panel for the selected record

### Data Dependencies

- `resgen.services.validate_resume()`

### Layout

- left: section selector
- center: item list within the active section
- right: detail view for the selected item

### Notes

- This stays read-only in the first TUI release.
- Long text such as summaries and highlights should be scrollable.

## Screen 3: Validation

### Purpose

Run schema validation in-app and make failures readable enough to fix quickly.

### Primary Content

- status banner: valid or invalid
- validation timestamp
- issue list showing:
  - error message
  - JSON path
  - failing value when safe to display
  - likely next action
- success panel when no errors are present

### Data Dependencies

- `resgen.services.validate_resume()`

### Layout

- top: action bar with `Run Validation`
- main: results panel
- optional side panel: explanation of common failure categories

### Notes

- The current `jsonschema` validation path is enough for the first version.
- If multiple errors are needed later, add a service that uses `iter_errors` rather than changing UI code first.

## Screen 4: Export

### Purpose

Run the existing export workflow without leaving the TUI.

### Primary Content

- format selector for `md`, `html`, and `pdf`
- output path input seeded with `resume_export.<format>`
- export action button
- result/log panel for success and failure messages
- optional preview metadata such as output file size and last-written time

### Data Dependencies

- `resgen.services.export_resume()`

### Layout

- top: format and output controls
- middle: contextual notes, such as PDF dependency requirements
- bottom: export result log

### Notes

- This screen should not render a document preview in the first version.
- Export should reuse the existing service exceptions and only translate them into screen messages.

## Screen 5: Settings

### Purpose

Show runtime configuration health without exposing secrets.

### Primary Content

- active `RESUME_JSON_PATH`
- schema path
- themes path
- environment variable presence indicators for `EMAIL`, `PHONE_NUMBER`, and any future secret-backed fields
- template availability status for `default.md`, `default.html`, and PDF prerequisites

### Data Dependencies

- `resgen.config`
- optional future helper in `resgen.services` for configuration diagnostics

### Layout

- top: path/status cards
- bottom: environment and dependency checklist

### Notes

- Secret values should never be rendered, only presence and source health.

## Shared Interaction Rules

- Heavy operations should show a loading indicator.
- Success and failure should use a consistent status region across screens.
- Keyboard-first navigation is mandatory; mouse support is optional.
- Each screen should degrade cleanly when data is missing or invalid.

## MVP Build Order

1. App shell with navigation and placeholder screens
2. Dashboard using `collect_resume_stats()` and `validate_resume()`
3. Validation screen
4. Export screen
5. Settings screen
6. Resume Summary screen

## Service Gaps Exposed By This Screen Map

These do not block the screen map, but they are likely follow-up helpers:

- `get_resume_overview()`: lightweight summary payload for dashboard and summary header
- `get_config_status()`: safe configuration diagnostics for Settings
- `validate_resume_detailed()`: multi-error output for a richer Validation screen
