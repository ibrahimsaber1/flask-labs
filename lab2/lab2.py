from flask import Flask, render_template, url_for, redirect, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from functools import wraps
import base64


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///project.db"
app.secret_key = '123'
app.permanent_session_lifetime = timedelta(days=5)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    books = db.relationship('Book', backref='owner', lazy='select')

    def __init__(self, username, password, is_admin=False):
        self.username = username
        self.password = generate_password_hash(password)
        self.is_admin = is_admin

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    image = db.Column(db.LargeBinary, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __init__(self, title, author=None, image=None, user_id=None):
        self.title = title
        self.author = author
        self.image = image
        self.user_id = user_id

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in first!")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in first!")
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash("Unauthorized access!")
            return redirect(url_for('profile'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        is_admin = 'is_admin' in request.form  
        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('signup'))

        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists!")
            return redirect(url_for('signup'))

        new_user = User(username=username, password=password, is_admin=is_admin)
        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! Please login.")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Logged in successfully!")
            return redirect(url_for('profile'))
        else:
            flash("Invalid credentials!")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully!")
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user, books=user.books)

@app.route('/add-book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        image = request.files['image'].read() if 'image' in request.files else None
        
        if 'admin' in session and session['admin']:
           
            new_book = Book(title=title, author=author, image=image)
        else:
            new_book = Book(title=title, author=author, image=image, user_id=session['user_id'])
        
        db.session.add(new_book)
        db.session.commit()
        
        flash("Book added successfully!")
        if 'admin' in session and session['admin']:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('profile'))

    return render_template('add_book.html')

@app.route('/delete-book/<int:book_id>')
@login_required
def delete_book(book_id):
    book = Book.query.get(book_id)
    if book and book.owner.id == session['user_id']:
        db.session.delete(book)
        db.session.commit()
        flash("Book deleted successfully!")
    else:
        flash("You do not have permission to delete this book!")
    return redirect(url_for('profile'))

@app.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    users = User.query.all()
    books = Book.query.all()
    return render_template('admin_dashboard.html', users=users, books=books)

@app.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("User not found!")
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        user.username = request.form['username']
        if request.form['password']:
            user.password = generate_password_hash(request.form['password'])
        user.is_admin = 'is_admin' in request.form
        db.session.commit()
        flash(f"User {user.username} updated successfully!")
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/delete-user/<int:user_id>')
@admin_required
def admin_delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.username} deleted!")
    else:
        flash("User not found!")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit-book/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash("Book not found!")
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        if 'image' in request.files:
            book.image = request.files['image'].read()
        db.session.commit()
        flash(f"Book {book.title} updated successfully!")
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_edit_book.html', book=book)

@app.route('/admin/delete-book/<int:book_id>')
@admin_required
def admin_delete_book(book_id):
    book = Book.query.get(book_id)
    if book:
        db.session.delete(book)
        db.session.commit()
        flash(f"Book {book.title} deleted!")
    else:
        flash("Book not found!")
    return redirect(url_for('admin_dashboard'))

@app.route('/view-books')
@login_required
def view_books():
    books = Book.query.all()
    return render_template('view_books.html', books=books)

with app.app_context():
    db.create_all()

@app.template_filter('b64encode')
def b64encode_filter(image):
    return base64.b64encode(image).decode('utf-8')
if __name__ == "__main__":
    app.run(debug=True, port=5000)
