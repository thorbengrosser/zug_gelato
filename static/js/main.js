// Utility functions for GeLATO

// Remove item from form
function removeItem(button) {
    const item = button.closest('.border');
    item.remove();
}

// Add smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Add form validation
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        // Add any custom form validation here
    });
}); 