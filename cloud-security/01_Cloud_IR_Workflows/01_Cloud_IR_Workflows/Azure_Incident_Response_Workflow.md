# Azure Incident Response Workflow

**Purpose:** Demonstrate response methodology for Azure cloud environments.

---

## 1. Detection Sources

• Azure AD sign-in logs  
• Azure Security Center alerts  
• Activity log anomalies  
• Conditional Access signals  
• Azure Monitor traces

---

## 2. Investigation Steps

1. Confirm risky sign-ins and location anomalies  
2. Review OAuth app permissions  
3. Validate MFA attempts and challenges  
4. Inspect mailbox rules for unauthorized forwarding  
5. Correlate with Sentinel or SIEM findings

---

## 3. Containment Strategy

• Reset compromised user credentials  
• Enforce MFA re-registration  
• Disable risky OAuth apps  
• Block malicious sign-in IP ranges

---

## 4. Recovery Steps

• Restore Azure resources from snapshots  
• Validate RBAC consistency  
• Deploy additional monitoring workbooks

---

## 5. Lessons Learned

• Tighten conditional access policies  
• Augment identity threat detection rules  
• Integrate Azure Policy for drift enforcement

---

## Skills Demonstrated

• Azure security investigation  
• Identity governance expertise  
• Conditional access remediation  
