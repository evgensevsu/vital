import unittest
from app import app, db, User, bcrypt
from flask import url_for

class FlaskTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Создаем тестовое приложение и тестовую базу данных
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Отключаем CSRF для тестов
        cls.client = app.test_client()

        # Создаем все таблицы для теста
        with app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        # Удаляем тестовую базу данных после тестов
        with app.app_context():
            db.drop_all()

    def test_login_page(self):
        # Проверка загрузки страницы входа
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход', response.data.decode('utf-8'))  # Проверка наличия текста "Вход"

    def test_login_invalid_user(self):
        # Тест для неверных данных входа
        response = self.client.post('/login', data=dict(
            username='wronguser',
            password='wrongpassword'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 401)  # Проверка статуса 401 для неверного входа
        self.assertIn('Неверный логин или пароль', response.data.decode('utf-8'))  # Проверка наличия ошибки

    def test_login_valid_user(self):
        # Создание тестового пользователя в контексте приложения
        with app.app_context():
            hashed_password = bcrypt.generate_password_hash('testpassword').decode('utf-8')
            user = User(username='testuser', password=hashed_password)
            db.session.add(user)
            db.session.commit()

        # Тест для правильных данных входа
        response = self.client.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Планировщик питания',
                      response.data.decode('utf-8'))  # Проверка наличия текста "Планировщик питания"

    def test_register_user(self):
        # Проверка регистрации нового пользователя
        response = self.client.post('/register', data=dict(
            username='newuser',
            password='newpassword'
        ), follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Вход', response.data.decode('utf-8'))  # После регистрации пользователь должен быть перенаправлен на страницу входа

if __name__ == '__main__':
    unittest.main()
