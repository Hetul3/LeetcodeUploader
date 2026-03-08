/**
 * Ultimate Link & Attribute Detector
 */

console.log("DEBUG-LOG: [Content Script] Ultra-Detector Active...");

let currentSubmissionId = null;
let userDismissedId = null;
let lastLogTime = 0;

setInterval(() => {
    try {
        const now = Date.now();
        const shouldLog = now - lastLogTime > 5000;

        // 1. Find the "Accepted" element
        const elements = Array.from(document.querySelectorAll('span, div, p')).filter(el => el.children.length === 0);
        let acceptedEl = null;
        for (let el of elements) {
            if (el.textContent.trim() === "Accepted") {
                const color = window.getComputedStyle(el).color;
                if (color.includes('rgb(44,') || color.includes('rgb(45,') || color.includes('rgb(46,') || color.includes('rgb(43,')) {
                    acceptedEl = el;
                    break;
                }
            }
        }

        // 2. Find the Submission ID (The "Real Submission" Proof)
        let subId = null;

        // Pattern A: Look for attributes that LeetCode often uses
        const idElements = document.querySelectorAll('[data-submission-id], [submission-id]');
        if (idElements.length > 0) {
            subId = idElements[0].getAttribute('data-submission-id') || idElements[0].getAttribute('submission-id');
        }

        // Pattern B: Scan URLs (The old reliable)
        if (!subId) {
            const allLinks = document.querySelectorAll('a');
            for (let a of allLinks) {
                const match = a.href.match(/submissions\/(?:detail\/)?(\d+)/);
                if (match) {
                    subId = match[1];
                    break;
                }
            }
        }

        // Pattern C: Check the current URL itself
        if (!subId) {
            const match = window.location.href.match(/submissions\/(?:detail\/)?(\d+)/);
            if (match) subId = match[1];
        }

        if (shouldLog) {
            console.log(`DEBUG-LOG: [Status] Accepted: ${!!acceptedEl}, SubID: ${subId || "NoneFound"}`);
            lastLogTime = now;
        }

        if (acceptedEl && subId) {
            if (subId !== currentSubmissionId) {
                currentSubmissionId = subId;
                userDismissedId = null;
                console.log(`DEBUG-LOG: [Content Script] Target Acquired: #${subId}`);
            }

            if (userDismissedId !== subId) {
                showApprovalUI(subId);
            } else {
                hideApprovalUI();
            }
        } else {
            hideApprovalUI();
        }
    } catch (err) {}
}, 2000);

function showApprovalUI(submissionId) {
    if (document.getElementById('leetcode-sync-approval')) return;

    const ui = document.createElement('div');
    ui.id = 'leetcode-sync-approval';
    ui.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: #0d1117;
        color: white;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.6);
        z-index: 2147483647;
        font-family: -apple-system, sans-serif;
        border: 1px solid #30363d;
        display: flex;
        flex-direction: column;
        gap: 12px;
        width: 250px;
    `;

    ui.innerHTML = `
        <div style="font-size: 14px; font-weight: 600; color: #3fb950;">🚀 Solution Accepted!</div>
        <div style="color: #8b949e; font-size: 11px;">Sync submission #${submissionId} to GitHub?</div>
        <button id="lc-sync-now" style="background:linear-gradient(180deg,#2ea043 0%,#238636 100%); color:white; border:1px solid rgba(27,31,36,0.15); padding:8px; border-radius:6px; font-weight:600; cursor:pointer; font-size:13px;">Sync to GitHub</button>
        <div id="lc-ignore-sync" style="color:#8b949e; cursor:pointer; font-size:12px; text-align:center;">Maybe later</div>
    `;

    document.body.appendChild(ui);

    document.getElementById('lc-sync-now').addEventListener('click', () => {
        const btn = document.getElementById('lc-sync-now');
        btn.disabled = true;
        btn.textContent = "🔄 Syncing...";
        
        chrome.runtime.sendMessage({ type: "FETCH_LATEST_AND_SYNC" }, (response) => {
            if (response && response.success) {
                btn.textContent = "✅ Success!";
                btn.style.background = "#2ea043";
                userDismissedId = submissionId;
                setTimeout(() => ui.remove(), 2000);
            } else {
                btn.textContent = "❌ Failed";
                btn.style.background = "#f85149";
                btn.disabled = false;
                alert("Sync Error: " + (response?.error || "Unknown error"));
            }
        });
    });

    document.getElementById('lc-ignore-sync').addEventListener('click', () => {
        userDismissedId = submissionId;
        ui.remove();
    });
}

function hideApprovalUI() {
    const existing = document.getElementById('leetcode-sync-approval');
    if (existing && !currentSubmissionId) {
        existing.remove();
    }
}
