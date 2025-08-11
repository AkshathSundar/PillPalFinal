import os
import logging
from datetime import datetime, time, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Configure upload settings
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage (replace with database in production)
users = {}  # {user_id: {email, password_hash, name}}
reminders = {}  # {user_id: [reminder_objects]}
voice_files = {}  # {user_id: [voice_file_objects]}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user():
    if 'user_id' in session:
        return users.get(session['user_id'])
    return None

def has_due_reminders(user_id):
    """Return True if user has any reminders due in the next 10 minutes."""
    now = datetime.now()
    soon = now + timedelta(minutes=10)
    user_reminders = reminders.get(user_id, [])
    for r in user_reminders:
        if not r.get('taken', False):
            try:
                reminder_time = datetime.strptime(r['time'], '%H:%M')
                # Replace date with today's date for accurate comparison
                reminder_time = reminder_time.replace(year=now.year, month=now.month, day=now.day)
            except Exception:
                continue
            if now <= reminder_time <= soon:
                return True
    return False

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_current_user()
    user_id = session['user_id']
    
    # Current time as string in HH:MM format (same format as reminder times)
    now_str = datetime.now().strftime('%H:%M')
    
    # Prepare today's reminders
    today_reminders = []
    due_reminders = []
    for reminder in reminders.get(user_id, []):
        # reminder['time'] expected as HH:MM string
        reminder_time = reminder['time']
        is_due = (reminder_time <= now_str) and (not reminder.get('taken', False))
        reminder['is_due'] = is_due
        # Format time display e.g. 09:00 AM
        reminder['time_display'] = datetime.strptime(reminder_time, '%H:%M').strftime('%I:%M %p')
        today_reminders.append(reminder)
        if is_due:
            due_reminders.append(reminder)
    
    # Sort reminders by time ascending
    today_reminders.sort(key=lambda r: r['time'])
    
    user_voice_files = voice_files.get(user_id, [])
    
    return render_template('dashboard.html',
                           user=user,
                           reminders=today_reminders,
                           due_reminders=due_reminders,
                           voice_files=user_voice_files)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')

        # Find user by email
        user_id = None
        for uid, user_data in users.items():
            if user_data['email'] == email:
                user_id = uid
                break

        if user_id and check_password_hash(users[user_id]['password_hash'], password):
            session['user_id'] = user_id
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not all([name, email, password, confirm_password]):
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')

        # Check if email already exists
        for user_data in users.values():
            if user_data['email'] == email:
                flash('Email already registered. Please use a different email.', 'error')
                return render_template('register.html')

        # Create new user
        user_id = str(uuid.uuid4())
        users[user_id] = {
            'name': name,
            'email': email,
            'password_hash': generate_password_hash(password),
            'caretaker_name': request.form.get('caretaker_name', '').strip(),
            'caretaker_number': request.form.get('caretaker_number', '').strip()

        }

        # Initialize user data
        reminders[user_id] = []
        voice_files[user_id] = []

        session['user_id'] = user_id
        flash('Account created successfully! Welcome to PillPal.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/add_reminder', methods=['GET', 'POST'])
def add_reminder():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        medication_name = request.form.get('medication_name', '').strip()
        dosage = request.form.get('dosage', '').strip()
        reminder_time = request.form.get('time', '')
        voice_file_id = request.form.get('voice_file', '')

        if not all([medication_name, dosage, reminder_time]):
            flash('Please fill in all required fields.', 'error')
            return render_template('add_reminder.html', voice_files=voice_files.get(user_id, []))

        # Create reminder
        reminder = {
            'id': str(uuid.uuid4()),
            'medication_name': medication_name,
            'dosage': dosage,
            'time': reminder_time,
            'voice_file_id': voice_file_id if voice_file_id else None,
            'taken': False,
            'created_at': datetime.now().isoformat()
        }

        if user_id not in reminders:
            reminders[user_id] = []

        reminders[user_id].append(reminder)
        flash('Reminder added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_reminder.html', voice_files=voice_files.get(user_id, []))

@app.route('/upload_voice', methods=['GET', 'POST'])
def upload_voice():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        name = request.form.get('name', '').strip()

        if 'voice_file' not in request.files:
            flash('No file selected.', 'error')
            return render_template('upload_voice.html')

        file = request.files['voice_file']

        if file.filename == '':
            flash('No file selected.', 'error')
            return render_template('upload_voice.html')

        if not name:
            flash('Please provide a name for this voice recording.', 'error')
            return render_template('upload_voice.html')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{user_id}_{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            voice_file_record = {
                'id': str(uuid.uuid4()),
                'name': name,
                'filename': unique_filename,
                'original_filename': filename,
                'uploaded_at': datetime.now().isoformat()
            }

            if user_id not in voice_files:
                voice_files[user_id] = []

            voice_files[user_id].append(voice_file_record)
            flash('Voice recording uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid file type. Please upload an MP3, WAV, OGG, or M4A file.', 'error')

    return render_template('upload_voice.html')

@app.route('/mark_taken/<reminder_id>')
def mark_taken(reminder_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Find and update reminder
    for reminder in reminders.get(user_id, []):
        if reminder['id'] == reminder_id:
            reminder['taken'] = True
            reminder['taken_at'] = datetime.now().isoformat()
            flash('Medication marked as taken!', 'success')
            break
    else:
        flash('Reminder not found.', 'error')

    return redirect(url_for('dashboard'))

@app.route('/delete_reminder/<reminder_id>')
def delete_reminder(reminder_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Find and remove reminder
    user_reminders = reminders.get(user_id, [])
    reminders[user_id] = [r for r in user_reminders if r['id'] != reminder_id]

    flash('Reminder deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/play_voice/<voice_file_id>')
def play_voice(voice_file_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Find voice file
    for voice_file in voice_files.get(user_id, []):
        if voice_file['id'] == voice_file_id:
            return send_from_directory(app.config['UPLOAD_FOLDER'], voice_file['filename'])

    flash('Voice file not found.', 'error')
    return redirect(url_for('dashboard'))

user_messages = []

@app.route("/community", methods=["GET", "POST"])
def community():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = get_current_user()

    if request.method == "POST":
        msg = request.form.get("message", "").strip()
        if msg:
            # Append a dict with username and message
            user_messages.append({
                "username": user['name'] if user else "Anonymous",
                "message": msg
            })
        return redirect(url_for("community"))

    return render_template("community.html", user_messages=user_messages, user=user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)