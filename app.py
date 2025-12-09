import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from models import db, Project, Client, Contact, Subscriber
from PIL import Image  # For image cropping

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize DB
db.init_app(app)

# Create tables on first run
with app.app_context():
    db.create_all()

# --- HELPER: Image Cropping (Bonus Feature) ---
def save_and_crop_image(form_picture, target_size):
    """Resizes and crops image to target_size (width, height)"""
    random_hex = os.urandom(8).hex()
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/uploads', picture_fn)

    i = Image.open(form_picture)
    
    # Resize/Crop logic
    i.thumbnail(target_size) # Resize maintaining aspect ratio
    # Provide a white background if aspect ratio differs (simple approach)
    new_img = Image.new("RGB", target_size, (255, 255, 255))
    new_img.paste(i, ((target_size[0]-i.size[0])//2, (target_size[1]-i.size[1])//2))
    
    new_img.save(picture_path)
    return picture_fn

# --- ROUTES: Landing Page ---
@app.route('/')
def index():
    projects = Project.query.all()
    clients = Client.query.all()
    return render_template('index.html', projects=projects, clients=clients)

@app.route('/contact', methods=['POST'])
def contact():
    if request.method == 'POST':
        new_contact = Contact(
            full_name=request.form['full_name'],
            email=request.form['email'],
            mobile=request.form['mobile'],
            city=request.form['city']
        )
        db.session.add(new_contact)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('index'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form['email']
    if email:
        exists = Subscriber.query.filter_by(email=email).first()
        if not exists:
            new_sub = Subscriber(email=email)
            db.session.add(new_sub)
            db.session.commit()
            flash('Subscribed successfully!', 'success')
    return redirect(url_for('index'))

# --- ROUTES: Admin Panel ---
@app.route('/admin')
def admin_dashboard():
    contacts = Contact.query.all()
    subscribers = Subscriber.query.all()
    return render_template('admin_dashboard.html', contacts=contacts, subscribers=subscribers)

@app.route('/admin/add_project', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        pic = request.files['image']
        # Bonus: Crop Project Image to specific size? Let's say 450x350
        filename = save_and_crop_image(pic, (450, 350))
        
        project = Project(
            name=request.form['name'],
            description=request.form['description'],
            image_file=filename
        )
        db.session.add(project)
        db.session.commit()
        return redirect(url_for('index')) # Redirect to home to see changes
    return render_template('admin_project.html')

@app.route('/admin/add_client', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        pic = request.files['image']
        filename = save_and_crop_image(pic, (300, 300)) # Square for clients
        
        client = Client(
            name=request.form['name'],
            designation=request.form['designation'],
            description=request.form['description'],
            image_file=filename
        )
        db.session.add(client)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('admin_client.html')

if __name__ == '__main__':
    app.run(debug=True)