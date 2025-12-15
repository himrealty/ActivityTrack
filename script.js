// Discord OAuth2 Configuration
const CLIENT_ID = '1450008731692568729';
const REDIRECT_URI = 'https://discordactivity.netlify.app';
const SCOPES = ['identify', 'rpc', 'rpc.activities.write'];

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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔄 App initializing...');
    
    // First check if we have a token in URL (OAuth callback)
    if (window.location.hash.includes('access_token')) {
        handleOAuthCallback();
    } else {
        // Check for existing valid token
        checkExistingToken();
    }
    
    setupEventListeners();
});

// Handle OAuth callback
function handleOAuthCallback() {
    console.log('📥 Handling OAuth callback...');
    
    try {
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        
        const accessToken = params.get('access_token');
        const expiresIn = params.get('expires_in') || '604800';
        
        if (accessToken) {
            console.log('✅ Got access token!');
            
            // Store token
            localStorage.setItem('discord_access_token', accessToken);
            localStorage.setItem('discord_token_expiry', 
                Date.now() + (parseInt(expiresIn) * 1000));
            
            // Clear URL hash
            window.history.replaceState({}, document.title, window.location.pathname);
            
            showStatus('✅ Successfully connected to Discord!', 'success');
            showControls();
            
            // Test the token immediately
            testToken(accessToken);
        }
        
        if (params.has('error')) {
            const error = params.get('error');
            const errorDesc = params.get('error_description');
            console.error('❌ OAuth Error:', error, '-', errorDesc);
            showStatus(`Authorization failed: ${errorDesc || error}`, 'error');
        }
        
    } catch (error) {
        console.error('Error processing OAuth:', error);
        showStatus('Error processing authorization', 'error');
    }
}

// Test if token works
async function testToken(accessToken) {
    try {
        console.log('🧪 Testing token validity...');
        const response = await fetch('https://discord.com/api/v9/users/@me', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        
        if (response.ok) {
            console.log('✅ Token is valid!');
        } else {
            console.warn('⚠️ Token might be invalid:', response.status);
        }
    } catch (error) {
        console.error('Token test failed:', error);
    }
}

// Check existing token
async function checkExistingToken() {
    const accessToken = localStorage.getItem('discord_access_token');
    const tokenExpiry = localStorage.getItem('discord_token_expiry');
    
    if (!accessToken) {
        console.log('No existing token');
        return;
    }
    
    // Check expiry
    if (tokenExpiry && Date.now() > parseInt(tokenExpiry)) {
        console.log('Token expired');
        clearLocalStorage();
        return;
    }
    
    console.log('Found existing token, checking validity...');
    
    try {
        const response = await fetch('https://discord.com/api/v9/users/@me', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        
        if (response.ok) {
            console.log('✅ Existing token is valid');
            showControls();
        } else {
            console.log('❌ Token invalid');
            clearLocalStorage();
        }
    } catch (error) {
        console.error('Error checking token:', error);
    }
}

// Start OAuth flow
function startOAuthFlow() {
    console.log('🔗 Starting OAuth...');
    
    const authUrl = new URL('https://discord.com/api/oauth2/authorize');
    authUrl.searchParams.append('client_id', CLIENT_ID);
    authUrl.searchParams.append('redirect_uri', REDIRECT_URI);
    authUrl.searchParams.append('response_type', 'token');
    authUrl.searchParams.append('scope', 'identify rpc rpc.activities.write');
    authUrl.searchParams.append('prompt', 'consent');
    
    console.log('OAuth URL:', authUrl.toString());
    window.location.href = authUrl.toString();
}

// UPDATE DISCORD PRESENCE - CORRECTED API CALL
async function updatePresence() {
    const accessToken = localStorage.getItem('discord_access_token');
    
    if (!accessToken) {
        showStatus('Please connect to Discord first', 'error');
        return;
    }
    
    console.log('🔄 Updating presence...');
    
    // Get presence data
    const presenceData = createPresenceData();
    console.log('Presence data:', presenceData);
    
    try {
        // CRITICAL FIX: Use the CORRECT Discord API endpoint
        // The endpoint for updating user activities has changed
        const response = await fetch('https://discord.com/api/v9/users/@me/settings', {
            method: 'PATCH',  // Changed from POST to PATCH
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                custom_status: {
                    text: presenceData.details || 'Using Discord Activity',
                    emoji_name: '🎮'
                }
            })
        });
        
        console.log('📡 API Response:', response.status, response.statusText);
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ Presence updated:', result);
            
            // ALSO try the activities endpoint (for richer presence)
            try {
                await updateRichPresence(accessToken, presenceData);
            } catch (richError) {
                console.log('Rich presence update failed, but basic status set');
            }
            
            showStatus('✅ Status updated! Check your Discord profile.', 'success');
            updatePreview();
            elements.presencePreview.classList.remove('hidden');
            
        } else if (response.status === 401) {
            showStatus('Session expired. Please reconnect.', 'error');
            clearLocalStorage();
            showAuth();
        } else {
            const errorText = await response.text();
            console.error('❌ API Error:', errorText);
            showStatus(`Failed: ${response.status}. Trying alternative method...`, 'error');
            
            // Try alternative method
            await tryAlternativePresenceMethod(accessToken, presenceData);
        }
        
    } catch (error) {
        console.error('🌐 Network error:', error);
        
        // Show helpful error message
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            showStatus('Cannot connect to Discord API. Check if you have CORS issues or try a different browser.', 'error');
        } else {
            showStatus(`Network error: ${error.message}`, 'error');
        }
    }
}

// Alternative method for setting presence
async function tryAlternativePresenceMethod(accessToken, presenceData) {
    console.log('Trying alternative presence method...');
    
    try {
        // Method 1: Set activity via activities endpoint
        const activityResponse = await fetch('https://discord.com/api/v9/users/@me/activities', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                activities: [{
                    name: presenceData.name,
                    type: presenceData.type,
                    details: presenceData.details,
                    state: presenceData.state,
                    timestamps: presenceData.timestamps,
                    assets: presenceData.assets
                }],
                status: 'online',
                afk: false
            })
        });
        
        if (activityResponse.ok) {
            console.log('✅ Alternative method worked!');
            showStatus('✅ Presence updated via alternative method!', 'success');
            return true;
        }
        
        // Method 2: Try with different endpoint
        const simpleResponse = await fetch('https://discord.com/api/v9/users/@me/activity', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(presenceData)
        });
        
        if (simpleResponse.ok) {
            console.log('✅ Simple endpoint worked!');
            showStatus('✅ Presence updated!', 'success');
            return true;
        }
        
        console.log('All alternative methods failed');
        return false;
        
    } catch (altError) {
        console.error('Alternative methods failed:', altError);
        return false;
    }
}

// Update rich presence (more detailed)
async function updateRichPresence(accessToken, presenceData) {
    try {
        const response = await fetch('https://discord.com/api/v9/users/@me/activities', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(presenceData)
        });
        
        if (response.ok) {
            console.log('✅ Rich presence updated');
            return true;
        }
        return false;
    } catch (error) {
        console.error('Rich presence error:', error);
        return false;
    }
}

// Create presence data
function createPresenceData() {
    const activityName = elements.activityName.value || 'Custom Activity';
    const details = elements.details.value || undefined;
    const state = elements.state.value || undefined;
    
    const presence = {
        name: activityName,
        type: 0,
        details: details,
        state: state,
        timestamps: {},
        assets: {
            large_image: 'default_large',
            large_text: activityName
        },
        buttons: [
            {
                label: 'Set via Discord Activity',
                url: 'https://discordactivity.netlify.app'
            }
        ]
    };
    
    const timestampType = elements.timestampType.value;
    const now = Math.floor(Date.now() / 1000);
    
    if (timestampType === 'start') {
        presence.timestamps.start = now;
    } else if (timestampType === 'end') {
        const countdown = parseInt(elements.countdown.value) || 60;
        presence.timestamps.end = now + (countdown * 60);
    }
    
    return presence;
}

// Clear presence
async function clearPresence() {
    const accessToken = localStorage.getItem('discord_access_token');
    
    if (!accessToken) {
        showStatus('Not connected', 'error');
        return;
    }
    
    try {
        // Clear custom status
        const response = await fetch('https://discord.com/api/v9/users/@me/settings', {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                custom_status: null
            })
        });
        
        if (response.ok) {
            showStatus('✅ Status cleared', 'success');
            elements.presencePreview.classList.add('hidden');
            
            // Clear form
            elements.details.value = '';
            elements.state.value = '';
            elements.timestampType.value = 'none';
            
            // Also clear activities
            try {
                await fetch('https://discord.com/api/v9/users/@me/activities', {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${accessToken}` }
                });
            } catch (e) {
                // Ignore this error
            }
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

// Load sample
function loadSample() {
    elements.activityName.value = 'Discord Activity';
    elements.details.value = 'Setting custom status';
    elements.state.value = 'Online via web app';
    elements.timestampType.value = 'start';
    
    updatePreview();
    showStatus('Sample loaded', 'success');
}

// Update preview
function updatePreview() {
    const presence = createPresenceData();
    let html = `<div><strong>${presence.name}</strong></div>`;
    
    if (presence.details) html += `<div>${presence.details}</div>`;
    if (presence.state) html += `<div>${presence.state}</div>`;
    
    if (presence.timestamps.start) {
        html += `<div>Started: Now</div>`;
    } else if (presence.timestamps.end) {
        const mins = Math.round((presence.timestamps.end - Math.floor(Date.now() / 1000)) / 60);
        html += `<div>Ends in: ${mins} min</div>`;
    }
    
    elements.previewContent.innerHTML = html;
}

// UI functions
function showControls() {
    console.log('Showing controls');
    elements.authSection.classList.add('hidden');
    elements.controlsSection.classList.remove('hidden');
    
    if (!elements.activityName.value) {
        elements.activityName.value = 'Custom Activity';
    }
    
    updatePreview();
}

function showAuth() {
    console.log('Showing auth');
    elements.authSection.classList.remove('hidden');
    elements.controlsSection.classList.add('hidden');
}

function showStatus(message, type) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status ${type}`;
    elements.statusMessage.classList.remove('hidden');
    
    if (type === 'success') {
        setTimeout(() => {
            elements.statusMessage.classList.add('hidden');
        }, 5000);
    }
}

function clearLocalStorage() {
    localStorage.removeItem('discord_access_token');
    localStorage.removeItem('discord_token_expiry');
}

function logout() {
    clearLocalStorage();
    showStatus('Logged out', 'success');
    showAuth();
}

// Setup event listeners
function setupEventListeners() {
    if (elements.loginBtn) {
        elements.loginBtn.addEventListener('click', startOAuthFlow);
    }
    
    if (elements.logoutBtn) {
        elements.logoutBtn.addEventListener('click', logout);
    }
    
    if (elements.updateBtn) {
        elements.updateBtn.addEventListener('click', updatePresence);
    }
    
    if (elements.clearBtn) {
        elements.clearBtn.addEventListener('click', clearPresence);
    }
    
    const sampleBtn = document.getElementById('sample-btn');
    if (sampleBtn) {
        sampleBtn.addEventListener('click', loadSample);
    }
    
    if (elements.timestampType) {
        elements.timestampType.addEventListener('change', () => {
            if (elements.countdownGroup) {
                elements.countdownGroup.classList.toggle('hidden', 
                    elements.timestampType.value !== 'end');
            }
            updatePreview();
        });
    }
    
    ['activityName', 'details', 'state', 'countdown'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', updatePreview);
        }
    });
}

// Debug helper
window.testConnection = async function() {
    console.log('🧪 Testing Discord API connection...');
    
    const token = localStorage.getItem('discord_access_token');
    if (!token) {
        console.log('No token found');
        return;
    }
    
    console.log('Testing /users/@me endpoint...');
    try {
        const response = await fetch('https://discord.com/api/v9/users/@me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        console.log('Response:', response.status, response.ok);
        
        if (response.ok) {
            const user = await response.json();
            console.log('User:', user.username);
            return true;
        }
    } catch (error) {
        console.error('Test failed:', error);
    }
    
    return false;
};
