import os
import json
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, flash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv

from utils.dicom_processor import DICOMProcessor
from utils.album_manager import AlbumManager
from utils.query_engine import QueryEngine
from database.db import DatabaseManager
from auth import AuthManager, User, auth_required, owner_required
from config import config
from cloud_storage import storage_manager
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Create Flask app with configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app = Flask(__name__)
app.config.from_object(config[config_name])
config[config_name].init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Configure logging
if not app.debug and config_name == 'production':
    os.makedirs('logs', exist_ok=True)
    
    file_handler = RotatingFileHandler('logs/dicom_explorer.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('DICOM Album Explorer startup')

# Initialize cloud storage
storage_manager.init_app(app)


# Ensure directories exist (backwards compatibility)
if not app.config.get('USE_CLOUD_STORAGE', False):
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    os.makedirs(app.config.get('ALBUMS_FOLDER', 'albums'), exist_ok=True)

# Initialize database and managers
db_manager = DatabaseManager(app.config.get('DATABASE_URL'))
auth_manager = AuthManager(db_manager)
album_manager = AlbumManager(db_manager=db_manager)

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return auth_manager.get_user_by_id(user_id)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('error.html', 
                         message='Page not found', 
                         error_code=404), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f'Internal server error: {error}')
    return render_template('error.html', 
                         message='Internal server error', 
                         error_code=500), 500

@app.errorhandler(403)
def access_denied(error):
    """Handle 403 errors"""
    return render_template('error.html', 
                         message='Access denied', 
                         error_code=403), 403

@app.errorhandler(413)
def file_too_large(error):
    """Handle file upload size errors"""
    return jsonify({'error': 'File too large. Maximum size is 100MB.'}), 413

current_dicom_data = None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        
        user, message = auth_manager.authenticate_user(username, password)
        
        if user:
            login_user(user, remember=remember_me)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash(message, 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Validate password strength
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        success, message = auth_manager.register_user(username, email, password)
        
        if success:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check endpoint for deployment platforms"""
    return jsonify({"status": "healthy", "app": "DICOM Album Explorer"}), 200

@app.route('/')
def index():
    """Main page with options to upload files or scan directory"""
    if app.config.get('ENABLE_USER_AUTH', True):
        if current_user.is_authenticated:
            # Show user's albums only
            albums = album_manager.get_user_albums(current_user.id)
        else:
            # Show public albums only
            albums = album_manager.get_public_albums()
    else:
        # Show all albums when auth is disabled
        albums = album_manager.get_all_albums()
    
    return render_template('index.html', albums=albums, user=current_user if current_user.is_authenticated else None)

@app.route('/upload', methods=['POST'])
@auth_required
def upload_files():
    """Handle file uploads"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    uploaded_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            uploaded_files.append(file_path)
    
    if not uploaded_files:
        return jsonify({'error': 'No valid DICOM files uploaded'}), 400
    
    
    file_data = []
    global current_dicom_data
    
    for file_path in uploaded_files:
        ds = DICOMProcessor.load_dicom_file(file_path)
        if ds is not None:
            metadata = DICOMProcessor.extract_metadata(ds)
            metadata['FilePath'] = file_path
            file_data.append(metadata)
    
    if file_data:
        current_dicom_data = pd.DataFrame(file_data)
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_files)} files',
            'file_count': len(uploaded_files)
        })
    else:
        return jsonify({'error': 'Could not process uploaded files'}), 400

@app.route('/scan', methods=['POST'])
@auth_required
def scan_directory():
    """Scan directory for DICOM files"""
    directory = request.form.get('directory')
    
    if not directory or not os.path.isdir(directory):
        return jsonify({'error': 'Invalid directory path'}), 400
    
    
    global current_dicom_data
    current_dicom_data = DICOMProcessor.scan_directory(directory)
    
    if current_dicom_data.empty:
        return jsonify({'error': 'No DICOM files found in directory'}), 404
    
    return jsonify({
        'success': True,
        'message': f'Found {len(current_dicom_data)} DICOM files',
        'file_count': len(current_dicom_data)
    })

@app.route('/metadata')
def show_metadata():
    """Show metadata of loaded DICOM files"""
    global current_dicom_data
    
    if current_dicom_data is None or current_dicom_data.empty:
        return jsonify({'error': 'No DICOM data loaded'}), 404
    
    
    sample = current_dicom_data.head(10).to_dict('records')
    
    
    fields = current_dicom_data.columns.tolist()
    fields.remove('FilePath') if 'FilePath' in fields else None
    
    return jsonify({
        'metadata_sample': sample,
        'total_files': len(current_dicom_data),
        'available_fields': fields
    })

@app.route('/query/simple', methods=['POST'])
def simple_query():
    """Perform simple query on loaded DICOM data"""
    global current_dicom_data
    
    if current_dicom_data is None or current_dicom_data.empty:
        return jsonify({'error': 'No DICOM data loaded'}), 404
    
    field = request.form.get('field')
    value = request.form.get('value')
    operator = request.form.get('operator', '=')
    
    if not field or value is None:
        return jsonify({'error': 'Field and value are required'}), 400
    
    results = QueryEngine.simple_query(current_dicom_data, field, value, operator)

    query_text = f"{field} {operator} {value}"
    db_manager.save_query_history(query_text, len(results))
    
    return jsonify({
        'success': True,
        'result_count': len(results),
        'results': results.head(100).to_dict('records') if not results.empty else [],
        'query': query_text
    })

@app.route('/query/advanced', methods=['POST'])
def advanced_query():
    """Perform advanced query on loaded DICOM data"""
    global current_dicom_data
    
    if current_dicom_data is None or current_dicom_data.empty:
        return jsonify({'error': 'No DICOM data loaded'}), 404
    
    try:
        data = request.get_json()
        query_conditions = data.get('conditions', [])
        join_operator = data.get('join_operator', 'AND')
        
        if not query_conditions:
            return jsonify({'error': 'No query conditions provided'}), 400

        results = QueryEngine.advanced_query(current_dicom_data, query_conditions, join_operator)

        query_text = QueryEngine.generate_query_summary(query_conditions, join_operator)
        

        db_manager.save_query_history(query_text, len(results))
        
        return jsonify({
            'success': True,
            'result_count': len(results),
            'results': results.head(100).to_dict('records') if not results.empty else [],
            'query': query_text
        })
    except Exception as e:
        return jsonify({'error': f'Query error: {str(e)}'}), 400

@app.route('/create_album', methods=['POST'])
@auth_required
def create_album():
    """Create album from query results"""
    global current_dicom_data
    
    if current_dicom_data is None or current_dicom_data.empty:
        return jsonify({'error': 'No DICOM data loaded'}), 404
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    # Use current user as creator if authenticated
    if current_user.is_authenticated:
        creator = current_user.username
        owner_id = current_user.id
    else:
        creator = request.form.get('creator', 'Anonymous')
        owner_id = None
    
    selected_files = request.form.getlist('selected_files')
    query_json = request.form.get('query_json')
    
    if selected_files:
        file_paths = selected_files
        album_id = album_manager.create_album(name, description, creator, file_paths=file_paths, owner_id=owner_id)
    elif query_json:
        try:
            query_data = json.loads(query_json)
            conditions = query_data.get('conditions', [])
            join_operator = query_data.get('join_operator', 'AND')
            
            query_results = QueryEngine.advanced_query(current_dicom_data, conditions, join_operator)
            
            album_id = album_manager.create_album(name, description, creator, query_results=query_results, owner_id=owner_id)
        except Exception as e:
            return jsonify({'error': f'Error creating album: {str(e)}'}), 400
    else:
        return jsonify({'error': 'No files selected for album'}), 400
    
    return jsonify({
        'success': True,
        'album_id': album_id,
        'redirect': url_for('view_album', album_id=album_id)
    })

@app.route('/album/<album_id>')
def view_album(album_id):
    """View a specific album"""
    album_metadata = album_manager.get_album_metadata(album_id)
    
    if album_metadata is None:
        return render_template('error.html', message='Album not found'), 404
    
    album_files = album_manager.get_album_files(album_id)
    
    return render_template(
        'album.html',
        album=album_metadata,
        files=album_files.to_dict('records') if album_files is not None and not album_files.empty else []
    )

@app.route('/album/<album_id>/image/<int:file_index>')
def get_album_image(album_id, file_index):
    """Get image data for a specific DICOM file in an album"""
    dicom_dataset = album_manager.get_dicom_file(album_id, file_index)
    
    if dicom_dataset is None:
        return jsonify({'error': 'File not found'}), 404
    
    window_center = request.args.get('windowCenter')
    window_width = request.args.get('windowWidth')
    
    image_data = DICOMProcessor.convert_to_image(
        dicom_dataset,
        window_center=float(window_center) if window_center else None,
        window_width=float(window_width) if window_width else None
    )
    
    if image_data is None:
        return jsonify({'error': 'Could not convert image'}), 500
    
    return jsonify({
        'success': True,
        'image_data': f"data:image/png;base64,{image_data}"
    })

@app.route('/album/<album_id>/file/<int:file_index>/download')
def download_dicom_file(album_id, file_index):
    """Download original DICOM file"""
    album_files = album_manager.get_album_files(album_id)
    
    if album_files is None or file_index >= len(album_files):
        return jsonify({'error': 'File not found'}), 404
    
    file_path = album_files.iloc[file_index]['AlbumFilePath']
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on disk'}), 404
    
    filename = os.path.basename(file_path)
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/dicom'
    )

@app.route('/album/<album_id>/delete', methods=['POST'])
@owner_required
def delete_album(album_id):
    """Delete an album"""
    success = album_manager.delete_album(album_id)
    
    if success:
        return jsonify({'success': True, 'redirect': url_for('index')})
    else:
        return jsonify({'error': 'Failed to delete album'}), 500

@app.route('/query_history')
def get_query_history():
    """Get query history"""
    history = db_manager.get_query_history()
    
    return jsonify({
        'success': True,
        'history': history
    })

@app.route('/advanced_query')
def advanced_query_page():
    """Show advanced query interface"""
    global current_dicom_data
    
    fields = []
    if current_dicom_data is not None and not current_dicom_data.empty:
        fields = current_dicom_data.columns.tolist()
        fields.remove('FilePath') if 'FilePath' in fields else None
    
    return render_template('advanced_query.html', fields=fields)

# Sharing routes
@app.route('/album/<album_id>/share', methods=['POST'])
@owner_required
def share_album(album_id):
    """Generate a shareable link for an album"""
    if not app.config.get('ENABLE_SHARING', True):
        return jsonify({'error': 'Sharing is not enabled'}), 403
    
    base_url = request.url_root.rstrip('/')
    share_url = album_manager.generate_share_link(album_id, base_url)
    
    if share_url:
        return jsonify({
            'success': True,
            'share_url': share_url,
            'message': 'Album is now publicly shareable!'
        })
    else:
        return jsonify({'error': 'Failed to generate share link'}), 500

@app.route('/album/<album_id>/toggle-public', methods=['POST'])
@owner_required
def toggle_album_public(album_id):
    """Toggle the public status of an album"""
    if not app.config.get('ENABLE_SHARING', True):
        return jsonify({'error': 'Sharing is not enabled'}), 403
    
    is_public = request.json.get('is_public') if request.is_json else None
    success = album_manager.toggle_album_public_status(album_id, is_public)
    
    if success:
        album = album_manager.get_album_metadata(album_id)
        return jsonify({
            'success': True,
            'is_public': album.get('is_public', False),
            'message': f'Album is now {"public" if album.get("is_public", False) else "private"}'
        })
    else:
        return jsonify({'error': 'Failed to update album status'}), 500

if __name__ == '__main__':
    app.run(debug=True)