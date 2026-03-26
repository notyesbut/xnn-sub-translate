# Desktop App Architecture

## Stack Decision

The desktop shell will use Tauri + React.

Reasons:

- lighter and more packaging-friendly than Electron for this project
- good local file access story
- straightforward desktop UX for drag and drop, previews, and local exports
- clean separation between UI shell and Python sidecar engine

## Process Model

- Tauri hosts the desktop shell
- React renders the user interface
- a Python sidecar process runs the engine locally
- the app talks to the engine through stable local API contracts

## Bridge Strategy

The desktop shell should launch the engine locally and communicate through a loopback-only API boundary. This keeps the UI and engine independently testable and makes later packaging clearer.

Initial bridge expectations:

- request and response JSON contracts
- progress updates for long-running jobs
- explicit job polling or event streaming

## Security And Privacy

- no mandatory remote backend for MVP
- project files stay local by default
- secrets, if used, should stay in local configuration only
- the UI must not expose raw API traces or token accounting in the default mode

## Main Screens

- home
- new project wizard
- project dashboard
- subtitle review editor
- sync screen
- export screen

## UX Constraint

The default view must always prioritize clarity over configurability. Advanced settings belong behind an explicit advanced mode.

