import os
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# Modelo para Agendamentos
class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    time = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(String, nullable=True)

# Modelo para Finanças
class Finance(Base):
    __tablename__ = 'finances'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    time = Column(String, nullable=False)

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/your_database")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar tabelas
Base.metadata.create_all(bind=engine)
