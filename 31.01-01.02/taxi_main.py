from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_socketio import SocketIO

app = Flask('Backend')

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:Multiplication1337%40@localhost/main_taxi"
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class Driver(db.Model):
    phone = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(20))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    car_model = db.Column(db.String(25))
    password = db.Column(db.String(20))

class Customer(db.Model):
    phone = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(20))
    age = db.Column(db.Integer)
    password = db.Column(db.String(20))

class Order_history(db.Model):
    id = db.Column(db.INT, primary_key=True, autoincrement=True)
    customer_phone = db.Column(db.String(20))
    customer_name=db.Column(db.String(20))
    from_location = db.Column(db.String(20))
    to_location = db.Column(db.String(20))
    order_time = db.Column(db.DateTime, default=func.now())
    status = db.Column(db.String(20), default='Waiting')
    driver_phone = db.Column(db.String(20), db.ForeignKey('driver.phone'), nullable=True)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/driver')
def driver():
    return render_template('driver.html')

@app.route('/customer')
def customer():
    return render_template('customer.html')

@app.route('/driver/register', methods=['GET', 'POST'])
def register_d():
    if request.method == 'POST':
        session.clear()
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        car_model = request.form['car_model']
        phone = request.form['phone']
        password = request.form['password']
        existing_driver = Driver.query.filter_by(phone=phone).first()
        existing_customer = Customer.query.filter_by(phone=phone).first()
        if existing_driver or existing_customer:
            return "This phone number is already used!", 400
        new_driver = Driver(name=name, age=age, gender=gender, car_model=car_model, phone=phone, password=password)
        db.session.add(new_driver)
        db.session.commit()
        session['driver_phone'] = new_driver.phone
        return render_template('driver_page.html')
    return render_template('register_d.html')

@app.route('/customer/register', methods=['GET', 'POST'])
def register_c():
    if request.method == 'POST':
        session.clear()
        name = request.form['name']
        age = request.form['age']
        phone = request.form['phone']
        password = request.form['password']
        existing_driver = Driver.query.filter_by(phone=phone).first()
        existing_customer = Customer.query.filter_by(phone=phone).first()
        if existing_driver or existing_customer:
            return "This phone number is already used!", 400
        new_customer = Customer(name=name, age=age, phone=phone, password=password)
        db.session.add(new_customer)
        db.session.commit()
        session['customer_phone'] = new_customer.phone
        return render_template('customer_page.html')
    return render_template('register_c.html')

@app.route('/driver/log_in', methods=['GET', 'POST'])
def log_in_d():
    error = None
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        driver = Driver.query.filter_by(phone=phone, password=password).first()
        if driver:
            session.clear()
            session['driver_phone'] = driver.phone
            return redirect(url_for('driver_home'))
        else:
            error = "Incorrect login details!"
    return render_template('log_in_d.html', error=error)

@app.route('/driver_home')
def driver_home():
    return render_template('driver_page.html')



@app.route('/customer_home')
def customer_home():
    return render_template('customer_page.html')

@app.route('/customer/log_in', methods=['GET', 'POST'])
def log_in_c():
    error = None
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']
        customer = Customer.query.filter_by(phone=phone, password=password).first()
        if customer:
            session.clear()
            session['customer_phone'] = customer.phone
            return redirect(url_for('customer_home'))
        else:
            error = "Incorrect log-in details!"
    return render_template('log_in_c.html', error=error)


@app.route('/order', methods=['GET', 'POST'])
def ordering():
    if request.method == 'POST':
        if 'customer_phone' not in session:
            return "Please log in first!", 401
        customer = Customer.query.filter_by(phone=session['customer_phone']).first()
        from_location=request.form['from_location']
        to_location=request.form['to_location']
        new_order = Order_history(customer_name=customer.name, customer_phone=customer.phone,from_location=from_location, to_location=to_location)
        db.session.add(new_order)
        db.session.commit()
        return render_template('customer_page.html')
    return render_template('order.html')

@app.route('/my_data', methods=['GET'])
def my_data():
    if 'driver_phone' in session:
        user = Driver.query.filter_by(phone=session['driver_phone']).first()
        user_type = "Driver"
    elif 'customer_phone' in session:
        user = Customer.query.filter_by(phone=session['customer_phone']).first()
        user_type = "Customer"
    else:
        return "Please, log in first!", 401

    return render_template('data_page.html', user=user, user_type=user_type)

@app.route('/my_orders', methods=['GET'])
def my_orders():
    if 'customer_phone' not in session:
        return "Please, log in first!", 401
    
    customer_phone = session['customer_phone']
    orders = Order_history.query.filter_by(customer_phone=customer_phone).all()
    
    return render_template('my_orders.html', orders=orders)


@app.route('/order/accept', methods=['GET','POST'])
def accept_orders():
    if request.method=='POST':
        print("Session data:", session)
        if 'driver_phone' not in session:
            return "Please log in first", 401
    
        driver_phone = session['driver_phone']
        print("Driver phone from session:", driver_phone)

        driver = Driver.query.filter_by(phone=driver_phone).first()
    
        if not driver:
            return "Driver not found", 404

        order_id = request.form.get('order_id')
        print("Order ID received:", order_id)

        order = Order_history.query.filter_by(id=order_id).first()
    
        if order and order.status == "Waiting":
            order.status = "Closed"
            order.driver_phone = driver.phone

            db.session.commit()
            socketio.emit('order_accepted', {
                'order_id': order.id,
                'driver': driver.phone,
                'status': order.status
            }, to="*")

            print("Order updated:", order.id, order.status, order.driver_phone)

            return redirect(url_for('driver_home'))
    elif request.method=='GET':
        orders=Order_history.query.all()
        return render_template('accept_orders.html', orders=orders)

app.secret_key = "supersecretkey"
app.app_context().push()
db.create_all()
app.run(port=9000, debug=True, host='0.0.0.0')