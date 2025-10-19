from app import create_app, db
from app.models import Usuario

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Usuario.query.filter_by(email='admin@gmail.com').first():
            admin = Usuario(nombre='Administrador', email='admin@gmail.com', rol='admin')
            admin.contraseña = 'admin123'
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)