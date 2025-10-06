// Global state
let token = localStorage.getItem('token'); // Access token'ı localStorage'dan al
let refreshToken = localStorage.getItem('refreshToken'); // Refresh token'ı localStorage'dan al
let currentUser = null;
let selectedNotesCustomerId = null; // currently selected customer for notes view
let currentTheme = localStorage.getItem('theme') || 'light'; // Theme state

// DOM Elements
const modalBackdrop = document.getElementById('modalBackdrop'); // Modal arka planı

// API endpoints - Updated for Router structure
const API_URL = '/api';  // API endpoint prefix
const endpoints = {
    // Authentication endpoints (moved to /api/auth)
    login: `${API_URL}/auth/token`, // Login endpoint
    refresh: `${API_URL}/auth/refresh`, // Refresh token endpoint
    register: `${API_URL}/auth/register`, // Register endpoint
    logout: `${API_URL}/auth/logout`, // Logout endpoint
    me: `${API_URL}/auth/me`, // Current user endpoint
    myTokens: `${API_URL}/auth/me/tokens`, // User tokens endpoint
    
    // Customer endpoints (unchanged)
    customers: `${API_URL}/customers`, // Customers endpoint
    customer: (id) => `${API_URL}/customers/${id}`, // Customer endpoint
    
    // Notes endpoints (unchanged)
    notes: (customerId) => `${API_URL}/customers/${customerId}/notes`, // Notes endpoint
    note: (customerId, noteId) => `${API_URL}/customers/${customerId}/notes/${noteId}`, // Note endpoint
    
    // System endpoints (moved to /api/system)
    health: `${API_URL}/system/health`, // Health check endpoint
    debug: `${API_URL}/system/debug/database`, // Debug endpoint
    stats: `${API_URL}/system/stats`, // System stats endpoint
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

async function updateNote(customerId, noteId, noteData) { // Note güncelle
    const response = await fetchAPI(endpoints.note(customerId, noteId), {
        method: 'PUT',
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
        customerSearchTimeout = setTimeout(async () => {
            const searchTerm = e.target.value.trim();
            if (searchTerm.length >= 2 || searchTerm.length === 0) {
                await loadCustomers(searchTerm);
            }
        }, 500); // Increased timeout for better UX
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
    logoutBtn: document.getElementById('logoutBtn'),
    themeToggle: document.getElementById('themeToggle'),
    themeIcon: document.getElementById('themeIcon'),
    themeText: document.getElementById('themeText'),
    dashboardTab: document.getElementById('dashboardTab'), // Added missing dashboardTab
    customersTab: document.getElementById('customersTab'),
    notesTab: document.getElementById('notesTab'),
    customersSection: document.getElementById('customersSection'),
    notesSection: document.getElementById('notesSection'),
    dashboardSection: document.getElementById('dashboardSection'),
    customersList: document.getElementById('customersList'),
    notesList: document.getElementById('notesList'),
    customerSelect: document.getElementById('customerSelect'),
    totalCustomers: document.getElementById('totalCustomers'),
    activeCustomers: document.getElementById('activeCustomers'),
    totalNotes: document.getElementById('totalNotes'),
    recentActivity: document.getElementById('recentActivity'),
    recentCustomersList: document.getElementById('recentCustomersList'),
    addCustomerBtn: document.getElementById('addCustomerBtn'),
    addNoteBtn: document.getElementById('addNoteBtn'),
    refreshDataBtn: document.getElementById('refreshDataBtn'),
    refreshNotesBtn: document.getElementById('refreshNotesBtn'),
    addCustomerModal: document.getElementById('addCustomerModal'),
    addNoteModal: document.getElementById('addNoteModal'),
    customerName: document.getElementById('customerName'),
    customerEmail: document.getElementById('customerEmail'),
    customerPhone: document.getElementById('customerPhone'),
    customerCompany: document.getElementById('customerCompany'),
    customerStatus: document.getElementById('customerStatus'),
    noteContent: document.getElementById('noteContent'),
};

// Token Management
async function refreshAccessToken() {
    if (!refreshToken) {
        console.log('No refresh token available');
        return false;
    }

    try {
        console.log('Attempting to refresh access token...');
        const response = await fetch(endpoints.refresh, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                refresh_token: refreshToken
            })
        });

        if (!response.ok) {
            console.log('Refresh token failed:', response.status);
            return false;
        }

        const data = await response.json();
        
        // Update tokens
        token = data.access_token;
        refreshToken = data.refresh_token;
        
        // Save to localStorage
        localStorage.setItem('token', token);
        localStorage.setItem('refreshToken', refreshToken);
        
        console.log('Access token refreshed successfully');
        return true;
    } catch (error) {
        console.error('Token refresh error:', error);
        return false;
    }
}

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
            console.log('401 Unauthorized - attempting token refresh...');
            
            // Try to refresh token
            const refreshSuccess = await refreshAccessToken();
            if (refreshSuccess) {
                console.log('Token refreshed, retrying original request...');
                
                // Retry original request with new token
                const retryHeaders = {
                    ...headers,
                    'Authorization': `Bearer ${token}`
                };
                
                const retryResponse = await fetch(endpoint, {
                    ...options,
                    headers: retryHeaders
                });
                
                if (retryResponse.ok) {
                    try {
                        return await retryResponse.json();
                    } catch (jsonError) {
                        console.warn('Retry response was successful but not valid JSON, returning null');
                        return null;
                    }
                }
            }
            
            // If refresh failed or retry failed, logout
            showNotification('Session expired. Please login again.', 'error');
            logout();
            return null;
        }

        if (!response.ok) {
            let message = response.statusText;
            
            try {
                // Clone the response to avoid "body stream already read" error
                const responseClone = response.clone();
                const responseText = await responseClone.text();
                console.log('Response text:', responseText);
                
                // Try to parse as JSON
                if (responseText) {
                    try {
                        const data = JSON.parse(responseText);
                        if (data && (data.detail || data.message)) {
                            message = data.detail || data.message;
                        }
                    } catch (parseError) {
                        console.error('JSON parse error:', parseError);
                        
                        // If it's HTML (like an error page), provide a better message
                        if (responseText.includes('<html>') || responseText.includes('<!DOCTYPE')) {
                            message = `Server returned HTML instead of JSON (Status: ${response.status}). This might be a server error or authentication issue.`;
                        } else {
                            message = `Invalid JSON response (Status: ${response.status}): ${responseText.substring(0, 100)}...`;
                        }
                    }
                }
            } catch (textError) {
                console.error('Error reading response text:', textError);
                message = `Failed to read error response (Status: ${response.status})`;
            }
            throw new Error(message);
        }

        // Try to parse JSON response
        try {
            return await response.json();
        } catch (jsonError) {
            console.error('JSON parse error in successful response:', jsonError);
            // For successful responses, if JSON parsing fails, return null instead of throwing
            console.warn('Response was successful but not valid JSON, returning null');
            return null;
        }
    } catch (error) {
        console.error('API Error:', error);
        const msg = typeof error?.message === 'string' ? error.message : JSON.stringify(error);
        showNotification(msg || 'Unexpected error', 'error');
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
        refreshToken = data.refresh_token;
        
        localStorage.setItem('token', token);
        localStorage.setItem('refreshToken', refreshToken);
        
        console.log('Login successful, tokens saved');
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

async function logout() {
    try {
        // Call backend logout endpoint if token exists
        if (token) {
            try {
                await fetchAPI(endpoints.logout, {
                    method: 'POST'
                });
            } catch (error) {
                // Ignore backend logout errors, continue with client-side logout
                console.warn('Backend logout failed:', error);
            }
        }
    } catch (error) {
        console.warn('Logout API call failed:', error);
    } finally {
        // Clear all user data
        token = null;
        refreshToken = null;
        currentUser = null;
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        
        // Clear any form data
        if (elements.email) elements.email.value = '';
        if (elements.password) elements.password.value = '';
        if (elements.loginError) elements.loginError.textContent = '';
        
        // Reset UI state
    showLoginWindow();
        
        // Show logout confirmation
        showNotification('Logged out successfully', 'success');
    }
}

// Theme Functions
function initTheme() {
    // Apply saved theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeUI();
}

function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
    updateThemeUI();
    showNotification(`Switched to ${currentTheme} mode`, 'success');
}

function updateThemeUI() {
    if (elements.themeIcon && elements.themeText) {
        if (currentTheme === 'dark') {
            elements.themeIcon.className = 'ri-moon-line';
            elements.themeText.textContent = 'Dark Mode';
        } else {
            elements.themeIcon.className = 'ri-sun-line';
            elements.themeText.textContent = 'Light Mode';
        }
    }
}

// UI Functions
function showLoginWindow() {
    // Hide CRM window and show login window
    elements.loginWindow.classList.remove('hidden');
    elements.crmWindow.classList.add('hidden');
    
    // Hide all modals
    elements.addCustomerModal.classList.add('hidden');
    elements.addNoteModal.classList.add('hidden');
    modalBackdrop.classList.add('hidden');
    
    // Reset form fields
    if (elements.email) elements.email.value = '';
    if (elements.password) elements.password.value = '';
    if (elements.loginError) elements.loginError.textContent = '';
    
    // Clear any data lists
    if (elements.customersList) elements.customersList.innerHTML = '';
    if (elements.notesList) elements.notesList.innerHTML = '';
    
    // Reset customer count
    const customerCountEl = document.getElementById('customerCount');
    if (customerCountEl) customerCountEl.textContent = '0';
    
    // Reset note count
    const noteCountEl = document.getElementById('noteCount');
    if (noteCountEl) noteCountEl.textContent = '0';
}

function showCRMWindow() {
    elements.loginWindow.classList.add('hidden');
    elements.crmWindow.classList.remove('hidden');
    
    // Initialize UI state - show dashboard section by default
    elements.dashboardSection.classList.remove('hidden');
    elements.customersSection.classList.add('hidden');
    elements.notesSection.classList.add('hidden');
    
    // Set active tab - dashboard by default
    elements.dashboardTab.classList.add('active');
    elements.customersTab.classList.remove('active');
    elements.notesTab.classList.remove('active');
    
    // Load dashboard data
    loadDashboard();
    // Also load customers for the dropdown in notes section
    loadCustomers();
}

function showDashboardTab() {
    // Update tab states
    elements.dashboardTab.classList.add('active');
    elements.customersTab.classList.remove('active');
    elements.notesTab.classList.remove('active');
    
    // Update sections
    elements.dashboardSection.classList.remove('hidden');
    elements.customersSection.classList.add('hidden');
    elements.notesSection.classList.add('hidden');
    
    loadDashboard();
}

function showCustomersTab() {
    // Update tab states
    elements.dashboardTab.classList.remove('active');
    elements.customersTab.classList.add('active');
    elements.notesTab.classList.remove('active');
    
    // Update sections
    elements.dashboardSection.classList.add('hidden');
    elements.customersSection.classList.remove('hidden');
    elements.notesSection.classList.add('hidden');
    
    loadCustomers();
}

function showNotesTab() {
    // Update tab states
    elements.dashboardTab.classList.remove('active');
    elements.customersTab.classList.remove('active');
    elements.notesTab.classList.add('active');
    
    // Update sections
    elements.dashboardSection.classList.add('hidden');
    elements.customersSection.classList.add('hidden');
    elements.notesSection.classList.remove('hidden');
    
    // Load customers for the dropdown first, then load notes
    loadCustomers().then(() => {
        loadNotes();
    });
}

// Data Loading Functions
async function refreshAllData() {
    // Refresh all data across the application
    try {
        await Promise.all([
            loadDashboard(),
            loadCustomers(),
            loadNotes()
        ]);
        showNotification('Data refreshed successfully', 'success');
    } catch (error) {
        console.error('Failed to refresh data:', error);
        showNotification('Failed to refresh data', 'error');
    }
}

async function loadDashboard() {
    try {
        // Load customers for dashboard
        const customers = await fetchAPI(endpoints.customers);
        let totalNotes = 0;
        
        // Load notes for all customers
        if (customers && customers.length > 0) {
            for (const customer of customers) {
                try {
                    const customerNotes = await fetchAPI(endpoints.notes(customer.id));
                    if (customerNotes) {
                        totalNotes += customerNotes.length;
                    }
                } catch (error) {
                    console.warn(`Failed to load notes for customer ${customer.id}:`, error);
                }
            }
        }
        
        if (customers) {
            // Update dashboard stats
            elements.totalCustomers.textContent = customers.length;
            
            // Count active customers
            const activeCount = customers.filter(c => c.status === 'Active').length;
            elements.activeCustomers.textContent = activeCount;
            
            // Show recent customers (last 5)
            const recentCustomers = customers.slice(0, 5);
            elements.recentCustomersList.innerHTML = recentCustomers.length > 0 
                ? recentCustomers.map(customer => `
                    <div class="recent-item">
                        <div class="recent-info">
                            <span class="recent-name">${customer.name}</span>
                            <span class="recent-company">${customer.company || 'No company'}</span>
                        </div>
                        <span class="status-badge status-${(customer.status || 'Active').toLowerCase()}">${customer.status || 'Active'}</span>
                    </div>
                `).join('')
                : '<p class="text-muted">No customers yet</p>';
        }
        
        // Update notes count
        elements.totalNotes.textContent = totalNotes;
        
        // Set recent activity (placeholder)
        elements.recentActivity.textContent = customers ? customers.length : 0;
        
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

async function loadCustomers(searchTerm = '') {
    try {
        const url = searchTerm ? `${endpoints.customers}?search=${encodeURIComponent(searchTerm)}` : endpoints.customers;
        const customers = await fetchAPI(url);
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
        // Use remembered selection when header select not available
        const headerSelect = elements.customerSelect; // may be null
        const customerId = (headerSelect && headerSelect.value) ? headerSelect.value : (selectedNotesCustomerId || '');
        let notes = [];
        let customerName = '';
        
        if (customerId) {
            // Load notes for specific customer
            const notesResponse = await fetchAPI(endpoints.notes(customerId));
            if (notesResponse) {
                notes = notesResponse;
                
                // Get customer name
                const customer = await fetchAPI(endpoints.customer(customerId));
                if (customer) {
                    customerName = customer.name;
                }
            }
        } else {
            // Load notes for all customers
            const customers = await fetchAPI(endpoints.customers);
            if (customers && customers.length > 0) {
                const allNotesPromises = customers.map(async (customer) => {
                    try {
                        const customerNotes = await fetchAPI(endpoints.notes(customer.id));
                        if (customerNotes && customerNotes.length > 0) {
                            // Add customer name to each note for display
                            return customerNotes.map(note => ({
                                ...note,
                                customerName: customer.name
                            }));
                        }
                        return [];
                    } catch (error) {
                        console.warn(`Failed to load notes for customer ${customer.id}:`, error);
                        return [];
                    }
                });
                
                const allNotesArrays = await Promise.all(allNotesPromises);
                notes = allNotesArrays.flat();
            }
        }

        renderNotes(notes, customerName);
    } catch (error) {
        console.error('Failed to load notes:', error);
        showNotification(error.message || 'Failed to load notes', 'error');
    }
}

async function viewNotes(customerId) {
    try {
        // Switch to notes tab
        elements.notesTab.click();
        
        // Remember current selection
        selectedNotesCustomerId = customerId;
        
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
            <td><span class="status-badge status-${(customer.status || 'Active').toLowerCase()}">${customer.status || 'Active'}</span></td>
            <td>
                <div class="table-actions">
                    <button class="btn btn-icon" onclick="editCustomer(${customer.id})" title="Edit Customer">
                        <i class="ri-edit-line"></i>
                    </button>
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
        elements.notesList.innerHTML = '<div class="no-data">No notes found</div>';
        document.getElementById('noteCount').textContent = '0';
        return;
    }

    if (notes.length === 0) {
        elements.notesList.innerHTML = '<div class="no-data">No notes found</div>';
        document.getElementById('noteCount').textContent = '0';
        return;
    }

    elements.notesList.innerHTML = notes.map(note => {
        // Use customerName from note object if available, otherwise use the passed customerName
        const displayName = note.customerName || customerName || `Customer #${note.customer_id}`;
        
        return `
            <div class="note-card">
                <div class="note-header">
                    <h4>${displayName}</h4>
                    <div>
                        <button class="btn btn-icon" onclick="startEditNote(${note.customer_id}, ${note.id}, ${JSON.stringify(note.content).replace(/"/g, '&quot;')})" title="Edit Note">
                            <i class="ri-edit-line"></i>
                        </button>
                        <button class="btn btn-icon" onclick="deleteNote(${note.customer_id}, ${note.id})" title="Delete Note">
                        <i class="ri-delete-bin-line"></i>
                        </button>
                    </div>
                </div>
                <div class="note-content">
                    ${note.content}
                </div>
                <div class="note-footer">
                    <span><i class="ri-time-line"></i> ${new Date(note.created_at).toLocaleString()}</span>
                </div>
            </div>
        `;
    }).join('');

    // Update note count
    document.getElementById('noteCount').textContent = notes.length;
}

function updateCustomerSelect(customers) {
    // Header customerSelect may not exist (we moved selection into modal)
    if (!elements.customerSelect) {
        return; // Nothing to update
    }
    if (!customers || !Array.isArray(customers)) {
        elements.customerSelect.innerHTML = '<option value="">No customers available</option>';
        return;
    }
    elements.customerSelect.innerHTML = `
        <option value="">All Customers</option>
        ${customers.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
    `;
}

// Customer Functions
async function addCustomer() {
    try {
        console.log('=== ADD/UPDATE CUSTOMER DEBUG ===');
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
            company: elements.customerCompany.value.trim(),
            status: (elements.customerStatus.value || '').toUpperCase()
        };
        
        console.log('Customer data:', customerData);

        // Show loading state
        const saveBtn = document.getElementById('saveCustomerBtn');
        const originalText = saveBtn.innerHTML;
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="ri-loader-4-line"></i> Saving...';

        // Check if we're editing an existing customer
        const customerId = elements.addCustomerModal.dataset.customerId;
        let response;
        
        if (customerId) {
            // Update existing customer
            response = await fetchAPI(endpoints.customer(customerId), {
                method: 'PUT',
                body: JSON.stringify(customerData)
            });
        } else {
            // Create new customer
            response = await createCustomer(customerData);
        }
        
        if (response) {
            elements.addCustomerModal.classList.add('hidden');
            modalBackdrop.classList.add('hidden');
            
            // Refresh all data after add/update
            await Promise.all([
                loadCustomers(),
                loadDashboard(),
                loadNotes()
            ]);
            
            const message = customerId ? 'Customer updated successfully' : 'Customer added successfully';
            showNotification(message, 'success');
            
            // Reset form and modal state
            resetCustomerForm();
        }
    } catch (error) {
        showNotification(error.message || 'Failed to save customer', 'error');
    } finally {
        // Reset button state
        const saveBtn = document.getElementById('saveCustomerBtn');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="ri-save-line"></i> Save Customer';
    }
}

function resetCustomerForm() {
    // Clear form fields
    elements.customerName.value = '';
    elements.customerEmail.value = '';
    elements.customerPhone.value = '';
    elements.customerCompany.value = '';
    elements.customerStatus.value = 'Active';
    
    // Remove customer ID from modal
    delete elements.addCustomerModal.dataset.customerId;
    
    // Reset modal title and button
    const modalTitle = elements.addCustomerModal.querySelector('.modal-title');
    const submitBtn = elements.addCustomerModal.querySelector('.btn-primary');
    
    if (modalTitle) modalTitle.textContent = 'Add New Customer';
    if (submitBtn) submitBtn.textContent = 'Add Customer';
}

async function deleteCustomer(id) {
    try {
        if (!confirm('Are you sure you want to delete this customer?')) return;

        const response = await fetchAPI(endpoints.customer(id), {
            method: 'DELETE'
        });

        if (response !== null) {
            // Refresh all data after deletion
            await Promise.all([
                loadCustomers(),
                loadDashboard(),
                loadNotes()
            ]);
            showNotification('Customer deleted successfully', 'success');
        }
    } catch (error) {
        showNotification(error.message || 'Failed to delete customer', 'error');
    }
}

async function editCustomer(id) {
    try {
        // Get customer data
        const customer = await fetchAPI(endpoints.customer(id));
        
        // Populate edit form
        elements.customerName.value = customer.name || '';
        elements.customerEmail.value = customer.email || '';
        elements.customerPhone.value = customer.phone || '';
        elements.customerCompany.value = customer.company || '';
        elements.customerStatus.value = customer.status || 'Active';
        
        // Store customer ID for update
        elements.addCustomerModal.dataset.customerId = id;
        
        // Change modal title and button
        const modalTitle = elements.addCustomerModal.querySelector('.modal-title');
        const submitBtn = elements.addCustomerModal.querySelector('.btn-primary');
        
        if (modalTitle) modalTitle.textContent = 'Edit Customer';
        if (submitBtn) submitBtn.textContent = 'Update Customer';
        
        // Show modal
        elements.addCustomerModal.classList.remove('hidden');
    } catch (error) {
        showNotification(error.message || 'Failed to load customer data', 'error');
    }
}

// Note Functions
async function addNote() {
    try {
        // Prefer modal's customer selector; fallback to header select
        const modalSelect = document.getElementById('noteCustomerSelect');
        const customerId = (modalSelect && modalSelect.value) ? modalSelect.value : elements.customerSelect?.value;
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

        // If editing, call update; else create
        const isEditing = elements.addNoteModal.dataset.editing === 'true';
        const existingNoteId = elements.addNoteModal.dataset.noteId;
        let response;
        if (isEditing && existingNoteId) {
            response = await updateNote(customerId, existingNoteId, noteData);
        } else {
            response = await createNote(customerId, noteData);
        }
        if (response) {
            elements.addNoteModal.classList.add('hidden');
            modalBackdrop.classList.add('hidden');
            
            // Reset form
            elements.noteContent.value = '';
            const modalSelect2 = document.getElementById('noteCustomerSelect');
            if (modalSelect2) modalSelect2.value = '';
            // Clear editing context
            delete elements.addNoteModal.dataset.editing;
            delete elements.addNoteModal.dataset.noteId;
            delete elements.addNoteModal.dataset.customerId;
            
            // Refresh all data after adding note
            await Promise.all([
                loadNotes(),
                loadDashboard(),
                loadCustomers()
            ]);
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
            // Refresh all data after deletion
            await Promise.all([
                loadNotes(),
                loadDashboard(),
                loadCustomers()
            ]);
            showNotification('Note deleted successfully', 'success');
        }
    } catch (error) {
        showNotification(error.message || 'Failed to delete note', 'error');
    }
}

// Start editing a note: reuse the Add Note modal
function startEditNote(customerId, noteId, content) {
    try {
        // Open modal
        elements.addNoteModal.classList.remove('hidden');
        modalBackdrop.classList.remove('hidden');
        
        // Fill fields
        const modalSelect = document.getElementById('noteCustomerSelect');
        if (modalSelect) {
            // Ensure the customer is present in the dropdown
            if (![...modalSelect.options].some(o => o.value == String(customerId))) {
                const opt = document.createElement('option');
                opt.value = customerId;
                opt.textContent = `Customer #${customerId}`;
                modalSelect.appendChild(opt);
            }
            modalSelect.value = String(customerId);
        }
        elements.noteContent.value = content || '';
        
        // Store editing context on modal element
        elements.addNoteModal.dataset.editing = 'true';
        elements.addNoteModal.dataset.customerId = String(customerId);
        elements.addNoteModal.dataset.noteId = String(noteId);
        
        // Update button text
        const saveBtn = document.getElementById('saveNoteBtn');
        if (saveBtn) saveBtn.innerHTML = '<i class="ri-save-line"></i> Update Note';
    } catch (e) {
        showNotification('Failed to open edit note dialog', 'error');
    }
}

// Event Listeners
function setupEventListeners() {
    if (elements.loginBtn) {
elements.loginBtn.addEventListener('click', () => {
    login(elements.email.value, elements.password.value);
});
    }

    if (elements.logoutBtn) {
        elements.logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            try {
                // Ask for confirmation before logout
                if (confirm('Are you sure you want to logout?')) {
                    logout();
                }
            } catch (error) {
                console.error('Logout error:', error);
                showNotification('Error during logout', 'error');
            }
        });
    }

    if (elements.themeToggle) {
        elements.themeToggle.addEventListener('click', (e) => {
            e.preventDefault();
            toggleTheme();
        });
    }

    // Other event listeners
    if (elements.dashboardTab) {
elements.dashboardTab.addEventListener('click', showDashboardTab);
    }
    if (elements.customersTab) {
elements.customersTab.addEventListener('click', showCustomersTab);
    }
    if (elements.notesTab) {
elements.notesTab.addEventListener('click', showNotesTab);
    }

    if (elements.addCustomerBtn) {
elements.addCustomerBtn.addEventListener('click', () => {
    // Reset form and modal state
    resetCustomerForm();
    
    // Show modal
    elements.addCustomerModal.classList.remove('hidden');
    modalBackdrop.classList.remove('hidden');
});
    }

    if (elements.addNoteBtn) {
        elements.addNoteBtn.addEventListener('click', async () => {
            // Open modal regardless of selection
            elements.addNoteModal.classList.remove('hidden');
            modalBackdrop.classList.remove('hidden');
            
            // Populate customer dropdown inside modal
            try {
                const customers = await fetchAPI(endpoints.customers);
                const select = document.getElementById('noteCustomerSelect');
                if (select) {
                    select.innerHTML = '<option value="">Select customer...</option>';
                    if (Array.isArray(customers)) {
                        customers.forEach(c => {
                            const opt = document.createElement('option');
                            opt.value = c.id;
                            opt.textContent = c.name || `Customer #${c.id}`;
                            select.appendChild(opt);
                        });
                    }
                }
            } catch (e) {
                console.warn('Failed to load customers for note modal');
            }
        });
    }

    // Refresh buttons
    if (elements.refreshDataBtn) {
        elements.refreshDataBtn.addEventListener('click', refreshAllData);
    }

    if (elements.refreshNotesBtn) {
        elements.refreshNotesBtn.addEventListener('click', async () => {
            await loadNotes();
            showNotification('Notes refreshed', 'success');
        });
    }

    const saveCustomerBtn = document.getElementById('saveCustomerBtn');
    if (saveCustomerBtn) {
        saveCustomerBtn.addEventListener('click', addCustomer);
    }

    const cancelCustomerBtn = document.getElementById('cancelCustomerBtn');
    if (cancelCustomerBtn) {
        cancelCustomerBtn.addEventListener('click', () => {
    elements.addCustomerModal.classList.add('hidden');
    modalBackdrop.classList.add('hidden');
});
    }

    const saveNoteBtn = document.getElementById('saveNoteBtn');
    if (saveNoteBtn) {
        saveNoteBtn.addEventListener('click', addNote);
    }

    const cancelNoteBtn = document.getElementById('cancelNoteBtn');
    if (cancelNoteBtn) {
        cancelNoteBtn.addEventListener('click', () => {
    elements.addNoteModal.classList.add('hidden');
    modalBackdrop.classList.add('hidden');
});
    }

    const closeCustomerModal = document.getElementById('closeCustomerModal');
    if (closeCustomerModal) {
        closeCustomerModal.addEventListener('click', () => {
    elements.addCustomerModal.classList.add('hidden');
    modalBackdrop.classList.add('hidden');
});
    }

    const closeNoteModal = document.getElementById('closeNoteModal');
    if (closeNoteModal) {
        closeNoteModal.addEventListener('click', () => {
    elements.addNoteModal.classList.add('hidden');
    modalBackdrop.classList.add('hidden');
});
    }

    if (elements.customerSelect) {
elements.customerSelect.addEventListener('change', loadNotes);
    }
}

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



// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+Q for logout
    if (e.ctrlKey && e.key === 'q') {
        e.preventDefault();
        if (elements.logoutBtn && !elements.logoutBtn.closest('.hidden')) {
            elements.logoutBtn.click();
        }
    }
    
    // Ctrl+T for theme toggle
    if (e.ctrlKey && e.key === 't') {
        e.preventDefault();
        if (elements.themeToggle && !elements.themeToggle.closest('.hidden')) {
            elements.themeToggle.click();
        }
    }
    
    // Ctrl+R for refresh data
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        if (elements.refreshDataBtn && !elements.refreshDataBtn.closest('.hidden')) {
            elements.refreshDataBtn.click();
        }
    }
});

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initTheme();
    
    // Set up event listeners
    setupEventListeners();

    if (token) {
        showCRMWindow();
        } else {
        showLoginWindow();
        checkRegistrationSuccess();
    }
});

// Also initialize immediately in case DOM is already loaded
if (document.readyState !== 'loading') {
    // Initialize theme
    initTheme();
    
    // Set up event listeners
    setupEventListeners();

    if (token) {
        showCRMWindow();
    } else {
        showLoginWindow();
        checkRegistrationSuccess();
    }
}
