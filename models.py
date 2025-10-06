from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    productos = db.relationship('Producto', backref='categoria', lazy=True)

class Productor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    finca = db.Column(db.String(100))
    telefono = db.Column(db.String(20), nullable=False)
    es_premium = db.Column(db.Boolean, default=False)
    fecha_suscripcion = db.Column(db.DateTime)
    meses_pagados = db.Column(db.Integer, default=0)
    # 🔑 Esta línea es la clave:
    productos = db.relationship('Producto', backref='productor', lazy=True)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    unidad = db.Column(db.String(20))
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.Text)
    estado = db.Column(db.String(20), default="disponible")
    productor_id = db.Column(db.Integer, db.ForeignKey('productor.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)