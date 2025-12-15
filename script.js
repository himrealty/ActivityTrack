// Discord OAuth2 Configuration - USE YOUR VALUES
const CLIENT_ID = '1450008731692568729';
const REDIRECT_URI = 'https://discordactivity.netlify.app';
const SCOPES = ['identify', 'activities.write']; // ONLY THESE TWO SCOPES

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
    
    // Form inputs
    activityName: document.getElementById('activity-name'),
    details: document.getElementById('details'),
    state: document.getElementById('state'),
    timestampType: document.getElementById('timestamp-type'),
    countdownGroup: document.getElementById('countdown-group'),
    countdown: document.getElementById('countdown')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('App initializing...');
    
    // Check if we're returning from OAuth with a token
    handleOAuthRedirect();
    
    // Check if we already have a valid token
    checkExistingToken();
    
    setupEventListeners();
});

// Handle OAuth redirect - THIS IS THE KEY FUNCTION
function handleOAuthRedirect() {
    console.log('Checking URL for OAuth response...');
    console.log('Full URL:', window.location.href);
    console.log('Hash:', window.location.hash);
    
    // Check for token in URL hash (response_type=token flow)
    if (window.location.hash.includes('access_token')) {
        console.log('Found access token in URL hash!');
        
        try {
            // Parse the hash parameters
            const hash = window.location.hash.substring(1);
            const params = new URLSearchParams(hash);
            
            const accessToken = params.get('access_token');
            const tokenType = params.get('token_type');
            const expiresIn = params.get('expires_in');
            
            console.log('Token received! Type:', tokenType, 'Expires in:', expiresIn, 'seconds');
            
            if (accessToken) {
                // Store the token
                localStorage.setItem('discord_access_token', accessToken);
                localStorage.setItem('discord_token_expiry', 
                    Date.now() + (parseInt(expiresIn || 604800) * 1000));
                
                // Clear the URL hash
                window.history.replaceState({}, document.title, window.location.pathname);
                
                console.log('Token saved successfully!');
                
                // Show success and controls
                showStatus('Successfully connected to Discord!', 'success');
                showControls();
                
                return true;
            }
        } catch (error) {
            console.error('Error parsing OAuth response:', error);
            showStatus('Error processing authorization. Please try again.', 'error');
        }
    }
    
    // Check for errors
    if (window.location.hash.includes('error')) {
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        const error = params.get('error');
        const errorDesc = params.get('error_description');
        
        console.error('OAuth error:', error, '-', errorDesc);
        showStatus(`Authorization failed: ${errorDesc || error}`, 'error');
        
        // Clear the URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    return false;
}

// Check if we already have a valid token
async function checkExistingToken() {
    const accessToken = localStorage.getItem('discord_access_token');
    const tokenExpiry = localStorage.getItem('discord_token_expiry');
    
    if (!accessToken) {
        console.log('No existing token found');
        return;
    }
    
    // Check if token is expired
    if (tokenExpiry && Date.now() > parseInt(tokenExpiry)) {
        console.log('Token expired');
        localStorage.removeItem('discord_access_token');
        showAuth();
        return;
    }
    
    console.log('Found existing token, validating...');
    
    // Try to validate the token with a simple API call
    try {
        const response = await fetch('https://discord.com/api/v9/users/@me', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            console.log('Existing token is valid');
            showControls();
        } else {
            console.log('Existing token invalid');
            localStorage.removeItem('discord_access_token');
            showAuth();
        }
    } catch (error) {
        console.error('Error validating token:', error);
        showAuth();
    }
}

// Start OAuth2 Flow - CORRECT IMPLEMENTATION
function startOAuthFlow() {
    console.log('Starting OAuth flow...');
    
    // Build the authorization URL - MUST use response_type=token
    const authUrl = new URL('https://discord.com/api/oauth2/authorize');
    
    // REQUIRED parameters
    authUrl.searchParams.append('client_id', CLIENT_ID);
    authUrl.searchParams.append('redirect_uri', REDIRECT_URI);
    authUrl.searchParams.append('response_type', 'token'); // MUST be 'token' for client-side
    authUrl.searchParams.append('scope', SCOPES.join(' '));
    
    // Optional but recommended
    authUrl.searchParams.append('prompt', 'consent');
    
    console.log('Redirecting to:', authUrl.toString());
    
    // Redirect to Discord authorization
    window.location.href = authUrl.toString();
}

// Update Discord Presence
async function updatePresence() {
    const accessToken = localStorage.getItem('discord_access_token');
    
    if (!accessToken) {
        showStatus('Not connected to Discord. Please connect first.', 'error');
        return;
    }
    
    try {
        // Prepare presence data
        const presenceData = createPresenceData();
        console.log('Updating presence with:', presenceData);
        
        // Make API request to update presence
        const response = await fetch('https://discord.com/api/v9/users/@me/activities', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(presenceData)
        });
        
        console.log('API Response status:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('Presence update successful!');
            showStatus('✅ Rich Presence updated successfully! Check your Discord status.', 'success');
            
            // Show preview
            elements.presencePreview.classList.remove('hidden');
            updatePreview();
            
        } else if (response.status === 401) {
            // Token expired or invalid
            showStatus('Session expired. Please reconnect.', 'error');
            localStorage.removeItem('discord_access_token');
            showAuth();
        } else {
            const errorText = await response.text();
            console.error('API Error response:', errorText);
            showStatus(`Failed to update: ${response.status} - Check console for details`, 'error');
        }
    } catch (error) {
        console.error('Update failed:', error);
        showStatus(`Network error: ${error.message}`, 'error');
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
        type: 0, // 0 = Playing
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
    
    // Add timestamps
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
        showStatus('Not connected to Discord.', 'error');
        return;
    }
    
    try {
        const response = await fetch('https://discord.com/api/v9/users/@me/activities', {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            }
        });
        
        if (response.ok) {
            showStatus('✅ Presence cleared', 'success');
            elements.presencePreview.classList.add('hidden');
            
            // Clear form
            elements.details.value = '';
            elements.state.value = '';
            
        } else if (response.status === 401) {
            showStatus('Session expired. Please reconnect.', 'error');
            localStorage.removeItem('discord_access_token');
            showAuth();
        } else {
            showStatus(`Failed to clear: ${response.status}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

// Load sample configuration
function loadSample() {
    elements.activityName.value = 'Rich Presence Manager';
    elements.details.value = 'Customizing Discord Status';
    elements.state.value = 'via Discord Activity';
    elements.timestampType.value = 'start';
    
    updatePreview();
    showStatus('Sample loaded. Click "Update Presence" to apply.', 'success');
}

// Update preview display
function updatePreview() {
    const presence = createPresenceData();
    let previewHTML = `
        <div style="margin-bottom: 10px;"><strong>${presence.name}</strong></div>
    `;
    
    if (presence.details) {
        previewHTML += `<div>📝 ${presence.details}</div>`;
    }
    
    if (presence.state) {
        previewHTML += `<div>🔹 ${presence.state}</div>`;
    }
    
    if (presence.timestamps.start) {
        previewHTML += `<div>🕒 Started just now</div>`;
    } else if (presence.timestamps.end) {
        const minutesLeft = Math.round((presence.timestamps.end - Math.floor(Date.now() / 1000)) / 60);
        previewHTML += `<div>⏱️ ${minutesLeft} minutes remaining</div>`;
    }
    
    elements.previewContent.innerHTML = previewHTML;
}

// UI Functions
function showControls() {
    console.log('Showing controls');
    elements.authSection.classList.add('hidden');
    elements.controlsSection.classList.remove('hidden');
    
    // Load default/sample data
    if (!elements.activityName.value) {
        elements.activityName.value = 'Custom Activity';
    }
    if (!elements.details.value) {
        elements.details.value = 'Setting up presence...';
    }
    if (!elements.state.value) {
        elements.state.value = 'via Discord Activity';
    }
    
    updatePreview();
}

function showAuth() {
    console.log('Showing auth screen');
    elements.authSection.classList.remove('hidden');
    elements.controlsSection.classList.add('hidden');
}

function showStatus(message, type) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status ${type}`;
    elements.statusMessage.classList.remove('hidden');
    
    // Auto-hide after 5 seconds (except errors)
    if (type !== 'error') {
        setTimeout(() => {
            elements.statusMessage.classList.add('hidden');
        }, 5000);
    }
}

// Logout function
function logout() {
    localStorage.removeItem('discord_access_token');
    localStorage.removeItem('discord_token_expiry');
    showStatus('Logged out successfully', 'success');
    showAuth();
}

// Setup event listeners
function setupEventListeners() {
    // Login button
    if (elements.loginBtn) {
        elements.loginBtn.addEventListener('click', startOAuthFlow);
    }
    
    // Logout button
    if (elements.logoutBtn) {
        elements.logoutBtn.addEventListener('click', logout);
    }
    
    // Update presence button
    if (elements.updateBtn) {
        elements.updateBtn.addEventListener('click', updatePresence);
    }
    
    // Clear presence button
    if (elements.clearBtn) {
        elements.clearBtn.addEventListener('click', clearPresence);
    }
    
    // Sample button (if exists)
    const sampleBtn = document.getElementById('sample-btn');
    if (sampleBtn) {
        sampleBtn.addEventListener('click', loadSample);
    }
    
    // Form input listeners for real-time preview
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
    const inputs = ['activityName', 'details', 'state', 'countdown'];
    inputs.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', updatePreview);
        }
    });
}

// Debug helper
window.debugApp = function() {
    console.log('=== APP DEBUG INFO ===');
    console.log('Client ID:', CLIENT_ID);
    console.log('Redirect URI:', REDIRECT_URI);
    console.log('Scopes:', SCOPES);
    console.log('Stored Token:', localStorage.getItem('discord_access_token') ? 'YES' : 'NO');
    console.log('Current URL:', window.location.href);
    console.log('URL Hash:', window.location.hash);
    console.log('=====================');
};
