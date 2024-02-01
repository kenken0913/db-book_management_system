from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with your secret key
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    books = db.relationship('Book', backref='user', lazy=True)
    reading_logs = db.relationship('ReadingLog', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    author = db.Column(db.String(80), nullable=False)
    published_date = db.Column(db.String(80), nullable=False)
    isbn = db.Column(db.String(80), unique=True, nullable=False)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ReadingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_page = db.Column(db.Integer, nullable=False)
    end_page = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    book = db.relationship('Book', backref='reading_logs')

@app.route('/')
def index():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        books = Book.query.filter_by(user=user).all()
        logs = ReadingLog.query.filter_by(user=user).all()
        return render_template('index.html', books=books, logs=logs)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form['username'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            user = User.query.filter_by(username=request.form['username']).first()
            if user is None or not user.check_password(request.form['password']):
                return redirect(url_for('login'))  # ユーザー名またはパスワードが間違っている場合
            session['username'] = user.username
            return redirect(url_for('index'))
        return render_template('login.html')
    except Exception as e:
        return str(e)  # エラーメッセージを表示

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/add', methods=['POST'])
def add_book():
    user = User.query.filter_by(username=session['username']).first()
    book = Book(title=request.form['title'], author=request.form['author'], published_date=request.form['published_date'], isbn=request.form['isbn'], user=user)
    db.session.add(book)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_book(id):
    book = Book.query.get(id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_log/<int:book_id>', methods=['POST'])
def add_log(book_id):
    user = User.query.filter_by(username=session['username']).first()
    book = Book.query.get(book_id)
    log = ReadingLog(book_id=book.id, user_id=user.id, start_page=request.form['start_page'], end_page=request.form['end_page'], comment=request.form['comment'])
    db.session.add(log)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/log_detail/<int:log_id>')
def log_detail(log_id):
    log = ReadingLog.query.get(log_id)
    return render_template('log_detail.html', log=log)

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists('test.db'):  # データベースファイルが存在しない場合のみ初期化
            db.create_all()  # 新たにテーブルを作成
    app.run(debug=True)
