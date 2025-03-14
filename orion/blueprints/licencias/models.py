"""
Licencias, modelos
"""

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import now

from lib.universal_mixin import UniversalMixin
from orion.extensions import database


class Licencia(database.Model, UniversalMixin):
    """Licencia"""

    TIPOS = {
        "SIN ESPECIFICAR": "Sin especificar",
        "ENFERMEDAD": "Enfermedad",
        "PERMISO": "Permiso",
        "VACACIONES": "Vacaciones",
        "OTRO": "Otro",
    }

    # https://developer.mozilla.org/es/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
    EXTENSIONES = {
        "jpg": ("Imagen", "image/jpg"),
        "jpeg": ("Imagen", "image/jpeg"),
        "png": ("Imagen", "image/png"),
        "pdf": ("Archivo PDF", "application/pdf"),
        "docx": ("Archivo Word", "application/msword"),
    }

    # Nombre de la tabla
    __tablename__ = "licencias"

    # Clave primaria
    id: Mapped[int] = mapped_column(primary_key=True)

    # Clave foránea
    persona_id: Mapped[int] = mapped_column(ForeignKey("personas.id"))
    persona: Mapped["Persona"] = relationship(back_populates="licencias")

    # Columnas
    tipo: Mapped[str] = mapped_column(Enum(*TIPOS, name="licencias_tipos", native_enum=False), index=True)
    fecha_inicio: Mapped[date]
    fecha_termino: Mapped[date]
    con_goce: Mapped[bool] = mapped_column(default=False)
    motivo: Mapped[str] = mapped_column(String(512))
    puesto_nombre: Mapped[str] = mapped_column(String(128))
    archivo: Mapped[Optional[str]] = mapped_column(String(64))
    url: Mapped[Optional[str]] = mapped_column(String(512))

    # Variables
    extension = ""

    @staticmethod
    def type_format(file_name):
        "Tipo de formato del archivo"
        try:
            extension = file_name.rsplit(".", 1)[1]
        except:
            return ""
        if extension in ("jpg", "jpeg", "png"):
            return "IMG"
        if extension in ("docx", "xlsx"):
            return "DOC"
        if extension == "pdf":
            return "PDF"
        return ""

    def set_extension(self, archivo_nombre):
        """Establece el tipo de extensión del archivo"""
        extensiones_permitidas = Licencia.EXTENSIONES.keys()
        if "." in archivo_nombre and archivo_nombre.rsplit(".", 1)[1] in extensiones_permitidas:
            self.extension = archivo_nombre.rsplit(".", 1)[1]
            return True
        return False

    def __repr__(self):
        """Representación"""
        return f"<Licencia {self.id}>"
