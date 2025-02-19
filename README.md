# NGO Events Management System

A web-based platform designed to help NGOs efficiently manage their events, volunteers, and resources.

## Features

- **Event Management**: Create, update, and track events
- **Volunteer Management**: Register and coordinate volunteers
- **Resource Allocation**: Track and manage event resources
- **Reporting**: Generate event reports and analytics
- **User Roles**: Admin dashboard and volunteer portal

## Tech Stack

- Backend: Python with Flask
- Database: SQLite
- Frontend: HTML, CSS, JavaScript
- Authentication: Flask-Login

## Setup

1. Create conda environment:
```bash
conda create -n ngo_events python=3.9
conda activate ngo_events
```

2. Install dependencies:
```bash
pip install flask flask-sqlalchemy flask-login flask-wtf
```

3. Run the application:
```bash
python app.py
```

## Project Structure

```
ngo_events/
├── app.py              # Main application file
├── models/            # Database models
├── templates/         # HTML templates
├── static/           # CSS, JS, images
└── instance/         # SQLite database
```

## PythonAnywhere Deployment Instructions

1. **Create a PythonAnywhere Account**
   - Go to www.pythonanywhere.com and create an account
   - Choose the appropriate plan (Free tier is sufficient for testing)

2. **Upload Your Code**
   ```bash
   # In PythonAnywhere bash console
   git clone https://github.com/yourusername/ngo_events_cursor.git
   cd ngo_events_cursor
   ```

3. **Create Virtual Environment**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.9 ngo_events
   workon ngo_events
   pip install -r requirements.txt
   ```

4. **Configure Web App**
   - Go to Web tab in PythonAnywhere dashboard
   - Click "Add a new web app"
   - Choose Manual Configuration
   - Select Python 3.9
   - Set source code directory: /home/yourusername/ngo_events_cursor
   - Set working directory: /home/yourusername/ngo_events_cursor
   - Set virtual environment: /home/yourusername/.virtualenvs/ngo_events

5. **Configure WSGI File**
   - In the Web tab, click on the WSGI configuration file link
   - Replace contents with the contents of your wsgi.py
   - Update the project_home path to match your PythonAnywhere username

6. **Set Up Static Files**
   - In Web tab, add static file mapping:
     - URL: /static/
     - Directory: /home/yourusername/ngo_events_cursor/static/

7. **Create Upload Directories**
   ```bash
   mkdir -p /home/yourusername/ngo_events_cursor/static/uploads/eposters
   chmod 755 /home/yourusername/ngo_events_cursor/static/uploads/eposters
   ```

8. **Initialize Database**
   ```bash
   # In PythonAnywhere bash console
   cd ngo_events_cursor
   python
   >>> from app import db, app
   >>> with app.app_context():
   ...     db.create_all()
   ```

9. **Reload Web App**
   - Click the Reload button in the Web tab

## Important Notes

1. **File Paths**: 
   - Replace 'yourusername' with your actual PythonAnywhere username
   - Update database and upload folder paths in app.py

2. **File Permissions**:
   - Ensure proper permissions for upload directories
   - Database file should be writable

3. **Environment Variables**:
   - Set any necessary environment variables in the Web app configuration

4. **Debugging**:
   - Check error logs in the Web tab
   - Use the error log viewer in PythonAnywhere

5. **Limitations**:
   - Free tier has CPU and bandwidth restrictions
   - File size limits apply
   - Some domains might be blocked

## Maintenance

1. **Database Backup**:
   ```bash
   # In PythonAnywhere bash console
   cd /home/yourusername/ngo_events_cursor
   sqlite3 events.db .dump > backup.sql
   ```

2. **Log Rotation**:
   - Logs are automatically managed by PythonAnywhere
   - Check Web tab for access to logs

3. **Updates**:
   ```bash
   # In PythonAnywhere bash console
   workon ngo_events
   pip install --upgrade -r requirements.txt
   ``` 