import os
import pytest
from app import app, allowed_file, create_color_chart
from PIL import Image
import numpy as np

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Отключаем CSRF для тестов
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def test_image():
    # Создаем тестовое изображение 10x10 пикселей
    img = Image.new('RGB', (10, 10), color='red')
    yield img
    # Удаляем тестовые файлы после использования
    if os.path.exists('test_img.png'):
        os.remove('test_img.png')

def test_allowed_file():
    assert allowed_file('test.jpg') is True
    assert allowed_file('test.png') is True
    assert allowed_file('test.txt') is False
    assert allowed_file('no_extension') is False

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Добавление креста на изображение' in response.data

def test_invalid_file_upload(client):
    response = client.post('/', data={'file': (None, '')})
    assert response.status_code == 302  # Редирект при ошибке
    follow_redirect = client.get(response.headers['Location'])
    assert b'Не выбран файл' in follow_redirect.data

def test_color_chart_creation(test_image):
    # Сохраняем тестовое изображение
    test_image.save('test_img.png')
    
    # Проверяем функцию создания диаграммы
    with Image.open('test_img.png') as img:
        chart = create_color_chart(img)
        assert isinstance(chart, str)
        assert chart.startswith('iVBORw0KGgo')  # Проверяем base64 PNG

def test_missing_route(client):
    response = client.get('/nonexistent')
    assert response.status_code == 404