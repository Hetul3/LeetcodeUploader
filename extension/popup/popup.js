document.addEventListener('DOMContentLoaded', async () => {
    const ghTokenInput = document.getElementById('ghToken');
    const ghRepoInput = document.getElementById('ghRepo');
    const saveBtn = document.getElementById('saveBtn');
    const messageEl = document.getElementById('message');
    const statusCard = document.getElementById('statusCard');
    const statusText = document.getElementById('statusText');

    // Load existing settings
    const settings = await chrome.storage.sync.get(['ghToken', 'ghRepo']);
    if (settings.ghToken) ghTokenInput.value = settings.ghToken;
    if (settings.ghRepo) ghRepoInput.value = settings.ghRepo;

    // Check status
    updateStatus();

    saveBtn.addEventListener('click', async () => {
        const ghToken = ghTokenInput.value.trim();
        const ghRepo = ghRepoInput.value.trim();

        if (!ghToken || !ghRepo) {
            showMessage('Please fill in all fields.', 'error');
            return;
        }

        // Simple validation of repo format (username/repo)
        if (!ghRepo.includes('/')) {
            showMessage('Repository must be in "username/repo" format.', 'error');
            return;
        }

        await chrome.storage.sync.set({ ghToken, ghRepo });
        showMessage('Settings saved successfully!', 'success');
        updateStatus();
    });

    async function updateStatus() {
        const settings = await chrome.storage.sync.get(['ghToken', 'ghRepo']);
        
        if (!settings.ghToken || !settings.ghRepo) {
            statusCard.className = 'status-card error';
            statusText.textContent = 'Configuration required';
            return;
        }

        // Verify LeetCode session via background
        chrome.runtime.sendMessage({ type: 'CHECK_STATUS' }, (response) => {
            if (response && response.signedIn) {
                statusCard.className = 'status-card active';
                statusText.textContent = `Connected as ${response.username}`;
            } else {
                statusCard.className = 'status-card error';
                statusText.textContent = 'LeetCode session expired';
            }
        });
    }

    function showMessage(text, type) {
        messageEl.textContent = text;
        messageEl.className = `message ${type}`;
        messageEl.classList.remove('hidden');
        setTimeout(() => {
            messageEl.classList.add('hidden');
        }, 3000);
    }
});
