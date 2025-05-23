import os
import pytest
import tempfile
from io import BytesIO
from app import create_app, allowed_file

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    app.config['PROCESSED_FOLDER'] = tempfile.mkdtemp()
    
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner() 

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
    response = client.post('/', data={
        'file': (BytesIO(b''), ''),
        'cross_type': 'vertical',
        'cross_color': '#FF0000',
        'g-recaptcha-response': 'dummy'
    }, content_type='multipart/form-data')
    assert response.status_code == 200  # Теперь возвращает 200 с flash-сообщением
    assert b'Не выбран файл' in response.data

def test_missing_route(client):
    response = client.get('/nonexistent')
    assert response_status_code == 404