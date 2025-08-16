// PyOrchestrate Web Interface - Static JavaScript Functions

function highlightJSON(jsonStr) {
    // Create a temporary div to safely escape HTML
    const tempDiv = document.createElement('div');
    tempDiv.textContent = jsonStr;
    let html = tempDiv.innerHTML;
    
    // Apply JSON syntax highlighting
    // Keys (quoted strings followed by colon)
    html = html.replace(/(&quot;[^&]*&quot;)(\s*:)/g, '<span class="json-key">$1</span>$2');
    
    // String values (quoted strings after colon)
    html = html.replace(/(:\s*)(&quot;[^&]*&quot;)/g, '$1<span class="json-string">$2</span>');
    
    // Boolean values
    html = html.replace(/(:\s*)(true|false)/g, '$1<span class="json-boolean">$2</span>');
    
    // Null values
    html = html.replace(/(:\s*)(null)/g, '$1<span class="json-null">$2</span>');
    
    // Numbers (including decimals and scientific notation)
    html = html.replace(/(:\s*)(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/g, '$1<span class="json-number">$2</span>');
    
    // Punctuation (braces, brackets, commas)
    html = html.replace(/([{}\[\],])/g, '<span class="json-punctuation">$1</span>');
    
    return html;
}

function displayJSON(jsonData) {
    document.getElementById('json-content').innerHTML = highlightJSON(jsonData);
}

function manualRefresh() {
    const btn = document.getElementById('refresh-btn');
    btn.disabled = true;
    btn.textContent = '🔄 Refreshing...';
    window.location.reload();
}

// Auto-refresh functionality
let refreshTimer = null;
let countdownTimer = null;
let secondsLeft = 0;

function updateCountdown() {
    if (secondsLeft > 0) {
        document.getElementById('countdown').textContent = `Next refresh in ${secondsLeft}s`;
        secondsLeft--;
    } else {
        document.getElementById('countdown').textContent = 'Refreshing...';
    }
}

function startAutoRefresh() {
    const interval = parseInt(document.getElementById('refresh-interval').value) * 1000;
    secondsLeft = Math.floor(interval / 1000);
    
    // Clear existing timers
    if (refreshTimer) clearTimeout(refreshTimer);
    if (countdownTimer) clearInterval(countdownTimer);
    
    // Start countdown
    countdownTimer = setInterval(updateCountdown, 1000);
    updateCountdown();
    
    // Set refresh timer
    refreshTimer = setTimeout(() => {
        window.location.reload();
    }, interval);
    
    document.getElementById('refresh-status').textContent = 'Active';
    document.getElementById('refresh-status').className = 'status-indicator status-active';
}

function stopAutoRefresh() {
    if (refreshTimer) clearTimeout(refreshTimer);
    if (countdownTimer) clearInterval(countdownTimer);
    refreshTimer = null;
    countdownTimer = null;
    
    document.getElementById('countdown').textContent = '';
    document.getElementById('refresh-status').textContent = 'Paused';
    document.getElementById('refresh-status').className = 'status-indicator status-paused';
}

function setupAutoRefresh() {
    if (document.getElementById('auto-refresh')) {
        const autoRefreshCheckbox = document.getElementById('auto-refresh');
        const intervalInput = document.getElementById('refresh-interval');
        
        function toggleAutoRefresh() {
            if (autoRefreshCheckbox.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        }
        
        autoRefreshCheckbox.addEventListener('change', toggleAutoRefresh);
        intervalInput.addEventListener('change', () => {
            if (autoRefreshCheckbox.checked) {
                stopAutoRefresh();
                startAutoRefresh();
            }
        });
        
        // Start auto-refresh if checkbox is checked
        if (autoRefreshCheckbox.checked) {
            startAutoRefresh();
        }
    }
}
