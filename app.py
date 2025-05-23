import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image, ImageDraw
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import requests
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config.from_object(config)

# Создаем папки для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_unique_filename(original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

def verify_recaptcha(response):
    if not response:
        return False
    try:
        result = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': app.config['RECAPTCHA_SECRET_KEY'],
                'response': response
            },
            timeout=5
        ).json()
        return result.get('success', False)
    except requests.RequestException:
        return False

def add_cross(img, cross_type, cross_color):
    draw = ImageDraw.Draw(img)
    width, height = img.size
    thickness = int(min(width, height) * 0.05)
    
    if cross_type == 'vertical':
        v_length = height * 0.8
        h_length = width * 0.5
    else:
        h_length = width * 0.8
        v_length = height * 0.5
    
    # Вертикальная линия
    v_x = width // 2
    draw.rectangle([
        (v_x - thickness//2, (height - v_length)//2),
        (v_x + thickness//2, (height + v_length)//2)
    ], fill=cross_color)
    
    # Горизонтальная линия
    draw.rectangle([
        ((width - h_length)//2, height//2 - thickness//2),
        ((width + h_length)//2, height//2 + thickness//2)
    ], fill=cross_color)
    
    return img

def create_color_chart(img):
    img = img.convert('RGB')
    pixels = np.array(img)
    colors, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
    total = pixels.shape[0] * pixels.shape[1]
    
    n_colors = min(10, len(colors))
    top_colors = colors[np.argsort(-counts)[:n_colors]]
    top_counts = counts[np.argsort(-counts)[:n_colors]]
    
    plt.figure(figsize=(8, 8))
    if n_colors > 0:
        labels = [f'#{r:02x}{g:02x}{b:02x}' for r, g, b in top_colors]
        colors_rgb = [(r/255, g/255, b/255) for r, g, b in top_colors]
        plt.pie(top_counts/total*100, labels=labels, colors=colors_rgb,
                autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Распределение цветов')
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not verify_recaptcha(request.form.get('g-recaptcha-response')):
            flash('Пройдите проверку reCAPTCHA', 'error')
            return redirect(request.url)
        
        if 'file' not in request.files:
            flash('Файл не загружен', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Не выбран файл', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                filename = generate_unique_filename(file.filename)
                original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                processed_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
                
                file.save(original_path)
                
                with Image.open(original_path) as img:
                    original_chart = create_color_chart(img.copy())
                    processed_img = add_cross(img.copy(), 
                                           request.form.get('cross_type', 'vertical'),
                                           request.form.get('cross_color', '#FF0000'))
                    processed_img.save(processed_path)
                    processed_chart = create_color_chart(processed_img)
                
                return render_template('results.html',
                    original_image=filename,
                    processed_image=filename,
                    original_chart=original_chart,
                    processed_chart=processed_chart)
            
            except Exception as e:
                flash(f'Ошибка обработки: {str(e)}', 'error')
                return redirect(request.url)
        
        flash('Допустимы только PNG, JPG, JPEG', 'error')
    
    return render_template('index.html', site_key=app.config['RECAPTCHA_SITE_KEY'])

if __name__ == '__main__':
    app.run(debug=True)