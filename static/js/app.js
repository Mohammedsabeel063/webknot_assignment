// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';
const DEFAULT_COLLEGE_ID = 'test_college_123'; // Default for testing

// Get auth token from localStorage or prompt for it
function getAuthToken() {
    return localStorage.getItem('auth_token') || '';
}

// Set auth token
function setAuthToken(token) {
    localStorage.setItem('auth_token', token);
}

// Get default headers with auth and college ID
function getDefaultHeaders() {
    return {
        'Content-Type': 'application/json',
        'X-College-ID': DEFAULT_COLLEGE_ID,
        'Authorization': `Bearer ${getAuthToken()}`
    };
}

// Handle API errors
async function handleApiError(response) {
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'An error occurred');
    }
    return response;
}

// DOM Elements
const statsCards = document.querySelectorAll('.stats-card');
const eventsTable = document.querySelector('.events-table tbody');
const createEventBtn = document.querySelector('.btn-primary');
const loadingIndicator = document.getElementById('loading-indicator');

// Global state
let currentCollegeId = 'test_college_123'; // Default for testing

// Initialize the application
async function initApp() {
    try {
        // Check if we have a valid session
        const token = getAuthToken();
        if (!token) {
            // For demo purposes, we'll continue without auth
            // In production, you would redirect to login
            console.warn('No auth token found. Running in demo mode with limited functionality.');
        }
        
        // Set up event listeners first
        setupEventListeners();
        
        // Show loading state
        showLoading(true);
        
        // Load initial data
        try {
            await loadStats();
            await loadEvents();
            await loadRecentActivity();
        } catch (error) {
            console.error('Error loading data:', error);
            showError('Some data could not be loaded. Please try refreshing the page.');
        }
        
        // Hide loading state
        showLoading(false);
        
    } catch (error) {
        console.error('Error initializing app:', error);
        showError('Failed to initialize application: ' + error.message);
        showLoading(false);
    }
}

// Login function
async function login(username, password) {
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-College-ID': DEFAULT_COLLEGE_ID
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }

        // Save token and initialize app
        setAuthToken(data.access_token);
        await initApp();
        
    } catch (error) {
        console.error('Login error:', error);
        showError('Login failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Show login modal
function showLoginModal() {
    // Implementation depends on your UI framework
    // This is a simplified version
    const modal = document.createElement('div');
    modal.className = 'login-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h2>Login</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit">Login</button>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Handle form submission
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        await login(formData.get('username'), formData.get('password'));
    });
}

// Show create event modal
function showCreateEventModal(eventId = null) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'eventModal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-hidden', 'true');
    
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title">${eventId ? 'Edit' : 'Create New'} Event</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form id="eventForm" class="needs-validation" novalidate>
                        <div class="row">
                            <div class="col-md-8 mb-3">
                                <label for="eventTitle" class="form-label">Event Title *</label>
                                <input type="text" class="form-control" id="eventTitle" name="title" required>
                                <div class="invalid-feedback">Please provide a title for the event.</div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <label for="eventType" class="form-label">Event Type *</label>
                                <select class="form-select" id="eventType" name="type" required>
                                    <option value="">Select type...</option>
                                    <option value="workshop">Workshop</option>
                                    <option value="seminar">Seminar</option>
                                    <option value="conference">Conference</option>
                                    <option value="hackathon">Hackathon</option>
                                    <option value="webinar">Webinar</option>
                                    <option value="other">Other</option>
                                </select>
                                <div class="invalid-feedback">Please select an event type.</div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="startTime" class="form-label">Start Time *</label>
                                <input type="datetime-local" class="form-control" id="startTime" name="start_time" required>
                                <div class="invalid-feedback">Please provide a start time.</div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label for="endTime" class="form-label">End Time *</label>
                                <input type="datetime-local" class="form-control" id="endTime" name="end_time" required>
                                <div class="invalid-feedback">Please provide an end time.</div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8 mb-3">
                                <label for="eventVenue" class="form-label">Venue</label>
                                <input type="text" class="form-control" id="eventVenue" name="venue" placeholder="e.g., Main Auditorium">
                            </div>
                            <div class="col-md-4 mb-3">
                                <label for="eventCapacity" class="form-label">Capacity</label>
                                <input type="number" class="form-control" id="eventCapacity" name="capacity" min="1" placeholder="Unlimited">
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label for="eventDescription" class="form-label">Description</label>
                            <textarea class="form-control" id="eventDescription" name="description" rows="3" placeholder="Provide details about the event..."></textarea>
                        </div>
                        
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle me-2"></i> Fields marked with * are required.
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">
                        <i class="bi bi-x-lg me-1"></i> Cancel
                    </button>
                    <button type="button" class="btn btn-primary" id="saveEventBtn">
                        <i class="bi bi-save me-1"></i> ${eventId ? 'Update' : 'Create'} Event
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Initialize modal
    const modalInstance = new bootstrap.Modal(modal);
    
    // Set current date/time as default for new events
    if (!eventId) {
        const now = new Date();
        const startTime = new Date(now.getTime() + 3600000); // 1 hour from now
        const endTime = new Date(startTime.getTime() + 7200000); // 3 hours from now
        
        document.getElementById('startTime').value = startTime.toISOString().slice(0, 16);
        document.getElementById('endTime').value = endTime.toISOString().slice(0, 16);
    } else {
        // Load event data if editing
        loadEventData(eventId);
    }
    
    // Show the modal
    modalInstance.show();
    
    // Set up form validation
    const form = document.getElementById('eventForm');
    form.addEventListener('submit', handleEventFormSubmit);
    
    // Set up save button
    document.getElementById('saveEventBtn').addEventListener('click', () => {
        if (form.checkValidity()) {
            const formData = new FormData(form);
            const eventData = {
                title: formData.get('title'),
                type: formData.get('type'),
                start_time: formData.get('start_time'),
                end_time: formData.get('end_time'),
                venue: formData.get('venue'),
                capacity: formData.get('capacity') ? parseInt(formData.get('capacity')) : null,
                description: formData.get('description')
            };
            
            saveEvent(eventData, eventId)
                .then(() => {
                    modalInstance.hide();
                    modal.remove();
                    loadEvents(); // Refresh the events list
                    showSuccess(`Event ${eventId ? 'updated' : 'created'} successfully!`);
                })
                .catch(error => {
                    console.error('Error saving event:', error);
                    showError(`Failed to ${eventId ? 'update' : 'create'} event: ${error.message}`);
                });
        } else {
            form.classList.add('was-validated');
        }
    });
    
    // Clean up on close
    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
    });
    
    // Function to load event data for editing
    async function loadEventData(eventId) {
        try {
            const response = await fetch(`${API_BASE_URL}/events/${eventId}`, {
                headers: getDefaultHeaders()
            });
            
            if (!response.ok) {
                throw new Error('Failed to load event data');
            }
            
            const event = await response.json();
            
            // Populate form fields
            document.getElementById('eventTitle').value = event.title || '';
            document.getElementById('eventType').value = event.type || '';
            document.getElementById('startTime').value = event.start_time ? event.start_time.slice(0, 16) : '';
            document.getElementById('endTime').value = event.end_time ? event.end_time.slice(0, 16) : '';
            document.getElementById('eventVenue').value = event.venue || '';
            document.getElementById('eventCapacity').value = event.capacity || '';
            document.getElementById('eventDescription').value = event.description || '';
            
        } catch (error) {
            console.error('Error loading event data:', error);
            showError('Failed to load event data: ' + error.message);
            modalInstance.hide();
        }
    }
}

// Load statistics
async function loadStats() {
    try {
        showLoading(true);
        
        // Get college ID from URL or use default
        const urlParams = new URLSearchParams(window.location.search);
        const collegeId = urlParams.get('college_id') || DEFAULT_COLLEGE_ID;
        
        // Fetch statistics from the API
        const response = await fetch(`${API_BASE_URL}/reports/stats?college_id=${collegeId}`, {
            headers: getDefaultHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch statistics');
        }
        
        const data = await response.json();
        
        // Update the UI with the fetched data
        updateStatCard('total-students', data.total_students || 0);
        updateStatCard('total-events', data.total_events || 0);
        updateStatCard('attendance-rate', `${data.attendance_rate || 0}%`);
        updateStatCard('upcoming-events', data.upcoming_events || 0);
        
    } catch (error) {
        console.error('Error loading stats:', error);
        showError('Failed to load statistics: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Load events
async function loadEvents() {
    try {
        showLoading(true);
        
        // Get college ID from URL or use default
        const urlParams = new URLSearchParams(window.location.search);
        const collegeId = urlParams.get('college_id') || DEFAULT_COLLEGE_ID;
        
        // Fetch events from the API
        const response = await fetch(`${API_BASE_URL}/events?college_id=${collegeId}`, {
            headers: getDefaultHeaders()
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch events');
        }
        
        const events = await response.json();
        
        // Render the events in the UI
        renderEvents(events);
        
        // Also load upcoming events
        await loadUpcomingEvents();
        
    } catch (error) {
        console.error('Error loading events:', error);
        showError('Failed to load events: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Load upcoming events
async function loadUpcomingEvents() {
    try {
        const headers = getAuthHeaders();
        const now = new Date().toISOString();
        const response = await fetch(
            `${API_BASE_URL}/events?start_time_after=${now}&ordering=start_time&limit=3`, 
            { headers }
        );
        
        if (!response.ok) throw new Error('Failed to load upcoming events');
        
        const events = await response.json();
        renderUpcomingEvents(events);
        
    } catch (error) {
        console.error('Error loading upcoming events:', error);
        showError('Failed to load upcoming events');
    }
}

// Load recent activity
async function loadRecentActivity() {
    try {
        const headers = getAuthHeaders();
        const response = await fetch(
            `${API_BASE_URL}/activity?limit=5`, 
            { headers }
        );
        
        if (!response.ok) return; // Optional feature
        
        const activities = await response.json();
        renderRecentActivity(activities);
        
    } catch (error) {
        console.error('Error loading recent activity:', error);
        // Don't show error as this is a non-critical feature
    }
}

// Helper function to get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    const headers = {
        'X-College-ID': currentCollegeId,
        'Content-Type': 'application/json'
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
}

// Update a stat card
function updateStatCard(className, value) {
    const card = document.querySelector(`.${className} .number`);
    if (card) {
        card.textContent = value;
    }
}

// Render events in the table
function renderEvents(events) {
    const eventsTable = document.querySelector('.events-table tbody');
    if (!eventsTable) return;
    
    eventsTable.innerHTML = '';
    
    if (!events || events.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" class="text-center py-4">No events found. Create your first event to get started!</td>';
        eventsTable.appendChild(row);
        return;
    }
    
    events.forEach(event => {
        const row = document.createElement('tr');
        const startDate = new Date(event.start_time);
        const endDate = new Date(event.end_time);
        const now = new Date();
        
        // Determine event status
        let statusClass = 'bg-secondary';
        let statusText = 'Upcoming';
        
        if (startDate > now) {
            statusClass = 'bg-info';
            statusText = 'Upcoming';
        } else if (startDate <= now && endDate >= now) {
            statusClass = 'bg-success';
            statusText = 'In Progress';
        } else {
            statusClass = 'bg-secondary';
            statusText = 'Completed';
        }
        
        row.innerHTML = `
            <td>
                <div class="fw-bold">${escapeHtml(event.title)}</div>
                <small class="text-muted">${event.type || 'Event'}</small>
            </td>
            <td>${startDate.toLocaleDateString()}<br>
                <small class="text-muted">${startDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - ${endDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</small>
            </td>
            <td>${event.venue || 'TBD'}</td>
            <td>
                <span class="badge ${statusClass}">
                    ${statusText}
                </span>
            </td>
            <td class="text-end">
                <button class="btn btn-sm btn-outline-primary me-1" onclick="viewEvent('${event.event_id || event.id}')">
                    <i class="bi bi-eye"></i> View
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteEvent('${event.event_id || event.id}')">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        eventsTable.appendChild(row);
    });
}

// Render upcoming events
function renderUpcomingEvents(events) {
    const container = document.getElementById('upcoming-events-list');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!events || events.length === 0) {
        container.innerHTML = '<div class="text-muted">No upcoming events</div>';
        return;
    }
    
    events.forEach(event => {
        const startTime = new Date(event.start_time);
        const eventElement = document.createElement('div');
        eventElement.className = 'upcoming-event mb-3';
        eventElement.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h6 class="mb-1">${escapeHtml(event.title)}</h6>
                    <small class="text-muted">
                        <i class="bi bi-calendar-event me-1"></i>
                        ${startTime.toLocaleDateString()} • ${startTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </small>
                </div>
                <span class="badge ${getStatusClass(event.start_time, event.end_time)}">
                    ${getStatusText(event.start_time, event.end_time)}
                </span>
            </div>
            <div class="mt-2">
                <button class="btn btn-sm btn-outline-primary" 
                        onclick="viewEvent('${event.event_id}')">
                    View Details
                </button>
            </div>
        `;
        container.appendChild(eventElement);
    });
}

// Render recent activity
function renderRecentActivity(activities) {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (!activities || activities.length === 0) {
        container.innerHTML = '<div class="text-muted">No recent activity</div>';
        return;
    }
    
    activities.forEach(activity => {
        const time = new Date(activity.timestamp);
        const timeAgo = timeAgoSince(time);
        
        const activityElement = document.createElement('div');
        activityElement.className = 'activity-item d-flex mb-3';
        activityElement.innerHTML = `
            <div class="flex-shrink-0 me-3">
                <div class="activity-icon bg-light text-primary rounded-circle">
                    <i class="bi ${getActivityIcon(activity.type)}"></i>
                </div>
            </div>
            <div>
                <h6 class="mb-0">${escapeHtml(activity.title)}</h6>
                <p class="small text-muted mb-1">${escapeHtml(activity.description || '')}</p>
                <small class="text-muted">${timeAgo}</small>
            </div>
        `;
        container.appendChild(activityElement);
    });
}

// Helper function to get activity icon
function getActivityIcon(activityType) {
    const icons = {
        'event_created': 'bi-calendar-plus',
        'registration': 'bi-person-plus',
        'attendance': 'bi-check-circle',
        'feedback': 'bi-chat-square-text',
        'default': 'bi-activity'
    };
    return icons[activityType] || icons.default;
}

// Format time as "X time ago"
function timeAgoSince(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    let interval = Math.floor(seconds / 31536000);
    if (interval >= 1) return interval + ' year' + (interval === 1 ? '' : 's') + ' ago';
    
    interval = Math.floor(seconds / 2592000);
    if (interval >= 1) return interval + ' month' + (interval === 1 ? '' : 's') + ' ago';
    
    interval = Math.floor(seconds / 86400);
    if (interval >= 1) return interval + ' day' + (interval === 1 ? '' : 's') + ' ago';
    
    interval = Math.floor(seconds / 3600);
    if (interval >= 1) return interval + ' hour' + (interval === 1 ? '' : 's') + ' ago';
    
    interval = Math.floor(seconds / 60);
    if (interval >= 1) return interval + ' minute' + (interval === 1 ? '' : 's') + ' ago';
    
    return 'just now';
}

// Escape HTML to prevent XSS
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Get status class based on event timing
function getStatusClass(startTime, endTime) {
    const now = new Date();
    const start = new Date(startTime);
    const end = new Date(endTime);
    
    if (now < start) return 'upcoming';
    if (now >= start && now <= end) return 'ongoing';
    return 'completed';
}

// Get status text
function getStatusText(startTime, endTime) {
    const status = getStatusClass(startTime, endTime);
    return status.charAt(0).toUpperCase() + status.slice(1);
}

// Save event (create or update)
async function saveEvent(eventData, eventId = null) {
    try {
        showLoading(true);
        
        // Get college ID from URL or use default
        const urlParams = new URLSearchParams(window.location.search);
        const collegeId = urlParams.get('college_id') || DEFAULT_COLLEGE_ID;
        
        // Add college ID to the event data
        const payload = {
            ...eventData,
            college_id: collegeId
        };
        
        const url = eventId 
            ? `${API_BASE_URL}/events/${eventId}`
            : `${API_BASE_URL}/events`;
            
        const method = eventId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                ...getDefaultHeaders()
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to save event');
        }
        
        return await response.json();
        
    } catch (error) {
        console.error('Error saving event:', error);
        throw error;
    } finally {
        showLoading(false);
    }
}

// View event details
window.viewEvent = async function(eventId) {
    try {
        const headers = getAuthHeaders();
        const response = await fetch(`${API_BASE_URL}/events/${eventId}`, { headers });
        
        if (!response.ok) throw new Error('Failed to fetch event details');
        
        const event = await response.json();
        
        // You can implement a proper modal to show event details
        const modal = document.getElementById('eventDetailsModal');
        if (modal) {
            // Update modal content with event details
            modal.querySelector('.modal-title').textContent = event.title;
            modal.querySelector('.event-description').textContent = event.description || 'No description available';
            modal.querySelector('.event-venue').textContent = event.venue || 'TBD';
            modal.querySelector('.event-capacity').textContent = event.capacity || 'Unlimited';
            
            const startTime = new Date(event.start_time);
            const endTime = new Date(event.end_time);
            
            modal.querySelector('.event-date').textContent = startTime.toLocaleDateString();
            modal.querySelector('.event-time').textContent = 
                `${startTime.toLocaleTimeString()} - ${endTime.toLocaleTimeString()}`;
            
            // Show the modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            // Fallback to alert
            alert(`Event: ${event.title}\nStarts: ${new Date(event.start_time).toLocaleString()}`);
        }
        
    } catch (error) {
        console.error('Error viewing event:', error);
        showError('Failed to load event details');
    }
};

// Delete event
window.deleteEvent = async function(eventId) {
    // Show confirmation dialog
    const confirmed = await Swal.fire({
        title: 'Delete Event',
        text: 'Are you sure you want to delete this event? This action cannot be undone.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel'
    });
    
    if (!confirmed.isConfirmed) {
        return;
    }
    
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/events/${eventId}`, {
            method: 'DELETE',
            headers: getDefaultHeaders()
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to delete event');
        }
        
        // Refresh events list
        await loadEvents();
        
        // Show success message
        await Swal.fire({
            title: 'Deleted!',
            text: 'The event has been deleted.',
            icon: 'success',
            timer: 2000,
            showConfirmButton: false
        });
        
    } catch (error) {
        console.error('Error deleting event:', error);
        
        await Swal.fire({
            title: 'Error',
            text: 'Failed to delete event: ' + error.message,
            icon: 'error',
            confirmButtonText: 'OK'
        });
    } finally {
        showLoading(false);
    }
};

// Show success message
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success alert-dismissible fade show';
    successDiv.role = 'alert';
    successDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(successDiv, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        const alert = bootstrap.Alert.getOrCreateInstance(successDiv);
        alert.close();
    }, 5000);
}

// Handle form submission for creating/editing events
function handleEventFormSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const eventData = {
        title: formData.get('title'),
        description: formData.get('description'),
        start_time: formData.get('start_time'),
        end_time: formData.get('end_time'),
        venue: formData.get('venue'),
        capacity: parseInt(formData.get('capacity'), 10) || null,
        type: formData.get('type') || 'general'
    };
    
    const eventId = form.dataset.eventId; // For updates
    
    saveEvent(eventData, eventId).then(() => {
        // Close the modal if it exists
        const modal = bootstrap.Modal.getInstance(form.closest('.modal'));
        if (modal) modal.hide();
        
        // Reset the form
        form.reset();
    });
}

// Show error message
function showError(message) {
    // Implement error display
    console.error('Error:', message);
}

// Make functions available globally
window.loadStats = loadStats;
window.loadEvents = loadEvents;
