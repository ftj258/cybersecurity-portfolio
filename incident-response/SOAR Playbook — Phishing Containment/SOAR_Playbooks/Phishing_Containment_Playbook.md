# SOAR Playbook — Phishing Containment

## Objective

Automate phishing detection, investigation, and containment to reduce analyst workload and MTTC.

---

# Trigger Sources

- Email security alert
- User-reported phishing
- SIEM rule detection

---

# Automated Workflow

1. Extract email metadata
2. Enrich URLs and hashes
3. Identify impacted users
4. Quarantine emails
5. Block malicious indicators
6. Reset credentials if clicked
7. Revoke active sessions
8. Generate incident ticket

---

## Escalation Criteria

Escalate if:

- Executive account involved
- Privileged credentials compromised
- Financial systems accessed

---

## Metrics Impact

- Reduced containment time
- Increased automation ratio
- Improved triage consistency

---

## Skills Demonstrated

- SOAR design logic
- Identity security response
- Alert enrichment workflow
- Automation governance balance
