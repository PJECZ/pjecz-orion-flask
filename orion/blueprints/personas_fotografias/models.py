"""
Personas Fotografías, modelos
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class PersonaFotografia(database.Model, UniversalMixin):
    """PersonaFotografia"""

    # Nombre de la tabla
    __tablename__ = "personas_fotografias"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    persona: Mapped["Persona"] = relationship(back_populates="fotografias")

    # Columnas
    archivo: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String(512))

    def __repr__(self):
        """Representación"""
        return f"<PersonaFotografia {self.id}>"
