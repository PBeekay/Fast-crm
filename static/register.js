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
    if (elements.password.value.length < 6) {
        showError("Password must be at least 6 characters long");
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

        // Registration successful - redirect to login
        window.location.href = '/?registered=true';
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