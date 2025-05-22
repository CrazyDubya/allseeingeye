/**
 * AllSeeingEye Web App Main JavaScript
 * Enhanced version with animations and improved UX
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
        });
    });
    
    // Flash messages auto-dismiss after 5 seconds
    const flashMessages = document.querySelectorAll('.alert:not(.alert-permanent)');
    flashMessages.forEach(message => {
        setTimeout(() => {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
    
    // Directory picker functionality
    const directoryInput = document.getElementById('directory-input');
    const directoryPickerBtn = document.getElementById('directory-picker-btn');
    
    if (directoryInput && directoryPickerBtn) {
        // Create a hidden file input element
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.setAttribute('webkitdirectory', '');
        fileInput.setAttribute('directory', '');
        fileInput.style.display = 'none';
        document.body.appendChild(fileInput);
        
        // Add click handler to our button
        directoryPickerBtn.addEventListener('click', function(e) {
            e.preventDefault();
            fileInput.click();
        });
        
        // When a directory is selected
        fileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                // Get the path from the first file
                const path = this.files[0].webkitRelativePath;
                
                // Extract the root directory path
                const rootDir = path.split('/')[0];
                
                // If we're on desktop, try to get the full path
                if (directoryInput.value) {
                    // If there was a previous value, try to replace the last part with the new dir
                    const parts = directoryInput.value.split('/');
                    parts[parts.length - 1] = rootDir;
                    directoryInput.value = parts.join('/');
                } else {
                    // Just use the selected directory name
                    directoryInput.value = rootDir;
                }
                
                // Highlight the input to indicate success
                directoryInput.classList.add('border-success');
                setTimeout(() => {
                    directoryInput.classList.remove('border-success');
                }, 2000);
            }
        });
    }
    
    // Add subtle pulse animation to the logo
    const logo = document.querySelector('.logo-svg');
    if (logo) {
        let pulseInterval;
        
        // Pulse effect on hover
        logo.addEventListener('mouseenter', function() {
            // Clear any existing interval
            if (pulseInterval) clearInterval(pulseInterval);
            
            // Start pulsing
            let scale = 1.0;
            let growing = false;
            pulseInterval = setInterval(() => {
                if (growing) {
                    scale += 0.01;
                    if (scale >= 1.1) growing = false;
                } else {
                    scale -= 0.01;
                    if (scale <= 1.0) growing = true;
                }
                logo.style.transform = `scale(${scale})`;
            }, 50);
        });
        
        // Stop pulsing when mouse leaves
        logo.addEventListener('mouseleave', function() {
            clearInterval(pulseInterval);
            logo.style.transform = 'scale(1)';
        });
    }
    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Directory path field auto-completion
    const directoryField = document.getElementById('directory');
    if (directoryField) {
        // Check if browser has support for the File System Access API
        if ('showDirectoryPicker' in window) {
            const browseButton = document.createElement('button');
            browseButton.type = 'button';
            browseButton.className = 'btn btn-outline-secondary';
            browseButton.innerText = 'Browse...';
            browseButton.addEventListener('click', async () => {
                try {
                    const directoryHandle = await window.showDirectoryPicker();
                    directoryField.value = directoryHandle.name;
                } catch (err) {
                    console.error('Error selecting directory: ', err);
                }
            });
            
            // Add button next to the directory field
            const directoryContainer = directoryField.parentElement;
            const inputGroup = document.createElement('div');
            inputGroup.className = 'input-group';
            
            directoryField.parentNode.insertBefore(inputGroup, directoryField);
            inputGroup.appendChild(directoryField);
            inputGroup.appendChild(browseButton);
        }
    }

    // Add custom file input behavior
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        const label = input.nextElementSibling;
        if (label) {
            input.addEventListener('change', e => {
                let fileName = '';
                if (input.files && input.files.length > 0) {
                    fileName = input.files[0].name;
                }
                label.textContent = fileName || 'Choose file';
            });
        }
    });

    // Format toggle listeners - could be used if we add format toggle buttons
    const formatToggles = document.querySelectorAll('[data-format-toggle]');
    formatToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const format = this.getAttribute('data-format-toggle');
            document.getElementById('output_format').value = format;
            
            // Update active state
            formatToggles.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
});