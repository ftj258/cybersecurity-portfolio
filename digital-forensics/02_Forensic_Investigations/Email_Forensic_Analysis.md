# Email Forensic Analysis

## Objective

Investigate suspected phishing email and determine compromise impact.

---

## Analysis Process

- Review full email header
- Validate SPF/DKIM/DMARC authentication
- Analyze sender domain age
- Extract embedded URLs
- Perform hash lookup on attachments

---

## Indicators Identified

- Spoofed sender domain
- Malicious redirect URL
- Credential harvesting landing page

---

## Containment Actions

- Quarantine matching emails
- Block sender domain
- Reset impacted user credentials
- Revoke active sessions

---

## Skills Demonstrated

- Header analysis
- Threat enrichment
- Credential compromise response
