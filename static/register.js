// DOM Elements
const elements = {
    registerForm: document.getElementById('registerForm'),
    fullName: document.getElementById('fullName'),
    email: document.getElementById('email'),
    password: document.getElementById('password'),
    confirmPassword: document.getElementById('confirmPassword'),
    registerBtn: document.getElementById('registerBtn'),
    registerError: document.getElementById('registerError')
};

// Form validation
function validateForm() {
    // Reset error
    clearError();

    // Check required fields
    if (!elements.fullName.value.trim()) {
        showError("Full name is required");
        return false;
    }

    if (!elements.email.value.trim()) {
        showError("Email is required");
        return false;
    }

    if (!elements.password.value) {
        showError("Password is required");
        return false;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(elements.email.value)) {
        showError("Please enter a valid email address");
        return false;
    }

    // Check password length
    if (elements.password.value.length < 8) {
        showError("Password must be at least 8 characters long");
        return false;
    }

    // Check password match
    if (elements.password.value !== elements.confirmPassword.value) {
        showError("Passwords don't match");
        return false;
    }

    return true;
}

// Show error message
function showError(message) {
    elements.registerError.textContent = message;
    elements.registerError.style.display = 'block';
}

// Clear error message
function clearError() {
    elements.registerError.textContent = '';
    elements.registerError.style.display = 'none';
}

// Show OAuth2 credentials
function showOAuth2Credentials(credentials) {
    const modal = document.createElement('div');
    modal.className = 'oauth2-modal';
    modal.innerHTML = `
        <div class="oauth2-modal-content">
            <div class="oauth2-header">
                <h2><i class="ri-key-line"></i> API Credentials Generated</h2>
                <p>Save these credentials securely! You'll need them to access the API.</p>
            </div>
            <div class="oauth2-credentials">
                <div class="credential-item">
                    <label>Client ID:</label>
                    <div class="credential-value">
                        <code id="client-id">${credentials.client_id}</code>
                        <button onclick="copyToClipboard('client-id')" class="copy-btn">
                            <i class="ri-file-copy-line"></i>
                        </button>
                    </div>
                </div>
                <div class="credential-item">
                    <label>Client Secret:</label>
                    <div class="credential-value">
                        <code id="client-secret">${credentials.client_secret}</code>
                        <button onclick="copyToClipboard('client-secret')" class="copy-btn">
                            <i class="ri-file-copy-line"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="oauth2-actions">
                <button onclick="closeOAuth2Modal()" class="btn btn-primary">
                    <i class="ri-check-line"></i> I've Saved These Credentials
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add modal styles
    const style = document.createElement('style');
    style.textContent = `
        .oauth2-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        }
        .oauth2-modal-content {
            background: white;
            border-radius: 12px;
            padding: 24px;
            max-width: 500px;
            width: 90%;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        .oauth2-header {
            text-align: center;
            margin-bottom: 24px;
        }
        .oauth2-header h2 {
            color: #1e293b;
            margin-bottom: 8px;
        }
        .oauth2-header p {
            color: #64748b;
            font-size: 14px;
        }
        .credential-item {
            margin-bottom: 16px;
        }
        .credential-item label {
            display: block;
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
        }
        .credential-value {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .credential-value code {
            background: #f1f5f9;
            padding: 8px 12px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            flex: 1;
            word-break: break-all;
        }
        .copy-btn {
            background: #4f46e5;
            color: white;
            border: none;
            padding: 8px;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .copy-btn:hover {
            background: #4338ca;
        }
        .oauth2-actions {
            text-align: center;
            margin-top: 24px;
        }
    `;
    document.head.appendChild(style);
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    navigator.clipboard.writeText(element.textContent).then(() => {
        const btn = element.nextElementSibling;
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="ri-check-line"></i>';
        btn.style.background = '#10b981';
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.style.background = '#4f46e5';
        }, 2000);
    });
}

function closeOAuth2Modal() {
    const modal = document.querySelector('.oauth2-modal');
    if (modal) {
        modal.remove();
    }
    // Redirect to login
    window.location.href = '/?registered=true';
}

// Register user
async function registerUser() {
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: elements.email.value,
                password: elements.password.value,
                full_name: elements.fullName.value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
        }

        // Show OAuth2 credentials
        if (data.oauth2_client) {
            showOAuth2Credentials(data.oauth2_client);
        } else {
            // Fallback - redirect to login
            window.location.href = '/?registered=true';
        }
    } catch (error) {
        showError(error.message);
        elements.registerBtn.disabled = false;
        elements.registerBtn.innerHTML = '<i class="ri-user-add-line"></i> Create Account';
    }
}

// Event listeners
elements.registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (validateForm()) {
        // Disable button and show loading state
        elements.registerBtn.disabled = true;
        elements.registerBtn.innerHTML = '<i class="ri-loader-4-line"></i> Creating Account...';

        await registerUser();
    }
});