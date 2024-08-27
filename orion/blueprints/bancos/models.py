"""
Bancos, modelos
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Banco(database.Model, UniversalMixin):
    """Banco"""

    # Nombre de la tabla
    __tablename__ = "bancos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columnas
    nombre: Mapped[str] = mapped_column(String(64), unique=True)

    # Hijos
    # TODO: Conectar hijos
    # pensiones_alimenticias = db.relationship("PersonaPensionAlimenticia", back_populates="banco")

    def __repr__(self):
        """Representación"""
        return f"<Banco {self.id}>"
