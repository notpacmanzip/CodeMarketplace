// Main JavaScript file for DevMarket

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeBootstrap();
    initializeFormHandling();
    initializeImageLazyLoading();
    initializeTooltips();
    initializeConfirmations();
    initializeSearch();
    initializeFileUploads();
    initializeMessageHandling();
});

// Initialize Bootstrap components
function initializeBootstrap() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Form handling improvements
function initializeFormHandling() {
    // Add loading state to submit buttons
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                submitBtn.disabled = true;
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });

    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    });

    // Character counter for text inputs with maxlength
    const inputsWithMaxLength = document.querySelectorAll('input[maxlength], textarea[maxlength]');
    inputsWithMaxLength.forEach(input => {
        const maxLength = input.getAttribute('maxlength');
        const counter = document.createElement('small');
        counter.className = 'text-muted character-counter';
        counter.textContent = `0/${maxLength} characters`;
        input.parentNode.appendChild(counter);
        
        input.addEventListener('input', function() {
            const currentLength = this.value.length;
            counter.textContent = `${currentLength}/${maxLength} characters`;
            counter.className = currentLength >= maxLength * 0.9 ? 'text-warning character-counter' : 'text-muted character-counter';
        });
    });
}

// Lazy loading for images
function initializeImageLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => imageObserver.observe(img));
    }
}

// Initialize tooltips for dynamically added elements
function initializeTooltips() {
    // Rating stars hover effect
    const ratingStars = document.querySelectorAll('.rating-stars .star');
    ratingStars.forEach((star, index) => {
        star.addEventListener('mouseenter', function() {
            highlightStars(star.parentNode, index + 1);
        });
        
        star.addEventListener('mouseleave', function() {
            const rating = star.parentNode.dataset.rating || 0;
            highlightStars(star.parentNode, rating);
        });
        
        star.addEventListener('click', function() {
            const rating = index + 1;
            star.parentNode.dataset.rating = rating;
            highlightStars(star.parentNode, rating);
            
            // Update hidden input if exists
            const hiddenInput = star.parentNode.querySelector('input[type="hidden"]');
            if (hiddenInput) {
                hiddenInput.value = rating;
            }
        });
    });
}

function highlightStars(container, rating) {
    const stars = container.querySelectorAll('.star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

// Confirmation dialogs
function initializeConfirmations() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'Are you sure?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

// Search functionality
function initializeSearch() {
    // Real-time search suggestions (if implemented)
    const searchInputs = document.querySelectorAll('input[name="query"]');
    searchInputs.forEach(input => {
        let timeout;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                // Could implement search suggestions here
                console.log('Search query:', this.value);
            }, 300);
        });
    });

    // Filter form auto-submit
    const filterForm = document.querySelector('.search-filters form');
    if (filterForm) {
        const selects = filterForm.querySelectorAll('select');
        selects.forEach(select => {
            select.addEventListener('change', function() {
                // Auto-submit filter form when selection changes
                filterForm.submit();
            });
        });
    }
}

// File upload handling
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                // Validate file size (16MB limit)
                if (file.size > 16 * 1024 * 1024) {
                    alert('File size must be less than 16MB');
                    this.value = '';
                    return;
                }
                
                // Show preview for images
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        let preview = input.parentNode.querySelector('.file-preview');
                        if (!preview) {
                            preview = document.createElement('div');
                            preview.className = 'file-preview mt-2';
                            input.parentNode.appendChild(preview);
                        }
                        preview.innerHTML = `<img src="${e.target.result}" alt="Preview" class="img-thumbnail" style="max-width: 200px; max-height: 150px;">`;
                    };
                    reader.readAsDataURL(file);
                }
                
                // Update file input label
                const label = input.parentNode.querySelector('label');
                if (label) {
                    label.textContent = `Selected: ${file.name}`;
                }
            }
        });
    });
}

// Message handling
function initializeMessageHandling() {
    // Auto-scroll to bottom of message container
    const messageContainer = document.getElementById('messagesContainer');
    if (messageContainer) {
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    // Message form handling
    const messageForm = document.querySelector('#messageForm');
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            const content = this.querySelector('textarea[name="content"]');
            if (content && content.value.trim() === '') {
                e.preventDefault();
                alert('Please enter a message');
                content.focus();
                return false;
            }
        });
    }

    // Auto-expand message textarea
    const messageTextarea = document.querySelector('textarea[name="content"]');
    if (messageTextarea) {
        messageTextarea.addEventListener('keydown', function(e) {
            // Submit on Ctrl+Enter
            if (e.ctrlKey && e.key === 'Enter') {
                this.form.submit();
            }
        });
    }
}

// Utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

function formatPrice(amount, currency = 'USD') {
    if (currency === 'USD') {
        return `$${parseFloat(amount).toFixed(2)}`;
    }
    return `${parseFloat(amount).toFixed(2)} ${currency}`;
}

function timeAgo(date) {
    const now = new Date();
    const diffMs = now - new Date(date);
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;
    return new Date(date).toLocaleDateString();
}

// Copy to clipboard functionality
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('Copied to clipboard!', 'success');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showAlert('Copied to clipboard!', 'success');
    }
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Handle back button
window.addEventListener('popstate', function(e) {
    // Could handle SPA-like navigation here if needed
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(() => {
            const perfData = performance.timing;
            const loadTime = perfData.loadEventEnd - perfData.navigationStart;
            console.log(`Page load time: ${loadTime}ms`);
        }, 0);
    });
}

// Error handling for async operations
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showAlert('An error occurred. Please try again.', 'danger');
});

// Accessibility improvements
document.addEventListener('keydown', function(e) {
    // Skip to main content on Tab key
    if (e.key === 'Tab' && !e.shiftKey && document.activeElement === document.body) {
        const main = document.querySelector('main');
        if (main) {
            main.focus();
            e.preventDefault();
        }
    }
});

// Export utility functions for use in other scripts
window.DevMarket = {
    showAlert,
    formatPrice,
    timeAgo,
    copyToClipboard
};
