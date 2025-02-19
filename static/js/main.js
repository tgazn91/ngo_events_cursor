// Utility Functions
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Flash Messages
function showAlert(message, type = 'info') {
    // Get existing alert container or create one
    let container = document.getElementById('alertContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'alertContainer';
        document.body.appendChild(container);
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.appendChild(alertDiv);

    // Force reflow to enable animation
    alertDiv.offsetHeight;
    
    // Add show class after DOM update
    setTimeout(() => alertDiv.classList.add('show'), 10);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        alertDiv.addEventListener('transitionend', () => {
            alertDiv.remove();
            // Remove container if empty
            if (container.children.length === 0) {
                container.remove();
            }
        });
    }, 5000);
    
    // Handle manual dismissal
    const closeButton = alertDiv.querySelector('.btn-close');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            alertDiv.classList.remove('show');
            alertDiv.addEventListener('transitionend', () => {
                alertDiv.remove();
                if (container.children.length === 0) {
                    container.remove();
                }
            });
        });
    }
}

// Form Validation
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            field.classList.add('is-invalid');
            
            // Add error message if not exists
            if (!field.nextElementSibling?.classList.contains('invalid-feedback')) {
                const feedback = document.createElement('div');
                feedback.className = 'invalid-feedback';
                feedback.textContent = `${field.getAttribute('placeholder') || 'This field'} is required`;
                field.parentNode.appendChild(feedback);
            }
        } else {
            field.classList.remove('is-invalid');
            const feedback = field.nextElementSibling;
            if (feedback?.classList.contains('invalid-feedback')) {
                feedback.remove();
            }
        }
    });
    
    return isValid;
}

// Password Strength Meter
function updatePasswordStrength(password) {
    const strengthMeter = document.getElementById('passwordStrength');
    if (!strengthMeter) return;
    
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/)) strength++;
    if (password.match(/[A-Z]/)) strength++;
    if (password.match(/[0-9]/)) strength++;
    if (password.match(/[^a-zA-Z0-9]/)) strength++;
    
    const strengthClasses = ['danger', 'warning', 'warning', 'info', 'success'];
    const strengthTexts = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
    
    strengthMeter.className = `progress-bar bg-${strengthClasses[strength - 1]}`;
    strengthMeter.style.width = `${strength * 20}%`;
    strengthMeter.textContent = strengthTexts[strength - 1];
}

// Dynamic Form Fields
function addFormField(containerId, template) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const fieldCount = container.children.length;
    const newField = template.replace(/\{index\}/g, fieldCount);
    
    const fieldDiv = document.createElement('div');
    fieldDiv.innerHTML = newField;
    container.appendChild(fieldDiv.firstChild);
}

function removeFormField(button) {
    const field = button.closest('.form-field');
    field.remove();
}

// API Helpers
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (response.status === 405) {
            console.error('Method not allowed. Please check the API endpoint and method.');
            throw new Error('Invalid API method');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'An error occurred');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        showAlert(error.message, 'danger');
        throw error;
    }
}

// Event fetching functions
async function fetchUpcomingEvents() {
    return apiRequest('/api/events/upcoming');
}

async function fetchManagedEvents() {
    return apiRequest('/api/events/managed');
}

async function fetchUserRegistrations() {
    return apiRequest('/api/registrations');
}

// User Management Functions
async function fetchUsers() {
    return apiRequest('/api/users');
}

async function updateUserRole(userId, newRole) {
    return apiRequest(`/api/users/${userId}/role`, {
        method: 'PUT',
        body: JSON.stringify({ role: newRole })
    });
}

async function deleteUser(userId) {
    return apiRequest(`/api/users/${userId}`, {
        method: 'DELETE'
    });
}

async function registerForEvent(eventId, buttonElement) {
    try {
        // Disable the button and show loading state
        buttonElement.disabled = true;
        buttonElement.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Registering...';
        
        const data = await apiRequest(`/api/events/${eventId}/register`, { method: 'POST' });
        
        if (data.success) {
            // Check if we're on the event details page
            const isEventDetailsPage = window.location.pathname.startsWith('/event/');
            
            if (isEventDetailsPage) {
                // Update UI for event details page
                buttonElement.className = 'btn btn-success w-100';
                buttonElement.innerHTML = '<i class="fas fa-check me-1"></i>Registered';
                buttonElement.disabled = true;

                // Update registration counter
                const counterElement = document.getElementById(`regCount-${eventId}`);
                if (counterElement) {
                    const [current, total] = counterElement.textContent.split('/');
                    const newCount = parseInt(current) + 1;
                    counterElement.textContent = `${newCount}/${total} registered`;
                }
            } else {
                // Refresh dashboard view
                await displayUpcomingEvents();
            }
            
            showAlert('Successfully registered for the event!', 'success');
        } else {
            throw new Error(data.error || 'Failed to register for event.');
        }
    } catch (error) {
        console.error('Error registering for event:', error);
        showAlert(error.message, 'danger');
        
        // Restore button state
        buttonElement.disabled = false;
        buttonElement.innerHTML = '<i class="fas fa-ticket-alt me-1"></i>Register';
    }
}

// Function to display upcoming events
async function displayUpcomingEvents() {
    try {
        const data = await fetchUpcomingEvents();
        if (!data.events) return;
        
        const eventsContainer = document.querySelector('#upcomingEventsList');
        if (!eventsContainer) return;
        
        eventsContainer.innerHTML = data.events.map(event => `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${event.title}</h5>
                    <p class="card-text">${event.description}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <small class="text-muted">
                                <i class="fas fa-calendar-alt me-1"></i>${formatDate(event.date)}
                            </small>
                            <br>
                            <small class="text-muted">
                                <i class="fas fa-map-marker-alt me-1"></i>${event.location}
                            </small>
                        </div>
                        <div>
                            <span class="badge bg-primary" id="regCount-${event.id}">${event.registered_count}/${event.capacity} registered</span>
                            <div class="btn-group ms-2">
                                <a href="/event/${event.id}" class="btn btn-info btn-sm">
                                    <i class="fas fa-eye me-1"></i>View
                                </a>
                                ${!event.is_registered && event.registered_count < event.capacity ? `
                                    <button class="btn btn-primary btn-sm" id="regBtn-${event.id}" onclick="registerForEvent(${event.id}, this)">
                                        <i class="fas fa-ticket-alt me-1"></i>Register
                                    </button>
                                ` : event.is_registered ? `
                                    <button class="btn btn-success btn-sm" disabled>
                                        <i class="fas fa-check me-1"></i>Registered
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error displaying upcoming events:', error);
        showAlert('Failed to load upcoming events', 'danger');
    }
}

// Sidebar Toggle Function
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.querySelector('.sidebar-backdrop');
    
    if (!sidebar) return;
    
    // Create backdrop if it doesn't exist
    if (!backdrop) {
        const newBackdrop = document.createElement('div');
        newBackdrop.className = 'sidebar-backdrop';
        document.body.appendChild(newBackdrop);
    }
    
    sidebar.classList.toggle('show');
    document.querySelector('.sidebar-backdrop')?.classList.toggle('show');
}

// Event Management Functions
async function deleteEvent(eventId) {
    if (!confirm('Are you sure you want to delete this event?')) {
        return;
    }
    
    try {
        await apiRequest(`/api/events/${eventId}`, {
            method: 'DELETE'
        });
        
        showAlert('Event deleted successfully', 'success');
        // Set the refresh flag and redirect
        localStorage.setItem('refreshPending', 'true');
        localStorage.setItem('activeTab', '#manage');
        window.location.reload();
    } catch (error) {
        console.error('Error deleting event:', error);
        showAlert('Failed to delete event', 'danger');
    }
}

// Event Handlers
document.addEventListener('DOMContentLoaded', function() {
    // Check URL parameters for active tab
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    if (tabParam === 'managed') {
        const tab = new bootstrap.Tab(document.querySelector('a[data-bs-target="#manage"]'));
        tab.show();
    }
    
    // Sidebar toggle handler
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', toggleSidebar);
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        const sidebar = document.querySelector('.sidebar');
        const navbarToggler = document.querySelector('.navbar-toggler');
        
        if (window.innerWidth < 768 && sidebar?.classList.contains('show')) {
            if (!sidebar.contains(e.target) && !navbarToggler.contains(e.target)) {
                toggleSidebar();
            }
        }
    });
    
    // Close sidebar when window is resized to desktop view
    window.addEventListener('resize', function() {
        const sidebar = document.querySelector('.sidebar');
        if (window.innerWidth >= 768 && sidebar?.classList.contains('show')) {
            toggleSidebar();
        }
    });
    
    // Password strength meter
    const passwordInput = document.querySelector('input[type="password"]');
    if (passwordInput) {
        passwordInput.addEventListener('input', (e) => updatePasswordStrength(e.target.value));
    }
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showAlert('Please fill in all required fields', 'danger');
            }
        });
    });
    
    // Dynamic form fields
    const addFieldButtons = document.querySelectorAll('[data-add-field]');
    addFieldButtons.forEach(button => {
        button.addEventListener('click', () => {
            const containerId = button.dataset.container;
            const template = document.getElementById(button.dataset.template).innerHTML;
            addFormField(containerId, template);
        });
    });
    
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
    
    // Initialize popovers
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    popovers.forEach(popover => {
        new bootstrap.Popover(popover);
    });
    
    // Load users for admin
    if (document.getElementById('usersList')) {
        fetchUsers()
            .then(data => {
                const tbody = document.getElementById('usersList');
                if (!data.users || data.users.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center">No users found.</td></tr>';
                    return;
                }
                
                tbody.innerHTML = '';
                data.users.forEach(user => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${user.name}</td>
                        <td>${user.email}</td>
                        <td>
                            <select class="form-select form-select-sm" onchange="updateUserRole(${user.id}, this.value)">
                                <option value="user" ${user.role === 'user' ? 'selected' : ''}>User</option>
                                <option value="coordinator" ${user.role === 'coordinator' ? 'selected' : ''}>Coordinator</option>
                                <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>Admin</option>
                            </select>
                        </td>
                        <td>${new Date(user.created_at).toLocaleDateString()}</td>
                        <td>
                            <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})">
                                <i class="fas fa-trash me-1"></i>Delete
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            })
            .catch(error => {
                console.error('Error fetching users:', error);
                const tbody = document.getElementById('usersList');
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Failed to load users.</td></tr>';
            });
    }
    
    // Handle tab changes
    const tabLinks = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabLinks.forEach(link => {
        link.addEventListener('shown.bs.tab', (e) => {
            const targetId = e.target.getAttribute('data-bs-target');
            if (targetId === '#upcoming') {
                displayUpcomingEvents();
            }
        });
    });
    
    
    // Initial load of upcoming events if we're on the dashboard
    if (document.querySelector('#upcomingEventsList')) {
        displayUpcomingEvents();
    }
});

// Keyboard Navigation
document.addEventListener('keydown', function(e) {
    // Skip links for keyboard users
    if (e.key === 'Tab') {
        document.body.classList.add('keyboard-navigation');
    }
});

// Focus management for modals
document.addEventListener('shown.bs.modal', function(event) {
    const modal = event.target;
    const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (focusable.length > 0) {
        focusable[0].focus();
    }
});

// ARIA live regions for dynamic content
function announceToScreenReader(message, priority = 'polite') {
    const liveRegion = document.getElementById('aria-live-region');
    if (!liveRegion) {
        const region = document.createElement('div');
        region.id = 'aria-live-region';
        region.setAttribute('aria-live', priority);
        region.setAttribute('role', 'status');
        region.classList.add('sr-only');
        document.body.appendChild(region);
    }
    liveRegion.textContent = message;
}
