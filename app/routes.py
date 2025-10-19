from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db
from .models import Usuario, Mesa, Horario, Reserva
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return redirect(url_for('main.login'))


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Usuario.query.filter_by(email=email).first()
        if user and user.verificar_contraseña(password):
            login_user(user)
            if user.rol == 'admin':
                return redirect(url_for('main.admin_panel'))
            else:
                return redirect(url_for('main.cliente_panel'))
        flash('Email o contraseña incorrectos')
    return render_template('login.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        
        if Usuario.query.filter_by(email=email).first():
            flash('El email ya está registrado')
            return redirect(url_for('main.register'))
        
        nuevo = Usuario(nombre=nombre, email=email, rol='cliente')
        nuevo.contraseña = password
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('main.login'))
    return render_template('register.html')


# --- ADMIN ---
@main.route('/admin')
@login_required
def admin_panel():
    if current_user.rol != 'admin':
        return redirect(url_for('main.cliente_panel'))
    mesas = Mesa.query.all()
    return render_template('admin/mesas.html', mesas=mesas)


@main.route('/admin/mesas/nueva', methods=['GET', 'POST'])
@login_required
def admin_nueva_mesa():
    if current_user.rol != 'admin':
        return redirect(url_for('main.cliente_panel'))
    if request.method == 'POST':
        numero = request.form['numero']
        capacidad = int(request.form['capacidad'])
        if Mesa.query.filter_by(numero=numero).first():
            flash('Ya existe una mesa con ese nombre/número')
        else:
            mesa = Mesa(numero=numero, capacidad=capacidad)
            db.session.add(mesa)
            db.session.commit()
            flash('Mesa creada exitosamente')
            return redirect(url_for('main.admin_panel'))
    return render_template('admin/nueva_mesa.html')

@main.route('/admin/reservas')
@login_required
def admin_reservas():
    if current_user.rol != 'admin':
        return redirect(url_for('main.cliente_panel'))
    reservas = Reserva.query.order_by(Reserva.fecha.desc(), Reserva.hora.desc()).all()
    return render_template('admin/reservas.html', reservas=reservas)

@main.route('/admin/horarios')
@login_required
def admin_horarios():
    if current_user.rol != 'admin':
        return redirect(url_for('main.cliente_panel'))
    horarios = Horario.query.all()
    return render_template('admin/horarios.html', horarios=horarios)

@main.route('/admin/reservas/<int:reserva_id>/<nuevo_estado>')
@login_required
def admin_cambiar_estado(reserva_id, nuevo_estado):
    if current_user.rol != 'admin':
        return redirect(url_for('main.cliente_panel'))
    
    if nuevo_estado not in ['atendida', 'cancelada']:
        flash('Estado no válido')
        return redirect(url_for('main.admin_reservas'))
    
    reserva = Reserva.query.get_or_404(reserva_id)
    reserva.estado = nuevo_estado
    db.session.commit()
    flash(f'Reserva actualizada a "{nuevo_estado}"')
    return redirect(url_for('main.admin_reservas'))

@main.route('/admin/horarios/nuevo', methods=['GET', 'POST'])
@login_required
def admin_nuevo_horario():
    if current_user.rol != 'admin':
        return redirect(url_for('main.cliente_panel'))
    if request.method == 'POST':
        dia = int(request.form['dia'])
        apertura = request.form['apertura']
        cierre = request.form['cierre']
        if Horario.query.filter_by(dia_semana=dia).first():
            flash('Ya existe un horario para este día')
        else:
            horario = Horario(dia_semana=dia, hora_apertura=apertura, hora_cierre=cierre)
            db.session.add(horario)
            db.session.commit()
            flash('Horario creado exitosamente')
            return redirect(url_for('main.admin_horarios'))
    return render_template('admin/nuevo_horario.html')


# --- CLIENTE ---
@main.route('/cliente')
@login_required
def cliente_panel():
    if current_user.rol == 'admin':
        return redirect(url_for('main.admin_panel'))
    return render_template('cliente/panel.html', nombre=current_user.nombre)


@main.route('/cliente/reservar', methods=['GET', 'POST'])
@login_required
def cliente_reservar():
    if current_user.rol == 'admin':
        return redirect(url_for('main.admin_panel'))
    
    if request.method == 'POST':
        fecha_str = request.form['fecha']
        hora_str = request.form['hora']
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora = hora_str
        except ValueError:
            flash('Formato de fecha u hora inválido')
            return redirect(url_for('main.cliente_reservar'))

        dia_semana = fecha.weekday()
        horario = Horario.query.filter_by(dia_semana=dia_semana).first()
        if not horario:
            flash('El restaurante está cerrado ese día')
            return redirect(url_for('main.cliente_reservar'))
        
        if hora < horario.hora_apertura or hora > horario.hora_cierre:
            flash(f'Horario fuera de rango. Abierto de {horario.hora_apertura} a {horario.hora_cierre}')
            return redirect(url_for('main.cliente_reservar'))

        reservas_ocupadas = Reserva.query.filter_by(fecha=fecha, hora=hora).all()
        ids_ocupados = [r.mesa_id for r in reservas_ocupadas]
        mesas_disponibles = Mesa.query.filter(Mesa.id.notin_(ids_ocupados)).all()

        return render_template('cliente/seleccion_mesa.html', 
                               fecha=fecha_str, 
                               hora=hora_str, 
                               mesas=mesas_disponibles)

    hoy = datetime.today().strftime('%Y-%m-%d')
    return render_template('cliente/reservar.html', hoy=hoy)


@main.route('/cliente/reservar/confirmar', methods=['POST'])
@login_required
def cliente_confirmar_reserva():
    if current_user.rol == 'admin':
        return redirect(url_for('main.admin_panel'))
    
    mesa_id = request.form['mesa_id']
    fecha_str = request.form['fecha']
    hora_str = request.form['hora']
    
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    mesa = Mesa.query.get(mesa_id)
    if not mesa:
        flash('Mesa no válida')
        return redirect(url_for('main.cliente_reservar'))
    
    if Reserva.query.filter_by(mesa_id=mesa_id, fecha=fecha, hora=hora_str).first():
        flash('Esta mesa ya fue reservada en ese horario')
        return redirect(url_for('main.cliente_reservar'))

    nueva_reserva = Reserva(
        usuario_id=current_user.id,
        mesa_id=mesa_id,
        fecha=fecha,
        hora=hora_str,
        estado='pendiente'
    )
    db.session.add(nueva_reserva)
    db.session.commit()
    
    flash(f'¡Reserva confirmada para el {fecha_str} a las {hora_str} en {mesa.numero}!')
    return redirect(url_for('main.cliente_panel'))


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))