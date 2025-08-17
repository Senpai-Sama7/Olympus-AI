window.addEventListener('pywebviewready', function() {
    const api = window.pywebview.api;

    // Settings
    const settingsForm = document.getElementById('settings-form');
    settingsForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(settingsForm);
        const settings = Object.fromEntries(formData.entries());
        api.save_settings(settings);
    });

    // Task queue
    const taskQueue = document.getElementById('task-queue');
    function updateTaskQueue() {
        api.get_task_queue().then(function(tasks) {
            taskQueue.innerHTML = '';
            tasks.forEach(function(task) {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = task;
                taskQueue.appendChild(li);
            });
        });
    }
    setInterval(updateTaskQueue, 5000);
    updateTaskQueue();

    // Artifacts
    const artifacts = document.getElementById('artifacts');
    function updateArtifacts() {
        api.get_artifacts().then(function(items) {
            artifacts.innerHTML = '';
            items.forEach(function(item) {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = item;
                artifacts.appendChild(li);
            });
        });
    }
    setInterval(updateArtifacts, 5000);
    updateArtifacts();

    // Status bar
    const statusModel = document.getElementById('status-model');
    const statusTokens = document.getElementById('status-tokens');
    const statusFallbackSpend = document.getElementById('status-fallback-spend');
    function updateStatusBar() {
        api.get_status().then(function(status) {
            statusModel.textContent = status.model;
            statusTokens.textContent = status.tokens_used;
            statusFallbackSpend.textContent = status.fallback_spend;
        });
    }
    setInterval(updateStatusBar, 5000);
    updateStatusBar();

    // Consent prompt
    const consentPrompt = document.getElementById('consent-prompt');
    const consentMessage = document.getElementById('consent-message');
    const consentApprove = document.getElementById('consent-approve');
    const consentDeny = document.getElementById('consent-deny');

    window.showConsentPrompt = function(message) {
        return new Promise(function(resolve) {
            consentMessage.textContent = message;
            $(consentPrompt).modal('show');

            consentApprove.onclick = function() {
                $(consentPrompt).modal('hide');
                resolve(true);
            };

            consentDeny.onclick = function() {
                $(consentPrompt).modal('hide');
                resolve(false);
            };
        });
    };
});