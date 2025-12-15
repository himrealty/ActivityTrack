// Discord OAuth2 Configuration - CORRECT SCOPES
const CLIENT_ID = '1450008731692568729';
const REDIRECT_URI = 'https://discordactivity.netlify.app';
const SCOPES = ['identify', 'rpc', 'rpc.activities.write']; // REQUIRES 'rpc' as base scope

// DOM Elements
const elements = {
    authSection: document.getElementById('auth-section'),
    controlsSection: document.getElementById('controls-section'),
    loginBtn: document.getElementById('login-btn'),
    logoutBtn: document.getElementById('logout-btn'),
    authStatus: document.getElementById('auth-status'),
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

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    console.log('Discord Presence Manager Initializing...');
    
    // First, handle any OAuth redirect
    const handledRedirect = handleOAuthRedirect();
    
    // If not handling a redirect, check for existing session
    if (!handledRedirect) {
        checkExistingSession();
    }
    
    setupEventListeners();
    console.log('App initialized. Stored token:', localStorage.getItem('discord_access_token') ? 'YES' : 'NO');
});

// Handle OAuth redirect with token
function handleOAuthRedirect() {
    console.log('Checking for OAuth redirect...');
    
    // Check URL hash for access token
    if (window.location.hash) {
        console.log('URL hash found:', window.location.hash);
        
        try {
            const hashParams = new URLSearchParams(window.location.hash.substring(1));
            
            if (hashParams.has('access_token')) {
                const accessToken = hashParams.get('access_token');
                const expiresIn = hashParams.get('expires_in') || '604800';
                
                console.log('✅ Access token received!');
                
                // Store the token
                localStorage.setItem('discord_access_token', accessToken);
                localStorage.setItem('discord_token_expiry', 
                    Date.now() + (parseInt(expiresIn) * 1000));
                
                // Clear URL hash (clean up the URL)
                window.history.replaceState({}, document.title, window.location.pathname);
                
                showStatus('Successfully connected to Discord!', 'success');
                showControls();
                
                return true;
            }
            
            if (hashParams.has('error')) {
                const error = hashParams.get('error');
                const errorDesc = hashParams.get('error_description');
                console.error('❌ OAuth Error:', error, '-', errorDesc);
                showStatus(`Authorization failed: ${errorDesc || error}`, 'error');
                
                window.history.replaceState({}, document.title, window.location.pathname);
                return false;
            }
            
        } catch (error) {
            console.error('Error parsing OAuth response:', error);
            showStatus('Error processing authorization', 'error');
        }
    }
    
    return false;
}

// Check for existing valid session
async function checkExistingSession() {
    const accessToken = localStorage.getItem('discord_access_token');
    const tokenExpiry = localStorage.getItem('discord_token_expiry');
    
    if (!accessToken) {
        console.log('No existing session found');
        return;
    }
    
    // Check if token is expired
    const isExpired = tokenExpiry && Date.now() > parseInt(tokenExpiry);
    if (isExpired) {
        console.log('Session expired');
        localStorage.removeItem('discord_access_token');
        localStorage.removeItem('discord_token_expiry');
        return;
    }
    
    // Validate token with Discord API
    try {
        const response = await fetch('https://discord.com/api/v9/users/@me', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        
        if (response.ok) {
            console.log('✅ Existing session is valid');
            showControls();
        } else {
            console.log('❌ Session invalid, clearing...');
            clearLocalStorage();
        }
    } catch (error) {
        console.error('Error validating session:', error);
        // Don't clear on network errors
    }
}

// Start OAuth2 authorization - CORRECT SCOPE
function startOAuthFlow() {
    console.log('🔗 Starting OAuth authorization...');
    
    // Build authorization URL with CORRECT scopes
    const authUrl = new URL('https://discord.com/api/oauth2/authorize');
    
    // REQUIRED parameters
    authUrl.searchParams.append('client_id', CLIENT_ID);
    authUrl.searchParams.append('redirect_uri', REDIRECT_URI);
    authUrl.searchParams.append('response_type', 'token'); // Implicit grant flow
    authUrl.searchParams.append('scope', 'identify rpc rpc.activities.write'); // CORRECT SCOPES
    
    // Optional parameters
    authUrl.searchParams.append('prompt', 'consent');
    
    console.log('OAuth URL:', authUrl.toString());
    console.log('Requesting scopes: identify, rpc, rpc.activities.write');
    
    // Redirect to Discord
    window.location.href = authUrl.toString();
}

// Update Discord Rich Presence
async function updatePresence() {
    const accessToken = localStorage.getItem('discord_access_token');
    
    if (!accessToken) {
        showStatus('Please connect to Discord first', 'error');
        return;
    }
    
    // Get presence data from form
    const presenceData = createPresenceData();
    console.log('Updating presence:', presenceData);
    
    try {
        // Make API request
        const response = await fetch('https://discord.com/api/v9/users/@me/activities', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(presenceData)
        });
        
        console.log('API Response:', response.status, response.statusText);
        
        if (response.ok) {
            showStatus('✅ Rich Presence updated successfully!', 'success');
            
            // Show preview
            elements.presencePreview.classList.remove('hidden');
            updatePreview();
            
            // Log success
            const result = await response.json();
            console.log('Presence update result:', result);
            
        } else if (response.status === 401) {
            // Unauthorized - token expired
            showStatus('Session expired. Please reconnect.', 'error');
            clearLocalStorage();
            showAuth();
        } else {
            // Other error
            const errorText = await response.text();
            console.error('API Error:', errorText);
            showStatus(`Failed to update: ${response.status}`, 'error');
        }
    } catch (error) {
        console.error('Network error:', error);
        showStatus('Network error. Please check connection.', 'error');
    }
}

// Create presence data from form
function createPresenceData() {
    const activityName = elements.activityName.value || 'Custom Activity';
    const details = elements.details.value || undefined;
    const state = elements.state.value || undefined;
    
    // Build presence object
    const presence = {
        name: activityName,
        type: 0, // 0 = Playing, 1 = Streaming, 2 = Listening, 3 = Watching
        details: details,
        state: state,
        timestamps: {},
        assets: {
            large_image: 'default_large',
            large_text: activityName
        }
    };
    
    // Add timestamps if selected
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

// Clear current presence
async function clearPresence() {
    const accessToken = localStorage.getItem('discord_access_token');
    
    if (!accessToken) {
        showStatus('Not connected to Discord', 'error');
        return;
    }
    
    try {
        const response = await fetch('https://discord.com/api/v9/users/@me/activities', {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        
        if (response.ok) {
            showStatus('✅ Presence cleared', 'success');
            elements.presencePreview.classList.add('hidden');
            
            // Clear form
            elements.details.value = '';
            elements.state.value = '';
            elements.timestampType.value = 'none';
            
        } else if (response.status === 401) {
            showStatus('Session expired', 'error');
            clearLocalStorage();
            showAuth();
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

// Load sample configuration
function loadSample() {
    elements.activityName.value = 'Discord Activity';
    elements.details.value = 'Setting up custom presence';
    elements.state.value = 'Using Presence Manager';
    elements.timestampType.value = 'start';
    
    updatePreview();
    showStatus('Sample loaded. Click "Update Presence" to apply.', 'success');
}

// Update the preview display
function updatePreview() {
    const presence = createPresenceData();
    let html = `<div style="margin-bottom: 8px;"><strong>${presence.name}</strong></div>`;
    
    if (presence.details) {
        html += `<div>📝 ${presence.details}</div>`;
    }
    
    if (presence.state) {
        html += `<div>🔹 ${presence.state}</div>`;
    }
    
    if (presence.timestamps.start) {
        html += `<div>🕒 Started now</div>`;
    } else if (presence.timestamps.end) {
        const mins = Math.round((presence.timestamps.end - Math.floor(Date.now() / 1000)) / 60);
        html += `<div>⏱️ ${mins} minutes remaining</div>`;
    }
    
    elements.previewContent.innerHTML = html;
}

// UI Control Functions
function showControls() {
    console.log('Showing controls section');
    elements.authSection.classList.add('hidden');
    elements.controlsSection.classList.remove('hidden');
    
    // Set default values if empty
    if (!elements.activityName.value) {
        elements.activityName.value = 'Custom Activity';
    }
    if (!elements.details.value) {
        elements.details.value = 'Managing Discord presence';
    }
    
    updatePreview();
}

function showAuth() {
    console.log('Showing auth section');
    elements.authSection.classList.remove('hidden');
    elements.controlsSection.classList.add('hidden');
}

function showStatus(message, type) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status ${type}`;
    elements.statusMessage.classList.remove('hidden');
    
    // Auto-hide success messages
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
    showStatus('Logged out successfully', 'success');
    showAuth();
}

// Setup all event listeners
function setupEventListeners() {
    // Login button
    if (elements.loginBtn) {
        elements.loginBtn.addEventListener('click', startOAuthFlow);
    }
    
    // Logout button
    if (elements.logoutBtn) {
        elements.logoutBtn.addEventListener('click', logout);
    }
    
    // Update button
    if (elements.updateBtn) {
        elements.updateBtn.addEventListener('click', updatePresence);
    }
    
    // Clear button
    if (elements.clearBtn) {
        elements.clearBtn.addEventListener('click', clearPresence);
    }
    
    // Sample button
    const sampleBtn = document.getElementById('sample-btn');
    if (sampleBtn) {
        sampleBtn.addEventListener('click', loadSample);
    }
    
    // Form interactions for preview
    if (elements.timestampType) {
        elements.timestampType.addEventListener('change', () => {
            if (elements.countdownGroup) {
                elements.countdownGroup.classList.toggle('hidden', 
                    elements.timestampType.value !== 'end');
            }
            updatePreview();
        });
    }
    
    // Real-time preview updates
    ['activityName', 'details', 'state', 'countdown'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', updatePreview);
        }
    });
}

// Debug function
window.debugApp = function() {
    console.log('=== APP DEBUG INFO ===');
    console.log('Client ID:', CLIENT_ID);
    console.log('Redirect URI:', REDIRECT_URI);
    console.log('Requested Scopes:', 'identify rpc rpc.activities.write');
    console.log('Stored Token:', localStorage.getItem('discord_access_token') ? 'YES' : 'NO');
    console.log('Current URL:', window.location.href);
    console.log('URL Hash:', window.location.hash);
    console.log('Local Storage:', {
        token: localStorage.getItem('discord_access_token')?.substring(0, 20) + '...',
        expiry: localStorage.getItem('discord_token_expiry')
    });
    console.log('=====================');
};

// Auto-test OAuth URL on load (for debugging)
window.generateOAuthUrl = function() {
    const authUrl = new URL('https://discord.com/api/oauth2/authorize');
    authUrl.searchParams.append('client_id', CLIENT_ID);
    authUrl.searchParams.append('redirect_uri', REDIRECT_URI);
    authUrl.searchParams.append('response_type', 'token');
    authUrl.searchParams.append('scope', 'identify rpc rpc.activities.write');
    authUrl.searchParams.append('prompt', 'consent');
    
    console.log('Generated OAuth URL:');
    console.log(authUrl.toString());
    console.log('Encoded for testing:');
    console.log(encodeURI(authUrl.toString()));
    
    return authUrl.toString();
};
