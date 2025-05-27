// Global state
let gameState = {
    lobbyPlayers: [],
    teams: [],
    legendBanStatus: {},
    connectionStatus: 'disconnected'
};

// Initialize application
document.addEventListener("DOMContentLoaded", function() {
    showNotification('Dashboard loaded successfully');
    
    // Initialize status check
    checkSystemStatus();
    checkPubSubStatus(); // Add this line
    
    // Set up periodic status checking
    setInterval(checkSystemStatus, 5000); // Check every 5 seconds
    setInterval(checkPubSubStatus, 5000); // Check Pub/Sub status every 5 seconds // Add this line
    
    // Set up form enhancements
    setupPlayerAutoComplete();
    setupFormEventListeners();
    
    // Auto-load lobby data if available
    setTimeout(() => {
        refreshLobbyData().catch(() => {
            console.log('Lobby data not available on startup');
        });
    }, 1000);
    
    // Set up contextual help
    updateContextualFormStates();
    
    // Add smart form interactions
    setupSmartFormInteractions();
});

// Setup form event listeners
function setupFormEventListeners() {
    // Settings form
    const setSettingsForm = safeGetElement("setSettingsForm");
    if (setSettingsForm) {
        setSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const settingsValue = safeGetValue("settings"); // Get value outside try block
            try {
                if (!settingsValue) {
                    showNotification('Settings field is empty', 'error');
                    console.warn('Settings JSON field was empty.'); // Log warning
                    return;
                }
                
                console.log("Attempting to parse settings JSON:", settingsValue); // Log the value being parsed
                let formData = JSON.parse(settingsValue);
                
                // Include player targeting if specified
                const playerName = safeGetValue("settingsPlayerName");
                const nucleusHash = safeGetValue("settingsNucleusHash");
                
                if (playerName) formData.targetPlayerName = playerName;
                if (nucleusHash) formData.targetNucleusHash = nucleusHash;
                
                submitForm('/set_settings', formData, e.submitter);
            } catch (error) {
                showNotification('Invalid JSON format in settings', 'error');
                // Enhanced error logging
                console.error('Settings JSON parse error:', error.message); 
                console.error('Value that failed to parse:', settingsValue);
                if (error.stack) {
                    console.error('Error stack:', error.stack);
                }
                // Optionally, display the raw value in the notification or a modal for the user to inspect
                // For example: showNotification(`Invalid JSON: ${error.message}. Value: ${settingsValue.substring(0,100)}...`, 'error');
            }
        });
    }

    // Team form
    const setTeamForm = safeGetElement("setTeamForm");
    if (setTeamForm) {
        setTeamForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = {
                teamId: safeGetValue("teamId"),
                targetHardwareName: safeGetValue("targetHardwareName"),
                targetNucleusHash: safeGetValue("targetNucleusHash")
            };
            submitForm('/set_team', formData, e.submitter);
        });
    }

    // Kick player form
    const kickPlayerForm = safeGetElement("kickPlayerForm");
    if (kickPlayerForm) {
        kickPlayerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = {
                targetHardwareName: safeGetValue("kickTargetHardwareName"),
                targetNucleusHash: safeGetValue("kickTargetNucleusHash")
            };
            submitForm('/kick_player', formData, e.submitter);
        });
    }

    // Chat form
    const sendChatForm = safeGetElement("sendChatForm");
    if (sendChatForm) {
        sendChatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = { text: safeGetValue("chatText") };
            submitForm('/send_chat', formData, e.submitter);
        });
    }

    // Matchmaking form
    const setMatchmakingForm = safeGetElement("setMatchmakingForm");
    if (setMatchmakingForm) {
        setMatchmakingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const enabledEl = safeGetElement("enabled");
            const formData = { enabled: enabledEl ? enabledEl.checked : false };
            submitForm('/set_matchmaking', formData, e.submitter);
        });
    }

    // Camera forms
    const changeCameraForm = document.getElementById("changeCameraForm");
    if (changeCameraForm) {
        changeCameraForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = { poi: document.getElementById("poi").value };
            submitForm('/change_camera', formData, e.submitter);
        });
    }

    const setCameraPositionForm = document.getElementById("setCameraPositionForm");
    if (setCameraPositionForm) {
        setCameraPositionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = {
                x: parseFloat(document.getElementById("x").value) || 0,
                y: parseFloat(document.getElementById("y").value) || 0,
                z: parseFloat(document.getElementById("z").value) || 0
            };
            submitForm('/set_camera_position', formData, e.submitter);
        });
    }

    // Legend ban form
    const setLegendBanForm = document.getElementById("setLegendBanForm");
    if (setLegendBanForm) {
        setLegendBanForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const checkedLegends = Array.from(document.querySelectorAll('#legendSelectionGrid input[type="checkbox"]:checked'))
                .map(checkbox => checkbox.value);
            
            const formData = { legend_references: checkedLegends };
            submitForm('/set_legend_ban', formData, e.submitter);
        });
    }
}

// System status functions
function checkSystemStatus() {
    fetch('/health-check')
        .then(response => response.json())
        .then(data => {
            updateStatusIndicator(data);
            gameState.connectionStatus = data.websocket?.connected ? 'connected' : 'disconnected';
        })
        .catch(error => {
            console.error('Error checking status:', error);
            updateStatusIndicator({ status: 'error', websocket: { connected: false }, redis: { connected: false }, game_data: { available: false } });
            gameState.connectionStatus = 'error';
        });
}

function updateStatusIndicator(status) {
    let statusElement = document.getElementById('statusIndicator');
    if (!statusElement) {
        statusElement = document.createElement('div');
        statusElement.id = 'statusIndicator';
        statusElement.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 20px;
            color: white;
            font-weight: 500;
            font-size: 0.9rem;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
        `;
        document.body.appendChild(statusElement);
    }
    
    const wsConnected = status.websocket?.connected || false;
    const redisConnected = status.redis?.connected || false;
    const gameDataAvailable = status.game_data?.available || false;
    const connectionCount = status.websocket?.connections || 0;
    
    let pubSubStatusElement = document.getElementById('pubSubStatusIndicator');
    if (!pubSubStatusElement) {
        pubSubStatusElement = document.createElement('div');
        pubSubStatusElement.id = 'pubSubStatusIndicator';
        pubSubStatusElement.style.cssText = `
            position: fixed;
            top: 60px; /* Adjust based on your layout */
            right: 20px;
            padding: 10px 15px;
            border-radius: 20px;
            color: white;
            font-weight: 500;
            font-size: 0.9rem;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
        `;
        // Prepend to allow original status indicator to be on top if preferred, or adjust top/right positioning
        document.body.insertBefore(pubSubStatusElement, statusElement.nextSibling); 
    }

    let statusText = '';
    let statusColor = '';
    
    if (status.status === 'error') {
        statusText = 'Apex Websocket link'; // Changed from 'System Error'
        statusColor = '#e53e3e';
    } else if (wsConnected && redisConnected && gameDataAvailable) {
        statusText = `🟢 Connected (${connectionCount} client${connectionCount !== 1 ? 's' : ''})`;
        statusColor = '#38a169';
    } else if (wsConnected && redisConnected) {
        statusText = `🟡 Ready - No Game Data (${connectionCount} client${connectionCount !== 1 ? 's' : ''})`;
        statusColor = '#d69e2e';
    } else if (redisConnected) {
        statusText = '🔴 WebSocket Disconnected';
        statusColor = '#e53e3e';
    } else {
        statusText = '🔴 System Offline';
        statusColor = '#e53e3e';
    }
    
    statusElement.style.backgroundColor = statusColor;
    statusElement.innerHTML = statusText;
    
    if (gameDataAvailable && !statusElement.dataset.autocompleteLoaded) {
        loadAutocompleteData();
        statusElement.dataset.autocompleteLoaded = 'true';
    }
    
    if (!gameDataAvailable) {
        statusElement.dataset.autocompleteLoaded = 'false';
    }
}

// Add this new function
function checkPubSubStatus() {
    fetch('/pubsub-status')
        .then(response => {
            if (!response.ok) {
                // Attempt to get text for more detailed error, then throw
                return response.text().then(text => {
                    throw new Error(`Pub/Sub status endpoint error ${response.status}: ${text || 'No error details'}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // data is the backend JSON: {streaming, last_publish, seconds_since_last, total_messages, errors}
            updatePubSubStatusIndicator(data);
        })
        .catch(error => {
            console.error('Error checking Pub/Sub status:', error);
            // Pass a specific structure for fetch/network errors or errors from response.ok check
            updatePubSubStatusIndicator({ client_error: error.message || 'Failed to fetch status from backend' });
        });
}

// Add this new function
function updatePubSubStatusIndicator(statusData) {
    const pubSubStatusElement = document.getElementById('pubSubStatusIndicator');
    if (!pubSubStatusElement) return;

    let statusText = '';
    let statusColor = '';
    let titleHint = ''; // For a tooltip

    if (statusData.client_error) { // Check for client-side fetch/network error or non-ok HTTP response
        statusText = '🔴 Pub/Sub Status Unavailable';
        statusColor = '#e53e3e'; // Red
        titleHint = `Error fetching status: ${statusData.client_error}`;
    } else {
        // Backend data is expected: {streaming, last_publish, seconds_since_last, total_messages, errors}
        const isStreaming = statusData.streaming;
        const lastPublish = statusData.last_publish;
        const totalMessages = statusData.total_messages;
        const publishErrors = statusData.errors; // Backend publishing errors
        const secondsSinceLast = statusData.seconds_since_last;

        let lastPublishStr = 'N/A';
        if (lastPublish) {
            try {
                lastPublishStr = new Date(lastPublish).toLocaleString();
            } catch (e) {
                console.warn("Error parsing last_publish date:", lastPublish, e);
                lastPublishStr = 'Invalid Date';
            }
        }

        if (publishErrors > 0) {
            statusText = `🟠 Pub/Sub: ${publishErrors} Error${publishErrors !== 1 ? 's' : ''}`;
            statusColor = '#dd6b20'; // Darker Orange (Tailwind orange-600)
            titleHint = `Total successful publishes: ${totalMessages}. Last successful publish: ${lastPublishStr}.`;
            if (isStreaming) {
                 titleHint += ` Still considered streaming (message in last 30s).`;
            } else if (lastPublish) {
                 titleHint += ` Not streaming (last successful message ${secondsSinceLast}s ago).`;
            }
        } else if (isStreaming) {
            statusText = '🟢 Pub/Sub Streaming';
            statusColor = '#38a169'; // Green (Tailwind green-600)
            titleHint = `Last publish: ${lastPublishStr}. Total messages: ${totalMessages}.`;
        } else { // Not streaming, no backend publish errors
            if (lastPublish) { // Successfully published in the past, but not recently
                statusText = `🟡 Pub/Sub Idle (Last: ${secondsSinceLast}s ago)`;
                statusColor = '#d69e2e'; // Yellow (Tailwind yellow-600)
                titleHint = `Last publish: ${lastPublishStr}. Total messages: ${totalMessages}.`;
            } else { // Never successfully published
                statusText = '⚪ Pub/Sub Idle (Never Published)';
                statusColor = '#a0aec0'; // Gray (Tailwind gray-500)
                titleHint = `No messages published yet. Total messages: ${totalMessages} (likely 0). Errors: ${publishErrors}.`;
            }
        }
    }

    pubSubStatusElement.style.backgroundColor = statusColor;
    pubSubStatusElement.innerHTML = statusText;
    pubSubStatusElement.title = titleHint; // Add a tooltip for more details
}

// Notification system
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 60px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1001;
        animation: slideIn 0.3s ease;
        max-width: 300px;
        background: ${type === 'error' ? '#e53e3e' : type === 'warning' ? '#d69e2e' : '#38a169'};
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Form submission helper with improved error handling
function submitForm(endpoint, formData, button) {
    let originalContent = null;
    
    if (button) {
        originalContent = button.innerHTML;
        button.innerHTML = '<span class="loading"></span> Sending...';
        button.disabled = true;
    }

    fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response headers:', response.headers);
        return response.text(); // Get as text first to debug
    })    .then(responseText => {
        console.log('Raw response:', responseText);
        
        // Try to parse JSON using robust parser
        let data;
        try {
            data = parseRobustJSON(responseText, 'form submission');
        } catch (parseError) {
            console.error('JSON Parse Error:', parseError);
            console.error('Failed to parse response:', responseText);
            
            // Create a fallback response
            data = {
                success: false,
                message: `Server response error: ${parseError.message}`,
                raw_response: responseText.substring(0, 200) + (responseText.length > 200 ? '...' : '')
            };
        }
        
        updateResponsePanel(data);
        
        if (data.success) {
            showNotification(data.message || 'Action completed successfully');
        } else {
            showNotification(data.message || 'Action failed', 'error');
        }
    })
    .catch(error => {
        console.error('Network Error:', error);
        showNotification('Network error occurred', 'error');
        updateResponsePanel({ error: error.message });
    })
    .finally(() => {
        if (button) {
            button.innerHTML = originalContent;
            button.disabled = false;
        }
    });
}

// Quick action request function for simple endpoints
function sendRequest(endpoint, method = 'POST', data = {}) {
    console.log(`sendRequest called with:`, { endpoint, method, data });
    console.log(`Method parameter type:`, typeof method);
    console.log(`Method parameter value:`, method);
    
    const requestOptions = {
        method: method,
        headers: { 'Content-Type': 'application/json' }
    };
    
    console.log(`Request options before fetch:`, requestOptions);
    
    if (method !== 'GET' && Object.keys(data).length > 0) {
        requestOptions.body = JSON.stringify(data);
        console.log(`Added body to request:`, requestOptions.body);
    }
    
    console.log(`Final request options:`, requestOptions);
    
    fetch(endpoint, requestOptions)
        .then(response => {
            console.log(`${endpoint} response status:`, response.status);
            console.log(`${endpoint} response headers:`, [...response.headers.entries()]);
            
            // Handle non-200 status codes
            if (!response.ok) {
                return response.text().then(errorText => {
                    console.error(`${endpoint} error response:`, errorText);
                    throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
                });
            }
            
            return response.text();
        })
        .then(responseText => {
            console.log(`${endpoint} raw response:`, responseText);
            
            // Handle empty responses
            if (!responseText || responseText.trim() === '') {
                showNotification(`${endpoint} completed (empty response)`, 'warning');
                updateResponsePanel({ message: 'Empty response received', endpoint: endpoint });
                return;
            }
            
            try {
                const data = parseRobustJSON(responseText, `${endpoint} response`);
                updateResponsePanel(data);
                
                if (data.success !== false) {
                    showNotification(data.message || `${endpoint} completed successfully`);
                    
                    // Auto-refresh lobby data after certain actions
                    if (endpoint === '/create_lobby' || endpoint === '/schedule_autostart') {
                        setTimeout(() => {
                            refreshLobbyData().catch(error => {
                                console.log('Auto-refresh failed after action:', error);
                            });
                        }, 1000);
                    }
                } else {
                    showNotification(data.message || `${endpoint} failed`, 'error');
                }
            } catch (error) {
                console.error(`Error parsing ${endpoint} response:`, error);
                showNotification(`${endpoint} completed (response format issue)`, 'warning');
                updateResponsePanel({ 
                    raw_response: responseText,
                    parse_error: error.message,
                    endpoint: endpoint 
                });
            }
        })
        .catch(error => {
            console.error(`Error for ${endpoint}:`, error);
            showNotification(`Error: ${error.message}`, 'error');
            updateResponsePanel({ 
                error: error.message,
                endpoint: endpoint,
                method: method,
                timestamp: new Date().toISOString()
            });
        });
}

// Quick action functions for specific endpoints
function enableMatchmaking() {
    sendRequest('/set_matchmaking', 'POST', { enabled: true });
}

function scheduleAutostart() {
    // You can customize the autostart parameters here
    const autostartData = {
        // Add any required parameters for schedule_autostart
        // Check the API documentation for required fields
    };
    sendRequest('/schedule_autostart', 'POST', autostartData);
}

// Settings functions
function getCurrentSettings() {
    const button = event?.target;
    if (!button) {
        console.error('getCurrentSettings called without proper event context');
        return;
    }
    
    const originalContent = button.innerHTML;
    button.innerHTML = '<span class="loading"></span> Loading...';
    button.disabled = true;    fetch('/get_settings')
        .then(response => {
            console.log('Settings response status:', response.status);
            return response.text();
        })
        .then(responseText => {
            console.log('Settings raw response:', responseText);
            
            let data;
            try {
                const cleanedResponse = responseText.trim();
                if (cleanedResponse.includes('}{')) {
                    const jsonParts = cleanedResponse.split('}{');
                    const lastPart = jsonParts[jsonParts.length - 1];
                    const jsonToParse = lastPart.startsWith('{') ? lastPart : '{' + lastPart;
                    data = JSON.parse(jsonToParse);
                } else {
                    data = JSON.parse(cleanedResponse);
                }
            } catch (parseError) {
                console.error('Settings JSON Parse Error:', parseError);
                data = { settings: null, error: parseError.message };
            }
            
            console.log('Settings response received:', data);
            const display = safeGetElement('currentSettingsDisplay');
            if (display) {
                if (data.settings) {
                    display.innerHTML = `<pre style="margin: 0; white-space: pre-wrap;">${JSON.stringify(data.settings, null, 2)}</pre>`;
                    showNotification('Current settings loaded');
                } else {
                    display.innerHTML = '<div style="color: #666;">No settings data available</div>';
                    showNotification('No settings data available', 'warning');
                }
            }
        })
        .catch(error => {
            console.error('Error loading settings:', error);
            showNotification('Failed to load settings', 'error');
            const display = safeGetElement('currentSettingsDisplay');
            if (display) {
                display.innerHTML = '<div style="color: #e53e3e;">Error loading settings</div>';
            }
        })
        .finally(() => {
            if (button) {
                button.innerHTML = originalContent;
                button.disabled = false;
            }
        });
}

function loadCurrentSettings() {
    const button = document.querySelector('#loadSettingsBtn');
    if (button) {
        const originalContent = button.innerHTML;
        button.innerHTML = '<span class="loading"></span> Loading...';
        button.disabled = true;
    }

    fetch('/get_settings')
        .then(response => response.json())
        .then(data => {
            if (data.settings) {
                const settingsTextarea = document.getElementById('settings');
                if (settingsTextarea) {
                    settingsTextarea.value = JSON.stringify(data.settings, null, 2);
                }
                showNotification('Current settings loaded');
            } else {
                showNotification('No settings data available', 'error');
            }
        })
        .catch(error => {
            console.error('Error loading settings:', error);
            showNotification('Failed to load settings', 'error');
        })
        .finally(() => {
            if (button) {
                button.innerHTML = originalContent;
                button.disabled = false;
            }
        });
}

function populateSettingsFromForm() {
    const settings = {};
    
    // Get playlist
    const playlist = safeGetValue('playlistName');
    if (playlist) settings.playlistName = playlist;
    
    // Get boolean settings
    const adminChatEl = safeGetElement('adminChat');
    const teamRenameEl = safeGetElement('teamRename');
    const selfAssignEl = safeGetElement('selfAssign');
    const aimAssistEl = safeGetElement('aimAssist');
    const anonModeEl = safeGetElement('anonMode');
    
    if (adminChatEl?.checked) settings.adminChat = true;
    if (teamRenameEl?.checked) settings.teamRename = true;
    if (selfAssignEl?.checked) settings.selfAssign = true;
    if (aimAssistEl?.checked) settings.aimAssist = true;
    if (anonModeEl?.checked) settings.anonMode = true;
    
    // Get target player settings
    const playerName = safeGetValue('settingsPlayerName');
    const nucleusHash = safeGetValue('settingsNucleusHash');
    
    if (playerName) settings.targetPlayerName = playerName;
    if (nucleusHash) settings.targetNucleusHash = nucleusHash;
    
    // Add other common settings
    settings.maxTeams = 20;
    settings.maxPlayersPerTeam = 3;
    
    const settingsTextarea = safeGetElement('settings');
    if (settingsTextarea) {
        settingsTextarea.value = JSON.stringify(settings, null, 2);
        showNotification('JSON generated from form including player selections');
    } else {
        showNotification('Settings textarea not found', 'error');
    }
}

// Autocomplete data functions
function loadAutocompleteData() {
    loadAutocompleteDataAdvanced();
}

function loadAutocompleteDataAdvanced() {
    const endpoints = [
        { url: '/get_player_names', target: 'playerNames', name: 'Player Names' },
        { url: '/get_hardware_names', target: 'hardwareNames', name: 'Hardware Names' },
        { url: '/get_hardware_names', target: 'kickHardwareNames', name: 'Kick Hardware Names' },
        { url: '/get_nucleus_hashes', target: 'nucleusHashes', name: 'Nucleus Hashes' },
        { url: '/get_nucleus_hashes', target: 'kickNucleusHashes', name: 'Kick Nucleus Hashes' }
    ];
    
    let completedRequests = 0;
    let successfulRequests = 0;
    
    endpoints.forEach(endpoint => {
        fetch(endpoint.url)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .then(data => {
                const dataList = document.getElementById(endpoint.target);
                if (dataList && Array.isArray(data)) {
                    dataList.innerHTML = '';
                    data.forEach(item => {
                        const option = document.createElement('option');
                        option.value = item;
                        dataList.appendChild(option);
                    });
                    successfulRequests++;
                }
            })
            .catch(error => {
                console.warn(`Failed to load ${endpoint.name}:`, error);
            })
            .finally(() => {
                completedRequests++;
                if (completedRequests === endpoints.length) {
                    if (successfulRequests > 0) {
                        showNotification(`Autocomplete data loaded (${successfulRequests}/${endpoints.length} sources)`);
                    } else {
                        showNotification('No autocomplete data available yet', 'error');
                    }
                }
            });
    });
}

// Player and lobby functions
function refreshLobbyData() {
    return fetch('/get_players')
        .then(response => {
            console.log('Lobby response status:', response.status);
            return response.text(); // Get as text first
        })
        .then(responseText => {
            console.log('Raw lobby response:', responseText);
            
            let data;
            try {
                data = parseRobustJSON(responseText, 'lobby data');
            } catch (parseError) {
                console.error('Lobby JSON Parse Error:', parseError);
                console.error('Failed response:', responseText);
                throw new Error(`JSON Parse Error: ${parseError.message}`);
            }
            
            updateLobbyDisplay(data);
            gameState.lobbyPlayers = data.players || [];
            gameState.teams = data.teams || [];
            populateTeamAssignmentOptions();
            showNotification(`Lobby updated - ${gameState.lobbyPlayers.length} players found`);
            return data;
        })
        .catch(error => {
            console.error('Error loading lobby data:', error);
            showNotification('Failed to load lobby data', 'error');
            throw error;
        });
}

function updateLobbyDisplay(data) {
    const display = document.getElementById('lobbyPlayersDisplay');
    if (!display) return;
    
    if (!data.players || data.players.length === 0) {
        display.innerHTML = '<div class="status-indicator">No players found in lobby</div>';
        return;
    }
    
    const playersByTeam = {};
    data.players.forEach(player => {
        const teamId = player.teamId || 0;
        if (!playersByTeam[teamId]) {
            playersByTeam[teamId] = [];
        }
        playersByTeam[teamId].push(player);
    });
    
    let html = '';
    Object.keys(playersByTeam).sort((a, b) => parseInt(a) - parseInt(b)).forEach(teamId => {
        const players = playersByTeam[teamId];
        const team = data.teams?.find(t => t.id === parseInt(teamId));
        const teamName = team?.name || (teamId === '0' ? 'Observers' : `Team ${teamId}`);
        
        html += `
            <div class="team-section">
                <h4>${teamName} (${players.length} player${players.length !== 1 ? 's' : ''})</h4>
                <div class="players-grid">
        `;
        
        players.forEach(player => {
            html += `
                <div class="player-card">
                    <strong>${player.name}</strong>
                    <small>Hardware: ${player.hardwareName || 'N/A'}</small>
                    <small>Hash: ${player.nucleusHash ? player.nucleusHash.substring(0, 8) + '...' : 'N/A'}</small>
                </div>
            `;
        });
        
        html += '</div></div>';
    });
    
    display.innerHTML = html;
}

// Legend ban functions
function loadLegendBanStatus() {
    const button = document.querySelector('#loadBanStatusBtn');
    if (button) {
        const originalContent = button.innerHTML;
        button.innerHTML = '<span class="loading"></span> Loading...';
        button.disabled = true;
    }

    fetch('/get_legend_ban_status')
        .then(response => response.json())
        .then(data => {
            updateLegendBanDisplay(data);
            showNotification('Legend ban status loaded');
        })
        .catch(error => {
            console.error('Error loading legend ban status:', error);
            showNotification('Failed to load legend ban status', 'error');
        })
        .finally(() => {
            if (button) {
                button.innerHTML = originalContent;
                button.disabled = false;
            }
        });
}

function updateLegendBanDisplay(banData) {
    const display = document.getElementById('legendBanStatusDisplay');
    const selectionGrid = document.getElementById('legendSelectionGrid');
    
    if (!display) return;
    
    console.log('Legend ban data received:', banData);
    
    let legends = [];
    if (banData && banData.legends) {
        legends = banData.legends;
    } else if (banData && Array.isArray(banData)) {
        legends = banData;
    } else if (typeof banData === 'string') {
        try {
            const parsed = JSON.parse(banData);
            legends = parsed.legends || [];
        } catch (e) {
            console.error('Failed to parse legend ban data:', e);
        }
    }
    
    if (legends && Array.isArray(legends) && legends.length > 0) {
        const bannedLegends = legends.filter(legend => legend.banned);
        if (bannedLegends.length === 0) {
            display.innerHTML = '<div class="status-indicator status-connected">✅ No legends are currently banned</div>';
        } else {
            const bannedList = bannedLegends.map(legend => 
                `<span class="ban-status banned">🚫 ${legend.name}</span>`
            ).join(' ');
            display.innerHTML = `<div style="margin-bottom: 10px;"><strong>Banned Legends (${bannedLegends.length}):</strong></div>${bannedList}`;
        }
        
        if (selectionGrid) {
            selectionGrid.innerHTML = '';
            legends.forEach(legend => {
                const legendDiv = document.createElement('div');
                legendDiv.className = `legend-card ${legend.banned ? 'banned' : 'available'}`;
                legendDiv.innerHTML = `
                    <div class="checkbox-group" style="margin: 0;">
                        <input type="checkbox" id="legend_${legend.reference}" value="${legend.reference}" ${legend.banned ? 'checked' : ''}>
                        <label for="legend_${legend.reference}" style="margin: 0; padding: 8px; display: block; cursor: pointer;">
                            <strong>${legend.name}</strong>
                            <br><small style="opacity: 0.7;">${legend.reference}</small>
                        </label>
                    </div>
                `;
                
                legendDiv.addEventListener('click', function(e) {
                    if (e.target.type !== 'checkbox') {
                        const checkbox = legendDiv.querySelector('input[type="checkbox"]');
                        checkbox.checked = !checkbox.checked;
                        legendDiv.className = `legend-card ${checkbox.checked ? 'banned' : 'available'}`;
                    }
                });
                
                legendDiv.querySelector('input[type="checkbox"]').addEventListener('change', function() {
                    legendDiv.className = `legend-card ${this.checked ? 'banned' : 'available'}`;
                });
                
                selectionGrid.appendChild(legendDiv);
            });
            
            const bulkActions = document.createElement('div');
            bulkActions.innerHTML = `
                <div style="grid-column: 1 / -1; padding-top: 15px; border-top: 1px solid #e2e8f0; margin-top: 15px;">
                    <button type="button" class="btn secondary" style="margin-right: 10px;" onclick="toggleAllLegends(false)">
                        <i class="fas fa-check"></i> Allow All
                    </button>
                    <button type="button" class="btn" style="background: #e53e3e;" onclick="toggleAllLegends(true)">
                        <i class="fas fa-ban"></i> Ban All
                    </button>
                </div>
            `;
            selectionGrid.appendChild(bulkActions);
        }
        
        gameState.legendBanStatus = banData;
    } else {
        display.innerHTML = '<div class="status-indicator">No legend ban data available. Try clicking "Load Ban Status" first.</div>';
        console.warn('No valid legend data found in:', banData);
    }
}

function toggleAllLegends(banned) {
    const checkboxes = document.querySelectorAll('#legendSelectionGrid input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = banned;
        const card = checkbox.closest('.legend-card');
        if (card) {
            card.className = `legend-card ${banned ? 'banned' : 'available'}`;
        }
    });
}

// Camera control functions
function changeToKillLeader() {
    const formData = { poi: "3" };
    submitForm('/change_camera', formData, null);
}

function changeToClosestEnemy() {
    const formData = { poi: "4" };
    submitForm('/change_camera', formData, null);
}

function changeToNextPlayer() {
    const formData = { poi: "1" };
    submitForm('/change_camera', formData, null);
}

function changeToPreviousPlayer() {
    const formData = { poi: "2" };
    submitForm('/change_camera', formData, null);
}

// Setup functions
function setupPlayerAutoComplete() {
    const playerNameInput = safeGetElement('playerName');
    const nucleusHashInput = safeGetElement('nucleusHash');
    
    if (playerNameInput) {
        playerNameInput.addEventListener('input', function() {
            const selectedPlayer = gameState.lobbyPlayers.find(p => p.name === this.value);
            if (selectedPlayer && nucleusHashInput) {
                nucleusHashInput.value = selectedPlayer.nucleusHash || '';
                nucleusHashInput.placeholder = `Auto-filled: ${selectedPlayer.nucleusHash || 'N/A'}`;
            }
        });
    }
}

function populateTeamAssignmentOptions() {
    const teamSelect = document.getElementById('teamId');
    const hardwareNameInput = document.getElementById('targetHardwareName');
    const nucleusHashInput = document.getElementById('targetNucleusHash');
    
    if (!teamSelect || !gameState.teams.length) return;
    
    teamSelect.innerHTML = '<option value="">Select team...</option>';
    teamSelect.innerHTML += '<option value="0">👁️ Observers</option>';
    
    for (let i = 1; i <= 20; i++) {
        const team = gameState.teams.find(t => t.id === i);
        const playersInTeam = gameState.lobbyPlayers.filter(p => p.teamId === i);
        const teamName = team?.name || `Team ${i}`;
        const playerCount = playersInTeam.length;
        
        teamSelect.innerHTML += `<option value="${i}">${teamName} (${playerCount} players)</option>`;
    }
}

function setupSmartFormInteractions() {
    const teamIdInputs = document.querySelectorAll('input[id*="teamId"], select[id*="teamId"]');
    teamIdInputs.forEach(input => {
        input.addEventListener('change', function() {
            const teamId = parseInt(this.value);
            if (teamId > 0) {
                const team = gameState.teams.find(t => t.id === teamId);
                if (team && team.name) {
                    showNotification(`Selected: ${team.name}`, 'success');
                }
            }
        });
    });
    
    const playerInputs = document.querySelectorAll('input[list="playerNames"]');
    playerInputs.forEach(input => {
        input.addEventListener('input', function() {
            const selectedPlayer = gameState.lobbyPlayers.find(p => p.name === this.value);
            if (selectedPlayer) {
                const nucleusInput = this.closest('form')?.querySelector('input[list*="nucleus"]');
                if (nucleusInput && selectedPlayer.nucleusHash) {
                    nucleusInput.value = selectedPlayer.nucleusHash;
                }
                
                showNotification(`Selected: ${selectedPlayer.name} (Team ${selectedPlayer.teamId})`, 'success');
            }
        });
    });
    
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateFormContext(this)) {
                e.preventDefault();
                return false;
            }
        });
    });
}

function validateFormContext(form) {
    const formId = form.id;
    
    if (['setTeamForm', 'kickPlayerForm', 'setTeamNameForm'].includes(formId)) {
        if (gameState.lobbyPlayers.length === 0) {
            showNotification('Please load lobby data first by clicking "Get Players"', 'error');
            return false;
        }
    }
    
    if (formId === 'setSettingsForm') {
        const settingsJson = document.getElementById('settings')?.value;
        try {
            JSON.parse(settingsJson);
        } catch (e) {
            showNotification('Invalid JSON format in settings', 'error');
            return false;
        }
    }
    
    return true;
}

function updateContextualFormStates() {
    // This function can be extended to update form states based on current context
    console.log('Updating contextual form states...');
}

// Tab functionality
function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    
    // Add active class to clicked button
    const activeBtn = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
}

// Specific function for create lobby to ensure GET method
function createLobby() {
    console.log('Creating lobby with explicit GET request...');
    
    fetch('/create_lobby', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => {
        console.log('Create lobby response status:', response.status);
        console.log('Create lobby response headers:', [...response.headers.entries()]);
        
        if (!response.ok) {
            return response.text().then(errorText => {
                console.error('Create lobby error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
            });
        }
        
        return response.text();
    })
    .then(responseText => {
        console.log('Create lobby raw response:', responseText);
        
        if (!responseText || responseText.trim() === '') {
            showNotification('Lobby created (empty response)', 'warning');
            updateResponsePanel({ message: 'Empty response received', endpoint: '/create_lobby' });
            return;
        }
        
        try {
            const data = parseRobustJSON(responseText, 'create lobby response');
            updateResponsePanel(data);
            showNotification(data.message || 'Lobby created successfully');
            
            // Auto-refresh lobby data
            setTimeout(() => {
                refreshLobbyData().catch(error => {
                    console.log('Auto-refresh failed after lobby creation:', error);
                });
            }, 1000);
        } catch (error) {
            console.error('Error parsing create lobby response:', error);
            showNotification('Lobby created (response format issue)', 'warning');
            updateResponsePanel({ 
                raw_response: responseText,
                parse_error: error.message,
                endpoint: '/create_lobby' 
            });
        }
    })
    .catch(error => {
        console.error('Error creating lobby:', error);
        showNotification(`Error creating lobby: ${error.message}`, 'error');
        updateResponsePanel({ 
            error: error.message,
            endpoint: '/create_lobby',
            method: 'GET',
            timestamp: new Date().toISOString()
        });
    });
}

// Test function to check which server routes are working
function testServerRoutes() {
    console.log('Testing server routes...');
    
    const testEndpoints = [
        { url: '/get_players', method: 'GET', name: 'Get Players (known working)' },
        { url: '/health-check', method: 'GET', name: 'Health Check' },
        { url: '/create_lobby', method: 'GET', name: 'Create Lobby' },
        { url: '/send_discord_token', method: 'GET', name: 'Discord Token' },
        { url: '/get_settings', method: 'GET', name: 'Get Settings' }
    ];
    
    testEndpoints.forEach((endpoint, index) => {
        setTimeout(() => {
            console.log(`Testing ${endpoint.name} (${endpoint.method} ${endpoint.url})`);
            
            fetch(endpoint.url, {
                method: endpoint.method,
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => {
                console.log(`${endpoint.name}: ${response.status} ${response.statusText}`);
                return response.text();
            })
            .then(text => {
                console.log(`${endpoint.name} response:`, text.substring(0, 100) + (text.length > 100 ? '...' : ''));
            })
            .catch(error => {
                console.error(`${endpoint.name} error:`, error.message);
            });
        }, index * 500); // Stagger requests by 500ms
    });
    
    showNotification('Testing server routes... check console for results');
}

// Utility function to safely get elements and avoid null errors
function safeGetElement(id) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element with ID '${id}' not found`);
    }
    return element;
}

// Utility function to safely set element values
function safeSetValue(id, value) {
    const element = safeGetElement(id);
    if (element) {
        element.value = value;
        return true;
    }
    return false;
}

// Utility function to safely get element values
function safeGetValue(id, defaultValue = '') {
    const element = safeGetElement(id);
    return element ? element.value : defaultValue;
}

// Utility function for robust JSON parsing
function parseRobustJSON(responseText, context = 'response') {
    console.log(`Parsing ${context}:`, responseText);
    
    let cleanedResponse = responseText.trim();
    
    if (!cleanedResponse) {
        throw new Error(`Empty ${context}`);
    }
    
    // Handle multiple JSON objects concatenated together
    if (cleanedResponse.includes('}{')) {
        console.warn(`Multiple JSON objects detected in ${context}, attempting to parse...`);
        
        // Try to split and find valid JSON objects
        const potentialJsons = [];
        let currentJson = '';
        let braceCount = 0;
        
        for (let i = 0; i < cleanedResponse.length; i++) {
            const char = cleanedResponse[i];
            currentJson += char;
            
            if (char === '{') {
                braceCount++;
            } else if (char === '}') {
                braceCount--;
                
                if (braceCount === 0 && currentJson.trim()) {
                    potentialJsons.push(currentJson.trim());
                    currentJson = '';
                }
            }
        }
        
        console.log(`Found ${potentialJsons.length} potential JSON objects in ${context}`);
        
        // Try to parse each JSON object, starting from the last one
        for (let i = potentialJsons.length - 1; i >= 0; i--) {
            try {
                const parsed = JSON.parse(potentialJsons[i]);
                console.log(`Successfully parsed JSON object ${i + 1} of ${potentialJsons.length} from ${context}`);
                return parsed;
            } catch (e) {
                console.warn(`Failed to parse JSON object ${i + 1} from ${context}:`, e.message);
            }
        }
        
        throw new Error(`No valid JSON object found in ${context}`);
    } else {
        // Handle single JSON object
        try {
            return JSON.parse(cleanedResponse);
        } catch (parseError) {
            console.error(`JSON Parse Error in ${context}:`, parseError);
            console.error(`Failed ${context}:`, responseText);
            console.error(`Response length:`, responseText.length);
            
            // Try aggressive cleaning
            try {
                let lastAttempt = responseText.replace(/^[^{]*/, '').replace(/[^}]*$/, '');
                
                // Find the first complete JSON object
                let braceCount = 0;
                let jsonEnd = -1;
                for (let i = 0; i < lastAttempt.length; i++) {
                    if (lastAttempt[i] === '{') braceCount++;
                    else if (lastAttempt[i] === '}') {
                        braceCount--;
                        if (braceCount === 0) {
                            jsonEnd = i + 1;
                            break;
                        }
                    }
                }
                
                if (jsonEnd > 0) {
                    const recovered = JSON.parse(lastAttempt.substring(0, jsonEnd));
                    console.log(`Recovered JSON from ${context} with aggressive cleaning`);
                    return recovered;
                }
            } catch (secondError) {
                console.error(`Aggressive cleaning also failed for ${context}:`, secondError);
            }
            
            throw parseError;
        }
    }
}
