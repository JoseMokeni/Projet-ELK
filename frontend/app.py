from flask import Flask, request, render_template, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Required for flashing messages
app.config['UPLOAD_FOLDER'] = 'uploads'  # Directory to store uploaded files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}  # Allowed file extensions

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            if file and file.filename:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # Save the file
                    file.save(file_path)
                    uploaded_files.append(filename)
                else:
                    flash(f'Invalid file type for {file.filename}')
        
        if uploaded_files:
            # chmod 777 the uploaded files
            os.chmod(app.config['UPLOAD_FOLDER'], 0o777)
            flash(f'Successfully uploaded: {", ".join(uploaded_files)}')
        
        return redirect(url_for('upload_files'))
    
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)