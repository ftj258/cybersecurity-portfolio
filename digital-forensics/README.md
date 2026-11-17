# Digital Forensics

My forensics work splits in two. The hands-on, tool-driven labs live in my separate [dfir-home-labs](https://github.com/ftj258/dfir-home-labs) repo: memory forensics with Volatility, disk and timeline reconstruction, malware pulled apart in a sandbox. This folder holds the reporting side.

## Autopsy case report

A full HTML report exported from [Autopsy](https://www.autopsy.com/) after working a disk image end to end. It's the real export, not a summary. Open `02_Forensic_Investigations/samples/index.html` and it links out to everything the analysis turned up:

- Web activity: history, bookmarks, cookies, search terms, downloads
- Email recovered from the image
- Recent documents, tagged and flagged files, and keyword hits
- Extension-mismatch findings (how you catch a file wearing the wrong extension)
- EXIF metadata pulled from recovered images

The disk image is a public training dataset, so there's no real-world PII in it.

## Related

- [dfir-home-labs](https://github.com/ftj258/dfir-home-labs) — the hands-on technical labs.
- [Forensic case studies](../projects/forensic-case-studies) — case write-ups from my graduate forensics coursework.

## Contact
Email: fjohra@hotmail.com  
LinkedIn: https://www.linkedin.com/in/fjohra/
