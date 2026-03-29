# Documentation

This repository is organized around the Bad Dream Button software stack.

## Structure

- `hardware-architecture/`: hardware planning, component tradeoffs, power constraints, prototype paths, and enclosure notes

As implementation work begins, the repository is intended to grow into these areas:

- `../sdk/`: shared libraries and integration helpers
- `../services/`: backend services for alert delivery, device registry, and notification workflows
- `../firmware/`: embedded firmware for the button and any local gateway hardware
- `../apps/`: optional mobile applications and related client software

The hardware docs in this folder are meant to help make the first architecture decision before firmware and services are built.
