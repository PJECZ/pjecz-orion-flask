"""
Personas Domicilios, modelos
"""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class PersonaDomicilio(database.Model, UniversalMixin):
    """PersonaDomicilio"""

    # Nombre de la tabla
    __tablename__ = "personas_domicilios"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    persona: Mapped["Persona"] = relationship(back_populates="personas_domicilios")
    domicilio_id: Mapped[int] = mapped_column(ForeignKey("domicilios.id"))
    domicilio: Mapped["Domicilio"] = relationship(back_populates="personas_domicilios")

    def __repr__(self):
        """Representación"""
        return f"<PersonaDomicilio {self.id}>"
