import os
from flask import Flask, render_template, request, session
from PIL import Image, ImageDraw
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import requests

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Конфигурация reCAPTCHA v2
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')

def verify_recaptcha(token):
    data = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': token
    }
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
    return response.json().get('success', False)

def add_cross(image_stream, cross_type, color):
    img = Image.open(image_stream)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    if cross_type == 'vertical':
        draw.line((width//2, 0, width//2, height), fill=color, width=5)
        draw.line((0, height//2, width, height//2), fill=color, width=3)
    else:
        draw.line((0, height//2, width, height//2), fill=color, width=5)
        draw.line((width//2, 0, width//2, height), fill=color, width=3)
    
    return img

def create_color_distribution_plot(image_stream):
    img = Image.open(image_stream)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    pixels = np.array(img)
    r, g, b = pixels[:,:,0], pixels[:,:,1], pixels[:,:,2]
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    # Графики распределения цветов
    ax1.imshow(r, cmap='Reds')
    ax1.set_title('Red Channel')
    ax1.axis('off')
    
    ax2.imshow(g, cmap='Greens')
    ax2.set_title('Green Channel')
    ax2.axis('off')
    
    ax3.imshow(b, cmap='Blues')
    ax3.set_title('Blue Channel')
    ax3.axis('off')
    
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    plt.close()
    
    return base64.b64encode(buf.read()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not verify_recaptcha(request.form.get('g-recaptcha-response')):
            return render_template('index.html', 
                                site_key=RECAPTCHA_SITE_KEY,
                                error="Пожалуйста, пройдите проверку reCAPTCHA")
        
        if 'image' not in request.files:
            return render_template('index.html',
                                 site_key=RECAPTCHA_SITE_KEY,
                                 error="Не выбрано изображение")
        
        file = request.files['image']
        if file.filename == '':
            return render_template('index.html',
                                 site_key=RECAPTCHA_SITE_KEY,
                                 error="Не выбрано изображение")
        
        try:
            # Обработка изображения
            img_stream = BytesIO(file.read())
            original_plot = create_color_distribution_plot(BytesIO(img_stream.getvalue()))
            
            cross_type = request.form.get('cross_type', 'vertical')
            color = request.form.get('color', '#FF0000')
            
            processed_img = add_cross(BytesIO(img_stream.getvalue()), cross_type, color)
            
            # Сохранение результата
            processed_stream = BytesIO()
            processed_img.save(processed_stream, format='PNG')
            processed_plot = create_color_distribution_plot(BytesIO(processed_stream.getvalue()))
            
            # Кодирование для отображения
            processed_img_base64 = base64.b64encode(processed_stream.getvalue()).decode('utf-8')
            
            return render_template('index.html',
                                 site_key=RECAPTCHA_SITE_KEY,
                                 original_plot=original_plot,
                                 processed_img=processed_img_base64,
                                 processed_plot=processed_plot)
        
        except Exception as e:
            return render_template('index.html',
                                 site_key=RECAPTCHA_SITE_KEY,
                                 error=f"Ошибка обработки: {str(e)}")
    
    return render_template('index.html', site_key=RECAPTCHA_SITE_KEY)

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', False))