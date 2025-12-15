// Discord Activity - Rich Presence Manager
// Using Discord Embedded App SDK for Activities

// Discord SDK instance
let discordSdk = null;
let isDiscordActivity = false;

// DOM Elements
const elements = {
    // Status
    statusDot: document.getElementById('status-dot'),
    statusText: document.getElementById('status-text'),
    statusMessage: document.getElementById('status-message'),
    
    // Form inputs
    activityName: document.getElementById('activity-name'),
    details: document.getElementById('details'),
    state: document.getElementById('state'),
    timestampType: document.getElementById('timestamp-type'),
    countdownGroup: document.getElementById('countdown-group'),
    countdown: document.getElementById('countdown'),
    
    // Buttons
    updateBtn: document.getElementById('update-btn'),
    clearBtn: document.getElementById('clear-btn'),
    
    // Preview
    previewContent: document.getElementById('preview-content'),
    previewName: document.getElementById('preview-name'),
    previewDetails: document.getElementById('preview-details'),
    previewState: document.getElementById('preview-state'),
    previewTimer: document.getElementById('preview-timer')
};

// Initialize the Activity
async function init() {
    console.log('🚀 Initializing Discord Activity...');
    
    // Check if we're running inside Discord
    isDiscordActivity = detectDiscordEnvironment();
    
    if (isDiscordActivity) {
        await initDiscordSdk();
    } else {
        showStandaloneMode();
    }
    
    setupEventListeners();
    updatePreview();
}

// Detect if running inside Discord
function detectDiscordEnvironment() {
    // Check if we're in an iframe (Discord loads Activities in iframes)
    if (window.self !== window.top) {
        return true;
    }
    
    // Check for Discord-specific user agent
    if (navigator.userAgent.includes('Discord')) {
        return true;
    }
    
    // Check URL for Discord's activity domain
    if (window.location.href.includes('discord.com/activity')) {
        return true;
    }
    
    return false;
}

// Initialize Discord SDK when running as Activity
async function initDiscordSdk() {
    try {
        updateConnectionStatus('Connecting to Discord...', 'connecting');
        
        // Create Discord SDK instance with your Client ID
        const { DiscordSDK } = window.DiscordSDK;
        discordSdk = new DiscordSDK('1450008731692568729');
        
        // Wait for SDK to be ready
        await discordSdk.ready();
        console.log('✅ Discord SDK is ready');
        
        // Get context info
        const guildId = discordSdk.guildId;
        const channelId = discordSdk.channelId;
        console.log(`📱 Running in: Guild ${guildId}, Channel ${channelId}`);
        
        // Authorize with required scopes
        const auth = await discordSdk.commands.authorize({
            client_id: '1450008731692568729',
            response_type: 'code',
            state: '',
            prompt: 'none',
            scope: ['identify', 'rpc.activities.write'],
        });
        
        console.log('🔑 Authorized successfully');
        updateConnectionStatus('Connected to Discord', 'connected');
        
        // Subscribe to SDK events
        setupSdkEvents();
        
    } catch (error) {
        console.error('❌ Discord SDK initialization failed:', error);
        updateConnectionStatus('Failed to connect', 'error');
        showStatusMessage('This app needs to run as a Discord Activity. Launch it from Discord\'s App Launcher.', 'error');
        showStandaloneMode();
    }
}

// Setup Discord SDK event listeners
function setupSdkEvents() {
    if (!discordSdk) return;
    
    // Listen for voice state updates
    discordSdk.subscribe('VOICE_STATE_UPDATE', (data) => {
        console.log('Voice state update:', data);
    });
    
    // Listen for user updates
    discordSdk.subscribe('CURRENT_USER_UPDATE', (data) => {
        console.log('User updated:', data);
    });
}

// Update Discord Rich Presence
async function updatePresence() {
    const activityData = createActivityData();
    
    if (isDiscordActivity && discordSdk) {
        try {
            console.log('🎮 Setting Discord Activity:', activityData);
            
            // Use Discord SDK to update presence
            await discordSdk.commands.setActivity(activityData);
            
            showStatusMessage('✅ Rich Presence updated! Your friends can now see your activity.', 'success');
            updatePreview();
            
        } catch (error) {
            console.error('❌ Failed to update activity:', error);
            
            if (error.message?.includes('permission')) {
                showStatusMessage('Missing permissions. Make sure your app has Activities enabled.', 'error');
            } else if (error.message?.includes('not authenticated')) {
                showStatusMessage('Not authenticated. Please relaunch the Activity.', 'error');
            } else {
                showStatusMessage(`Error: ${error.message || 'Unknown error'}`, 'error');
            }
        }
    } else {
        // Not in Discord - show instructions
        showStatusMessage('⚠️ Launch this as a Discord Activity to update your status.', 'info');
        updatePreview();
    }
}

// Clear Discord Presence
async function clearPresence() {
    if (isDiscordActivity && discordSdk) {
        try {
            await discordSdk.commands.setActivity(null);
            showStatusMessage('✅ Status cleared', 'success');
            
            // Reset form
            elements.details.value = '';
            elements.state.value = '';
            
        } catch (error) {
            showStatusMessage(`Error clearing: ${error.message}`, 'error');
        }
    } else {
        showStatusMessage('Not connected to Discord', 'info');
    }
    
    updatePreview();
}

// Create activity data from form
function createActivityData() {
    const activityName = elements.activityName.value || 'Custom Activity';
    const details = elements.details.value?.trim();
    const state = elements.state.value?.trim();
    
    // Build Discord Activity object
    const activity = {
        name: activityName,
        type: 0, // 0 = Playing, 1 = Streaming, 2 = Listening, 3 = Watching, 4 = Custom
        details: details || undefined,
        state: state || undefined,
        timestamps: {},
        assets: {
            large_image: 'default_large',
            large_text: activityName,
            small_image: undefined,
            small_text: undefined
        },
        buttons: [
            {
                label: 'Rich Presence Manager',
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
        const minutes = parseInt(elements.countdown.value) || 60;
        activity.timestamps = { end: now + (minutes * 60) };
    }
    
    return activity;
}

// Update the preview display
function updatePreview() {
    const activity = createActivityData();
    
    // Update preview name
    elements.previewName.textContent = activity.name;
    
    // Update details preview
    if (activity.details) {
        elements.previewDetails.classList.remove('hidden');
        elements.previewDetails.querySelector('span:last-child').textContent = activity.details;
    } else {
        elements.previewDetails.classList.add('hidden');
    }
    
    // Update state preview
    if (activity.state) {
        elements.previewState.classList.remove('hidden');
        elements.previewState.querySelector('span:last-child').textContent = activity.state;
    } else {
        elements.previewState.classList.add('hidden');
    }
    
    // Update timer preview
    if (activity.timestamps.start) {
        elements.previewTimer.classList.remove('hidden');
        elements.previewTimer.querySelector('span:last-child').textContent = 'Started now';
    } else if (activity.timestamps.end) {
        const minutes = Math.round((activity.timestamps.end - Math.floor(Date.now() / 1000)) / 60);
        elements.previewTimer.classList.remove('hidden');
        elements.previewTimer.querySelector('span:last-child').textContent = `${minutes} minutes remaining`;
    } else {
        elements.previewTimer.classList.add('hidden');
    }
}

// Show standalone mode (when not running in Discord)
function showStandaloneMode() {
    updateConnectionStatus('Standalone Mode', 'connected');
    showStatusMessage('To use this app: 1) Open Discord → 2) Find "Rich Presence Manager" in Activities → 3) Launch it', 'info');
}

// Update connection status UI
function updateConnectionStatus(text, status) {
    elements.statusText.textContent = text;
    elements.statusDot.className = 'status-dot';
    
    switch (status) {
        case 'connected':
            elements.statusDot.classList.add('connected');
            break;
        case 'error':
            elements.statusDot.style.background = '#ed4245';
            break;
        case 'connecting':
            // Keep pulsing animation
            break;
    }
}

// Show status message
function showStatusMessage(message, type) {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status-message ${type}`;
    
    // Auto-hide success messages
    if (type === 'success') {
        setTimeout(() => {
            elements.statusMessage.className = 'status-message';
        }, 5000);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Update button
    elements.updateBtn.addEventListener('click', updatePresence);
    
    // Clear button
    elements.clearBtn.addEventListener('click', clearPresence);
    
    // Timestamp type change
    elements.timestampType.addEventListener('change', function() {
        elements.countdownGroup.classList.toggle('hidden', this.value !== 'end');
        updatePreview();
    });
    
    // Real-time preview updates
    const previewInputs = ['activity-name', 'details', 'state', 'countdown'];
    previewInputs.forEach(id => {
        document.getElementById(id).addEventListener('input', updatePreview);
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            updatePresence();
        }
    });
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', init);

// Export functions for debugging
window.debugActivity = {
    getActivityData: createActivityData,
    checkDiscordConnection: () => ({
        isDiscordActivity,
        sdkReady: !!discordSdk?._ready,
        guildId: discordSdk?.guildId,
        channelId: discordSdk?.channelId
    }),
    testUpdate: updatePresence,
    testClear: clearPresence
};
