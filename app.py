from flask import Flask, render_template, request, redirect, url_for
import os
from models import db, Productor, Producto, Categoria
from datetime import datetime, timedelta

app = Flask(__name__)

CATEGORIA_ESTILOS = {
    "Alimentos": {"icono": "🍲", "color": "#fff3e0"},
    "Frutas": {"icono": "🍎", "color": "#ffecd2"},
    "Verduras": {"icono": "🥬", "color": "#e8f5e9"},
    "Tubérculos": {"icono": "🥔", "color": "#fff8e1"},
    "Lácteos": {"icono": "🥛", "color": "#f3e5f5"},
    "Huevos": {"icono": "🥚", "color": "#e3f2fd"},
    "Miel": {"icono": "🍯", "color": "#fff3e0"},
    "Carnes": {"icono": "🥩", "color": "#ffebee"},
    "Granos": {"icono": "🌾", "color": "#f1f8e9"},
    "Artesanías": {"icono": "🧺", "color": "#f8bbd0"},
    "Insumos": {"icono": "🌱", "color": "#e8f5e9"},
    "Herramientas": {"icono": "🛠️", "color": "#f5f5f5"},
    "Servicios": {"icono": "👨‍🌾", "color": "#e3f2fd"},
    "Maquinaria": {"icono": "🚜", "color": "#ffe0b2"},
    "Otros": {"icono": "📦", "color": "#eeeeee"},
}

basedir = os.path.abspath(os.path.dirname(__file__))
if os.environ.get("RENDER"):
    DATABASE_URL = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL.replace("postgres://", "postgresql://")
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'marketplace.db')}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

def init_db():
    with app.app_context():
        db.create_all()
        if not Categoria.query.first():
            for nombre in CATEGORIA_ESTILOS.keys():
                db.session.add(Categoria(nombre=nombre))
            db.session.commit()

        if not Productor.query.first():
            prod = Productor(
                nombre="Productor Ejemplo",
                finca="Finca Demo",
                telefono="3000000000",
                es_premium=False
            )
            db.session.add(prod)
            db.session.commit()

init_db()

@app.route("/")
def inicio():
    productos = Producto.query\
        .join(Productor)\
        .filter(Producto.estado == "disponible")\
        .order_by(Productor.es_premium.desc(), Producto.id.desc())\
        .all()
    categorias = Categoria.query.all()
    return render_template(
        "inicio.html",
        productos=productos,
        todas_categorias=categorias,
        categoria_estilos=CATEGORIA_ESTILOS
    )

@app.route("/categoria/<int:cat_id>")
def por_categoria(cat_id):
    productos = Producto.query.filter_by(estado="disponible", categoria_id=cat_id).all()
    categorias = Categoria.query.all()
    return render_template(
        "inicio.html",
        productos=productos,
        todas_categorias=categorias,
        categoria_estilos=CATEGORIA_ESTILOS
    )

@app.route("/publicar", methods=["GET"])
def publicar_inicio():
    return render_template("publicar.html")

@app.route("/publicar-paso2", methods=["POST"])
def publicar_paso2():
    telefono = request.form["telefono"]
    productor = Productor.query.filter_by(telefono=telefono).first()
    categorias = Categoria.query.all()
    return render_template(
        "publicar_paso2.html",
        telefono=telefono,
        nombre=productor.nombre if productor else "",
        finca=productor.finca if productor else "",
        es_existente=bool(productor),
        categorias=categorias,
        categoria_estilos=CATEGORIA_ESTILOS
    )

@app.route("/publicar", methods=["POST"])
def guardar_producto():
    try:
        nombre_prod = request.form["productor_nombre"]
        finca_prod = request.form.get("productor_finca", "")
        telefono_prod = request.form["productor_telefono"]

        productor = Productor.query.filter_by(telefono=telefono_prod).first()
        if not productor:
            productor = Productor(
                nombre=nombre_prod,
                finca=finca_prod,
                telefono=telefono_prod,
                es_premium=False
            )
            db.session.add(productor)
            db.session.flush()

        if not productor.es_premium:
            productos_activos = Producto.query.filter_by(
                productor_id=productor.id,
                estado="disponible"
            ).count()
            if productos_activos >= 1:
                return """
                <div style="max-width:600px; margin:50px auto; padding:20px; text-align:center; font-family:sans-serif;">
                    <h3>❌ Límite alcanzado</h3>
                    <p>En el plan <strong>Gratis</strong>, solo puedes tener <strong>1 producto activo</strong>.</p>
                    <p>¿Quieres publicar más? ¡Activa tu plan <strong>Premium por $10.000/mes</strong>!</p>
                    <a href="https://wa.me/573143539351?text=Hola,%20quiero%20activar%20mi%20plan%20Premium%20de%20$10.000%20mensuales"
                       style="display:inline-block; background:#28a745; color:white; padding:10px 20px; text-decoration:none; border-radius:8px; margin-top:15px;">
                        ⭐ Activar Premium
                    </a>
                    <br><br>
                    <a href="/" style="color:#155724; text-decoration:underline;">← Volver a La Tiendita</a>
                </div>
                """, 403

        producto = Producto(
            nombre=request.form["nombre"],
            cantidad=float(request.form["cantidad"]),
            unidad=request.form["unidad"],
            precio=float(request.form["precio"]),
            descripcion=request.form.get("descripcion", ""),
            productor_id=productor.id,
            categoria_id=int(request.form["categoria_id"])
        )
        db.session.add(producto)
        db.session.commit()
        return redirect(url_for("inicio"))

    except Exception as e:
        db.session.rollback()
        print("Error:", str(e))
        return "Error al guardar. Verifica los datos.", 500

# === RUTA TEMPORAL PARA ACTUALIZAR BASE DE DATOS EN RENDER GRATUITO ===
@app.route("/admin/actualizar-db")
def actualizar_db():
    with app.app_context():
        try:
            db.engine.execute("ALTER TABLE productor ADD COLUMN es_premium BOOLEAN DEFAULT FALSE")
        except Exception as e:
            print("es_premium ya existe o error:", str(e))
        try:
            db.engine.execute("ALTER TABLE productor ADD COLUMN fecha_suscripcion TIMESTAMP")
        except Exception as e:
            print("fecha_suscripcion ya existe o error:", str(e))
        try:
            db.engine.execute("ALTER TABLE productor ADD COLUMN meses_pagados INTEGER DEFAULT 0")
        except Exception as e:
            print("meses_pagados ya existe o error:", str(e))
        return "✅ Base de datos actualizada. Ahora puedes publicar productos."

# === RUTAS DE GESTIÓN DE PRODUCTOS ===
@app.route("/mis-productos", methods=["GET", "POST"])
def mis_productos():
    if request.method == "POST":
        telefono = request.form["telefono"]
        productor = Productor.query.filter_by(telefono=telefono).first()
        if productor:
            productos = Producto.query.filter_by(
                productor_id=productor.id,
                estado="disponible"
            ).all()
            categorias = Categoria.query.all()
            return render_template("mis_productos.html", productos=productos, telefono=telefono, categoria_estilos=CATEGORIA_ESTILOS, todas_categorias=categorias)
        else:
            return "❌ Número no encontrado. Publica al menos un producto primero.", 404
    return render_template("ingresar_telefono.html")

@app.route("/admin/editar/<int:id>", methods=["POST"])
def editar_producto_admin(id):
    telefono = request.form.get("telefono")
    producto = Producto.query.get_or_404(id)
    if not telefono or telefono != producto.productor.telefono:
        return "🔒 Acceso denegado.", 403
    
    producto.nombre = request.form["nombre"]
    producto.cantidad = float(request.form["cantidad"])
    producto.unidad = request.form["unidad"]
    producto.precio = float(request.form["precio"])
    producto.descripcion = request.form.get("descripcion", "")
    producto.categoria_id = int(request.form["categoria_id"])
    db.session.commit()
    return redirect(url_for("mis_productos_post", telefono=telefono))

@app.route("/mis-productos/<telefono>")
def mis_productos_post(telefono):
    productor = Productor.query.filter_by(telefono=telefono).first()
    if not productor:
        return "❌ Número no válido.", 404
    productos = Producto.query.filter_by(
        productor_id=productor.id,
        estado="disponible"
    ).all()
    categorias = Categoria.query.all()
    return render_template("mis_productos.html", productos=productos, telefono=telefono, categoria_estilos=CATEGORIA_ESTILOS, todas_categorias=categorias)

@app.route("/admin/retirar/<int:id>")
def retirar_producto_admin(id):
    telefono = request.args.get("token")
    producto = Producto.query.get_or_404(id)
    if not telefono or telefono != producto.productor.telefono:
        return "🔒 Acceso denegado.", 403
    producto.estado = "vendido"
    db.session.commit()
    return redirect(url_for("mis_productos_post", telefono=telefono))

# === RUTAS DE ADMINISTRACIÓN ===
@app.route("/admin/vender/<int:id>")
def vender_admin(id):
    clave_secreta = os.environ.get("CLAVE_VENDER", "mi-clave-secreta")
    if request.args.get("clave") != clave_secreta:
        return "🔒 Acceso denegado. Clave incorrecta.", 403
    prod = Producto.query.get(id)
    if prod:
        prod.estado = "vendido"
        db.session.commit()
        return f"✅ Producto ID {id} retirado de La Tiendita."
    else:
        return "❌ Producto no encontrado.", 404

@app.route("/admin/activar-por-telefono")
def activar_por_telefono():
    telefono = request.args.get("tel")
    meses = int(request.args.get("meses", 1))
    if telefono:
        prod = Productor.query.filter_by(telefono=telefono).first()
        if prod:
            prod.es_premium = True
            prod.fecha_suscripcion = datetime.utcnow()
            prod.meses_pagados = meses
            db.session.commit()
            return f"✅ ¡Activado! {prod.nombre} es Premium por {meses} meses."
        else:
            return "❌ Productor no encontrado."
    return "📞 Usa: ?tel=3101234567&meses=2"

@app.route("/admin/actualizar-suscripciones")
def actualizar_suscripciones():
    premium_activos = Productor.query.filter_by(es_premium=True).all()
    actualizados = 0
    for p in premium_activos:
        if p.fecha_suscripcion and p.meses_pagados:
            vencimiento = p.fecha_suscripcion + timedelta(days=30 * p.meses_pagados)
            if datetime.utcnow() > vencimiento:
                p.es_premium = False
                actualizados += 1
    db.session.commit()
    return f"✅ {actualizados} suscripciones desactivadas por vencimiento."

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)