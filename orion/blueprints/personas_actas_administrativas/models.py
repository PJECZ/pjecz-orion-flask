"""
Actas Administrativas, modelos
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class PersonaActaAdministrativa(database.Model, UniversalMixin):
    """PersonaActaAdministrativa"""

    # Nombre de la tabla
    __tablename__ = "personas_actas_administrativas"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    persona: Mapped["Persona"] = relationship(back_populates="personas_actas_administrativas")

    # Columnas
    fecha: Mapped[datetime] = mapped_column(DateTime, default=now())
    falta: Mapped[Optional[str]] = mapped_column(String(128))
    sancion: Mapped[Optional[str]] = mapped_column(String(128))

    def __repr__(self):
        """Representación"""
        return f"<PersonaActaAdministrativa {self.id}>"
