from flask import Flask, request, render_template, flash, redirect, url_for, send_from_directory
import os
import re
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv  # Add this import

load_dotenv()  # Load environment variables

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this-is-my-secret-key'  # Message flashing
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Get 'infra' environment variable
infra = os.getenv('infra')

# Set UPLOAD_FOLDER based on 'infra' variable
if infra == 'docker':
    app.config['UPLOAD_FOLDER'] = '/logs'
else:
    app.config['UPLOAD_FOLDER'] = 'uploads'

ALLOWED_EXTENSIONS = {'txt', 'csv', 'json', 'log'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Define base directories for each log type
LOG_DIRS = {
    'mysql': os.path.join(app.config['UPLOAD_FOLDER'], 'mysql'),
    'nginx': os.path.join(app.config['UPLOAD_FOLDER'], 'nginx'),
    'system': os.path.join(app.config['UPLOAD_FOLDER'], 'system')
}

# Create all required directories
for directory in LOG_DIRS.values():
    os.makedirs(directory, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_log_type(file_content):
    """Detect the type of log based on content patterns"""
    # Convert bytes to string if necessary
    if isinstance(file_content, bytes):
        content = file_content.decode('utf-8', errors='ignore')
    else:
        content = file_content

    # Check for MySQL slow query patterns
    if re.search(r'# Time:|# User@Host:|# Query_time:', content):
        return 'mysql'
    
    # Check for Nginx access log patterns (JSON format)
    if re.search(r'{"timestamp":.*"request_method":.*"request_uri":.*"status":', content):
        return 'nginx'
    
    # Check for system metrics patterns
    if re.search(r'(cpu_usage|memory_usage|disk_usage|network_in|network_out|load_average)\s+\d+', content):
        return 'system'
    
    return None

# Dashboard URLs mapping
DASHBOARD_URLS = {
    'mysql': "http://localhost:5601/app/dashboards#/view/8029e723-caa7-4bb0-93bd-eda0f1bebffa?embed=true&_g=(refreshInterval%3A(pause%3A!t%2Cvalue%3A60000)%2Ctime%3A(from%3A'2010-12-06T23%3A43%3A00.141Z'%2Cto%3Anow))&show-time-filter=true",
    'nginx': "http://localhost:5601/app/dashboards#/view/fdadd43f-5c66-4334-9fbe-d142dd837d00?embed=true&_g=(refreshInterval%3A(pause%3A!t%2Cvalue%3A60000)%2Ctime%3A(from%3Anow-15y%2Cto%3Anow))&show-time-filter=true",
    'system': "http://localhost:5601/app/dashboards#/view/85500e31-d06f-4eb6-89d8-0a00fdcfab90?embed=true&_g=(refreshInterval%3A(pause%3A!t%2Cvalue%3A60000)%2Ctime%3A(from%3Anow-15y%2Cto%3Anow))&show-time-filter=true"
}
@app.route('/dashboard')
def show_dashboard():
    dashboard_type = request.args.get('dashboard')
    if dashboard_type not in DASHBOARD_URLS:
        flash('Invalid dashboard selection')
        return redirect(url_for('upload_files'))
    
    dashboard_url = DASHBOARD_URLS[dashboard_type]
    return render_template('dashboard.html', dashboard_url=dashboard_url)

def parse_filename_date(filename):
    """Extract datetime from filename format: logtype-YYYYMMDD-HHMMSS.ext"""
    match = re.match(r'.*-(\d{8})-(\d{6})\..*', filename)
    if match:
        date_str, time_str = match.groups()
        try:
            return datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return "Unknown date"
    return "Unknown date"

def get_files_by_type():
    """Get all uploaded files organized by type with their upload dates"""
    files_by_type = {}
    for log_type, directory in LOG_DIRS.items():
        files = []
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                files.append({
                    'name': filename,
                    'datetime': parse_filename_date(filename)
                })
        files_by_type[log_type] = sorted(files, key=lambda x: x['datetime'], reverse=True)
    return files_by_type

@app.route('/history')
def upload_history():
    files_by_type = get_files_by_type()
    return render_template('history.html', files_by_type=files_by_type)

@app.route('/download/<log_type>/<filename>')
def download_file(log_type, filename):
    if log_type not in LOG_DIRS:
        flash('Invalid log type')
        return redirect(url_for('upload_history'))
    
    directory = LOG_DIRS[log_type]
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        # Check if any file was submitted
        if 'files[]' not in request.files:
            flash('No files selected')
            return redirect(request.url)
        
        files = request.files.getlist('files[]')
        
        # Check if any file was selected
        if not any(file.filename for file in files):
            flash('No files selected')
            return redirect(request.url)
        
        uploaded_files = []
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                # Read file content to detect type
                file_content = file.read()
                log_type = detect_log_type(file_content)
                
                if log_type:
                    # Reset file pointer to beginning
                    file.seek(0)
                    
                    # Get the appropriate directory
                    save_dir = LOG_DIRS[log_type]
                    
                    # Generate timestamp and create new filename
                    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                    original_ext = os.path.splitext(secure_filename(file.filename))[1]
                    new_filename = f"{log_type}-{timestamp}{original_ext}"
                    
                    file_path = os.path.join(save_dir, new_filename)
                    
                    # Save the file
                    file.save(file_path)
                    os.chmod(file_path, 0o777)  # Set permissions
                    uploaded_files.append(f"{new_filename} ({log_type})")
                else:
                    flash(f'Unable to determine log type for {file.filename}')
            else:
                if file.filename:
                    flash(f'Invalid file type for {file.filename}')
        
        if uploaded_files:
            flash(f'Successfully uploaded: {", ".join(uploaded_files)}')
        
        return redirect(url_for('upload_files'))
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)