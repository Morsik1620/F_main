import werkzeug
from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user, logout_user


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'False' # шифрования сессий, и без него ваши сессии будут небезопасными
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # куда перенаправлять пользователя, если он попытается получить доступ к странице

CARDS_PER_PAGE = 4  # Количество карточек на странице

class Card(db.Model):
    id = db.Column(db.Integer,  primary_key=True)
    title = db.Column(db.String(64), unique=True, nullable = False) # unique - уникальный, nullable - поле не должно быть пустым
    subtitle = db.Column(db.String(100), unique=True, nullable = False) # unique - уникальный, nullable - поле не должно быть пустым
    text = db.Column(db.String(220), unique=True, nullable = False) # unique - уникальный, nullable - поле не должно быть пустым

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer,  primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable = False) # unique - уникальный, nullable - поле не должно быть пустым
    password = db.Column(db.String(16), nullable = False)               # nullable - поле не должно быть пустым

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Users).get(user_id)

#--------------------------------------register-----------------------------------------------------------
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_hash = werkzeug.security.generate_password_hash(password) # шифрую пароль
        if username and password:
            users = Users(username = username, password = password_hash)  # заносим данные в БД Notes
            db.session.add(users)
            try:
                db.session.commit()
            except SQLAlchemy.exc.IntegrityError as e:
                return 'Такой пользователь уже есть'
            return redirect(url_for('login'))
    return render_template("F_register.html")

#--------------------------------------login-----------------------------------------------------------
@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        password = request.form['password']
        user = Users.query.filter_by(username = request.form['username']).first()
        if user is not None and werkzeug.security.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('F_login.html')
    return render_template('F_login.html')

@app.route('/protected')
@login_required
def protected():
    return "Protected area!  Logged in as: " + str(current_user.username)

#--------------------------------------index-----------------------------------------------------------
@app.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)  # Получаем номер страницы из запроса (по умолчанию 1)
    pagination = Card.query.paginate(page=page, per_page=CARDS_PER_PAGE)
    cards = pagination.items  # Получаем карточки для текущей страницы
# добавляю пустую карточку для добавления новой
    if page == pagination.page: # только на следующей странице
        cards.append(None)
    return render_template('F_index.html', cards=cards, pagination=pagination)

#------------------------------card_detail-----------------------------------------------------------------
@app.route('/card/<int:id>')
@login_required
def card(id):
    card = Card.query.get_or_404(id)  # Получаем карточку по ID или возвращаем 404, если не найдена
    return render_template('F_card_detail.html', card=card) # Отображает шаблон card_detail.html и передает ему карточку.

#-----------------------------------home------------------------------------------------------------------
@app.route('/home', methods=["GET", "POST"])
def home():
    return render_template("F_home.html")

#-----------------------------------form_create------------------------------------------------------------------
@app.route('/form_create', methods=['GET', 'POST'])
@login_required
def form_create():
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        text = request.form.get('text')
        new_card = Card(title=title, subtitle=subtitle, text=text)
        db.session.add(new_card)
        db.session.commit()
        return redirect(url_for('index'))# Перенаправляем на главную страницу
    else:
        return render_template('F_form_create.html')

#-----------------------------------logout------------------------------------------------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.secret_key = 'lol'
    app.run(debug=True)