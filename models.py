from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Distrito(Base):
    __tablename__ = "distritos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)

    lugares = relationship("Lugar", back_populates="distrito", cascade="all, delete-orphan")


class Lugar(Base):
    __tablename__ = "lugares"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    distrito_id = Column(Integer, ForeignKey("distritos.id"), nullable=False)

    distrito = relationship("Distrito", back_populates="lugares")

    __table_args__ = (
        UniqueConstraint('nome', 'distrito_id', name='uq_lugar_distrito'),
    )