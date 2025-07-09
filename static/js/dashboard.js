document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    if (tabButtons.length > 0) {
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons and contents
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked button
                button.classList.add('active');
                
                // Show corresponding content
                const tabId = button.getAttribute('data-tab');
                const activeContent = document.getElementById(`${tabId}-tab`);
                if (activeContent) {
                    activeContent.classList.add('active');
                }
            });
        });
    }
    const openBtn = document.getElementById("newRequestBtn");
    const modal = document.getElementById("newRequestModal");
    const closeBtn = modal.querySelector(".close-modal");

    openBtn.addEventListener("click", () => {
        modal.classList.add("show");
        modal.style.display = "block";
    });

    closeBtn.addEventListener("click", () => {
        modal.classList.remove("show");
        modal.style.display = "none";
    });

    // Optional: Close modal when clicking outside the modal content
    window.addEventListener("click", function (event) {
        if (event.target === modal) {
            modal.classList.remove("show");
            modal.style.display = "none";
        }
    });
    
    const sortBy = document.getElementById('sort-by');
    const filterAccess = document.getElementById('filter-access');
    const patientCards = Array.from(document.querySelectorAll('#patients-list .record-card'));

    function updatePatientsList() {
        const sortValue = sortBy.value;
        const accessFilter = filterAccess.value;

        let filteredCards = patientCards.filter(card => {
            const access = card.dataset.access;
            return accessFilter === 'all' || access === accessFilter;
        });

        if (sortValue === 'name') {
            filteredCards.sort((a, b) => {
                return a.dataset.name.localeCompare(b.dataset.name);
            });
        } else if (sortValue === 'access') {
            const priority = { full: 1, limited: 2, emergency: 3 };
            filteredCards.sort((a, b) => {
                return priority[a.dataset.access] - priority[b.dataset.access];
            });
        } else if (sortValue === 'recent') {
            filteredCards.sort((a, b) => {
                return new Date(b.dataset.timestamp) - new Date(a.dataset.timestamp);
            });
        }

        const container = document.getElementById('patients-list');
        container.innerHTML = '';
        filteredCards.forEach(card => container.appendChild(card));
    }

    sortBy.addEventListener('change', updatePatientsList);
    filterAccess.addEventListener('change', updatePatientsList);

    updatePatientsList();



    // Modal functionality
    const modals = document.querySelectorAll('.modal');
    const modalTriggers = document.querySelectorAll('[id$="Btn"]');
    const closeButtons = document.querySelectorAll('.close-modal');
    
    // Open modal
    if (modalTriggers.length > 0) {
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', () => {
                const modalId = trigger.id.replace('Btn', 'Modal');
                const modal = document.getElementById(modalId);
                if (modal) {
                    modal.style.display = 'flex';
                    setTimeout(() => {
                        modal.classList.add('show');
                    }, 10);
                }
            });
        });
    }
    
    // Close modal with close button
    if (closeButtons.length > 0) {
        closeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const modal = button.closest('.modal');
                if (modal) {
                    modal.classList.remove('show');
                    setTimeout(() => {
                        modal.style.display = 'none';
                    }, 300);
                }
            });
        });
    }
    
    // Close modal when clicking outside
    if (modals.length > 0) {
        modals.forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                    setTimeout(() => {
                        modal.style.display = 'none';
                    }, 300);
                }
            });
        });
    }
    
    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    if (fileInputs.length > 0) {
        fileInputs.forEach(input => {
            input.addEventListener('change', () => {
                const fileSelectedText = input.parentElement.querySelector('.file-selected');
                if (fileSelectedText) {
                    if (input.files.length > 0) {
                        if (input.files.length === 1) {
                            fileSelectedText.textContent = input.files[0].name;
                        } else {
                            fileSelectedText.textContent = `${input.files.length} files selected`;
                        }
                    } else {
                        fileSelectedText.textContent = 'No files selected';
                    }
                }
            });
        });
    }
    
    // Form submissions
    const forms = document.querySelectorAll('form');
    
    if (forms.length > 0) {
        forms.forEach(form => {
        form.addEventListener('submit', (e) => {
        if (form.classList.contains('search-form')) return;
        e.preventDefault();
                const modal = form.closest('.modal');
                if (modal) {
                    modal.classList.remove('show');
                    setTimeout(() => {
                        modal.style.display = 'none';
                        // Reset form
                        form.reset();
                    }, 300);
                }
                
                // Show success notification
                showNotification('Success', 'Your changes have been saved successfully.');
            });
        });
    }
    
    // Notification function
    function showNotification(title, message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.innerHTML = `
            <div class="notification-header">
                <h3>${title}</h3>
                <button class="close-notification">&times;</button>
            </div>
            <div class="notification-body">
                <p>${message}</p>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
        
        // Close button functionality
        const closeButton = notification.querySelector('.close-notification');
        closeButton.addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
    }
});