from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from flask_migrate import Migrate

# Инициализация Flask-Migrate


# Инициализация объектов
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meal_planner.db'  # Новая база данных
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)
# Модели данных

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    carbohydrates = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Recipe {self.name}>"



class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.String(50), nullable=False)  # Понедельник, Вторник и т.д.
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    recipe = db.relationship('Recipe', backref=db.backref('meals', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Связь с пользователем

    user = db.relationship('User', backref=db.backref('meals', lazy=True))  # Связь с пользователем

    def __repr__(self):
        return f"<Meal {self.name} on {self.day_of_week}>"


class ShoppingList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.Column(db.Text, nullable=False)

    user = db.relationship('User', backref=db.backref('shopping_lists', lazy=True))

    def __repr__(self):
        return f"<ShoppingList for {self.user.username}>"


# Функция загрузки пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Основные маршруты

# Основные маршруты

@app.route('/recipes', methods=['GET'])
@login_required
def recipes():
    recipes = Recipe.query.all()
    return render_template('recipe_list.html', recipes=recipes)

@app.route('/recipes/new', methods=['GET', 'POST'])
@login_required
def new_recipe():
    if request.method == 'POST':
        name = request.form['name']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        calories = request.form['calories']
        protein = request.form['protein']
        fat = request.form['fat']
        carbohydrates = request.form['carbohydrates']

        new_recipe = Recipe(
            name=name,
            ingredients=ingredients,
            instructions=instructions,
            calories=calories,
            protein=protein,
            fat=fat,
            carbohydrates=carbohydrates
        )
        db.session.add(new_recipe)
        db.session.commit()

        return redirect(url_for('recipes'))

    return render_template('new_recipe.html')


@app.route('/meals', methods=['GET', 'POST'])
@login_required
def meals():
    if request.method == 'POST':
        meal_name = request.form['meal_name']
        day_of_week = request.form['day_of_week']
        recipe_id = request.form['recipe_id']

        new_meal = Meal(name=meal_name, day_of_week=day_of_week, recipe_id=recipe_id, user_id=current_user.id)
        db.session.add(new_meal)
        db.session.commit()
        return redirect(url_for('meals'))

    recipes = Recipe.query.all()
    meals = Meal.query.all()
    return render_template('meal_plan.html', meals=meals, recipes=recipes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('recipes'))
        else:
            return 'Неверный логин или пароль', 401
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Стартовая страница
@app.route('/')
def index():
    if current_user.is_authenticated:
        recipes = Recipe.query.all()
        return render_template('recipe_list.html', recipes=recipes)
    return redirect(url_for('login'))

@app.route('/menu', methods=['GET', 'POST'])
@login_required
def menu():
    if request.method == 'POST':
        days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

        # Удаляем старые записи для текущего пользователя
        Meal.query.filter_by(user_id=current_user.id).delete()

        ingredients = set()

        # Перебираем все дни недели и обрабатываем данные для каждого дня
        for day in days_of_week:
            breakfast = request.form.get(f'{day}_breakfast')
            lunch = request.form.get(f'{day}_lunch')
            dinner = request.form.get(f'{day}_dinner')

            if breakfast:
                meal = Meal(name="Завтрак", day_of_week=day.capitalize(), recipe_id=breakfast, user_id=current_user.id)
                db.session.add(meal)
                recipe = Recipe.query.get(breakfast)
                if recipe:
                    ingredients.update([ingredient.strip() for ingredient in recipe.ingredients.split(',') if ingredient.strip()])

            if lunch:
                meal = Meal(name="Обед", day_of_week=day.capitalize(), recipe_id=lunch, user_id=current_user.id)
                db.session.add(meal)
                recipe = Recipe.query.get(lunch)
                if recipe:
                    ingredients.update([ingredient.strip() for ingredient in recipe.ingredients.split(',') if ingredient.strip()])

            if dinner:
                meal = Meal(name="Ужин", day_of_week=day.capitalize(), recipe_id=dinner, user_id=current_user.id)
                db.session.add(meal)
                recipe = Recipe.query.get(dinner)
                if recipe:
                    ingredients.update([ingredient.strip() for ingredient in recipe.ingredients.split(',') if ingredient.strip()])

        db.session.commit()

        return redirect(url_for('view_menu'))

    recipes = Recipe.query.all()
    return render_template('menu_creation.html', recipes=recipes)



@app.route('/view_menu')
@login_required
def view_menu():
    # Получаем все блюда для текущего пользователя
    meals = Meal.query.filter_by(user_id=current_user.id).all()

    # Сгруппируем блюда по дням недели
    weekly_menu = {'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': [], 'Friday': [], 'Saturday': [], 'Sunday': []}

    # Разбиваем блюда по дням недели
    for meal in meals:
        weekly_menu[meal.day_of_week].append(meal)

    # Отправляем данные в шаблон
    return render_template('view_menu.html', weekly_menu=weekly_menu)


@app.route('/choose_recipe', methods=['GET', 'POST'])
@login_required
def choose_recipe():
    recipes = Recipe.query.all()

    if request.method == 'POST':
        selected_recipe_id = request.form.get('recipe_id')
        return redirect(url_for('menu'))

    return render_template('choose_recipe.html', recipes=recipes)


@app.route('/analytics')
@login_required
def analytics():
    # Суммируем значения для всех рецептов в базе данных
    recipes = Recipe.query.all()

    total_calories = sum(recipe.calories for recipe in recipes)
    total_protein = sum(recipe.protein for recipe in recipes)
    total_fat = sum(recipe.fat for recipe in recipes)
    total_carbs = sum(recipe.carbohydrates for recipe in recipes)

    # Передаем вычисленные данные в шаблон
    return render_template('analytics.html',
                           total_calories=total_calories,
                           total_protein=total_protein,
                           total_fat=total_fat,
                           total_carbs=total_carbs)

# Запуск приложения
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
