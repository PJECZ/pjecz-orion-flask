"""
Alimentar Usuarios
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

import click

from orion.blueprints.usuarios.models import Usuario
from orion.extensions import pwd_context
from lib.pwgen import generar_contrasena
from lib.safe_string import safe_email, safe_string

USUARIOS_CSV = "seed/usuarios_roles.csv"


def alimentar_usuarios():
    """Alimentar Usuarios"""
    ruta = Path(USUARIOS_CSV)
    if not ruta.exists():
        click.echo(f"AVISO: {ruta.name} no se encontró.")
        sys.exit(1)
    if not ruta.is_file():
        click.echo(f"AVISO: {ruta.name} no es un archivo.")
        sys.exit(1)
    click.echo("Alimentando usuarios: ", nl=False)
    contador = 0
    with open(ruta, encoding="utf8") as puntero:
        rows = csv.DictReader(puntero)
        for row in rows:
            usuario_id = int(row["usuario_id"])
            email = safe_email(row["email"])
            nombres = safe_string(row["nombres"], save_enie=True)
            apellido_paterno = safe_string(row["apellido_paterno"], save_enie=True)
            apellido_materno = safe_string(row["apellido_materno"], save_enie=True)
            curp = safe_string(row["curp"])
            puesto = safe_string(row["puesto"], save_enie=True)
            estatus = row["estatus"]
            # if usuario_id != contador + 1:
            #     click.echo(click.style(f"  AVISO: usuario_id {usuario_id} no es consecutivo", fg="red"))
            #     sys.exit(1)
            Usuario(
                email=email,
                nombres=nombres,
                apellido_paterno=apellido_paterno,
                apellido_materno=apellido_materno,
                curp=curp,
                puesto=puesto,
                estatus=estatus,
                api_key="",
                api_key_expiracion=datetime(year=2000, month=1, day=1),
                contrasena=pwd_context.hash(generar_contrasena()),
            ).save()
            contador += 1
            click.echo(click.style(".", fg="green"), nl=False)
    click.echo()
    click.echo(click.style(f"  {contador} usuarios alimentados.", fg="green"))
