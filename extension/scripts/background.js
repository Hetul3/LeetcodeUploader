import { LANGUAGE_MAPPING, GITHUB_API_BASE, LEETCODE_API_ENDPOINT } from './constants.js';

console.log("DEBUG-LOG: [Background] Service Worker Initialized.");

/**
 * Global Message Listener
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log(`DEBUG-LOG: [Background] Message Received: ${message.type}`);
    
    if (message.type === "FETCH_LATEST_AND_SYNC") {
        handleLatestSubmissionSync()
            .then(() => sendResponse({ success: true }))
            .catch(err => {
                const msg = err?.message || "Internal sync error";
                console.error("DEBUG-LOG: [Background] Sync Fail:", msg);
                showNotification("Sync Failed", msg);
                sendResponse({ success: false, error: msg });
            });
        return true; 
    }

    if (message.type === "CHECK_STATUS") {
        checkLeetCodeStatus().then(sendResponse);
        return true; 
    }
});

/**
 * Core Logic: Fetch latest AC and sync it
 */
async function handleLatestSubmissionSync() {
    console.log("DEBUG-LOG: [Background] Starting 'Latest Scan'...");
    
    const cookies = await getLeetCodeCookies();
    const status = await checkLeetCodeStatus();
    
    if (!status.signedIn) {
        showNotification("Not Logged In", "Please login to LeetCode in your browser.");
        throw new Error("User is not signed in to LeetCode.");
    }

    // 1. Fetch latest submission ID
    const query = `query recentAcSubmissions($username: String!, $limit: Int!) {
        recentAcSubmissionList(username: $username, limit: $limit) { id title }
    }`;
    const data = await leetcodeQuery(query, { username: status.username, limit: 1 }, cookies);
    
    if (!data || !data.recentAcSubmissionList || data.recentAcSubmissionList.length === 0) {
        throw new Error("No recent accepted submissions found.");
    }

    const submissionId = data.recentAcSubmissionList[0].id;
    console.log(`DEBUG-LOG: [Background] Targeting Latest Submission: ${submissionId} (${data.recentAcSubmissionList[0].title})`);
    
    return handleAcceptedSubmission(submissionId, cookies);
}

async function handleAcceptedSubmission(submissionId, cookies) {
    showNotification("Syncing Solution...", "Sending your code to GitHub repository.");
    
    const settings = await chrome.storage.sync.get(['ghToken', 'ghRepo']);
    if (!settings.ghToken || !settings.ghRepo) {
        throw new Error("GitHub Configuration Missing. Open extension settings.");
    }
    
    // 1. Get detailed submission info (code, language)
    const details = await getSubmissionDetails(submissionId, cookies);
    
    // 2. Get detailed question info (description, difficulty)
    const question = await getQuestionDetails(details.question.titleSlug, cookies);

    // 3. Process paths
    const extension = LANGUAGE_MAPPING[details.lang.name] || ".txt";
    const safeTitle = question.title.replace(/\s+/g, '-').replace(/\//g, '-');
    const folderPath = `${question.difficulty}/${question.questionFrontendId}-${safeTitle}`;
    
    const solutionPath = `${folderPath}/solution${extension}`;
    const readmePath = `${folderPath}/README.md`;

    // 4. Content generation
    const newCode = details.code.trim();
    const newReadme = formatMarkdown(question, details);

    // 5. Upload to GitHub
    const solutionUpdated = await uploadToGitHub(settings.ghRepo, solutionPath, newCode, `feat: add ${details.lang.verboseName} solution for ${question.title}`, settings.ghToken);
    const readmeUpdated = await uploadToGitHub(settings.ghRepo, readmePath, newReadme, `docs: update README for ${question.title}`, settings.ghToken);

    if (!solutionUpdated && !readmeUpdated) {
        showNotification("Up to Date", `"${question.title}" matches the version on GitHub.`);
    } else {
        showNotification("Success!", `Successfully synced "${question.title}"!`);
    }
}

/**
 * API Helpers
 */
async function leetcodeQuery(query, variables, cookies) {
    const response = await fetch(LEETCODE_API_ENDPOINT, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json", 
            "x-csrftoken": cookies.csrf || ""
        },
        body: JSON.stringify({ query, variables })
    });
    
    if (!response.ok) throw new Error("LeetCode API Network Error: " + response.statusText);
    
    const data = await response.json();
    if (data.errors) throw new Error(data.errors[0].message);
    return data.data;
}

async function getLeetCodeCookies() {
    return new Promise((resolve) => {
        chrome.cookies.getAll({ domain: "leetcode.com" }, (cookies) => {
            const result = { session: null, csrf: null };
            cookies.forEach(c => {
                if (c.name === "LEETCODE_SESSION") result.session = c.value;
                if (c.name === "csrftoken") result.csrf = c.value;
            });
            resolve(result);
        });
    });
}

async function checkLeetCodeStatus() {
    try {
        const cookies = await getLeetCodeCookies();
        const query = `query userStatus { userStatus { username isSignedIn } }`;
        const data = await leetcodeQuery(query, {}, cookies);
        return { signedIn: data.userStatus.isSignedIn, username: data.userStatus.username };
    } catch (e) { return { signedIn: false }; }
}

async function getSubmissionDetails(submissionId, cookies) {
    const query = `query submissionDetails($submissionId: Int!) {
      submissionDetails(submissionId: $submissionId) {
        runtimeDisplay memoryDisplay code timestamp
        lang { name verboseName }
        question { title titleSlug }
      }
    }`;
    const data = await leetcodeQuery(query, { submissionId: parseInt(submissionId) }, cookies);
    return data.submissionDetails;
}

async function getQuestionDetails(titleSlug, cookies) {
    const query = `query questionData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId questionFrontendId title titleSlug difficulty content
        topicTags { name }
      }
    }`;
    const data = await leetcodeQuery(query, { titleSlug }, cookies);
    return data.question;
}

async function uploadToGitHub(repo, path, content, message, token) {
    const url = `${GITHUB_API_BASE}/repos/${repo}/contents/${path}`;
    
    const checkRes = await fetch(url, { headers: { "Authorization": `token ${token}` } });
    let sha = null;
    
    if (checkRes.status === 200) {
        const data = await checkRes.json();
        sha = data.sha;
        try {
            const existing = decodeURIComponent(escape(atob(data.content.replace(/\s/g, ''))));
            if (existing.trim() === content.trim()) return false;
        } catch (e) { console.warn("GitHub content comparison failed, updating anyway."); }
    }

    const res = await fetch(url, {
        method: "PUT",
        headers: { "Authorization": `token ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ message, content: btoa(unescape(encodeURIComponent(content))), sha })
    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error("GitHub Error: " + (err.message || res.statusText));
    }
    return true;
}

function formatMarkdown(question, details) {
    const { difficulty, title, titleSlug, content, topicTags } = question;
    const tagsMd = topicTags.map(t => `\`${t.name}\``).join(' ');
    const badgeColor = { "Easy": "brightgreen", "Medium": "orange", "Hard": "red" }[difficulty] || "blue";

    return `# [${question.questionFrontendId}. ${title}](https://leetcode.com/problems/${titleSlug}/)

![Difficulty: ${difficulty}](https://img.shields.io/badge/Difficulty-${difficulty}-${badgeColor})
${tagsMd}

## Problem Description
${content ? simpleHtmlToMarkdown(content) : "Description not available."}

## Submission Details
| Status | Language | Runtime | Memory | Date |
| :--- | :--- | :--- | :--- | :--- |
| Accepted | ${details.lang.verboseName} | ${details.runtimeDisplay} | ${details.memoryDisplay} | ${new Date(details.timestamp * 1000).toLocaleString()} |

---
*Generated by [LeetcodeUploader](https://github.com/Hetul3/LeetcodeUploader)*
`;
}

function simpleHtmlToMarkdown(html) {
    let md = html;
    md = md.replace(/<pre>[\s\S]*?<\/pre>/g, (m) => m.replace(/<(b|strong)>/ig, '').replace(/<\/(b|strong)>/ig, ''));
    md = md.replace(/<code>(.*?)<\/code>/g, '`$1`').replace(/<(b|strong)>(.*?)<\/(b|strong)>/g, '**$2**');
    md = md.replace(/<p>(.*?)<\/p>/g, '$1\n\n').replace(/<br\s*\/?>/g, '\n');
    md = md.replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&').replace(/&quot;/g, '"');
    return md.trim();
}

function showNotification(title, message) {
    console.log(`DEBUG-LOG: [Background] Showing Notification: ${title} - ${message}`);
    chrome.notifications.create({
        type: "basic",
        iconUrl: chrome.runtime.getURL("icons/icon128.png"),
        title: title,
        message: message,
        priority: 2
    });
}
