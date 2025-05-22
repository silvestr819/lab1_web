import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import config

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PROCESSED_FOLDER'] = 'static/processed'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Конфигурация reCAPTCHA
app.config['RECAPTCHA_SITE_KEY'] = config.RECAPTCHA_SITE_KEY
app.config['RECAPTCHA_SECRET_KEY'] = config.RECAPTCHA_SECRET_KEY

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def add_cross(image_path, cross_type, cross_color, output_path):
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    if cross_type == 'vertical':
        # Вертикальный крест (вертикальная линия длиннее)
        vertical_width = width // 3
        horizontal_width = height // 5
        
        # Вертикальная линия
        left = (width - vertical_width) // 2
        top = (height - horizontal_width) // 2
        right = left + vertical_width
        bottom = top + horizontal_width
        draw.rectangle([left, 0, right, height], fill=cross_color)
        
        # Горизонтальная линия
        left = 0
        top = (height - horizontal_width) // 2
        right = width
        bottom = top + horizontal_width
        draw.rectangle([left, top, right, bottom], fill=cross_color)
    else:
        # Горизонтальный крест (горизонтальная линия длиннее)
        vertical_width = width // 5
        horizontal_width = height // 3
        
        # Вертикальная линия
        left = (width - vertical_width) // 2
        top = (height - horizontal_width) // 2
        right = left + vertical_width
        bottom = top + horizontal_width
        draw.rectangle([left, 0, right, height], fill=cross_color)
        
        # Горизонтальная линия
        left = 0
        top = (height - horizontal_width) // 2
        right = width
        bottom = top + horizontal_width
        draw.rectangle([left, top, right, bottom], fill=cross_color)
    
    img.save(output_path)
    return img

def create_color_distribution_chart(image_path):
    img = Image.open(image_path)
    img = img.convert('RGB')
    pixels = list(img.getdata())
    
    # Получаем уникальные цвета и их количество
    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
    total_pixels = len(pixels)
    
    # Ограничиваем количество цветов до 10
    if len(unique_colors) > 10:
        # Берем 10 самых распространенных цветов
        sorted_indices = np.argsort(counts)[::-1][:10]
        unique_colors = unique_colors[sorted_indices]
        counts = counts[sorted_indices]
    
    # Преобразуем цвета в hex
    colors = [f'#{r:02x}{g:02x}{b:02x}' for r, g, b in unique_colors]
    percentages = [(count / total_pixels) * 100 for count in counts]
    
    # Создаем круговую диаграмму
    plt.figure(figsize=(8, 8))
    plt.pie(percentages, labels=colors, colors=colors, startangle=90)
    plt.axis('equal')
    plt.title('Color Distribution')
    
    # Сохраняем в буфер
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    # Преобразуем в base64
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    
    return image_base64

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Проверка reCAPTCHA
        if not verify_recaptcha(request.form.get('g-recaptcha-response')):
            flash('Пожалуйста, пройдите проверку reCAPTCHA', 'error')
            return redirect(url_for('index'))
        
        # Проверка загруженного файла
        if 'file' not in request.files:
            flash('Файл не загружен', 'error')
            return redirect(url_for('index'))
        
        file = request.files['file']
        if file.filename == '':
            flash('Не выбран файл', 'error')
            return redirect(url_for('index'))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(original_path)
            
            cross_type = request.form.get('cross_type')
            cross_color = request.form.get('cross_color')
            
            processed_filename = f'processed_{filename}'
            processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
            
            # Добавляем крест на изображение
            processed_img = add_cross(original_path, cross_type, cross_color, processed_path)
            
            # Создаем графики распределения цветов
            original_chart = create_color_distribution_chart(original_path)
            processed_chart = create_color_distribution_chart(processed_path)
            
            return render_template('results.html', 
                                 original_image=original_path, 
                                 processed_image=processed_path,
                                 original_chart=original_chart,
                                 processed_chart=processed_chart)
        else:
            flash('Недопустимый формат файла. Разрешены: png, jpg, jpeg', 'error')
    
    return render_template('index.html', site_key=app.config['RECAPTCHA_SITE_KEY'])

def verify_recaptcha(response):
    if not response:
        return False
    
    # Здесь должна быть реализация проверки reCAPTCHA через API Google
    # Для упрощения в учебных целях пропускаем реальную проверку
    return True

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['PROCESSED_FOLDER']):
        os.makedirs(app.config['PROCESSED_FOLDER'])
    app.run(debug=True)