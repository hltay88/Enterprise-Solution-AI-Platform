# Project Atlas  
  
> **Commercial Product Name:** Enterprise Solution AI Platform  
  
**Foundation Version:** Atlas Foundation 0.1  
  
**Sprint:** Sprint 1  
  
**Status:** Development  
  
---  
  
# Vision  
  
Project Atlas is an AI-powered Enterprise Solution Platform that assists Presales Engineers, Solution Architects, Enterprise Architects, and IT Consultants in transforming customer business requirements into complete enterprise solutions.  
  
Instead of manually preparing proposals, solution designs, presentations, and Statements of Work (SOW), Project Atlas guides users through a structured workflow and uses AI to accelerate solution development while keeping humans in control.  
  
The platform is designed to support multiple industries and multiple technology domains, including IT infrastructure, cloud, cybersecurity, audiovisual systems, digital signage, smart buildings, industrial solutions, and more.  
  
---  
  
# Mission  
  
Reduce enterprise presales effort from days to minutes while improving:  
  
- Quality  
- Consistency  
- Standardization  
- Productivity  
- Knowledge reuse  
  
---  
  
# Long-Term Product Vision  
  
Project Atlas will evolve into a complete Enterprise Solution AI Platform capable of:  
  
- Requirement Intelligence  
- Business Analysis  
- Architecture Recommendation  
- Multi-vendor Solution Recommendation  
- Proposal Generation  
- PowerPoint Generation  
- Statement of Work Generation  
- Bill of Materials Assistance  
- Knowledge Management  
- Risk Assessment  
- Compliance Review  
- Cost Estimation  
  
---  
  
# Sprint 1 Objective  
  
Deliver a working MVP.  
  
Users should be able to:  
  
1. Login  
2. Create Project  
3. Upload Customer Requirement  
4. AI Requirement Analysis  
5. Generate Clarification Questions  
6. Save Project  
7. View Previous Projects  
  
---  
  
# Technology Stack  
  
## Frontend  
  
- Next.js  
- TypeScript  
- TailwindCSS  
  
## Backend  
  
- FastAPI  
- Python  
  
## Database  
  
- PostgreSQL  
- SQLAlchemy  
  
## AI  
  
The AI layer must remain provider-independent.  
  
Supported providers may include:  
  
- OpenAI  
- Anthropic  
- Azure OpenAI  
- Local LLMs  
  
---  
  
# Design Principles  
  
- Keep architecture modular.  
- Build one feature at a time.  
- AI assists the consultant.  
- Human review is mandatory.  
- Vendor recommendations are optional, not mandatory.  
- Solutions come before products.  
  
---  
  
# Project Structure  
  
```text  
project-atlas/  
  
backend/  
  
frontend/  
  
knowledge/  
  
templates/  
  
docs/  
  
docker/  
  
README.md  
  
PROJECT.md  
  
ENGINEERING_PRINCIPLES.md  
  
TASKS.md  
```  
  
---  
  
# Development Workflow  
  
1. Select one task from TASKS.md  
2. Complete only that task  
3. Test locally  
4. Commit changes  
5. Continue to the next task  
  
---  
  
# Coding Philosophy  
  
The project should follow:  
  
- Clean Architecture  
- RESTful API  
- Modular Design  
- Separation of Concerns  
- Reusable Components  
- Testable Code  
  
---  
  
# AI Coding Assistant Instructions  
  
Any AI coding assistant working on this repository should:  
  
1. Read README.md first.  
2. Read PROJECT.md.  
3. Read ENGINEERING_PRINCIPLES.md.  
4. Read TASKS.md.  
5. Complete only the requested task.  
6. Do not modify unrelated modules.  
7. Explain architectural decisions.  
8. Prefer maintainability over cleverness.  
  
These instructions apply equally to:  
  
- Cursor  
- Claude Code  
- Codex  
- Grok  
- GitHub Copilot  
- Gemini  
- Windsurf  
- Future AI coding assistants  
  
---  
  
# Future Modules  
  
- Architecture Recommendation Engine  
- Proposal Generator  
- PowerPoint Generator  
- Statement of Work Generator  
- BOM Intelligence  
- Knowledge Base  
- Vendor Intelligence  
- Cost Estimation  
- Risk Assessment  
- Compliance Engine  
  
---  
  
# Repository Standards  
  
- All source code must be version controlled.  
- No secrets should be committed.  
- Configuration belongs in environment variables.  
- Business logic should remain separate from API routes.  
- AI prompts should be stored independently from application logic.  
  
---  
  
# Atlas Foundation Versioning  
  
Atlas Foundation 0.1 – Sprint 1  
  
Atlas Foundation 0.2 – Sprint 2  
  
Atlas Foundation 0.3 – Sprint 3  
  
Atlas Foundation 0.4 – Sprint 4  
  
Atlas Foundation 0.5 – Sprint 5  
  
Atlas Foundation 1.0 – Commercial Release  
  
---  
  
# Next Steps  
  
Sprint 1 focuses on building a stable local MVP that runs on a MacBook using Docker Compose.  
  
Once Sprint 1 is complete and tested, the project will gradually evolve into a production-ready SaaS platform.  
