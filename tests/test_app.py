import pytest
from app import app, allowed_file

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_allowed_file():
    assert allowed_file('test.jpg') is True
    assert allowed_file('test.png') is True
    assert allowed_file('test.txt') is False

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Добавление креста на изображение' in response.data

def test_upload_invalid_file(client):
    response = client.post('/', data={'file': (None, '')})
    assert b'Не выбран файл' in response.data