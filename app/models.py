from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contraseña_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default="cliente")

    @property
    def contraseña(self):
        raise AttributeError('No se puede leer la contraseña')

    @contraseña.setter
    def contraseña(self, password):
        self.contraseña_hash = generate_password_hash(password)

    def verificar_contraseña(self, password):
        return check_password_hash(self.contraseña_hash, password)

    def get_id(self):
        return str(self.id)


class Mesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False, unique=True)
    capacidad = db.Column(db.Integer, nullable=False)


class Horario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.Integer, nullable=False)
    hora_apertura = db.Column(db.String(5), nullable=False)
    hora_cierre = db.Column(db.String(5), nullable=False)


class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesa.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.String(5), nullable=False)
    estado = db.Column(db.String(20), default="pendiente")
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref=db.backref('reservas', lazy=True))
    mesa = db.relationship('Mesa', backref=db.backref('reservas', lazy=True))