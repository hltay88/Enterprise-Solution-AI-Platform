version: "3.9"  
  
services:  
  
  db:  
  
    image: postgres:16  
  
    container_name: atlas-db  
  
    environment:  
  
      POSTGRES_USER: atlas  
  
      POSTGRES_PASSWORD: atlas  
  
      POSTGRES_DB: atlas  
  
    ports:  
  
      - "5432:5432"  
  
    volumes:  
  
      - postgres-data:/var/lib/postgresql/data  
  
volumes:  
  
  postgres-data:  
