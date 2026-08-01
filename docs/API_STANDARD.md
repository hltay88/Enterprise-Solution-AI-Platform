# API_STANDARD.md  
  
REST API  
  
Foundation Version: Atlas Foundation 0.1  
Sprint: 1  
  
Related decisions: ATLAS-011, ATLAS-014  
  
---  
  
# Base URL  
  
All endpoints are prefixed with `/api`.  
  
---  
  
# Response Envelope  
  
Every JSON response uses the same shape.  
  
## Success  
  
```json  
{  
  "success": true,  
  "data": {},  
  "message": null  
}  
```  
  
`data` may be an object, an array, or `null` when there is nothing to return.  
  
## Error  
  
```json  
{  
  "success": false,  
  "data": null,  
  "error": {  
    "code": "NOT_FOUND",  
    "message": "Project not found"  
  }  
}  
```  
  
## Common error codes  
  
| Code | HTTP | Meaning |  
|------|------|---------|  
| `UNAUTHORIZED` | 401 | Missing or invalid JWT |  
| `FORBIDDEN` | 403 | Authenticated but not allowed |  
| `NOT_FOUND` | 404 | Resource does not exist |  
| `VALIDATION_ERROR` | 422 | Request body/query invalid |  
| `CONFLICT` | 409 | Duplicate or invalid state |  
| `INTERNAL_ERROR` | 500 | Unexpected server error |  
  
---  
  
# Authentication  
  
Protected routes require:  
  
```http  
Authorization: Bearer <jwt>  
```  
  
## Login  
  
```http  
POST /api/auth/login  
```  
  
Request:  
  
```json  
{  
  "email": "demo@atlas.local",  
  "password": "changeme"  
}  
```  
  
Response `data`:  
  
```json  
{  
  "access_token": "<jwt>",  
  "token_type": "bearer",  
  "user": {  
    "id": "...",  
    "name": "...",  
    "email": "..."  
  }  
}  
```  
  
## Current user  
  
```http  
GET /api/auth/me  
```  
  
Requires auth. Response `data` is the user object.  
  
---  
  
# Projects  
  
All project routes require auth. Users only access their own projects.  
  
```http  
GET    /api/projects  
POST   /api/projects  
GET    /api/projects/{id}  
PUT    /api/projects/{id}  
DELETE /api/projects/{id}  
```  
  
## Create / update body  
  
```json  
{  
  "project_name": "ACME Network Refresh",  
  "customer": "ACME Corp",  
  "industry": "Manufacturing",  
  "status": "draft"  
}  
```  
  
`GET /api/projects` returns an array of project summaries in `data`.  
  
---  
  
# Documents / Upload  
  
```http  
POST /api/projects/{id}/upload  
GET  /api/projects/{id}/documents  
```  
  
Upload is `multipart/form-data` with field `file`.  
  
Allowed types: `pdf`, `docx`, `txt`.  
Max size: 10 MB.  
  
---  
  
# Analysis  
  
```http  
POST /api/projects/{id}/analyze  
GET  /api/projects/{id}/analysis  
```  
  
`POST` runs AI requirement analysis and stores the result.  
`GET` returns the latest saved analysis for the project, or `404` if none exists.  
  
---  
  
# Clarification  
  
```http  
POST /api/projects/{id}/clarification  
GET  /api/projects/{id}/clarifications  
```  
  
`POST` generates clarification questions and stores them.  
`GET` returns the list of clarification questions for the project.  
  
---  
  
# Health Check  
  
```http  
GET /api/health  
```  
  
Public. Used by Docker / local checks.  
  
Response `data` example:  
  
```json  
{  
  "status": "ok",  
  "database": "ok"  
}  
```  
