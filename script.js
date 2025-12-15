// Discord OAuth2 Configuration
const CLIENT_ID = '1450008731692568729';
const REDIRECT_URI = 'https://discordactivity.netlify.app';

// DOM Elements
const elements = {
    authSection: document.getElementById('auth-section'),
    controlsSection: document.getElementById('controls-section'),
    loginBtn: document.getElementById('login-btn'),
    logoutBtn: document.getElementById('logout-btn'),
    statusMessage: document.getElementById('status-message'),
    updateBtn: document.getElementById('update-btn'),
    clearBtn: document.getElementById('clear-btn'),
    presencePreview: document.getElementById('presence-preview'),
    previewContent: document.getElementById('preview-content'),
    
    activityName: document.getElementById('activity-name'),
    details: document.getElementById('details'),
    state: document.getElementById('state'),
    timestampType: document.getElementById('timestamp-type'),
    countdownGroup: document.getElementById('countdown-group'),
    countdown: document.getElementById('countdown')
};

// Try different scope combinations
const SCOPE_VARIANTS = [
    'identify activities.write',
    'identify rpc rpc.activities.write',
    'identify rpc.activities.write',
    'identify'
];

let currentScopeIndex = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Discord Presence Manager');
    
    // Handle OAuth redirect
    if (window.location.hash.includes('access_token')) {
        handleOAuthRedirect();
    } else {
        checkExistingSession();
    }
    
    setupEventListeners();
});

// Handle OAuth redirect
function handleOAuthRedirect() {
    try {
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        
        if (params.has('access_token')) {
            const accessToken = params.get('access_token');
            localStorage.setItem('discord_access_token', accessToken);
            
            // Clear URL
            window.history.replaceState({}, document.title, window.location.pathname);
            
            showStatus('✅ Connected to Discord', 'success');
            showControls();
            
            // Test what permissions we have
            testPermissions(accessToken);
        }
    } catch (error) {
        console.error('OAuth error:', error);
    }
}

// Test API permissions
async function testPermissions(token) {
    console.log('Testing API permissions...');
    
    const tests = [
        { name: 'User Info', url: 'https://discord.com/api/v9/users/@me', method: 'GET' },
        { name: 'Update Status', url: 'https://discord.com/api/v9/users/@me/settings', method: 'PATCH', 
          body: { custom_status: { text: 'Testing API', emoji_name: '🔧' } } },
        { name: 'Set Activity', url: 'https://discord.com/api/v9/users/@me/activities', method: 'POST',
          body: { name: 'Test', type: 0, details: 'Testing' } }
    ];
    
    for (const test of tests) {
        try {
            const options = {
                method: test.method,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            };
            
            if (test.body) {
                options.body = JSON.stringify(test.body);
            }
            
            const response = await fetch(test.url, options);
            console.log(`${test.name}: ${response.status} ${response.ok ? '✅' : '❌'}`);
            
            if (!response.ok && response.status !== 401) {
                const error = await response.text();
                console.log(`  Error: ${error.substring(0, 100)}`);
            }
        } catch (error) {
            console.log(`${test.name}: ❌ ${error.message}`);
        }
    }
}

// Start OAuth with current scope
function startOAuthFlow() {
    const scope = SCOPE_VARIANTS[currentScopeIndex];
    console.log(`Trying scope: ${scope}`);
    
    const authUrl = new URL('https://discord.com/api/oauth2/authorize');
    authUrl.searchParams.append('client_id', CLIENT_ID);
    authUrl.searchParams.append('redirect_uri', REDIRECT_URI);
    authUrl.searchParams.append('response_type', 'token');
    authUrl.searchParams.append('scope', scope);
    authUrl.searchParams.append('prompt', 'consent');
    
    window.location.href = authUrl.toString();
}

// Try next scope variant
function tryNextScope() {
    currentScopeIndex = (currentScopeIndex + 1) % SCOPE_VARIANTS.length;
    showStatus(`Trying different permissions...`, 'info');
    setTimeout(() => startOAuthFlow(), 1000);
}

// Update presence - tries multiple methods
async function updatePresence() {
    const token = localStorage.getItem('discord_access_token');
    if (!token) {
        showStatus('Please connect first', 'error');
        return;
    }
    
    const presenceData = createPresenceData();
    console.log('Updating with:', presenceData);
    
    // Try Method 1: Custom Status
    try {
        const statusResponse = await fetch('https://discord.com/api/v9/users/@me/settings', {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                custom_status: {
                    text: presenceData.details || presenceData.state || 'Using Discord Activity',
                    emoji_name: '🎮'
                }
            })
        });
        
        if (statusResponse.ok) {
            showStatus('✅ Custom status updated', 'success');
            updatePreview();
            elements.presencePreview.classList.remove('hidden');
            return;
        }
    } catch (error) {
        console.log('Method 1 failed:', error.message);
    }
    
    // Try Method 2: Activity
    try {
        const activityResponse = await fetch('https://discord.com/api/v9/users/@me/activities', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(presenceData)
        });
        
        if (activityResponse.ok) {
            showStatus('✅ Activity set successfully', 'success');
            updatePreview();
            elements.presencePreview.classList.remove('hidden');
            return;
        }
    } catch (error) {
        console.log('Method 2 failed:', error.message);
    }
    
    // If both fail
    showStatus('Failed to update. Trying different permissions...', 'error');
    setTimeout(() => tryNextScope(), 2000);
}

// Create presence data
function createPresenceData() {
    const activityName = elements.activityName.value || 'Custom Activity';
    const details = elements.details.value || undefined;
    const state = elements.state.value || undefined;
    
    return {
        name: activityName,
        type: 0,
        details: details,
        state: state,
        timestamps: {},
        assets: {
            large_image: 'default_large',
            large_text: activityName
        }
    };
}

// Check existing session
async function checkExistingSession() {
    const token = localStorage.getItem('discord_access_token');
    if (token) {
        try {
            const response = await fetch('https://discord.com/api/v9/users/@me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                showControls();
            }
        } catch (error) {
            console.log('Session check failed');
        }
    }
}

// UI Functions
function showControls() {
    elements.authSection.classList.add('hidden');
    elements.controlsSection.classList.remove('hidden');
    updatePreview();
}

function showStatus(message, type) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status ${type}`;
    elements.statusMessage.classList.remove('hidden');
    
    if (type === 'success') {
        setTimeout(() => elements.statusMessage.classList.add('hidden'), 5000);
    }
}

// Setup event listeners
function setupEventListeners() {
    if (elements.loginBtn) elements.loginBtn.addEventListener('click', startOAuthFlow);
    if (elements.logoutBtn) elements.logoutBtn.addEventListener('click', logout);
    if (elements.updateBtn) elements.updateBtn.addEventListener('click', updatePresence);
    if (elements.clearBtn) elements.clearBtn.addEventListener('click', clearPresence);
    
    // Real-time preview
    ['activityName', 'details', 'state', 'countdown'].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.addEventListener('input', updatePreview);
    });
}

function logout() {
    localStorage.removeItem('discord_access_token');
    showStatus('Logged out', 'success');
    elements.authSection.classList.remove('hidden');
    elements.controlsSection.classList.add('hidden');
}

function clearPresence() {
    const token = localStorage.getItem('discord_access_token');
    if (!token) return;
    
    fetch('https://discord.com/api/v9/users/@me/settings', {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ custom_status: null })
    }).then(() => {
        showStatus('✅ Status cleared', 'success');
        elements.presencePreview.classList.add('hidden');
    });
}

function updatePreview() {
    const presence = createPresenceData();
    let html = `<strong>${presence.name}</strong>`;
    if (presence.details) html += `<br>${presence.details}`;
    if (presence.state) html += `<br>${presence.state}`;
    elements.previewContent.innerHTML = html;
}
