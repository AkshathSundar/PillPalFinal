// PillPal JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap tooltips are used
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            // Add loading state to submit buttons
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                
                // Re-enable button after 3 seconds if form hasn't submitted
                setTimeout(function() {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 3000);
            }
        });
    });

    // Password confirmation validation
    const confirmPasswordField = document.getElementById('confirm_password');
    const passwordField = document.getElementById('password');
    
    if (confirmPasswordField && passwordField) {
        confirmPasswordField.addEventListener('input', function() {
            if (passwordField.value !== confirmPasswordField.value) {
                confirmPasswordField.setCustomValidity('Passwords do not match');
            } else {
                confirmPasswordField.setCustomValidity('');
            }
        });
    }

    // File upload validation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                const maxSize = 16 * 1024 * 1024; // 16MB
                if (file.size > maxSize) {
                    alert('File size too large. Please select a file smaller than 16MB.');
                    event.target.value = '';
                    return;
                }
                
                const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Invalid file type. Please select an MP3, WAV, OGG, or M4A file.');
                    event.target.value = '';
                    return;
                }
                
                // Show file preview info
                const fileName = file.name;
                const fileSize = (file.size / 1024 / 1024).toFixed(2) + ' MB';
                console.log(`Selected file: ${fileName} (${fileSize})`);
            }
        });
    });

    // Audio controls enhancement
    const audioElements = document.querySelectorAll('audio');
    audioElements.forEach(function(audio) {
        audio.addEventListener('error', function() {
            console.error('Error loading audio file');
            const errorMsg = document.createElement('p');
            errorMsg.className = 'text-danger fs-6';
            errorMsg.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Unable to load audio file';
            audio.parentNode.replaceChild(errorMsg, audio);
        });
    });

    // Confirmation dialogs enhancement
    const confirmLinks = document.querySelectorAll('a[onclick*="confirm"]');
    confirmLinks.forEach(function(link) {
        link.addEventListener('click', function(event) {
            // Add visual feedback
            event.target.style.opacity = '0.7';
            setTimeout(function() {
                event.target.style.opacity = '1';
            }, 200);
        });
    });

    // Time input formatting for better UX
    const timeInputs = document.querySelectorAll('input[type="time"]');
    timeInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            // Convert to 12-hour format in a helper display
            const time24 = this.value;
            if (time24) {
                const [hours, minutes] = time24.split(':');
                const hour12 = hours % 12 || 12;
                const ampm = hours < 12 ? 'AM' : 'PM';
                const time12 = `${hour12}:${minutes} ${ampm}`;
                
                // Could add a display helper here
                console.log(`Time set: ${time12}`);
            }
        });
    });

    // Keyboard navigation enhancement
    document.addEventListener('keydown', function(event) {
        // Escape key to close modals or go back
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            if (modals.length === 0) {
                // If no modals, could implement back navigation
                console.log('Escape pressed - could implement back navigation');
            }
        }
    });

    // Reminder status checking (could be enhanced with real-time updates)
    function checkReminderStatus() {
        const reminderCards = document.querySelectorAll('.card.border-warning');
        reminderCards.forEach(function(card) {
            // Could implement real-time reminder checking here
            // For now, just visual feedback
            card.style.animation = 'pulse-warning 2s infinite';
        });
    }

    // Add CSS animation for due reminders
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse-warning {
            0% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 193, 7, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
        }
        
        .loading-btn {
            pointer-events: none;
            opacity: 0.7;
        }
    `;
    document.head.appendChild(style);

    // Initialize reminder status checking
    checkReminderStatus();

    // Voice file preview
    const voiceSelect = document.getElementById('voice_file');
    if (voiceSelect) {
        voiceSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption.value) {
                console.log(`Selected voice: ${selectedOption.text}`);
                // Could add preview functionality here
            }
        });
    }

    console.log('PillPal JavaScript initialized successfully');
});

// Utility functions
function showNotification(message, type = 'info') {
    // Simple notification system
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(function() {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('JavaScript error:', event.error);
    // Could implement user-friendly error reporting here
});
