# DATABASE.md  
  
Sprint 1 Database  
  
---  
  
Users  
  
id  
  
name  
  
email  
  
password_hash  
  
created_at  
  
---  
  
Projects  
  
id  
  
user_id  
  
project_name  
  
customer  
  
industry  
  
status  
  
created_at  
  
updated_at  
  
---  
  
RequirementDocuments  
  
id  
  
project_id  
  
filename  
  
file_type  
  
storage_path  
  
uploaded_at  
  
---  
  
RequirementAnalysis  
  
id  
  
project_id  
  
business_objectives  
  
functional_requirements  
  
non_functional_requirements  
  
assumptions  
  
risks  
  
analysis_json  
  
created_at  
  
---  
  
ClarificationQuestions  
  
id  
  
project_id  
  
question  
  
status  
  
created_at  
