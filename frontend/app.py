from flask import Flask, request, render_template, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this-is-my-secret-key'  # Message flashing
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'txt', 'csv', 'json', 'log'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Dashboard URLs mapping
DASHBOARD_URLS = {
    'mysql': "http://localhost:5601/app/dashboards#/view/8029e723-caa7-4bb0-93bd-eda0f1bebffa?embed=true&_g=(refreshInterval%3A(pause%3A!t%2Cvalue%3A60000)%2Ctime%3A(from%3A'2010-12-06T23%3A43%3A00.141Z'%2Cto%3Anow))",
    'nginx': 'http://localhost:5601/app/dashboards#/view/nginx-access-dashboard?embed=true&_g=(refreshInterval:(pause:!t,value:60000),time:(from:now-24h,to:now))&hide-filter-bar=true',
    'system': 'http://localhost:5601/app/dashboards#/view/8029e723-caa7-4bb0-93bd-eda0f1bebffa?embed=true&_g=(refreshInterval:(pause:!t,value:60000),time:(from:now-24h,to:now))&hide-filter-bar=true'
}
@app.route('/dashboard')
def show_dashboard():
    dashboard_type = request.args.get('dashboard')
    if dashboard_type not in DASHBOARD_URLS:
        flash('Invalid dashboard selection')
        return redirect(url_for('upload_files'))
    
    dashboard_url = DASHBOARD_URLS[dashboard_type]
    return render_template('dashboard.html', dashboard_url=dashboard_url)

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