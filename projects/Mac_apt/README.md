# Mac_apt Artifact Analysis

Raw output from running [mac_apt](https://github.com/ydkhatri/mac_apt) (macOS Artifact Parsing Tool) against a macOS disk image, from coursework for CFRS 764 (Mac Forensics) at George Mason University. I contributed a parsing module to mac_apt as part of this coursework.

## What's here

CSV exports of parsed system artifacts:

- **Basic_Info** — system identification, timezone, and locale data
- **Dock Items** — applications and folders pinned to the Dock, with modification timestamps
- **InstallHistory** — software installation and update history
- **BashSessions** — recovered shell history across multiple user accounts
- **FsEvents** — file system event log (file creation, modification, deletion activity)
- **iDevice_Backups** — iOS device backup metadata found on the system

## Notable finding

The recovered bash history shows activity consistent with anti-forensic behavior on the account under investigation: deletion of a VirtualBox directory, removal of a kernel extension used for system logging (`com.apple.logKext`), repeated `crontab -e` edits, and file deletions (`rm -rf`) shortly before other activity. This is the kind of pattern mac_apt is built to surface — reconstructing what a user did to cover their tracks from artifacts left behind despite the cleanup attempt.

## What this demonstrates

Multi-source macOS artifact correlation — tying system metadata, shell history, and file system events together to reconstruct user activity and identify evidence tampering.
