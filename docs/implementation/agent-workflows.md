# Agent Workflows

## Purpose

This document explains how future agents should work inside this repository without drifting away from the product goal or creating avoidable conflicts.

## Default Execution Pattern

1. read the relevant docs first
2. split independent read-only questions when useful
3. merge findings serially
4. edit one subsystem boundary at a time
5. verify behavior
6. update docs when contracts or scope changed

## Recommended Task Boundaries

- `apps/desktop`: screens, state, view models, preview UX
- `services/engine`: parsing, translation, QA, sync, export, storage
- `packages/contracts`: schemas and DTOs
- `docs`: plans, architecture, and decision updates

## Coordination Rules

- parallel scouting is encouraged for independent questions
- overlapping edits to the same file set are discouraged
- shared contract changes should land with both doc and implementation updates
- if a task changes implementation order, update the roadmap or backlog

## Definition Of A Good Vertical Slice

A strong task should end with a user-visible or system-verifiable outcome such as:

- parse `.srt` into stored segments
- translate one stored batch with validated output
- export a project to `.srt`
- show translation progress in the dashboard

## Required Context Before Editing

Agents should read the relevant subset of:

- `README.md`
- `AGENTS.md`
- `docs/architecture/*.md`
- `docs/implementation/*.md`

## Handoff Rule

If work stops midstream, leave:

- current state
- verified commands
- remaining risks
- next concrete task

in the task summary so the next agent can continue without re-discovery.

