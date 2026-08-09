# ENGINEERING_PRINCIPLES.md  
  
Project: Project Atlas  
Foundation Version: Atlas Foundation 0.1  
Sprint: 1  
  
---  
  
# Engineering Philosophy  
  
Project Atlas is built with the philosophy that simplicity, maintainability, and modularity are more valuable than premature optimization.  
  
---  
  
## General Principles  
  
1. Complete one task at a time.  
2. Every task must compile before continuing.  
3. Keep modules independent.  
4. Business logic belongs in Services.  
5. API routes remain lightweight.  
6. Database access goes through repositories.  
7. Configuration comes from environment variables.  
8. Never hardcode secrets.  
9. Every feature should be testable.  
10. Keep AI provider independent.  
  
---  
  
## AI Design Principles  
  
The AI layer must never depend on a single vendor.  
  
Create an abstraction layer:  
  
AI Provider  
  
↓  
  
OpenAI  
  
Anthropic  
  
Azure OpenAI  
  
Local Models  
  
---  
  
## Folder Responsibility  
  
backend/  
  
Business logic  
  
frontend/  
  
User Interface  
  
knowledge/  
  
Reference documents  
  
templates/  
  
Proposal templates  
  
docs/  
  
Project documentation  
  
---  
  
## Git Rules  
  
One feature = One commit.  
  
Never commit broken code.  
  
---  
  
## Sprint Rule  
  
Finish Sprint 1 completely before starting Sprint 2.  
