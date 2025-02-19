# System Patterns

## Architecture Overview
The application follows a Model-View-Controller (MVC) pattern with Flask:
- Models: SQLAlchemy ORM for database interactions
- Views: Jinja2 templates for rendering
- Controllers: Flask routes and API endpoints

## Key Components

### 1. Frontend Architecture
- Bootstrap 5 for responsive design
- JavaScript modules for dynamic functionality
- AJAX for asynchronous data fetching
- Real-time updates via API polling (to be enhanced with WebSocket)

### 2. Backend Architecture
- Flask application server
- SQLite database
- SQLAlchemy ORM
- Flask-Login for authentication
- RESTful API endpoints

### 3. Data Flow
```
User Action → Frontend JS → API Endpoint → Database → Response → UI Update
```

### 4. Real-time Updates
Current Implementation:
- API polling for event updates
- Manual refresh triggers
- Client-side rendering

Planned Enhancements:
- WebSocket integration
- Server-sent events
- Optimistic UI updates

### 5. Security Patterns
- Session-based authentication
- Role-based access control
- CSRF protection
- Input validation
- Secure password handling

### 6. Error Handling
- Client-side validation
- Server-side validation
- User-friendly error messages
- Logging and monitoring

## Technical Decisions
1. Chose SQLite for simplicity and portability
2. Using Bootstrap for rapid UI development
3. Implementing real-time updates in phases:
   - Phase 1: API polling (current)
   - Phase 2: WebSocket (planned)
4. Keeping frontend and backend loosely coupled
5. Following RESTful API design principles

## System Architecture
1. **MVC Pattern**
   - Models: SQLAlchemy models in models/
   - Views: Flask routes in routes/
   - Templates: Jinja2 templates in templates/

2. **Authentication Flow**
   - Login required for protected routes
   - Role-based access control
   - Session management

3. **Database Design**
   - Users table (admins, volunteers)
   - Events table
   - Resources table
   - Volunteer_Events relationship table

## Key Technical Decisions
1. **Flask Framework**
   - Lightweight and flexible
   - Easy to extend
   - Good documentation and community support

2. **SQLite Database**
   - Simple setup
   - File-based storage
   - Suitable for prototype development

3. **Blueprint Pattern**
   - Modular route organization
   - Separate admin and volunteer interfaces
   - Scalable structure

## Architecture Patterns
1. **Service Layer**
   - Separation of business logic
   - Reusable service functions
   - Clean controller routes

2. **Form Objects**
   - WTForms for validation
   - Separate form classes
   - Input sanitization

3. **Template Inheritance**
   - Base template with common elements
   - Extended templates for specific views
   - Consistent layout and styling 