from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tzimmer_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Tzimmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    reservations = db.relationship('Reservation', backref='tzimmer', cascade='all, delete-orphan')

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tzimmer_id = db.Column(db.Integer, db.ForeignKey('tzimmer.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    arrival_date = db.Column(db.Date, nullable=False)
    departure_date = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash('אנא התחבר תחילה', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            flash('התחברת בהצלחה', 'success')
            return redirect(url_for('index'))
        else:
            flash('שם משתמש או סיסמה שגויים', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('יצאת מהמערכת בהצלחה', 'success')
    return redirect(url_for('login'))

@app.route('/tzimmers', methods=['GET', 'POST'])
@login_required
def manage_tzimmers():
    if request.method == 'POST':
        data = request.json
        new_tzimmer = Tzimmer(name=data['name'])
        db.session.add(new_tzimmer)
        db.session.commit()
        return jsonify({"id": new_tzimmer.id, "name": new_tzimmer.name}), 201
    
    tzimmers = Tzimmer.query.all()
    return jsonify([{"id": t.id, "name": t.name} for t in tzimmers])

@app.route('/tzimmers/<int:tzimmer_id>', methods=['DELETE'])
@login_required
def delete_tzimmer(tzimmer_id):
    tzimmer = Tzimmer.query.get_or_404(tzimmer_id)
    db.session.delete(tzimmer)
    db.session.commit()
    return jsonify({"message": "צימר נמחק בהצלחה"}), 200

@app.route('/reservations', methods=['GET', 'POST'])
@login_required
def manage_reservations():
    if request.method == 'POST':
        data = request.json
        new_reservation = Reservation(
            tzimmer_id=data['tzimmer_id'],
            customer_name=data['customer_name'],
            customer_phone=data.get('customer_phone', ''),
            arrival_date=datetime.strptime(data['arrival_date'], '%Y-%m-%d').date(),
            departure_date=datetime.strptime(data['departure_date'], '%Y-%m-%d').date(),
            total_price=float(data['total_price'])
        )
        db.session.add(new_reservation)
        db.session.commit()
        return jsonify({
            "id": new_reservation.id, 
            "customer_name": new_reservation.customer_name
        }), 201
    
    reservations = Reservation.query.all()
    return jsonify([{
        "id": r.id,
        "tzimmer_name": r.tzimmer.name,
        "customer_name": r.customer_name,
        "arrival_date": r.arrival_date.strftime('%Y-%m-%d'),
        "departure_date": r.departure_date.strftime('%Y-%m-%d'),
        "total_price": r.total_price
    } for r in reservations])

@app.route('/reservations/<int:reservation_id>', methods=['DELETE'])
@login_required
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    db.session.delete(reservation)
    db.session.commit()
    return jsonify({"message": "הזמנה נמחקה בהצלחה"}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        existing_admin = User.query.filter_by(username='admin').first()
        if not existing_admin:
            hashed_password = generate_password_hash('pass')
            admin_user = User(username='admin', password=hashed_password)
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully")
    

    app.run()
