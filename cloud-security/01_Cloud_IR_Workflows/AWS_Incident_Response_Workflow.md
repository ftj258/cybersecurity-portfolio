# AWS Incident Response Workflow

**Purpose:** Document best-practice IR steps for AWS environments.

---

## 1. Detection Sources

• CloudTrail logs  
• GuardDuty findings  
• VPC Flow Logs  
• IAM event history  
• AWS Config changes

---

## 2. Investigation Steps

1. Identify alert source and validate event  
2. Review CloudTrail for API anomalies  
3. Analyze GuardDuty findings for IOCs  
4. Collect VPC flow logs for lateral movement indicators  
5. Validate IAM role assumption anomalies

---

## 3. Containment Strategy

• Revoke suspicious IAM credentials  
• Isolate compromised EC2 instances  
• Update security groups to restrict traffic  
• Disable unauthorized session tokens

---

## 4. Recovery Steps

• Restore workloads from validated AMIs  
• Validate service integrity (health checks/logs)  
• Monitor for any reinfection indicators

---

## 5. Lessons Learned

• Update IR playbooks  
• Add detection rules for unusual API calls  
• Increase logging verbosity for critical services

---

## Skills Demonstrated

• AWS investigation logic  
• IAM governance  
• Service isolation strategy  
• Cloud log correlation
