## Technologies Used
- **Backend Framework**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **ORM**: Flask-SQLAlchemy

## Development Setup
1. Python Environment:
   - Python 3.9
   - Conda environment: ngo_events

2. Required Packages:
   - flask
   - flask-sqlalchemy
   - flask-login
   - flask-wtf

3. Project Structure:
   ```
   ngo_events/
   ├── app.py              # Main application file
   ├── models/            # Database models
   ├── templates/         # HTML templates
   ├── static/           # CSS, JS, images
   └── instance/         # SQLite database
   ```

## Technical Constraints
1. Database:
   - Using SQLite for development
   - Database file stored in instance/ directory

2. Authentication:
   - Session-based authentication
   - Password hashing required
   - Role-based access control

3. Frontend:
   - Responsive design required
   - Cross-browser compatibility needed
   - Mobile-friendly interface

4. Security:
   - CSRF protection enabled
   - Secure password storage
   - Input validation required 