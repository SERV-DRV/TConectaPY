import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8080/api")
ADMIN_URL = os.getenv("ADMIN_URL", "http://localhost:3001/TCONECTA/v1")
CLIENT_URL = os.getenv("CLIENT_URL", "http://localhost:3002/TRANSMETRO-CONECTA-CLIENTE/v1")
