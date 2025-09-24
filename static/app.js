// Global state
let token = localStorage.getItem('token'); // Tokeni localStorage'dan al
let currentUser = null;

// DOM Elements
const modalBackdrop = document.getElementById('modalBackdrop'); // Modal arka planı

// API endpoints
const API_URL = '/api';  // API endpoint prefix
const endpoints = {
    login: `${API_URL}/token`, // Login endpoint
    register: `${API_URL}/register`, // Register endpoint
    customers: `${API_URL}/customers`, // Customers endpoint
    customer: (id) => `${API_URL}/customers/${id}`, // Customer endpoint
    notes: (customerId) => `${API_URL}/customers/${customerId}/notes`, // Notes endpoint
    note: (customerId, noteId) => `${API_URL}/customers/${customerId}/notes/${noteId}`, // Note endpoint
};

// API Functions
async function createCustomer(customerData) { // Customer oluştur
    const response = await fetchAPI(endpoints.customers, { // Customers endpoint
        method: 'POST', // POST request
        body: JSON.stringify(customerData) // Customer data
    });
    return response;
}

async function deleteCustomer(customerId) { // Customer sil
    const response = await fetchAPI(endpoints.customer(customerId), { // Customer endpoint
        method: 'DELETE'
    });
    return response;
}

async function createNote(customerId, noteData) { // Note oluştur
    const response = await fetchAPI(endpoints.notes(customerId), {
        method: 'POST',
        body: JSON.stringify(noteData)
    });
    return response;
}


// Customer Search
let customerSearchTimeout;
const customerSearch = document.getElementById('customerSearch');
if (customerSearch) {
    customerSearch.addEventListener('input', (e) => {
        clearTimeout(customerSearchTimeout);
        customerSearchTimeout = setTimeout(() => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#customersList tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        }, 300);
    });
}

// DOM Elements
const elements = {
    loginWindow: document.getElementById('loginWindow'), // Login window
    crmWindow: document.getElementById('crmWindow'),
    loginError: document.getElementById('loginError'),
    email: document.getElementById('email'),
    password: document.getElementById('password'),
    loginBtn: document.getElementById('loginBtn'),
    registerBtn: document.getElementById('registerBtn'),
    logoutBtn: document.getElementById('logoutBtn'),
    customersTab: document.getElementById('customersTab'),
    notesTab: document.getElementById('notesTab'),
    customersSection: document.getElementById('customersSection'),
    notesSection: document.getElementById('notesSection'),
    customersList: document.getElementById('customersList'),
    notesList: document.getElementById('notesList'),
    customerSelect: document.getElementById('customerSelect'),
    addCustomerBtn: document.getElementById('addCustomerBtn'),
    addNoteBtn: document.getElementById('addNoteBtn'),
    addCustomerModal: document.getElementById('addCustomerModal'),
    addNoteModal: document.getElementById('addNoteModal'),
    customerName: document.getElementById('customerName'),
    customerEmail: document.getElementById('customerEmail'),
    customerPhone: document.getElementById('customerPhone'),
    customerCompany: document.getElementById('customerCompany'),
    noteContent: document.getElementById('noteContent'),
};

// API Helpers
async function fetchAPI(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
        console.log('Authorization header set:', headers['Authorization'].substring(0, 30) + '...');
    } else {
        console.log('No token available for request');
    }
    
    console.log('Making request to:', endpoint);
    console.log('Request headers:', headers);
    
    try {
        const response = await fetch(endpoint, {
            ...options,
            headers
        });

        if (response.status === 401) {
            showNotification('Session expired. Please login again.', 'error');
            logout();
            return null;
        }

        if (!response.ok) {
            let message = response.statusText;
            try {
                const data = await response.json();
                if (data && (data.detail || data.message)) {
                    message = data.detail || data.message;
                }
            } catch (_) {}
            throw new Error(message);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showNotification(error.message || 'Unexpected error', 'error');
        return null;
    }
}

// Authentication Functions
async function login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
        const response = await fetch(endpoints.login, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        const data = await response.json();
        token = data.access_token;
        localStorage.setItem('token', token);
        showCRMWindow();
    } catch (error) {
        elements.loginError.textContent = 'Invalid email or password';
    }
}

async function register(email, password) {
    try {
        const response = await fetchAPI(endpoints.register, {
            method: 'POST',
            body: JSON.stringify({
                email,
                password,
                full_name: email.split('@')[0]
            })
        });

        if (response) {
            await login(email, password);
        }
    } catch (error) {
        elements.loginError.textContent = 'Registration failed';
    }
}

function logout() {
    token = null;
    localStorage.removeItem('token');
    showLoginWindow();
}

// UI Functions
function showLoginWindow() {
    elements.loginWindow.classList.remove('hidden');
    elements.crmWindow.classList.add('hidden');
    elements.addCustomerModal.classList.add('hidden');
    elements.addNoteModal.classList.add('hidden');
}

function showCRMWindow() {
    elements.loginWindow.classList.add('hidden');
    elements.crmWindow.classList.remove('hidden');
    loadCustomers();
}

function showCustomersTab() {
    elements.customersTab.setAttribute('aria-selected', 'true');
    elements.notesTab.setAttribute('aria-selected', 'false');
    elements.customersSection.classList.remove('hidden');
    elements.notesSection.classList.add('hidden');
}

function showNotesTab() {
    elements.customersTab.setAttribute('aria-selected', 'false');
    elements.notesTab.setAttribute('aria-selected', 'true');
    elements.customersSection.classList.add('hidden');
    elements.notesSection.classList.remove('hidden');
    loadNotes();
}

// Data Loading Functions
async function loadCustomers() {
    try {
        const customers = await fetchAPI(endpoints.customers);
        if (customers) {
            renderCustomers(customers);
            updateCustomerSelect(customers);
        }
    } catch (error) {
        showNotification(error.message || 'Failed to load customers', 'error');
    }
}

async function loadNotes() {
    try {
        const customerId = elements.customerSelect.value;
        let notes = [];
        let customerName = '';
        
        if (customerId) {
            notes = await fetchAPI(endpoints.notes(customerId));
            const customer = await fetchAPI(endpoints.customer(customerId));
            if (customer) {
                customerName = customer.name;
            }
        } else {
            // Load notes for all customers
            const customers = await fetchAPI(endpoints.customers);
            if (customers) {
                for (const customer of customers) {
                    const customerNotes = await fetchAPI(endpoints.notes(customer.id));
                    if (customerNotes) {
                        notes = notes.concat(customerNotes);
                    }
                }
            }
        }

        if (notes) {
            renderNotes(notes, customerName);
        }
    } catch (error) {
        showNotification(error.message || 'Failed to load notes', 'error');
    }
}

async function viewNotes(customerId) {
    try {
        // Switch to notes tab
        elements.notesTab.click();
        
        // Select the customer in the dropdown
        elements.customerSelect.value = customerId;
        
        // Load notes for this customer
        await loadNotes();
    } catch (error) {
        showNotification(error.message || 'Failed to load customer notes', 'error');
    }
}

// Rendering Functions
function renderCustomers(customers) {
    if (!Array.isArray(customers)) {
        console.error('Invalid customers data:', customers);
        return;
    }

    elements.customersList.innerHTML = customers.map(customer => `
        <tr>
            <td>
                <div class="customer-info">
                    <span class="customer-name">${customer.name}</span>
                    ${customer.phone ? `<span class="customer-phone">${customer.phone}</span>` : ''}
                </div>
            </td>
            <td>${customer.email || '-'}</td>
            <td>${customer.company || '-'}</td>
            <td>
                <div class="table-actions">
                    <button class="btn btn-icon" onclick="viewNotes(${customer.id})" title="View Notes">
                        <i class="ri-file-list-line"></i>
                    </button>
                    <button class="btn btn-icon" onclick="deleteCustomer(${customer.id})" title="Delete Customer">
                        <i class="ri-delete-bin-line"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');

    // Update customer count
    document.getElementById('customerCount').textContent = customers.length;
}

function renderNotes(notes, customerName = '') {
    if (!Array.isArray(notes)) {
        console.error('Invalid notes data:', notes);
        return;
    }

    elements.notesList.innerHTML = notes.map(note => `
        <div class="note-card">
            <div class="note-header">
                <h4>${customerName || `Customer #${note.customer_id}`}</h4>
                <button class="btn btn-icon" onclick="deleteNote(${note.customer_id}, ${note.id})" title="Delete Note">
                    <i class="ri-delete-bin-line"></i>
                </button>
            </div>
            <div class="note-content">
                ${note.content}
            </div>
            <div class="note-footer">
                <span><i class="ri-time-line"></i> ${new Date(note.created_at).toLocaleString()}</span>
            </div>
        </div>
    `).join('');

    // Update note count
    document.getElementById('noteCount').textContent = notes.length;
}

function updateCustomerSelect(customers) {
    elements.customerSelect.innerHTML = `
        <option value="">Select Customer</option>
        ${customers.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
    `;
}

// Customer Functions
async function addCustomer() {
    try {
        console.log('=== ADD CUSTOMER DEBUG ===');
        console.log('Current token:', token ? 'Present' : 'Missing');
        console.log('Token length:', token ? token.length : 'N/A');
        
        // Validate form
        if (!elements.customerName.value.trim()) {
            showNotification('Customer name is required', 'error');
            return;
        }

        const customerData = {
            name: elements.customerName.value.trim(),
            email: elements.customerEmail.value.trim(),
            phone: elements.customerPhone.value.trim(),
            company: elements.customerCompany.value.trim()
        };
        
        console.log('Customer data:', customerData);

        // Show loading state
        const saveBtn = document.getElementById('saveCustomerBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="ri-loader-4-line"></i> Saving...';

        const response = await createCustomer(customerData);
        if (response) {
            elements.addCustomerModal.classList.add('hidden');
            modalBackdrop.classList.add('hidden');
            await loadCustomers();
            showNotification('Customer added successfully', 'success');
        }
    } catch (error) {
        showNotification(error.message || 'Failed to add customer', 'error');
    } finally {
        // Reset button state
        const saveBtn = document.getElementById('saveCustomerBtn');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="ri-save-line"></i> Save Customer';
    }
}

async function deleteCustomer(id) {
    try {
        if (!confirm('Are you sure you want to delete this customer?')) return;

        const response = await fetchAPI(endpoints.customer(id), {
            method: 'DELETE'
        });

        if (response !== null) {
            await loadCustomers();
            showNotification('Customer deleted successfully', 'success');
        }
    } catch (error) {
        showNotification(error.message || 'Failed to delete customer', 'error');
    }
}

// Note Functions
async function addNote() {
    try {
        const customerId = elements.customerSelect.value;
        if (!customerId) {
            showNotification('Please select a customer', 'error');
            return;
        }

        if (!elements.noteContent.value.trim()) {
            showNotification('Note content is required', 'error');
            return;
        }

        const noteData = {
            content: elements.noteContent.value.trim()
        };

        // Show loading state
        const saveBtn = document.getElementById('saveNoteBtn');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="ri-loader-4-line"></i> Saving...';

        const response = await createNote(customerId, noteData);
        if (response) {
            elements.addNoteModal.classList.add('hidden');
            modalBackdrop.classList.add('hidden');
            await loadNotes();
            showNotification('Note added successfully', 'success');
        }
    } catch (error) {
        showNotification(error.message || 'Failed to add note', 'error');
    } finally {
        // Reset button state
        const saveBtn = document.getElementById('saveNoteBtn');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="ri-save-line"></i> Save Note';
    }
}

async function deleteNote(customerId, noteId) {
    try {
        if (!confirm('Are you sure you want to delete this note?')) return;

        const response = await fetchAPI(endpoints.note(customerId, noteId), {
            method: 'DELETE'
        });

        if (response !== null) {
            await loadNotes();
            showNotification('Note deleted successfully', 'success');
        }
    } catch (error) {
        showNotification(error.message || 'Failed to delete note', 'error');
    }
}

// Event Listeners
elements.loginBtn.addEventListener('click', () => {
    login(elements.email.value, elements.password.value);
});

elements.registerBtn.addEventListener('click', () => {
    register(elements.email.value, elements.password.value);
});

elements.logoutBtn.addEventListener('click', logout);

elements.customersTab.addEventListener('click', showCustomersTab);
elements.notesTab.addEventListener('click', showNotesTab);

elements.addCustomerBtn.addEventListener('click', () => {
    // Clear form
    elements.customerName.value = '';
    elements.customerEmail.value = '';
    elements.customerPhone.value = '';
    elements.customerCompany.value = '';
    
    // Show modal
    elements.addCustomerModal.classList.remove('hidden');
    modalBackdrop.classList.remove('hidden');
});

elements.addNoteBtn.addEventListener('click', () => {
    if (elements.customerSelect.value) {
        elements.addNoteModal.classList.remove('hidden');
        modalBackdrop.classList.remove('hidden');
    } else {
        alert('Please select a customer first');
    }
});

document.getElementById('saveCustomerBtn').addEventListener('click', addCustomer);
document.getElementById('cancelCustomerBtn').addEventListener('click', () => {
    elements.addCustomerModal.classList.add('hidden');
    modalBackdrop.classList.add('hidden');
});

document.getElementById('saveNoteBtn').addEventListener('click', addNote);
document.getElementById('cancelNoteBtn').addEventListener('click', () => {
    elements.addNoteModal.classList.add('hidden');
    modalBackdrop.classList.add('hidden');
});

document.getElementById('closeCustomerModal').addEventListener('click', () => {
    elements.addCustomerModal.classList.add('hidden');
    modalBackdrop.classList.add('hidden');
});

document.getElementById('closeNoteModal').addEventListener('click', () => {
    elements.addNoteModal.classList.add('hidden');
    modalBackdrop.classList.add('hidden');
});

elements.customerSelect.addEventListener('change', loadNotes);

// Check for registration success message
function checkRegistrationSuccess() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('registered') === 'true') {
        elements.loginError.style.color = 'var(--success)';
        elements.loginError.textContent = 'Account created successfully! Please login.';
        // Remove the query parameter
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="ri-${type === 'success' ? 'checkbox-circle' : type === 'error' ? 'error-warning' : 'information'}-line"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}


// Test function for debugging
window.testAddCustomer = async function() {
    console.log('Testing add customer API...');
    console.log('Current token:', token);
    
    const testData = {
        name: 'Test Customer',
        email: 'test@example.com',
        phone: '123-456-7890',
        company: 'Test Company'
    };
    
    try {
        const response = await fetch('/api/customers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(testData)
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        
        if (response.ok) {
            const data = await response.json();
            console.log('Success:', data);
        } else {
            const errorText = await response.text();
            console.log('Error:', errorText);
        }
    } catch (error) {
        console.log('Exception:', error);
    }
};

// Initialize
if (token) {
    showCRMWindow();
} else {
    showLoginWindow();
    checkRegistrationSuccess();
}
