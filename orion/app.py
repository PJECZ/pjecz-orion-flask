"""
Flask App
"""

import rq
from flask import Flask
from redis import Redis

from config.settings import Settings
from orion.blueprints.areas.views import areas
from orion.blueprints.atribuciones.views import atribuciones
from orion.blueprints.bancos.views import bancos
from orion.blueprints.bitacoras.views import bitacoras
from orion.blueprints.carreras.views import carreras
from orion.blueprints.centros_trabajos.views import centros_trabajos
from orion.blueprints.distritos.views import distritos
from orion.blueprints.entradas_salidas.views import entradas_salidas
from orion.blueprints.historial_puestos.views import historial_puestos
from orion.blueprints.licencias.views import licencias
from orion.blueprints.modulos.views import modulos
from orion.blueprints.niveles_academicos.views import niveles_academicos
from orion.blueprints.organos.views import organos
from orion.blueprints.permisos.views import permisos
from orion.blueprints.personas.views import personas
from orion.blueprints.puestos.views import puestos
from orion.blueprints.puestos_funciones.views import puestos_funciones
from orion.blueprints.roles.views import roles
from orion.blueprints.sistemas.views import sistemas
from orion.blueprints.tareas.views import tareas
from orion.blueprints.turnos.views import turnos
from orion.blueprints.usuarios.models import Usuario
from orion.blueprints.usuarios.views import usuarios
from orion.blueprints.usuarios_roles.views import usuarios_roles
from orion.extensions import csrf, database, login_manager, moment


def create_app():
    """Crear app"""
    # Definir app
    app = Flask(__name__, instance_relative_config=True)

    # Cargar la configuración
    app.config.from_object(Settings())

    # Redis
    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = rq.Queue(app.config["TASK_QUEUE"], connection=app.redis, default_timeout=3000)

    # Registrar blueprints
    app.register_blueprint(areas)
    app.register_blueprint(atribuciones)
    app.register_blueprint(bancos)
    app.register_blueprint(bitacoras)
    app.register_blueprint(carreras)
    app.register_blueprint(centros_trabajos)
    app.register_blueprint(distritos)
    app.register_blueprint(entradas_salidas)
    app.register_blueprint(historial_puestos)
    app.register_blueprint(licencias)
    app.register_blueprint(modulos)
    app.register_blueprint(niveles_academicos)
    app.register_blueprint(organos)
    app.register_blueprint(permisos)
    app.register_blueprint(personas)
    app.register_blueprint(puestos)
    app.register_blueprint(puestos_funciones)
    app.register_blueprint(roles)
    app.register_blueprint(sistemas)
    app.register_blueprint(tareas)
    app.register_blueprint(turnos)
    app.register_blueprint(usuarios)
    app.register_blueprint(usuarios_roles)

    # Inicializar extensiones
    extensions(app)

    # Inicializar autenticación
    authentication(Usuario)

    # Entregar app
    return app


def extensions(app):
    """Inicializar extensiones"""
    csrf.init_app(app)
    database.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)
    # socketio.init_app(app)


def authentication(user_model):
    """Inicializar Flask-Login"""
    login_manager.login_view = "usuarios.login"

    @login_manager.user_loader
    def load_user(uid):
        return user_model.query.get(uid)
