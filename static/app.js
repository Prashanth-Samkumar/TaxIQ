// Session details
const userId = "test_user";
let activeProfileName = "";
let threadId = generateUUID();

// Elements
const chatFeed = document.getElementById('chat-feed');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const profilesList = document.getElementById('profiles-list');
const activeProfileNameEl = document.getElementById('active-profile-name');
const activeProfileMetaEl = document.getElementById('active-profile-meta');
const refreshProfilesBtn = document.getElementById('refresh-profiles-btn');
const welcomeCard = document.getElementById('welcome-card');

// Helper to generate UUID v4
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Initial state load
document.addEventListener('DOMContentLoaded', () => {
    loadProfiles();
    
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendMessage();
    });

    refreshProfilesBtn.addEventListener('click', () => {
        loadProfiles();
    });
});

// Load profiles from backend
async function loadProfiles() {
    profilesList.innerHTML = `
        <div class="loading-spinner">
            <i class="fa-solid fa-circle-notch fa-spin"></i>
        </div>
    `;

    try {
        const response = await fetch(`/api/profiles?user_id=${userId}`);
        const data = await response.json();
        
        if (data.profiles && data.profiles.length > 0) {
            renderProfiles(data.profiles);
            
            // Auto select latest profile if none selected
            if (!activeProfileName) {
                // Find most recent updated
                const latest = data.profiles.reduce((prev, current) => 
                    (new Date(prev.last_updated) > new Date(current.last_updated)) ? prev : current
                );
                selectProfile(latest.name, `${latest.age} years • ${latest.city}`);
            }
        } else {
            profilesList.innerHTML = `<div style="text-align: center; color: var(--text-secondary); font-size: 13px; padding: 12px 0;">No profiles found</div>`;
            activeProfileNameEl.innerText = "No Active Profile";
            activeProfileMetaEl.innerText = "Ask TaxIQ to load or create a profile.";
        }
    } catch (error) {
        console.error("Error loading profiles:", error);
        profilesList.innerHTML = `<div style="text-align: center; color: var(--accent-rose); font-size: 13px; padding: 12px 0;">Error loading profiles</div>`;
    }
}

// Render profiles to sidebar
function renderProfiles(profiles) {
    profilesList.innerHTML = '';
    
    profiles.forEach(p => {
        const card = document.createElement('div');
        card.className = `profile-card ${p.name === activeProfileName ? 'active' : ''}`;
        
        card.innerHTML = `
            <div class="profile-card-header">
                <span class="profile-card-name">${p.name}</span>
                <span class="profile-card-badge">${p.notes || 'Family'}</span>
            </div>
            <div class="profile-card-details">
                <span>Age: ${p.age} | City: ${p.city}</span>
                <span>Gross Income: ₹${p.gross_salary.toLocaleString('en-IN')}</span>
            </div>
        `;
        
        card.addEventListener('click', () => {
            selectProfile(p.name, `${p.age} years • ${p.city}`);
            // Let the user know the profile has been selected in conversation
            appendSystemMessage(`Switched active workspace context to: ${p.name}`);
        });
        
        profilesList.appendChild(card);
    });
}

// Select active profile
function selectProfile(name, meta) {
    activeProfileName = name;
    activeProfileNameEl.innerText = name;
    activeProfileMetaEl.innerText = meta;
    
    // Highlight active card in sidebar
    const cards = document.querySelectorAll('.profile-card');
    cards.forEach(card => {
        const cardName = card.querySelector('.profile-card-name').innerText;
        if (cardName === name) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });
}

// Append system message to chat
function appendSystemMessage(text) {
    const sysDiv = document.createElement('div');
    sysDiv.className = 'message system';
    sysDiv.style.alignSelf = 'center';
    sysDiv.style.margin = '8px 0';
    sysDiv.innerHTML = `<span style="font-size: 12px; color: var(--text-secondary); background: rgba(255,255,255,0.05); padding: 4px 12px; border-radius: 12px; border: 1px solid var(--border-color);">${text}</span>`;
    chatFeed.appendChild(sysDiv);
    chatFeed.scrollTop = chatFeed.scrollHeight;
}

// Send suggestion quickly
function sendSuggestion(text) {
    chatInput.value = text;
    sendMessage();
}

// Format message contents (converts simple markdown bold and lists)
function formatMessage(text) {
    // Escape HTML
    let escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
        
    // Format bolding **text** -> <strong>text</strong>
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Format inline code `code` -> <code>code</code>
    escaped = escaped.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Format bullets
    escaped = escaped.replace(/^\s*-\s+(.*)/gm, '<li>$1</li>');
    
    // Wrap lists in ul
    if (escaped.includes('<li>')) {
        // Simple regex replace to group <li> tags
        escaped = escaped.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
    }
    
    // Replace newlines with br, except inside code blocks
    return escaped.replace(/\n/g, '<br>');
}

// Send user message
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    // Remove welcome card if visible
    if (welcomeCard) {
        welcomeCard.remove();
    }
    
    appendMessage(text, 'user');
    chatInput.value = '';
    
    // Add typing indicator
    const typingIndicator = appendTypingIndicator();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                user_id: userId,
                profile_name: activeProfileName,
                thread_id: threadId
            })
        });
        
        typingIndicator.remove();
        
        if (response.ok) {
            const data = await response.json();
            appendMessage(data.response, 'assistant');
            // Refresh profiles list as changes/creations might have happened
            loadProfiles();
        } else {
            const errData = await response.json();
            appendMessage(`Error: ${errData.detail || 'Unable to fetch response'}`, 'assistant error');
        }
    } catch (error) {
        console.error("Network error sending message:", error);
        typingIndicator.remove();
        appendMessage("Network connection error. Please verify the backend is running.", 'assistant error');
    }
}

// Append message bubble
function appendMessage(text, role) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    const isUser = role === 'user';
    const avatarIcon = isUser ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
    
    msgDiv.innerHTML = `
        <div class="message-avatar">${avatarIcon}</div>
        <div class="message-bubble">${isUser ? formatMessage(text) : formatMessage(text)}</div>
    `;
    
    chatFeed.appendChild(msgDiv);
    chatFeed.scrollTop = chatFeed.scrollHeight;
}

// Typing indicator bubble
function appendTypingIndicator() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant';
    
    msgDiv.innerHTML = `
        <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        </div>
    `;
    
    chatFeed.appendChild(msgDiv);
    chatFeed.scrollTop = chatFeed.scrollHeight;
    return msgDiv;
}
