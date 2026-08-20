from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Routes
from routes.auth_routes import auth_router
from routes.supervisor_routes import supervisor_bp
from routes.encuesta_routes import encuesta_router
from routes.scanner_routes import scanner_router
from routes.vendedor_routes import vendedor_router
from database import engine, Base
import models

app = FastAPI(title="Encuestas API")

SQLALCHEMY_DATABASE_URL = "sqlite:///./scanner.db" 

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar todas las rutas
app.include_router(auth_router)
app.include_router(supervisor_bp)
app.include_router(encuesta_router)
app.include_router(scanner_router)
app.include_router(vendedor_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8082, reload=True)