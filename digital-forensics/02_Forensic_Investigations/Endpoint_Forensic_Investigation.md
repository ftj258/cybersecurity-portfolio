# Endpoint Forensic Investigation

## Scenario

Suspected malware infection on enterprise workstation.

---

## Investigation Steps

1. Identify suspicious process activity
2. Review event logs for anomalies
3. Analyze persistence mechanisms
4. Inspect registry changes
5. Extract suspicious binaries
6. Compare file hashes against threat intelligence

---

## Findings

- Suspicious executable located in temp directory
- Registry autorun key modified
- Outbound connections to flagged IP address

---

## Containment

- Isolate host from network
- Remove persistence mechanisms
- Reset associated credentials

---

## Skills Demonstrated

- Artifact analysis
- Timeline reconstruction
- Malware behavior review
- Endpoint containment strategy
