// Cabinet Médical - JavaScript utilities

document.addEventListener('DOMContentLoaded', function() {
    console.log('Cabinet Médical - Application loaded');
    
    // Initialize all components
    initializeTooltips();
    initializePopovers();
    initializeAnimations();
    initializeFormValidations();
    initializeDataTables();
    initializeNotifications();
    
    // Auto-hide success messages
    autoHideMessages();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [title]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            placement: 'top',
            trigger: 'hover'
        });
    });
}

// Initialize Bootstrap popovers
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Initialize animations
function initializeAnimations() {
    // Fade in cards on page load
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Animate elements with fade-in-up class
    const fadeElements = document.querySelectorAll('.fade-in-up');
    fadeElements.forEach((element, index) => {
        setTimeout(() => {
            element.style.animationDelay = `${index * 0.1}s`;
        }, 100);
    });
}

// Form validation utilities
function initializeFormValidations() {
    // Real-time validation for forms
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            form.classList.add('was-validated');
        });
        
        // Real-time validation on input
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
        });
    });
    
    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"], input[name*="telephone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            formatPhoneNumber(this);
        });
    });
    
    // Date validation
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('change', function() {
            validateDate(this);
        });
    });
}

// Initialize enhanced data tables
function initializeDataTables() {
    const tables = document.querySelectorAll('.table-sortable');
    tables.forEach(table => {
        makeTableSortable(table);
    });
    
    // Add search functionality to tables
    const searchInputs = document.querySelectorAll('.table-search');
    searchInputs.forEach(input => {
        const tableId = input.dataset.table;
        const table = document.getElementById(tableId);
        if (table) {
            input.addEventListener('input', function() {
                filterTable(table, this.value);
            });
        }
    });
}

// Notification system
function initializeNotifications() {
    // Check for browser notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        // Don't request permission automatically, wait for user action
    }
    
    // Setup notification for appointment reminders
    setupAppointmentReminders();
}

// Auto-hide success messages
function autoHideMessages() {
    const successMessages = document.querySelectorAll('.alert-success');
    successMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease';
            message.style.opacity = '0';
            setTimeout(() => {
                if (message.parentNode) {
                    message.parentNode.removeChild(message);
                }
            }, 500);
        }, 5000);
    });
    
    const infoMessages = document.querySelectorAll('.alert-info');
    infoMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease';
            message.style.opacity = '0';
            setTimeout(() => {
                if (message.parentNode) {
                    message.parentNode.removeChild(message);
                }
            }, 500);
        }, 7000);
    });
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Only trigger shortcuts when not in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.contentEditable === 'true') {
            return;
        }
        
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'h':
                    e.preventDefault();
                    window.location.href = '/';
                    break;
                case 'n':
                    e.preventDefault();
                    if (window.location.pathname.includes('/patients/')) {
                        window.location.href = '/patients/ajouter/';
                    } else if (window.location.pathname.includes('/rendez-vous/')) {
                        window.location.href = '/rendez-vous/ajouter/';
                    }
                    break;
                case 'p':
                    e.preventDefault();
                    window.location.href = '/planning/';
                    break;
                case 'f':
                    e.preventDefault();
                    const searchInput = document.querySelector('input[type="search"], input[name="search"], input[name="query"]');
                    if (searchInput) {
                        searchInput.focus();
                        searchInput.select();
                    }
                    break;
            }
        }
    });
}

// Utility Functions

// Phone number formatting
function formatPhoneNumber(input) {
    let value = input.value.replace(/\D/g, '');
    
    if (value.startsWith('33')) {
        value = '+' + value;
    } else if (value.startsWith('0') && value.length === 10) {
        // French mobile/landline
        value = value.replace(/(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/, '$1 $2 $3 $4 $5');
    }
    
    input.value = value;
}

// Date validation
function validateDate(input) {
    const date = new Date(input.value);
    const today = new Date();
    
    if (input.classList.contains('future-only') && date < today) {
        input.setCustomValidity('La date doit être dans le futur');
        input.classList.add('is-invalid');
    } else if (input.classList.contains('past-only') && date > today) {
        input.setCustomValidity('La date doit être dans le passé');
        input.classList.add('is-invalid');
    } else {
        input.setCustomValidity('');
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    }
}

// Make table sortable
function makeTableSortable(table) {
    const headers = table.querySelectorAll('th[data-sortable]');
    
    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.innerHTML += ' <i class="fas fa-sort text-muted"></i>';
        
        header.addEventListener('click', function() {
            const column = this.dataset.sortable;
            const currentSort = this.dataset.sort || 'none';
            
            // Reset all other headers
            headers.forEach(h => {
                if (h !== this) {
                    h.dataset.sort = 'none';
                    const icon = h.querySelector('i');
                    if (icon) {
                        icon.className = 'fas fa-sort text-muted';
                    }
                }
            });
            
            // Update current header
            let newSort = 'asc';
            if (currentSort === 'asc') {
                newSort = 'desc';
            }
            
            this.dataset.sort = newSort;
            const icon = this.querySelector('i');
            if (icon) {
                icon.className = `fas fa-sort-${newSort === 'asc' ? 'up' : 'down'} text-primary`;
            }
            
            sortTable(table, column, newSort);
        });
    });
}

// Sort table
function sortTable(table, column, direction) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aVal = a.querySelector(`[data-sort="${column}"]`)?.textContent || a.cells[column]?.textContent || '';
        const bVal = b.querySelector(`[data-sort="${column}"]`)?.textContent || b.cells[column]?.textContent || '';
        
        // Try to parse as numbers
        const aNum = parseFloat(aVal.replace(/[^\d.-]/g, ''));
        const bNum = parseFloat(bVal.replace(/[^\d.-]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return direction === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison
        return direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// Filter table
function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm.toLowerCase())) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Appointment reminders
function setupAppointmentReminders() {
    // Check for appointments today
    const today = new Date().toDateString();
    const appointmentElements = document.querySelectorAll('[data-appointment-date]');
    
    appointmentElements.forEach(element => {
        const appointmentDate = new Date(element.dataset.appointmentDate).toDateString();
        if (appointmentDate === today) {
            element.classList.add('appointment-today');
            
            // Add notification if time is soon
            const appointmentTime = new Date(element.dataset.appointmentDate);
            const now = new Date();
            const timeDiff = appointmentTime - now;
            
            if (timeDiff > 0 && timeDiff < 30 * 60 * 1000) { // 30 minutes
                showAppointmentReminder(element.dataset.patientName, appointmentTime);
            }
        }
    });
}

// Show appointment reminder
function showAppointmentReminder(patientName, appointmentTime) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Rappel de rendez-vous', {
            body: `RDV avec ${patientName} à ${appointmentTime.toLocaleTimeString()}`,
            icon: '/static/favicon.ico',
            tag: 'appointment-reminder'
        });
    }
    
    // Also show in-app notification
    showToast(`Rappel: RDV avec ${patientName} à ${appointmentTime.toLocaleTimeString()}`, 'warning');
}

// Toast notifications
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: duration
    });
    
    bsToast.show();
    
    // Remove element after hiding
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Get or create toast container
function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    return container;
}

// Confirmation dialogs
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Loading spinner
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border spinner-border-sm me-2';
    spinner.setAttribute('role', 'status');
    
    if (element.tagName === 'BUTTON') {
        element.disabled = true;
        element.insertBefore(spinner, element.firstChild);
    }
    
    return spinner;
}

function hideLoading(element, spinner) {
    if (element.tagName === 'BUTTON') {
        element.disabled = false;
    }
    if (spinner && spinner.parentNode) {
        spinner.parentNode.removeChild(spinner);
    }
}

// AJAX utilities
function makeAjaxRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    // Add CSRF token for POST requests
    if (options.method === 'POST' || options.method === 'PUT' || options.method === 'DELETE') {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (csrfToken) {
            defaultOptions.headers['X-CSRFToken'] = csrfToken;
        }
    }
    
    return fetch(url, { ...defaultOptions, ...options });
}

// Local storage utilities
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (e) {
        console.warn('Could not save to localStorage:', e);
    }
}

function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : defaultValue;
    } catch (e) {
        console.warn('Could not load from localStorage:', e);
        return defaultValue;
    }
}

// Export functions for global use
window.CabinetMedical = {
    showToast,
    confirmAction,
    showLoading,
    hideLoading,
    makeAjaxRequest,
    saveToLocalStorage,
    loadFromLocalStorage,
    formatPhoneNumber
};

// Service Worker registration (for offline functionality)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
            }, function(err) {
                console.log('ServiceWorker registration failed');
            });
    });
}