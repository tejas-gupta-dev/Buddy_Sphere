from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user 
from sqlalchemy.exc import IntegrityError
#from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_BINDS'] = {
    'db2': 'sqlite:///Connection.db',
    'db1': 'sqlite:///message.db'
}
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home'

class user(UserMixin, db.Model):
    __tablename__ = 'user'
    email = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), unique=True, primary_key=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    des = db.Column(db.String(150), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    hobby = db.Column(db.String(150), nullable=False)
    hobby2 = db.Column(db.String(150), nullable=False)

    def get_id(self):
        return self.username

'''app.config['SQLALCHEMY_BINDS'] = {
    'db2': 'sqlite:///Connection.db'
}
db = SQLAlchemy(app)'''
#db2 = SQLAlchemy(app)

class Connection(db.Model):
    __bind_key__ = 'db2'
    id = db.Column(db.Integer, primary_key=True)
    user_username = db.Column(db.String(150),nullable=False)
    connected_user_username = db.Column(db.String(150), nullable=False)

# Message model
class message(db.Model):
    __bind_key__ = 'db1'
    id = db.Column(db.Integer, primary_key=True)
    sender_username = db.Column(db.String(150), nullable=False)
    receiver_username = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return user.query.get(user_id)

@app.route("/", methods=['POST','GET'])
def home():
    if request.method == "GET":
        User = user.query.all()
        connections = Connection.query.filter(
            (Connection.user_username == current_user.username) |
            (Connection.connected_user_username == current_user.username)
            ).all()

    return render_template("index.html", User=User, connections=connections)


@app.route("/signup", methods=['POST','GET'])
def sign_up():
    if request.method =='POST':
        email_=request.form.get('email')
        des_=request.form.get('des')
        username_=request.form.get('username')
        password_=request.form.get('password')
        city_=request.form.get('city')
        hobby_=request.form.get('hobby')
        hobby2_=request.form.get('hobby2')
        User = user.query.filter_by(email=email_).first()
        if User:
            flash("user already exist",category="error")
        elif len(email_)<6:
            flash("ENTER A VALID EMAIL",category='error')
        elif len(password_)<8:
             flash("PASSWORD MUST HAVE 8 CHARACTER",category='error')
        elif len(hobby_)<=3:
            flash("ENTER HOBBY IS MUST",category='error')
        elif len(hobby2_)<=3:
            flash("ENTER HOBBY2 IS MUST",category='error')
        elif len(city_)<=3:
            flash("ENTER CITY IS MUST",category='error')
        elif len(username_)<=3:
            flash("ENTER USERNAME IS MUST",category='error')
        else:
            try:
                new_user = user(email=email_, username=username_, password=password_, des=des_, city=city_, hobby=hobby_, hobby2=hobby2_)
                db.session.add(new_user)
                db.session.commit()
                User = user.query.filter_by(email=email_).first()
                login_user(User, remember=True)
                flash("ACCOUNT CREATED SUCCESSFULLY",category='success')
                return redirect(url_for('home'))
            except IntegrityError:
                db.session.rollback()

    return render_template("signup.html")

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html",User=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))




@app.route("/connected/<string:connected_user>", methods =['POST','GET'])
def connected(connected_user):
    if connected_user != current_user.username:
        new_connection = Connection(user_username = current_user.username,connected_user_username = connected_user)
        try:
            db.session.add(new_connection)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("You are already connected to this user.", category='error')
    return redirect(url_for('chat'))

@app.route("/chat", methods =['POST','GET'])
def chat():
    if request.method == 'GET':
        connection = Connection.query.filter(
            (Connection.user_username == current_user.username) |
            (Connection.connected_user_username == current_user.username)
            ).all()
    
    return render_template("chat.html" , connection=connection, Connection = Connection)


@app.route("/chat/<string:reciever>", methods =['POST','GET'])
def chatbox(reciever):
    if request.method == 'GET':
        msgget = message.query.filter(
            (message.sender_username == current_user.username) & 
            (message.receiver_username == reciever) |
            (message.sender_username == reciever) & 
            (message.receiver_username == current_user.username)
        ).all()

        incoming_message = request.args.get('message')
        if incoming_message:
            new_message = message(sender_username=current_user.username, receiver_username=reciever, message=incoming_message)
            db.session.add(new_message)
            db.session.commit()
            return redirect(url_for('chatbox', reciever=reciever))
    return render_template("chatbox.html", reciever=reciever, msgget=msgget)

@app.route("/chatbox", methods = ['POST', 'GET'])
def final():

    return render_template("chatbox.html")


@app.route("/login", methods=['POST','GET'])
def login():
    if request.method == 'POST':
        email_=request.form.get('email')
        password_=request.form.get('password')
        User = user.query.filter_by(email=email_).first()
        if User:
            if (password_==User.password):
                flash("logging success", category='success')
                login_user(User, remember=True)
                ''''if user:
                    login_user(User)
                    return redirect(url_for('profile'))'''
                return redirect(url_for('home'))
            else:
                flash("incorrect password", category='error')
        else:
            flash("email doesnot exist", category='error')


    return render_template("login.html",User=current_user)



if __name__ == '__main__':
    with app.app_context():
        db.create_all(bind_key= ['db2'])
        db.create_all(bind_key= ['db1'])
        db.create_all()  # Create database tables
    app.run(debug=True, port=3000)