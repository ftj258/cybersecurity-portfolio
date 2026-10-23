# Mac_apt Artifact Analysis

Raw output from running [mac_apt](https://github.com/ydkhatri/mac_apt) (macOS Artifact Parsing Tool) against a macOS disk image, from coursework for CFRS 764 (Mac Forensics) at George Mason University. I contributed a parsing module to mac_apt as part of this coursework.

Test subject was a synthetic/training disk image provided for the course (a MacBook Air running OS X Lion, E01 format) — not a real case, but analyzed with the same methodology as one.

## What's here

CSV exports of parsed system artifacts:

- **Basic_Info** — system identification, timezone, and locale data
- **Dock Items** — applications and folders pinned to the Dock, with modification timestamps
- **InstallHistory** — software installation and update history
- **BashSessions** — recovered shell history across multiple user accounts
- **FsEvents** — file system event log (file creation, modification, deletion activity)
- **iDevice_Backups** — iOS device backup metadata found on the system
- **Safari** — browser history, searches, and downloads recovered from Safari's caches
- **Quarantine** — download provenance (origin URL, timestamp) for files brought onto the system

Full methodology and walkthrough: [Mac_APT_Presentation.pdf](Mac_APT_Presentation.pdf)

## Notable finding

Cross-artifact analysis surfaced evidence of a keylogger (`LogKext`) being installed, researched, used, and later removed — corroborated independently across six different artifact types:

1. **InstallHistory** shows `LogKext` installed via the macOS Installer.
2. **Safari history** (under a since-deleted user account) shows searches for how the keylogger works (`"what does minimum megs do logkext"`), a visit to the tool's project page, a download of its readme, and that readme open in the last browser session — establishing the user actively researched and used it.
3. **BashSessions** for that same account show it being configured and run with `sudo` (`sudo logKextClient`, `vim com.fsb.logKext`).
4. A separate root-level bash session shows the cleanup: `crontab -e` edits, `rm` of the logKext preference file, and the session's log file being piped and mailed out to an external Gmail address — consistent with covering tracks while exfiltrating captured data.
5. **FSEvents** independently confirms the timeline: the logKext preference file is removed and the kernel extension cache is rebuilt shortly after.
6. **Spotlight**'s search index still shows the logKext files (plist, kernel extension, client binary) even after removal — the index wasn't cleared along with the files themselves, so indexing metadata outlived the deliberate deletion.

This is the kind of pattern mac_apt is built to surface: reconstructing what a user did — install, use, and attempt to clean up after — from artifacts left behind across multiple independent data sources, despite a deliberate cleanup attempt.

## What this demonstrates

Multi-source macOS artifact correlation — tying system metadata, shell history, browser activity, search-index data, and file system events together to reconstruct user activity and identify evidence tampering, even when direct evidence has been deleted.
