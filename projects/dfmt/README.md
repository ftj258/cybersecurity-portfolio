# dfmt — Digital Forensics Sector Hashing Tool

A tool I built and tested as part of my Graduate Research Assistantship, for sector-hashing disk images so investigators can search for deleted or partial files — surfacing evidence that can support probable cause for a search warrant even when files have been deleted or only exist in fragments.

## What it does

dfmt builds hash databases from disk images at the sector level (not just whole-file hashes), so a file can be identified even if it's been deleted, fragmented, or only partially overwritten. It's built on top of [NPS hashdb](https://github.com/NPS-DEEP/hashdb) and `md5deep` for the underlying hashing engine. It supports:

- Creating and deleting hash catalogs
- Loading multiple disk images into a catalog (with duplicate-load prevention)
- Querying multiple files against a catalog to check for matches, including partial/sector-level matches

## Two interfaces

- **`dfmt/`** — a packaged Python module (Flask + Flask-RESTX) exposing the same functionality as a REST API, so it can be driven from Postman, curl, or any HTTP client rather than only a local GUI. See [DfmtAPIDocs.md](DfmtAPIDocs.md) for full setup and usage, including authentication and example requests.
- An earlier version was a standalone desktop GUI (Tkinter) with the same core hashing/query logic.

## Dependencies

The hashing backend (`hashdb`, `md5deep64`, `trunc`) are third-party binaries referenced in `dfmt/config.json` by path — not included in this repo. Source: [NPS-DEEP/hashdb](https://github.com/NPS-DEEP/hashdb), [md5deep](https://github.com/jessek/hashdeep).

## What this demonstrates

Building a working forensic tool end-to-end — from the underlying sector-hashing methodology (Garfinkel, *Using Purpose-Built Functions and Block Hashes to Enable Small Block and Sub-File Forensics*) through to a packaged, documented API that other investigators could actually install and use.
