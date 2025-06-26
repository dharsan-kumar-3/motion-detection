from flask import Flask, render_template, request, url_for, redirect, session, flash, send_from_directory, send_file
import subprocess
import os
import pandas as pd
import base64
import hashlib
from datetime import datetime
import io
import zipfile

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key_here'  # Needed for session management

UPLOADS_ROOT = os.path.join(os.getcwd(), 'uploads')

USERS_FILE = os.path.join(os.getcwd(), 'users.xlsx')

# Ensure uploads directory exists
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Ensure users.xlsx exists
if not os.path.exists(USERS_FILE):
    df = pd.DataFrame(columns=['username', 'email', 'password', 'mobile_number'])
    df.to_excel(USERS_FILE, index=False)
else:
    # Ensure mobile_number column exists for robustness
    df = pd.read_excel(USERS_FILE)
    if 'mobile_number' not in df.columns:
        df['mobile_number'] = ''
        df.to_excel(USERS_FILE, index=False)

# Utility to get user-specific save directory
def get_user_save_dir():
    username = session.get('username')
    if not username:
        return UPLOADS_ROOT
    user_dir = os.path.join(UPLOADS_ROOT, username)
    screenshots_dir = os.path.join(user_dir, 'Screenshots')
    videos_dir = os.path.join(user_dir, 'Videos')
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(videos_dir, exist_ok=True)
    return user_dir

@app.route('/')
def landing():
    if 'username' in session:
        return redirect(url_for('home'))
    return render_template('landing.html')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('landing'))
    return render_template('home4.html', username=session.get('username'))

@app.route('/start_tracking', methods=['POST'])
def start_tracking():
    if request.method == 'POST':
        username = session.get('username', 'anonymous')
        mobile_number = session.get('mobile_number', '') # Get number from session
        subprocess.Popen(["python", "main.py", username, mobile_number])
    return "Tracking started!"

@app.route('/start_executing', methods=['POST'])
def start_executing():
    if request.method == 'POST':
        subprocess.Popen(["python", "main3.py"])
    return "Tracking started!"

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video_file' not in request.files:
        return 'No file part', 400
    file = request.files['video_file']
    if file.filename == '':
        return 'No selected file', 400
    user_dir = get_user_save_dir()
    save_path = os.path.join(user_dir, file.filename)
    file.save(save_path)
    username = session.get('username', 'anonymous')
    mobile_number = session.get('mobile_number', '') # Get number from session
    subprocess.Popen(["python", "main3.py", save_path, username, mobile_number])
    return redirect(url_for('results'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        mobile = request.form['mobile'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # --- Start of new validation ---
        if not all([username, email, mobile, password, confirm_password]):
            flash('All fields are required!')
            return render_template('Registration.html')
        # --- End of new validation ---

        if password != confirm_password:
            flash('Passwords do not match!')
            return render_template('Registration.html')

        # Encode username and email
        username_enc = base64.b64encode(username.encode('utf-8')).decode('utf-8')
        email_enc = base64.b64encode(email.encode('utf-8')).decode('utf-8')
        mobile_enc = base64.b64encode(mobile.encode('utf-8')).decode('utf-8')
        # Hash password
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        # Save to Excel
        df = pd.read_excel(USERS_FILE).fillna('')
        if (df['username'] == username_enc).any():
            flash('That username is already taken. Please choose another.')
            return render_template('Registration.html')
        if (df['email'] == email_enc).any():
            flash('That email is already registered. Please log in.')
            return render_template('Registration.html')
        new_row = pd.DataFrame([{'username': username_enc, 'email': email_enc, 'password': password_hash, 'mobile_number': mobile_enc}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(USERS_FILE, index=False)
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('Registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_identifier = request.form['username'].strip() # Can be username or email
        password = request.form['password']
        
        # --- Start of new validation ---
        if not all([login_identifier, password]):
            flash('All fields are required!')
            return render_template('login_page.html')
        # --- End of new validation ---

        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        df = pd.read_excel(USERS_FILE).fillna('')
        
        # Try to log in with username
        login_identifier_enc_user = base64.b64encode(login_identifier.encode('utf-8')).decode('utf-8')
        user_row = df[(df['username'] == login_identifier_enc_user) & (df['password'] == password_hash)]
        
        # If not found, try to log in with email
        if user_row.empty:
            login_identifier_enc_email = base64.b64encode(login_identifier.encode('utf-8')).decode('utf-8')
            user_row = df[(df['email'] == login_identifier_enc_email) & (df['password'] == password_hash)]

        if not user_row.empty:
            # Decode username to store in session
            username_enc = user_row.iloc[0]['username']
            username = base64.b64decode(username_enc).decode('utf-8')
            session['username'] = username

            # Decode and store mobile number in session
            mobile_enc = user_row.iloc[0]['mobile_number']
            if pd.notna(mobile_enc):
                session['mobile_number'] = base64.b64decode(mobile_enc).decode('utf-8')
            else:
                session['mobile_number'] = '' # Handle case where number is missing
            
            flash('Login successful!')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials!')
            return render_template('login_page.html')
    return render_template('login_page.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('mobile_number', None) # Also clear mobile number
    flash('You have been logged out.')
    return redirect(url_for('landing'))

@app.route('/select_save_location', methods=['GET', 'POST'])
def select_save_location():
    if request.method == 'POST':
        save_dir = request.form['save_dir']
        session['save_dir'] = save_dir
        return redirect(url_for('start_tracking'))
    return '''
        <form method="post">
            <label for="save_dir">Enter directory to save screenshots and video:</label>
            <input type="text" id="save_dir" name="save_dir" required style="width: 400px;">
            <button type="submit">Continue</button>
        </form>
    '''

@app.route('/results')
def results():
    user_dir = get_user_save_dir()
    screenshots_dir = os.path.join(user_dir, 'Screenshots')
    video_dir = os.path.join(user_dir, 'Videos')
    screenshots = []
    if os.path.exists(screenshots_dir):
        screenshots = sorted([f for f in os.listdir(screenshots_dir) if f.endswith('.png')], reverse=True)[:10]
    video_files = []
    if os.path.exists(video_dir):
        video_files = sorted([f for f in os.listdir(video_dir) if f.endswith('.mp4v') or f.endswith('.mp4')], reverse=True)
    return render_template('results.html', screenshots=screenshots, video_files=video_files, save_dir=user_dir)

@app.route('/show_screenshot/<filename>')
def show_screenshot(filename):
    user_dir = get_user_save_dir()
    screenshots_dir = os.path.join(user_dir, 'Screenshots')
    return send_from_directory(screenshots_dir, filename)

@app.route('/show_video/<filename>')
def show_video(filename):
    user_dir = get_user_save_dir()
    video_dir = os.path.join(user_dir, 'Videos')
    return send_from_directory(video_dir, filename)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please log in to view the dashboard.', 'info')
        return redirect(url_for('login'))

    username = session['username']
    user_dir = os.path.join(UPLOADS_ROOT, username)
    screenshots_dir = os.path.join(user_dir, 'Screenshots')
    videos_dir = os.path.join(user_dir, 'Videos')

    media_files = []
    
    # Collect and parse video files
    if os.path.exists(videos_dir):
        for fname in os.listdir(videos_dir):
            if fname.startswith('video_') and (fname.endswith('.mp4v') or fname.endswith('.mp4')):
                try:
                    ts_str = fname.replace('video_', '').rsplit('.', 1)[0]
                    dt = datetime.strptime(ts_str, '%Y-%m-%d_%H-%M-%S')
                    media_files.append({'type': 'video', 'datetime': dt, 'filename': fname})
                except ValueError:
                    continue # Skip files with bad timestamp format

    # Collect and parse screenshot files
    if os.path.exists(screenshots_dir):
        for fname in os.listdir(screenshots_dir):
            if fname.startswith('screenshot_') and fname.endswith('.png'):
                try:
                    ts_str = fname.replace('screenshot_', '').rsplit('.', 1)[0]
                    dt = datetime.strptime(ts_str, '%Y-%m-%d_%H-%M-%S')
                    media_files.append({'type': 'screenshot', 'datetime': dt, 'filename': fname})
                except ValueError:
                    continue # Skip files with bad timestamp format

    # Sort all media files by datetime
    media_files.sort(key=lambda x: x['datetime'])

    sessions = []
    current_session = None

    for media in media_files:
        if media['type'] == 'video':
            # A new video starts a new session.
            # First, save the previous session if it exists.
            if current_session:
                sessions.append(current_session)
            
            # Start a new session
            current_session = {
                'video': media['filename'],
                'screenshots': [],
                'datetime': media['datetime'].strftime('%B %d, %Y at %I:%M %p'),
                'location': user_dir # Not used in template, but good to have
            }
        elif media['type'] == 'screenshot' and current_session:
            # Add screenshot to the currently active session
            current_session['screenshots'].append(media['filename'])

    # Append the last session if it exists
    if current_session:
        sessions.append(current_session)

    # Sort sessions by datetime descending to show newest first
    sessions.sort(key=lambda x: datetime.strptime(x['datetime'], '%B %d, %Y at %I:%M %p'), reverse=True)

    return render_template('dashboard.html', username=username, sessions=sessions)

@app.route('/download_session/<session_datetime>')
def download_session(session_datetime):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user_dir = os.path.join(UPLOADS_ROOT, username)
    
    # Find the session data based on the datetime string
    # Note: This is a simplified search. A more robust app might use a unique session ID.
    dt_object = datetime.strptime(session_datetime, '%B %d, %Y at %I:%M %p')
    
    # Reconstruct filenames based on how they are created
    screenshots_dir = os.path.join(user_dir, 'Screenshots')
    videos_dir = os.path.join(user_dir, 'Videos')
    
    files_to_zip = []

    # Find the video file for the session
    for fname in os.listdir(videos_dir):
        if fname.startswith('video_'):
            try:
                ts_str = fname.replace('video_', '').rsplit('.', 1)[0]
                video_dt = datetime.strptime(ts_str, '%Y-%m-%d_%H-%M-%S')
                if video_dt.strftime('%B %d, %Y at %I:%M %p') == session_datetime:
                    files_to_zip.append(os.path.join(videos_dir, fname))
                    break # Assuming one video per session
            except ValueError:
                continue

    # Find screenshots for the session
    if files_to_zip: # Only look for screenshots if a video was found
        video_start_time = dt_object
        
        # Determine the end time for this session (start of the next video, or now)
        # This is a bit complex, for now we just grab all screenshots from that day.
        # A more robust solution is needed for multi-session days.
        for fname in os.listdir(screenshots_dir):
            if fname.startswith('screenshot_'):
                 try:
                    ts_str = fname.replace('screenshot_', '').rsplit('.', 1)[0]
                    ss_dt = datetime.strptime(ts_str, '%Y-%m-%d_%H-%M-%S')
                    if ss_dt.date() == video_start_time.date() and ss_dt >= video_start_time:
                         files_to_zip.append(os.path.join(screenshots_dir, fname))
                 except ValueError:
                    continue

    if not files_to_zip:
        flash('Could not find session files to download.', 'error')
        return redirect(url_for('dashboard'))

    # Create a zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in files_to_zip:
            zip_file.write(file_path, os.path.basename(file_path))
    
    zip_buffer.seek(0)
    
    zip_filename = f"session_{dt_object.strftime('%Y-%m-%d_%H-%M')}.zip"
    
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=zip_filename,
        mimetype='application/zip'
    )

if __name__ == '__main__':
    app.run(debug=True)

