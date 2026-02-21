document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('mashupForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const submitBtn = document.getElementById('submitBtn');
    const messages = document.getElementById('messages');
    const progressBar = document.getElementById('progressBar');
    const progressStatus = document.getElementById('progressStatus');

    let pollInterval = null;

    // Helper to render error messages
    function showErrors(errorsList) {
        messages.innerHTML = `
            <div class="message error fade-in">
                <ul>
                    ${errorsList.map(err => `<li>${err}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    // Helper to render single success/error message
    function showSingleMessage(text, type) {
        messages.innerHTML = `
            <div class="message ${type} fade-in">${text}</div>
        `;
    }

    // Clear previous messages when typing
    const inputs = form.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            if (messages.innerHTML.trim() !== '') {
                messages.style.opacity = '0';
                setTimeout(() => {
                    messages.innerHTML = '';
                    messages.style.opacity = '1';
                }, 400);
            }
        });
    });

    form.addEventListener('submit', (e) => {
        e.preventDefault();

        if (!form.checkValidity()) {
            return;
        }

        // 1. Prepare UI for loading
        messages.innerHTML = '';
        loadingOverlay.classList.remove('hidden');
        void loadingOverlay.offsetWidth;
        loadingOverlay.classList.add('visible');
        progressBar.style.width = '0%';
        progressStatus.textContent = 'Initializing pipeline...';

        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.7';
        submitBtn.style.cursor = 'not-allowed';

        // 2. Submit form via AJAX
        const formData = new FormData(form);
        fetch('/submit', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(res => {
            if (res.status === 200 && res.body.status === 'success') {
                const jobId = res.body.job_id;
                startPolling(jobId);
            } else {
                // Validation error or initialization failure
                stopLoading();
                const errors = res.body.errors || [res.body.message || 'An unknown error occurred during initialization.'];
                showErrors(errors);
            }
        })
        .catch(err => {
            stopLoading();
            showSingleMessage('Network error. Failed to initiate mashup request.', 'error');
            console.error('Error submitting form:', err);
        });
    });

    function startPolling(jobId) {
        pollInterval = setInterval(() => {
            fetch(`/status/${jobId}`)
            .then(res => {
                if (!res.ok) {
                    throw new Error('Failed to fetch job status.');
                }
                return res.json();
            })
            .then(job => {
                // Update progress elements
                progressBar.style.width = `${job.progress}%`;
                progressStatus.textContent = job.message;

                if (job.status === 'completed') {
                    clearInterval(pollInterval);
                    stopLoading();
                    showSingleMessage(job.message, 'success');
                    form.reset();
                } else if (job.status === 'failed') {
                    clearInterval(pollInterval);
                    stopLoading();
                    showSingleMessage(job.message, 'error');
                }
            })
            .catch(err => {
                clearInterval(pollInterval);
                stopLoading();
                showSingleMessage('Error tracking progress. Please check your email later or try again.', 'error');
                console.error('Polling error:', err);
            });
        }, 1500);
    }

    function stopLoading() {
        loadingOverlay.classList.remove('visible');
        setTimeout(() => {
            loadingOverlay.classList.add('hidden');
        }, 400);

        submitBtn.disabled = false;
        submitBtn.style.opacity = '1';
        submitBtn.style.cursor = 'pointer';
    }
});
