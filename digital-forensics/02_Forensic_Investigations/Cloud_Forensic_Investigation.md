# Cloud Forensic Investigation

## Scenario

Suspicious IAM activity detected in cloud environment.

---

## Investigation Steps

1. Review CloudTrail API activity
2. Identify anomalous role assumptions
3. Analyze geographic sign-in anomalies
4. Validate resource modification history
5. Review OAuth and token usage

---

## Findings

- Unauthorized privilege escalation attempt
- IAM policy modification outside change window
- API calls from unfamiliar IP range

---

## Containment

- Disable compromised account
- Revoke session tokens
- Restore previous IAM policy version

---

## Skills Demonstrated

- Cloud audit log analysis
- IAM governance review
- Incident containment strategy
