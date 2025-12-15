// Discord OAuth2 Configuration
const CLIENT_ID = 'YOUR_CLIENT_ID_HERE'; // Get from Discord Developer Portal
const REDIRECT_URI = window.location.origin + window.location.pathname;
const SCOPES = ['identify', 'activities.write']; // activities.write is KEY

// Token storage
let accessToken = localStorage.getItem('discord_access_token');
let refreshToken = localStorage.getItem('discord_refresh_token');
let tokenExpiry = localStorage.getItem('discord_token_expiry');

// DOM Elements
const elements = {
    authSection: document.getElementById('auth-section'),
    controlsSection: document.getElementById('controls-section'),
    loginBtn: document.getElementById('login-btn'),
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
    // Check for OAuth callback
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    
    if (params.has('access_token')) {
        handleOAuthCallback(params);
    } else if (accessToken && tokenExpiry && Date.now() < tokenExpiry) {
        // Already logged in with valid token
        showControls();
    } else if (accessToken) {
        // Token might be expired, try to refresh
        refreshAccessToken();
    }
    
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    elements.loginBtn.addEventListener('click', startOAuthFlow);
    elements.updateBtn.addEventListener('click', updatePresence);
    elements.clearBtn.addEventListener('click', clearPresence);
    
    elements.timestampType.addEventListener('change', () => {
        elements.countdownGroup.classList.toggle('hidden', 
            elements.timestampType.value !== 'end');
        updatePreview();
    });
    
    // Real-time preview updates
    ['activityName', 'details', 'state', 'countdown'].forEach(id => {
        document.getElementById(id).addEventListener('input', updatePreview);
    });
}

// Start OAuth2 Flow
function startOAuthFlow() {
    const authUrl = new URL('https://discord.com/api/oauth2/authorize');
    authUrl.searchParams.append('client_id', CLIENT_ID);
    authUrl.searchParams.append('redirect_uri', REDIRECT_URI);
    authUrl.searchParams.append('response_type', 'token');
    authUrl.searchParams.append('scope', SCOPES.join(' '));
    authUrl.searchParams.append('prompt', 'consent');
    
    window.location.href = authUrl.toString();
}

// Handle OAuth callback
function handleOAuthCallback(params) {
    accessToken = params.get('access_token');
    refreshToken = params.get('refresh_token');
    const expiresIn = parseInt(params.get('expires_in')) * 1000;
    tokenExpiry = Date.now() + expiresIn;
    
    // Store tokens
    localStorage.setItem('discord_access_token', accessToken);
    localStorage.setItem('discord_refresh_token', refreshToken);
    localStorage.setItem('discord_token_expiry', tokenExpiry);
    
    // Clear URL hash
    window.history.replaceState({}, document.title, window.location.pathname);
    
    showStatus('Successfully connected to Discord!', 'success');
    showControls();
}

// Refresh access token
async function refreshAccessToken() {
    if (!refreshToken) {
        showStatus('Session expired. Please reconnect.', 'error');
        return;
    }
    
    try {
        const response = await fetch('https://discord.com/api/oauth2/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                client_id: CLIENT_ID,
                client_secret: 'YOUR_CLIENT_SECRET', // From Discord Dev Portal
                grant_type: 'refresh_token',
                refresh_token: refreshToken
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            accessToken = data.access_token;
            refreshToken = data.refresh_token;
            tokenExpiry = Date.now() + (data.expires_in * 1000);
            
            localStorage.setItem('discord_access_token', accessToken);
            localStorage.setItem('discord_refresh_token', refreshToken);
            localStorage.setItem('discord_token_expiry', tokenExpiry);
            
            showControls();
        } else {
            throw new Error('Token refresh failed');
        }
    } catch (error) {
        console.error('Refresh failed:', error);
        showStatus('Session expired. Please reconnect.', 'error');
        clearTokens();
    }
}

// Update Discord Presence via REST API
async function updatePresence() {
    if (!accessToken) {
        showStatus('Not authenticated. Please connect first.', 'error');
        return;
    }
    
    try {
        // Prepare presence data
        const presenceData = createPresenceData();
        
        // Make API request to update presence
        const response = await fetch('https://discord.com/api/v9/users/@me/activities', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(presenceData)
        });
        
        if (response.ok) {
            showStatus('✓ Presence updated successfully!', 'success');
            
            // Show preview
            elements.presencePreview.classList.remove('hidden');
            updatePreview();
            
            // Also update via RPC for real-time updates (if available)
            try {
                await updateViaRPC(presenceData);
            } catch (rpcError) {
                // RPC is optional, API already worked
            }
            
        } else if (response.status === 401) {
            // Token expired, try to refresh
            await refreshAccessToken();
            await updatePresence(); // Retry
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Failed to update presence');
        }
    } catch (error) {
        console.error('Update failed:', error);
        showStatus(`Error: ${error.message}`, 'error');
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
        application_id: CLIENT_ID,
        details: details,
        state: state,
        timestamps: {},
        assets: {
            large_image: 'default_large', // You can customize these
            large_text: activityName
        },
        buttons: [
            {
                label: 'Powered by Presence Manager',
                url: window.location.href
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

// Clear presence (set to nothing)
async function clearPresence() {
    if (!accessToken) return;
    
    try {
        const response = await fetch('https://discord.com/api/v9/users/@me/activities', {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            }
        });
        
        if (response.ok) {
            showStatus('✓ Presence cleared', 'success');
            elements.presencePreview.classList.add('hidden');
            
            // Clear form
            elements.details.value = '';
            elements.state.value = '';
            
        } else if (response.status === 401) {
            await refreshAccessToken();
            await clearPresence();
        }
    } catch (error) {
        showStatus(`Error clearing: ${error.message}`, 'error');
    }
}

// Optional: Try to update via WebSocket RPC for instant updates
async function updateViaRPC(presenceData) {
    // This is the fallback for instant updates in Discord desktop
    // It's optional but provides better UX
    return new Promise((resolve, reject) => {
        if (!window.DiscordRPC) {
            reject(new Error('RPC not available'));
            return;
        }
        
        const client = new window.DiscordRPC.Client({ transport: 'websocket' });
        
        client.on('ready', async () => {
            try {
                await client.setActivity(presenceData);
                client.destroy();
                resolve();
            } catch (error) {
                reject(error);
            }
        });
        
        client.login({ clientId: CLIENT_ID }).catch(reject);
        
        // Timeout after 5 seconds
        setTimeout(() => {
            client.destroy();
            reject(new Error('RPC timeout'));
        }, 5000);
    });
}

// Update preview display
function updatePreview() {
    const presence = createPresenceData();
    let previewHTML = `
        <strong>${presence.name}</strong><br>
        ${presence.details ? `Details: ${presence.details}<br>` : ''}
        ${presence.state ? `State: ${presence.state}<br>` : ''}
    `;
    
    if (presence.timestamps.start) {
        previewHTML += `Started: ${formatTime(presence.timestamps.start)}<br>`;
    } else if (presence.timestamps.end) {
        previewHTML += `Ends: ${formatTime(presence.timestamps.end)} (${Math.round((presence.timestamps.end - Math.floor(Date.now() / 1000)) / 60)}min)<br>`;
    }
    
    elements.previewContent.innerHTML = previewHTML;
}

// Format timestamp
function formatTime(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Show/hide controls
function showControls() {
    elements.authSection.classList.add('hidden');
    elements.controlsSection.classList.remove('hidden');
    
    // Load sample data
    elements.activityName.value = 'Custom Activity';
    elements.details.value = 'Setting up presence...';
    elements.state.value = 'via Presence Manager';
    
    updatePreview();
}

// Show status message
function showStatus(message, type) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status ${type}`;
    elements.statusMessage.classList.remove('hidden');
    
    setTimeout(() => {
        elements.statusMessage.classList.add('hidden');
    }, 5000);
}

// Clear stored tokens
function clearTokens() {
    localStorage.removeItem('discord_access_token');
    localStorage.removeItem('discord_refresh_token');
    localStorage.removeItem('discord_token_expiry');
    accessToken = null;
    refreshToken = null;
}

// Logout function (optional)
function logout() {
    clearTokens();
    elements.authSection.classList.remove('hidden');
    elements.controlsSection.classList.add('hidden');
    showStatus('Logged out successfully', 'success');
}