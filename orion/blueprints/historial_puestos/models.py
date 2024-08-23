"""
Historial de Puestos, modelos
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class HistorialPuesto(database.Model, UniversalMixin):
    """HistorialPuesto"""

    ESTADOS = {
        "PENDIENTE": "Pendiente",
        "CANCELADO": "Cancelado",
    }

    # Nombre de la tabla
    __tablename__ = "historial_puestos"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    persona: Mapped["Persona"] = relationship(back_populates="historial_puestos")
    puesto_funcion_id: Mapped[int] = mapped_column(ForeignKey("puestos_funciones.id"))
    puesto_funcion: Mapped["PuestoFuncion"] = relationship(back_populates="historial_puestos")
    turno_id: Mapped[int] = mapped_column(ForeignKey("turnos.id"))
    turno: Mapped["Turno"] = relationship(back_populates="historial_puestos")

    # Columnas
    area: Mapped[str] = mapped_column(String(128))
    centro_trabajo: Mapped[Optional[str]] = mapped_column(String(128))
    fecha_inicio: Mapped[datetime]
    fecha_termino: Mapped[Optional[datetime]]
    nivel: Mapped[Optional[int]] = mapped_column(Integer, default=1)
    quinquenio: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    nombramiento: Mapped[Optional[str]] = mapped_column(String(512))
    tipo_nombramiento: Mapped[Optional[str]] = mapped_column(String(512))
    nombramiento_observaciones: Mapped[Optional[str]] = mapped_column(String(512))

    def __repr__(self):
        """Representación"""
        return f"<HistorialPuesto {self.id}>"
