from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
import json
import logging
import sys
import io
import csv
from flask import Response
from werkzeug.utils import secure_filename
import time
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed from DEBUG to INFO to reduce verbosity
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            'app.log',
            maxBytes=1024 * 1024,  # 1MB per file
            backupCount=3,  # Keep up to 3 backup files
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')

# Database configuration
if 'pythonanywhere' in os.environ.get('HOSTNAME', '').lower():
    # PythonAnywhere database path
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/yourusername/ngo_events_cursor/events.db'
else:
    # Local database path
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600  # Recycle connections after 1 hour
app.config['SQLALCHEMY_POOL_SIZE'] = 5  # Maximum number of connections
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# File upload configuration
if 'pythonanywhere' in os.environ.get('HOSTNAME', '').lower():
    UPLOAD_FOLDER = '/home/yourusername/ngo_events_cursor/static/uploads/eposters'
else:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'eposters')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB limit for uploads
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    try:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    finally:
        # Ensure we don't keep filename in memory
        filename = None

# Add a function to check file size
def allowed_file_size(file):
    try:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)  # Reset file pointer
        return size <= MAX_UPLOAD_SIZE
    except Exception:
        return False

@app.before_request
def log_request_info():
    # Only log non-GET requests or requests with specific paths
    if request.method != 'GET' or request.path.startswith('/api/'):
        logger.info(f"Request: {request.method} {request.path}")
        if request.method in ['POST', 'PUT', 'DELETE']:
            logger.debug(f"Request Body: {request.get_data()}")

@app.after_request
def log_response_info(response):
    # Only log non-200 responses or responses from API endpoints
    if response.status_code != 200 or request.path.startswith('/api/'):
        logger.info(f"Response: {request.method} {request.path} - Status: {response.status_code}")
    return response

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

@app.errorhandler(413)
def request_entity_too_large(e):
    logger.warning("File upload too large")
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'File too large',
            'message': 'The uploaded file exceeds the maximum allowed size'
        }), 413
    flash('The uploaded file is too large. Maximum size is 16MB.', 'danger')
    return redirect(request.referrer or url_for('dashboard'))

@app.errorhandler(403)
def forbidden_error(e):
    logger.error("403 Forbidden Error - %s %s - User: %s", 
                 request.method, 
                 request.path, 
                 current_user.get_id() if not current_user.is_anonymous else 'Anonymous')
    
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    flash('You do not have permission to access this page.', 'danger')
    return redirect(url_for('login'))

@app.errorhandler(405)
def method_not_allowed(e):
    logger.error("405 Method Not Allowed - %s %s", request.method, request.path)
    return jsonify({
        'error': 'Method not allowed',
        'message': f'The method {request.method} is not allowed for this endpoint'
    }), 405

@app.errorhandler(404)
def page_not_found(e):
    logger.error("404 Not Found - %s %s", request.method, request.path)
    
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found'
        }), 404
    
    flash('The requested page was not found.', 'danger')
    return redirect(url_for('dashboard'))

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

print("Initializing Event Management System...")

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, coordinator, volunteer
    phone = db.Column(db.String(20))
    company = db.Column(db.String(120))
    preferences = db.Column(db.Text)  # JSON string for user preferences
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    events_organized = db.relationship('Event', backref='organizer', lazy=True)
    registrations = db.relationship('EventRegistration', backref='user', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50), nullable=False)  # conference, seminar, annual_dinner etc.
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    capacity = db.Column(db.Integer)
    eposter = db.Column(db.String(255))  # Store the path to the uploaded eposter
    registrations = db.relationship('EventRegistration', backref='event', lazy=True)

class EventRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, cancelled
    payment_status = db.Column(db.Boolean, default=False)
    special_requests = db.Column(db.Text)

class EventComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref='comments')
    event = db.relationship('Event', backref='comments')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    logger.debug("\n=== Index Route ===")
    try:
        logger.debug("Attempting to render index page")
        logger.debug(f"User authenticated: {current_user.is_authenticated}")
        logger.debug(f"Request headers: {dict(request.headers)}")
        logger.debug(f"Request method: {request.method}")
        logger.debug(f"Request path: {request.path}")
        logger.debug(f"Request remote addr: {request.remote_addr}")
        
        # Test database connection
        try:
            db.session.query(User).first()
            logger.debug("Database connection successful")
        except Exception as db_error:
            logger.error(f"Database connection error: {str(db_error)}")
            return "Database connection error", 500

        # Test template rendering
        try:
            return render_template('index.html')
        except Exception as template_error:
            logger.error(f"Template rendering error: {str(template_error)}")
            return f"Template error: {str(template_error)}", 500
            
    except Exception as e:
        logger.error(f"Unexpected error in index route: {str(e)}")
        return f"Server error: {str(e)}", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    print("\n=== Login Route ===")
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        print(f"Login attempt for email: {email}")
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            print(f"Login successful for user: {user.name} (Role: {user.role})")
            flash('Welcome back! You are logged in as ' + user.name, 'success')
            return redirect(url_for('dashboard'))
        
        print("Login failed: Invalid credentials")
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    print("\n=== Registration Route ===")
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        role = request.form.get('role')
        
        print(f"Registration attempt - Name: {name}, Email: {email}, Role: {role}")
        
        if User.query.filter_by(email=email).first():
            print(f"Registration failed: Email {email} already exists")
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            email=email,
            name=name,
            password=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        print(f"Registration successful - User ID: {user.id}")
        flash('Registration successful', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if current_user.role not in ['admin', 'coordinator']:
        flash('You do not have permission to create events.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            eposter_path = None
            
            if 'eposter' in request.files:
                file = request.files['eposter']
                try:
                    if file and file.filename:
                        if not allowed_file(file.filename):
                            flash('Invalid file type. Allowed types are: png, jpg, jpeg, gif, webp', 'danger')
                            return render_template('create_event.html')
                        
                        if not allowed_file_size(file):
                            flash('File size exceeds the maximum limit of 5MB', 'danger')
                            return render_template('create_event.html')
                        
                        filename = secure_filename(file.filename)
                        filename = f"{int(time.time())}_{filename}"
                        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        
                        try:
                            file.save(save_path)
                            eposter_path = f"uploads/eposters/{filename}"
                        except Exception as save_error:
                            logger.error("Failed to save file: %s", str(save_error))
                            flash('Failed to save the uploaded file', 'danger')
                            return render_template('create_event.html')
                finally:
                    # Ensure file object is closed and memory is freed
                    if 'file' in locals():
                        file.close()
                        del file

            try:
                event = Event(
                    title=request.form['title'],
                    description=request.form['description'],
                    event_type=request.form['event_type'],
                    date=datetime.fromisoformat(request.form['date'].replace('Z', '+00:00')),
                    location=request.form['location'],
                    capacity=int(request.form['capacity']),
                    organizer_id=current_user.id,
                    eposter=eposter_path
                )
                
                db.session.add(event)
                db.session.commit()
                
                flash('Event created successfully!', 'success')
                return redirect(url_for('dashboard'))
                
            except ValueError as ve:
                if "fromisoformat" in str(ve):
                    flash("Please enter a valid date and time", 'danger')
                else:
                    flash("Please check your input values", 'danger')
                return render_template('create_event.html')
                
            except Exception as e:
                logger.error("Failed to create event: %s", str(e))
                flash('Failed to create event. Please try again.', 'danger')
                return render_template('create_event.html')
                
        except Exception as e:
            db.session.rollback()
            logger.error("Error in create_event: %s", str(e))
            flash('An unexpected error occurred. Please try again.', 'danger')
            return render_template('create_event.html')
            
        finally:
            # Ensure we clean up any temporary data
            db.session.remove()
    
    return render_template('create_event.html')

@app.route('/event/<int:event_id>')
@login_required
def event_details(event_id):
    try:
        # Optimize query with joins to load all needed data at once
        event = db.session.query(Event).options(
            db.joinedload(Event.organizer),
            db.joinedload(Event.registrations),
            db.joinedload(Event.comments).joinedload(EventComment.user)
        ).filter(Event.id == event_id).first_or_404()
        
        is_registered = any(reg.user_id == current_user.id for reg in event.registrations)
        
        return render_template('event_details.html', 
                             event=event, 
                             is_registered=is_registered)
    except Exception as e:
        logger.error("Error fetching event details: %s", str(e))
        flash('Failed to load event details', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        db.session.remove()

# API Routes
@app.route('/api/events/upcoming')
def get_upcoming_events():
    try:
        current_time = datetime.utcnow()
        
        # Use query optimization to reduce memory usage
        events = db.session.query(
            Event.id,
            Event.title,
            Event.description,
            Event.date,
            Event.location,
            Event.capacity,
            db.func.count(EventRegistration.id).label('registration_count')
        ).outerjoin(
            EventRegistration
        ).filter(
            Event.date >= current_time
        ).group_by(
            Event.id
        ).order_by(Event.date).all()
        
        logger.info("Found %d upcoming events", len(events))
        
        result = [{
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': event.date.isoformat(),
            'location': event.location,
            'capacity': event.capacity,
            'registered_count': event.registration_count,
            'is_registered': False  # Default value for anonymous users
        } for event in events]
        
        # Only check registration status for authenticated users
        if not current_user.is_anonymous:
            user_registrations = set(
                db.session.query(EventRegistration.event_id).filter(
                    EventRegistration.user_id == current_user.id,
                    EventRegistration.event_id.in_([e['id'] for e in result])
                ).all()
            )
            
            for event in result:
                event['is_registered'] = (event['id'],) in user_registrations
        
        return jsonify({'events': result})
        
    except Exception as e:
        logger.error("Error fetching upcoming events: %s", str(e))
        return jsonify({'error': 'Failed to fetch events'}), 500
    finally:
        db.session.remove()

@app.route('/api/events/managed')
@login_required
def get_managed_events():
    try:
        if current_user.role not in ['admin', 'coordinator']:
            logger.warning("Unauthorized access attempt to managed events by user %s", current_user.name)
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Use optimized query with joins
        events = db.session.query(
            Event.id,
            Event.title,
            Event.description,
            Event.date,
            Event.location,
            Event.capacity,
            db.func.count(EventRegistration.id).label('registration_count')
        ).outerjoin(
            EventRegistration
        ).filter(
            Event.organizer_id == current_user.id
        ).group_by(
            Event.id
        ).order_by(Event.date.desc()).all()
        
        logger.info("Found %d managed events for user %s", len(events), current_user.name)
        
        return jsonify({
            'events': [{
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'date': event.date.isoformat(),
                'location': event.location,
                'capacity': event.capacity,
                'registered_count': event.registration_count
            } for event in events]
        })
        
    except Exception as e:
        logger.error("Error fetching managed events: %s", str(e))
        return jsonify({'error': 'Failed to fetch events'}), 500
    finally:
        db.session.remove()

@app.route('/api/events', methods=['POST'])
@login_required
def create_event_api():
    print("\n=== Create Event API ===")
    print(f"Request from user: {current_user.name} (ID: {current_user.id})")
    print(f"Request Method: {request.method}")
    print(f"Content Type: {request.content_type}")
    print(f"Request Data: {request.get_json()}")
    
    try:
        if current_user.role not in ['admin', 'coordinator']:
            print("Error: Insufficient permissions")
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        print(f"Processing event data: {data}")
        
        # Validate required fields
        required_fields = ['title', 'description', 'event_type', 'date', 'location', 'capacity']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            print(f"Error: Missing required fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        print("All required fields present, creating event")
        event = Event(
            title=data['title'],
            description=data['description'],
            event_type=data['event_type'],
            date=datetime.fromisoformat(data['date'].replace('Z', '+00:00')),
            location=data['location'],
            capacity=data['capacity'],
            organizer_id=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        print(f"Event created successfully with ID: {event.id}")
        
        return jsonify({
            'message': 'Event created successfully',
            'event_id': event.id
        }), 201
        
    except Exception as e:
        print(f"Error creating event: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Registration Management
@app.route('/api/registrations/<int:registration_id>/status', methods=['PUT'])
@login_required
def update_registration_status(registration_id):
    if current_user.role not in ['admin', 'coordinator']:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        if 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400

        registration = EventRegistration.query.get_or_404(registration_id)
        event = Event.query.get(registration.event_id)

        if current_user.role == 'coordinator' and event.organizer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        if data['status'] == 'deleted':
            db.session.delete(registration)
        else:
            registration.status = data['status']
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Registration {data["status"]} successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/<int:event_id>/registrations/export')
@login_required
def export_registrations(event_id):
    if current_user.role not in ['admin', 'coordinator']:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        event = Event.query.get_or_404(event_id)
        if current_user.role == 'coordinator' and event.organizer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Name', 'Email', 'Registration Date', 'Status'])

        for reg in event.registrations:
            writer.writerow([
                reg.user.name,
                reg.user.email,
                reg.registration_date.strftime('%Y-%m-%d %H:%M'),
                reg.status
            ])

        # Create response
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=registrations_{event_id}.csv'
            }
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/<int:event_id>/register', methods=['POST'])
@login_required
def register_for_event(event_id):
    logger.debug(f"\n=== Event Registration API - Event ID: {event_id} ===")
    logger.debug(f"User: {current_user.name} (ID: {current_user.id})")
    logger.debug(f"Request Method: {request.method}")
    logger.debug(f"Request Headers: {dict(request.headers)}")
    
    try:
        # Get the event
        event = Event.query.get_or_404(event_id)
        logger.debug(f"Found event: {event.title}")
        
        # Check if user is already registered
        existing_registration = EventRegistration.query.filter_by(
            event_id=event_id,
            user_id=current_user.id
        ).first()
        
        if existing_registration:
            logger.debug(f"User {current_user.name} is already registered for this event")
            return jsonify({
                'error': 'You are already registered for this event'
            }), 400
        
        # Check event capacity
        if len(event.registrations) >= event.capacity:
            logger.debug("Event is at full capacity")
            return jsonify({
                'error': 'This event is already full'
            }), 400
        
        # Create registration
        registration = EventRegistration(
            event_id=event_id,
            user_id=current_user.id,
            status='approved'  # Auto-approve for now
        )
        
        db.session.add(registration)
        db.session.commit()
        
        logger.debug(f"Successfully registered user {current_user.name} for event {event.title}")
        return jsonify({
            'success': True,
            'message': 'Successfully registered for the event'
        }), 201
        
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Failed to register for the event'
        }), 500

@app.route('/api/registrations')
@login_required
def get_user_registrations():
    try:
        # Optimize query with joins
        registrations = db.session.query(
            EventRegistration.status,
            Event.id,
            Event.title,
            Event.date
        ).join(
            Event
        ).filter(
            EventRegistration.user_id == current_user.id
        ).all()
        
        return jsonify({
            'registrations': [{
                'event': {
                    'id': reg.id,
                    'title': reg.title,
                    'date': reg.date.isoformat()
                },
                'status': reg.status
            } for reg in registrations]
        })
    except Exception as e:
        logger.error("Error fetching user registrations: %s", str(e))
        return jsonify({'error': 'Failed to fetch registrations'}), 500
    finally:
        db.session.remove()

@app.route('/api/users')
@login_required
def get_users():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    
    return jsonify({
        'users': [{
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.isoformat()
        } for user in users]
    })

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    logger.debug(f"\n=== Delete User API - User ID: {user_id} ===")
    logger.debug(f"User: {current_user.name} (ID: {current_user.id}, Role: {current_user.role})")
    
    try:
        if current_user.role != 'admin':
            logger.error(f"Unauthorized deletion attempt by user {current_user.name}")
            return jsonify({'error': 'Unauthorized'}), 403
        
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return jsonify({'error': 'User not found'}), 404
            
        if user.id == current_user.id:
            logger.error("Attempt to delete own account")
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Delete user's registrations first to avoid foreign key constraints
        EventRegistration.query.filter_by(user_id=user.id).delete()
        
        # Delete user's events and their registrations
        events = Event.query.filter_by(organizer_id=user.id).all()
        for event in events:
            EventRegistration.query.filter_by(event_id=event.id).delete()
            db.session.delete(event)
        
        # Delete user's comments
        EventComment.query.filter_by(user_id=user.id).delete()
        
        # Finally delete the user
        db.session.delete(user)
        db.session.commit()
        logger.debug(f"User {user.name} deleted successfully")
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Failed to delete user: {str(e)}'}), 500

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    logger.debug(f"\n=== Delete Event API - Event ID: {event_id} ===")
    logger.debug(f"User: {current_user.name} (ID: {current_user.id}, Role: {current_user.role})")
    
    try:
        # First check if event exists
        event = Event.query.get(event_id)
        if not event:
            logger.error(f"Event {event_id} not found")
            return jsonify({'error': 'Event not found'}), 404
            
        logger.debug(f"Found event: {event.title}")
        logger.debug(f"Event organizer ID: {event.organizer_id}")
        
        # Check user permissions
        if current_user.role not in ['admin', 'coordinator'] or (
            current_user.role == 'coordinator' and event.organizer_id != current_user.id
        ):
            logger.error(f"Unauthorized deletion attempt by user {current_user.name}")
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Delete eposter file if it exists
        if event.eposter:
            eposter_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(event.eposter))
            logger.debug(f"Checking for eposter file at: {eposter_path}")
            if os.path.exists(eposter_path):
                logger.debug("Deleting eposter file")
                os.remove(eposter_path)
                logger.debug("Eposter file deleted successfully")
            else:
                logger.debug("Eposter file not found on filesystem")
        
        # Delete all comments associated with the event first
        logger.debug("Deleting event comments")
        EventComment.query.filter_by(event_id=event.id).delete()
        logger.debug("Event comments deleted successfully")
            
        # First delete related records to avoid foreign key constraints
        if event.registrations:
            logger.debug(f"Deleting {len(event.registrations)} registrations")
            for registration in event.registrations:
                db.session.delete(registration)
        
        # Delete the event
        logger.debug("Deleting event")
        db.session.delete(event)
        db.session.commit()
        logger.debug("Event deleted successfully")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete event: ' + str(e)}), 500

@app.route('/api/events/<int:event_id>', methods=['PUT'])
@login_required
def update_event(event_id):
    logger.debug(f"\n=== Update Event API - Event ID: {event_id} ===")
    logger.debug(f"User: {current_user.name} (ID: {current_user.id}, Role: {current_user.role})")
    
    try:
        event = Event.query.get_or_404(event_id)
        
        # Check user permissions
        if current_user.role not in ['admin', 'coordinator'] or (
            current_user.role == 'coordinator' and event.organizer_id != current_user.id
        ):
            logger.error(f"Unauthorized update attempt by user {current_user.name}")
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Handle file upload first
        eposter_path = event.eposter  # Keep existing path by default
        if 'eposter' in request.files:
            file = request.files['eposter']
            if file and file.filename:
                if allowed_file(file.filename):
                    # Delete old eposter if it exists
                    if event.eposter:
                        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(event.eposter))
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                    
                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    eposter_path = f"uploads/eposters/{filename}"
        
        # Update other fields
        form_data = request.form
        event.title = form_data.get('title', event.title)
        event.description = form_data.get('description', event.description)
        event.event_type = form_data.get('event_type', event.event_type)
        event.location = form_data.get('location', event.location)
        event.capacity = int(form_data.get('capacity', event.capacity))
        if 'date' in form_data:
            event.date = datetime.fromisoformat(form_data['date'].replace('Z', '+00:00'))
        event.eposter = eposter_path
        
        db.session.commit()
        logger.debug("Event updated successfully")
        
        return jsonify({'success': True, 'message': 'Event updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update event: ' + str(e)}), 500

@app.route('/test')
def test():
    logger.debug("\n=== Test Route ===")
    return jsonify({
        'status': 'ok',
        'message': 'Flask server is running',
        'debug': True,
        'database': 'connected' if db.session.is_active else 'disconnected'
    })

@app.route('/event/<int:event_id>/comment', methods=['POST'])
@login_required
def add_comment(event_id):
    comment_text = request.form.get('comment')
    if not comment_text:
        flash('Comment cannot be empty', 'danger')
        return redirect(url_for('event_details', event_id=event_id))
    
    try:
        comment = EventComment(
            event_id=event_id,
            user_id=current_user.id,
            comment=comment_text
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to add comment', 'danger')
    
    return redirect(url_for('event_details', event_id=event_id))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = EventComment.query.get_or_404(comment_id)
    
    # Check if user is authorized to delete
    if current_user.id != comment.user_id and current_user.role not in ['admin', 'coordinator']:
        abort(403)
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete comment', 'danger')
    
    return redirect(url_for('event_details', event_id=comment.event_id))

@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    logger.debug(f"\n=== Update User API - User ID: {user_id} ===")
    logger.debug(f"User: {current_user.name} (ID: {current_user.id}, Role: {current_user.role})")
    
    try:
        if current_user.role != 'admin':
            logger.error(f"Unauthorized update attempt by user {current_user.name}")
            return jsonify({'error': 'Unauthorized'}), 403
        
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found")
            return jsonify({'error': 'User not found'}), 404
        
        # Get the update data
        data = request.get_json()
        
        # Prevent editing other admin users
        if user.role == 'admin' and user.id != current_user.id:
            logger.error(f"Attempt to edit another admin user by {current_user.name}")
            return jsonify({'error': 'Cannot modify other admin users'}), 403
        
        # Update user fields
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        if 'role' in data:
            # Prevent changing own role
            if user.id == current_user.id:
                logger.error("Attempt to change own role")
                return jsonify({'error': 'Cannot change your own role'}), 400
            # Prevent changing to/from admin role
            if (user.role == 'admin' or data['role'] == 'admin'):
                logger.error("Attempt to change admin role")
                return jsonify({'error': 'Cannot change admin role'}), 400
            user.role = data['role']
        
        db.session.commit()
        logger.debug(f"User {user.name} updated successfully")
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
