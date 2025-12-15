// Discord Activity Manager using Embedded App SDK
const { DiscordSDK } = window.DiscordSDK;

// Initialize the Discord SDK with your Application ID
const discordSdk = new DiscordSDK('1450008731692568729'); // Your Client ID

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

// Store the current activity data
let currentActivity = null;

// Initialize the SDK when the page loads
async function setupDiscordSdk() {
    console.log('🔄 Initializing Discord Embedded App SDK...');
    showStatus('Connecting to Discord...', 'info');

    try {
        // Wait for the SDK to be ready (this happens when Discord loads your app in an iframe)
        await discordSdk.ready();
        
        console.log('✅ Discord SDK is ready!');
        console.log('   Guild ID:', discordSdk.guildId);
        console.log('   Channel ID:', discordSdk.channelId);
        
        // Authorize with the necessary scopes for the Activity
        // For SET_ACTIVITY, you typically need 'identify' and 'rpc.activities.write'
        const auth = await discordSdk.commands.authorize({
            client_id: '1450008731692568729',
            response_type: 'code',
            state: '',
            prompt: 'none',
            scope: [
                'identify',
                'rpc.activities.write'
            ],
        });

        console.log('✅ Authorized with Discord');
        showStatus('Connected to Discord!', 'success');
        
        // Show the controls since we're connected
        showControls();
        
        // You can also fetch the user's info if needed
        // const user = await discordSdk.commands.getUser();
        // console.log('User:', user);

    } catch (error) {
        console.error('❌ Failed to initialize Discord SDK:', error);
        
        // This error is EXPECTED if you're NOT running inside Discord as an Activity
        // It means you're viewing the page directly in a browser
        showStatus('⚠️ Run this as a Discord Activity to connect. Launch it from Discord\'s App Launcher.', 'error');
        
        // For demo purposes, we'll still show controls but indicate it's offline
        showControls();
        showStatus('Running in demo mode (not connected to Discord).', 'info');
    }
}

// Update the user's Rich Presence (Activity)
async function updatePresence() {
    console.log('🎮 Updating Rich Presence...');
    
    const presenceData = createPresenceData();
    currentActivity = presenceData; // Store it
    
    try {
        // This is the CORRECT way to set Activity in an Embedded App
        await discordSdk.commands.setActivity(presenceData);
        
        console.log('✅ Rich Presence updated successfully!');
        showStatus('✅ Activity updated! Others can now see your status.', 'success');
        
        updatePreview();
        elements.presencePreview.classList.remove('hidden');
        
    } catch (error) {
        console.error('❌ Failed to update activity:', error);
        
        // Provide helpful error messages
        if (error.message?.includes('not authenticated')) {
            showStatus('Not connected to Discord. Launch as an Activity first.', 'error');
        } else if (error.message?.includes('SET_ACTIVITY')) {
            showStatus('Missing SET_ACTIVITY permission. Check your app settings.', 'error');
        } else {
            showStatus(`Error: ${error.message || 'Unknown error'}`, 'error');
        }
    }
}

// Clear the current Activity
async function clearPresence() {
    console.log('🗑️ Clearing Rich Presence...');
    
    try {
        // Pass null to clear the activity
        await discordSdk.commands.setActivity(null);
        
        currentActivity = null;
        console.log('✅ Activity cleared');
        showStatus('✅ Activity cleared', 'success');
        
        elements.presencePreview.classList.add('hidden');
        
        // Clear form inputs
        elements.details.value = '';
        elements.state.value = '';
        elements.timestampType.value = 'none';
        
    } catch (error) {
        console.error('Failed to clear activity:', error);
        showStatus(`Error: ${error.message}`, 'error');
    }
}

// Create presence data from form
function createPresenceData() {
    const activityName = elements.activityName.value || 'Custom Activity';
    const details = elements.details.value || undefined;
    const state = elements.state.value || undefined;
    
    // Build the Activity object according to Discord's spec
    const activity = {
        name: activityName,
        type: 0, // 0 = Playing, 1 = Streaming, 2 = Listening, 3 = Watching, 4 = Custom
        details: details,
        state: state,
        timestamps: {},
        assets: {
            large_image: 'default_large',
            large_text: activityName,
            small_image: undefined,
            small_text: undefined
        },
        buttons: [
            {
                label: 'Set via Activity',
                url: 'https://discordactivity.netlify.app'
            }
        ]
    };
    
    // Add timestamps if selected
    const timestampType = elements.timestampType.value;
    const now = Math.floor(Date.now() / 1000);
    
    if (timestampType === 'start') {
        activity.timestamps = { start: now };
    } else if (timestampType === 'end') {
        const countdown = parseInt(elements.countdown.value) || 60;
        activity.timestamps = { end: now + (countdown * 60) };
    }
    
    return activity;
}

// UI Functions
function showControls() {
    console.log('Showing controls');
    elements.authSection.classList.add('hidden');
    elements.controlsSection.classList.remove('hidden');
    
    // Set default values
    if (!elements.activityName.value) {
        elements.activityName.value = 'Custom Activity';
    }
    
    updatePreview();
}

function showStatus(message, type) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status ${type}`;
    elements.statusMessage.classList.remove('hidden');
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            elements.statusMessage.classList.add('hidden');
        }, 5000);
    }
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

// Setup event listeners
function setupEventListeners() {
    // Remove old OAuth login listener
    if (elements.loginBtn) {
        elements.loginBtn.remove();
    }
    
    // Update presence button
    if (elements.updateBtn) {
        elements.updateBtn.addEventListener('click', updatePresence);
    }
    
    // Clear presence button
    if (elements.clearBtn) {
        elements.clearBtn.addEventListener('click', clearPresence);
    }
    
    // Logout button (just hides controls in this context)
    if (elements.logoutBtn) {
        elements.logoutBtn.addEventListener('click', () => {
            elements.authSection.classList.remove('hidden');
            elements.controlsSection.classList.add('hidden');
            showStatus('Disconnected', 'info');
        });
    }
    
    // Real-time preview updates
    ['activityName', 'details', 'state', 'countdown'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', updatePreview);
        }
    });
    
    // Timestamp type change
    if (elements.timestampType) {
        elements.timestampType.addEventListener('change', () => {
            if (elements.countdownGroup) {
                elements.countdownGroup.classList.toggle('hidden', 
                    elements.timestampType.value !== 'end');
            }
            updatePreview();
        });
    }
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 Discord Presence Manager loaded');
    
    // Setup the Discord SDK connection
    setupDiscordSdk();
    
    // Setup all UI event listeners
    setupEventListeners();
    
    // Initial preview update
    updatePreview();
});

// Debug helper function
window.debugActivity = function() {
    console.log('=== DEBUG INFO ===');
    console.log('Current Activity:', currentActivity);
    console.log('SDK Ready State:', discordSdk?._ready || 'Not initialized');
    console.log('Form Data:', {
        name: elements.activityName.value,
        details: elements.details.value,
        state: elements.state.value
    });
    console.log('==================');
};
