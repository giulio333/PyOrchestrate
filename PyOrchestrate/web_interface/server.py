"""
HTTP Server for PyOrchestrate Web Interface

Provides a REST API that exposes orchestrator data in read-only mode.
Communicates with the orchestrator via Unix socket using the same
protocol as the CLI.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Depends, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from PyOrchestrate.core.utilities.messaging import MessageChannel, ServiceMessage
from PyOrchestrate.cli import CLIConstants


class WebServerConfig(BaseModel):
    """Configuration for the web server."""

    host: str = "127.0.0.1"
    port: int = 8000
    socket_path: str = CLIConstants.DEFAULT_SOCKET_PATH
    enable_auth: bool = False
    auth_token: Optional[str] = None
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


class OrchestratorClient:
    """Client for communicating with the orchestrator via Unix socket."""

    def __init__(self, socket_path: str):
        self.socket_path = socket_path

    def send_command(
        self, command: str, args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send a command to the orchestrator and return the response."""
        try:
            client = MessageChannel("unix_socket_client", self.socket_path)

            msg = ServiceMessage.create_command(
                sender="web_interface",
                command=command,
                args=args or [],
            )

            response_msg = client.send_and_receive(msg, timeout=5.0)

            if response_msg:
                return response_msg.payload
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"Cannot connect to orchestrator at {self.socket_path}",
                )

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Communication error: {str(e)}"
            )


def create_pretty_json_response(data: Dict[str, Any]) -> JSONResponse:
    """Create a pretty-formatted JSON response."""
    pretty_json = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
    return JSONResponse(
        content=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        media_type="application/json",
    )


def create_html_response(
    title: str,
    data: Dict[str, Any],
    endpoint: str,
    is_stats: bool = False,
    show_filters: bool = False,
    current_params: Optional[Dict[str, Any]] = None,
) -> HTMLResponse:
    """Create an HTML response with syntax-highlighted JSON."""
    pretty_json = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - PyOrchestrate</title>
        <style>
            :root {{
                --primary-bg: #0a0a0b;
                --secondary-bg: #111113;
                --surface-bg: #18181b;
                --surface-hover: #1f1f23;
                --border-primary: #27272a;
                --border-secondary: #3f3f46;
                --text-primary: #fafafa;
                --text-secondary: #a1a1aa;
                --text-muted: #71717a;
                --accent-primary: #6366f1;
                --accent-secondary: #8b5cf6;
                --success: #10b981;
                --warning: #f59e0b;
                --error: #ef4444;
                --glass-bg: rgba(24, 24, 27, 0.7);
                --glass-border: rgba(39, 39, 42, 0.8);
            }}
            
            * {{ 
                margin: 0; 
                padding: 0; 
                box-sizing: border-box; 
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', system-ui, sans-serif;
                background: var(--primary-bg);
                color: var(--text-primary);
                min-height: 100vh;
                line-height: 1.5;
                font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
                -webkit-font-smoothing: antialiased;
                text-rendering: optimizeLegibility;
                padding: 24px;
            }}
            
            .header {{
                background: var(--glass-bg);
                padding: 32px 40px;
                border-radius: 16px;
                margin-bottom: 32px;
                backdrop-filter: blur(20px) saturate(180%);
                border: 1px solid var(--glass-border);
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
            }}
            
            .header h1 {{
                color: var(--text-primary);
                font-size: 2.25rem;
                font-weight: 600;
                margin-bottom: 8px;
                letter-spacing: -0.025em;
            }}
            
            .header p {{
                color: var(--text-secondary);
                font-size: 1rem;
                font-weight: 400;
                opacity: 0.8;
            }}
            
            .navigation {{
                display: flex;
                justify-content: center;
                gap: 8px;
                margin: 32px 0;
                padding: 8px;
                background: var(--surface-bg);
                border-radius: 12px;
                border: 1px solid var(--border-primary);
                width: fit-content;
                margin-left: auto;
                margin-right: auto;
            }}
            
            .navigation a {{
                color: var(--text-secondary);
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 8px;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                font-weight: 500;
                font-size: 14px;
                position: relative;
            }}
            
            .navigation a:hover {{
                color: var(--text-primary);
                background: var(--surface-hover);
            }}
            
            .navigation a.current {{
                background: var(--accent-primary);
                color: white;
                box-shadow: 0 1px 3px rgba(99, 102, 241, 0.3);
            }}
            
            .controls {{
                display: flex;
                gap: 16px;
                align-items: center;
                margin-bottom: 24px;
                flex-wrap: wrap;
                background: var(--glass-bg);
                padding: 20px;
                border-radius: 12px;
                border: 1px solid var(--glass-border);
                backdrop-filter: blur(20px) saturate(180%);
            }}
            
            .filters-section {{
                display: flex;
                gap: 16px;
                align-items: center;
                flex-wrap: wrap;
                background: var(--surface-bg);
                padding: 16px;
                border-radius: 10px;
                border: 1px solid var(--border-primary);
                margin-bottom: 20px;
            }}
            
            .filter-group {{
                display: flex;
                flex-direction: column;
                gap: 6px;
                min-width: 120px;
            }}
            
            .filter-group label {{
                color: var(--text-secondary);
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .filter-group input, .filter-group select {{
                background: var(--surface-hover);
                border: 1px solid var(--border-secondary);
                color: var(--text-primary);
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.2s;
            }}
            
            .filter-group input:focus, .filter-group select:focus {{
                outline: none;
                border-color: var(--accent-primary);
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }}
            
            .filter-actions {{
                display: flex;
                gap: 8px;
                align-items: end;
                margin-left: auto;
            }}
            
            .filter-btn {{
                background: var(--accent-primary);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                transition: all 0.2s;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }}
            
            .filter-btn:hover {{
                background: var(--accent-secondary);
                transform: translateY(-1px);
            }}
            
            .filter-btn.secondary {{
                background: var(--surface-hover);
                color: var(--text-secondary);
                border: 1px solid var(--border-secondary);
            }}
            
            .filter-btn.secondary:hover {{
                background: var(--surface-bg);
                color: var(--text-primary);
            }}
            
            .auto-refresh-control {{
                display: flex;
                align-items: center;
                gap: 12px;
                background: var(--surface-bg);
                padding: 12px 16px;
                border-radius: 10px;
                border: 1px solid var(--border-primary);
            }}
            
            .auto-refresh-control label {{
                color: var(--text-secondary);
                font-size: 14px;
                font-weight: 500;
                white-space: nowrap;
            }}
            
            .auto-refresh-control input[type="number"] {{
                background: var(--surface-hover);
                border: 1px solid var(--border-secondary);
                color: var(--text-primary);
                padding: 8px 12px;
                border-radius: 6px;
                width: 80px;
                font-size: 14px;
                transition: border-color 0.2s;
            }}
            
            .auto-refresh-control input[type="number"]:focus {{
                outline: none;
                border-color: var(--accent-primary);
                box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
            }}
            
            .auto-refresh-control input[type="checkbox"] {{
                width: 18px;
                height: 18px;
                accent-color: var(--accent-primary);
                cursor: pointer;
            }}
            
            .status-indicator {{
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .status-active {{
                background: rgba(16, 185, 129, 0.15);
                color: var(--success);
                border: 1px solid rgba(16, 185, 129, 0.3);
            }}
            
            .status-paused {{
                background: rgba(245, 158, 11, 0.15);
                color: var(--warning);
                border: 1px solid rgba(245, 158, 11, 0.3);
            }}
            
            .json-container {{
                background: var(--secondary-bg);
                border-radius: 12px;
                padding: 24px;
                border: 1px solid var(--border-primary);
                overflow-x: auto;
                font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 13px;
                line-height: 1.6;
                font-variant-ligatures: common-ligatures;
            }}
            
            .json-content {{
                white-space: pre;
                color: var(--text-primary);
            }}
            
            /* JSON syntax highlighting - refined colors */
            .json-key {{ color: #7dd3fc; font-weight: 500; }}
            .json-string {{ color: #fbbf24; }}
            .json-number {{ color: #34d399; }}
            .json-boolean {{ color: #c084fc; font-weight: 500; }}
            .json-null {{ color: #94a3b8; font-style: italic; }}
            .json-punctuation {{ color: var(--text-muted); }}
            
            .refresh-btn {{
                background: var(--accent-primary);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                position: relative;
                overflow: hidden;
            }}
            
            .refresh-btn:hover {{
                background: var(--accent-secondary);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
            }}
            
            .refresh-btn:active {{
                transform: translateY(0);
            }}
            
            .refresh-btn:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }}
            
            .api-info {{
                background: rgba(59, 130, 246, 0.1);
                color: #93c5fd;
                padding: 16px;
                border-radius: 10px;
                border: 1px solid rgba(59, 130, 246, 0.2);
                margin: 20px 0;
            }}
            
            .api-info code {{
                background: var(--surface-bg);
                padding: 4px 8px;
                border-radius: 4px;
                font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 12px;
            }}
            
            .countdown {{
                color: var(--text-muted);
                font-size: 13px;
                margin-left: 12px;
                font-weight: 500;
                font-variant-numeric: tabular-nums;
            }}
            
            .error {{
                background: rgba(239, 68, 68, 0.1);
                color: #fca5a5;
                padding: 16px;
                border-radius: 10px;
                border: 1px solid rgba(239, 68, 68, 0.2);
                margin: 20px 0;
            }}
            
            /* Scrollbar styling */
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: var(--surface-bg);
                border-radius: 4px;
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: var(--border-secondary);
                border-radius: 4px;
            }}
            
            ::-webkit-scrollbar-thumb:hover {{
                background: var(--text-muted);
            }}
            
            /* Responsive design */
            @media (max-width: 768px) {{
                body {{ padding: 16px; }}
                .header {{ padding: 24px; }}
                .header h1 {{ font-size: 1.875rem; }}
                .navigation {{ flex-direction: column; width: 100%; }}
                .navigation a {{ text-align: center; }}
                .controls {{ flex-direction: column; align-items: stretch; }}
                .auto-refresh-control {{ justify-content: space-between; }}
            }}
            
            /* Subtle animations */
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .json-container {{ animation: fadeIn 0.3s ease-out; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🐍 PyOrchestrate Web Interface</h1>
            <p>Real-time monitoring and API access</p>
        </div>
        
        <div class="navigation">
            <a href="/api/orchestrator/status" class="{'current' if endpoint == 'status' else ''}">📊 Status</a>
            <a href="/api/agents" class="{'current' if endpoint == 'agents' else ''}">🤖 Agents</a>
            <a href="/api/orchestrator/stats" class="{'current' if endpoint == 'stats' else ''}">📈 Stats</a>
            <a href="/api/orchestrator/report" class="{'current' if endpoint == 'report' else ''}">📋 Report</a>
            <a href="/api/orchestrator/dependencies" class="{'current' if endpoint == 'dependencies' else ''}">🔗 Dependencies</a>
            <a href="/api/history" class="{'current' if endpoint == 'history' else ''}">📜 History</a>
            <a href="/docs" target="_blank">📚 API Docs</a>
        </div>
        
        <div class="api-info">
            <strong>Endpoint:</strong> <code>GET {endpoint}</code><br>
            <strong>API URL:</strong> <code>{endpoint}?format=json</code> (for raw JSON)<br>
            <strong>Updated:</strong> <span id="timestamp">{data.get('timestamp', 'N/A')}</span>
        </div>
        
        {'''
        <div class="filters-section">
            ''' + ('''
            <div class="filter-group">
                <label for="filter-agent">Agent Name</label>
                <input type="text" id="filter-agent" placeholder="Enter agent name..." value="''' + str(current_params.get('agent', '') if current_params else '') + '''">
            </div>
            ''' if endpoint == '/api/agents' else '') + '''
            ''' + ('''
            <div class="filter-group">
                <label for="filter-agent">Agent</label>
                <input type="text" id="filter-agent" placeholder="Enter agent name..." value="''' + str(current_params.get('agent', '') if current_params else '') + '''">
            </div>
            <div class="filter-group">
                <label for="filter-event-type">Event Type</label>
                <select id="filter-event-type">
                    <option value="">All Events</option>
                    <option value="AGENT_START"''' + (' selected' if current_params and current_params.get('event_type') == 'AGENT_START' else '') + '''>Agent Start</option>
                    <option value="AGENT_READY"''' + (' selected' if current_params and current_params.get('event_type') == 'AGENT_READY' else '') + '''>Agent Ready</option>
                    <option value="AGENT_CLOSE"''' + (' selected' if current_params and current_params.get('event_type') == 'AGENT_CLOSE' else '') + '''>Agent Close</option>
                    <option value="AGENT_ERROR"''' + (' selected' if current_params and current_params.get('event_type') == 'AGENT_ERROR' else '') + '''>Agent Error</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="filter-last">Last N Events</label>
                <input type="number" id="filter-last" min="1" max="1000" placeholder="50" value="''' + str(current_params.get('last', '') if current_params and current_params.get('last') else '') + '''">
            </div>
            <div class="filter-group">
                <label for="filter-after-seq">After Sequence</label>
                <input type="number" id="filter-after-seq" min="0" placeholder="0" value="''' + str(current_params.get('after_seq', '') if current_params and current_params.get('after_seq') else '') + '''">
            </div>
            ''' if endpoint == '/api/history' else '') + '''
            <div class="filter-actions">
                <button class="filter-btn" onclick="applyFilters()">🔍 Apply Filters</button>
                <button class="filter-btn secondary" onclick="clearFilters()">🗑️ Clear</button>
            </div>
        </div>
        ''' if show_filters else ''}
        
        <div class="controls">
            <button class="refresh-btn" onclick="manualRefresh()" id="refresh-btn">🔄 Refresh</button>
            
            {'''
            <div class="auto-refresh-control">
                <input type="checkbox" id="auto-refresh" ''' + ('checked' if is_stats else '') + '''>
                <label for="auto-refresh">Auto-refresh every</label>
                <input type="number" id="refresh-interval" min="1" max="60" value="5" step="1">
                <label for="refresh-interval">seconds</label>
                <span class="status-indicator" id="refresh-status">''' + ('Active' if is_stats else 'Paused') + '''</span>
                <span class="countdown" id="countdown"></span>
            </div>
            ''' if is_stats else ''}
        </div>
        
        <div class="json-container">
            <div class="json-content" id="json-content"></div>
        </div>
        
        <script>
            // JSON data to display
            const jsonData = {json.dumps(pretty_json)};
            
            // Simple JSON highlighting using DOM methods (no regex)
            function highlightJSON(jsonStr) {{
                // Create a pre element to preserve formatting
                const pre = document.createElement('pre');
                pre.style.margin = '0';
                pre.style.fontFamily = 'inherit';
                pre.style.whiteSpace = 'pre';
                pre.style.overflow = 'visible';
                
                // Split by lines and process each
                const lines = jsonStr.split('\\n');
                
                lines.forEach(function(line, index) {{
                    const lineElement = document.createElement('div');
                    
                    // Create a safe text node first
                    const textNode = document.createTextNode(line);
                    const tempDiv = document.createElement('div');
                    tempDiv.appendChild(textNode);
                    
                    // Get safely escaped HTML
                    let lineHTML = tempDiv.innerHTML;
                    
                    // Apply basic highlighting using safe string replacements
                    // This approach avoids regex issues in Python f-strings
                    
                    // Highlight JSON keys (quoted strings before colons)
                    lineHTML = lineHTML.split('&quot;').join('"');
                    
                    // Use simple string methods instead of regex
                    if (line.indexOf(':') !== -1 && line.indexOf('"') !== -1) {{
                        const parts = line.split(':');
                        if (parts.length >= 2) {{
                            const keyPart = parts[0];
                            const valuePart = parts.slice(1).join(':');
                            
                            let highlightedKey = keyPart;
                            let highlightedValue = valuePart;
                            
                            // Color keys
                            if (keyPart.indexOf('"') !== -1) {{
                                const keyStart = keyPart.indexOf('"');
                                const keyEnd = keyPart.lastIndexOf('"');
                                if (keyStart !== -1 && keyEnd !== -1 && keyEnd > keyStart) {{
                                    const beforeKey = keyPart.substring(0, keyStart);
                                    const keyText = keyPart.substring(keyStart, keyEnd + 1);
                                    const afterKey = keyPart.substring(keyEnd + 1);
                                    highlightedKey = beforeKey + '<span class="json-key">' + keyText + '</span>' + afterKey;
                                }}
                            }}
                            
                            // Color values
                            const trimmedValue = valuePart.trim();
                            if (trimmedValue.startsWith('"')) {{
                                highlightedValue = valuePart.replace(trimmedValue, '<span class="json-string">' + trimmedValue + '</span>');
                            }} else if (trimmedValue === 'true' || trimmedValue === 'false' || trimmedValue.startsWith('true,') || trimmedValue.startsWith('false,')) {{
                                highlightedValue = valuePart.replace(/\\b(true|false)\\b/g, '<span class="json-boolean">$1</span>');
                            }} else if (trimmedValue === 'null' || trimmedValue.startsWith('null,')) {{
                                highlightedValue = valuePart.replace(/\\bnull\\b/g, '<span class="json-null">null</span>');
                            }} else if (!isNaN(parseFloat(trimmedValue.replace(',', '')))) {{
                                const numMatch = trimmedValue.match(/^-?\\d+(\\.\\d+)?/);
                                if (numMatch) {{
                                    highlightedValue = valuePart.replace(numMatch[0], '<span class="json-number">' + numMatch[0] + '</span>');
                                }}
                            }}
                            
                            lineHTML = highlightedKey + ':' + highlightedValue;
                        }}
                    }}
                    
                    // Highlight punctuation
                    lineHTML = lineHTML.replace(/{{/g, '<span class="json-punctuation">{{</span>');
                    lineHTML = lineHTML.replace(/}}/g, '<span class="json-punctuation">}}</span>');
                    lineHTML = lineHTML.replace(/\\[/g, '<span class="json-punctuation">[</span>');
                    lineHTML = lineHTML.replace(/\\]/g, '<span class="json-punctuation">]</span>');
                    lineHTML = lineHTML.replace(/,/g, '<span class="json-punctuation">,</span>');
                    
                    lineElement.innerHTML = lineHTML;
                    pre.appendChild(lineElement);
                }});
                
                return pre.outerHTML;
            }}
            
            function displayJSON() {{
                const content = document.getElementById('json-content');
                if (content) {{
                    content.innerHTML = highlightJSON(jsonData);
                }}
            }}
            
            function manualRefresh() {{
                const btn = document.getElementById('refresh-btn');
                if (btn) {{
                    btn.disabled = true;
                    btn.textContent = '🔄 Refreshing...';
                }}
                window.location.reload();
            }}
            
            // Auto-refresh variables
            let refreshTimer = null;
            let countdownTimer = null;
            let secondsLeft = 0;
            
            function updateCountdown() {{
                if (secondsLeft > 0) {{
                    const countdownEl = document.getElementById('countdown');
                    if (countdownEl) {{
                        countdownEl.textContent = 'Next refresh in ' + secondsLeft + 's';
                    }}
                    secondsLeft--;
                }} else {{
                    const countdownEl = document.getElementById('countdown');
                    if (countdownEl) {{
                        countdownEl.textContent = 'Refreshing...';
                    }}
                }}
            }}
            
            function startAutoRefresh() {{
                const intervalInput = document.getElementById('refresh-interval');
                if (!intervalInput) return;
                
                const interval = parseInt(intervalInput.value) * 1000;
                secondsLeft = Math.floor(interval / 1000);
                
                if (refreshTimer) clearTimeout(refreshTimer);
                if (countdownTimer) clearInterval(countdownTimer);
                
                countdownTimer = setInterval(updateCountdown, 1000);
                updateCountdown();
                
                refreshTimer = setTimeout(function() {{
                    window.location.reload();
                }}, interval);
                
                const statusEl = document.getElementById('refresh-status');
                if (statusEl) {{
                    statusEl.textContent = 'Active';
                    statusEl.className = 'status-indicator status-active';
                }}
            }}
            
            function stopAutoRefresh() {{
                if (refreshTimer) clearTimeout(refreshTimer);
                if (countdownTimer) clearInterval(countdownTimer);
                refreshTimer = null;
                countdownTimer = null;
                
                const countdownEl = document.getElementById('countdown');
                const statusEl = document.getElementById('refresh-status');
                
                if (countdownEl) countdownEl.textContent = '';
                if (statusEl) {{
                    statusEl.textContent = 'Paused';
                    statusEl.className = 'status-indicator status-paused';
                }}
            }}
            
            // Initialize page
            displayJSON();
            
            // Filter functions
            function applyFilters() {{
                const currentUrl = new URL(window.location);
                const params = new URLSearchParams();
                
                // Get filter values based on current page
                const endpoint = currentUrl.pathname;
                
                if (endpoint === '/api/agents') {{
                    const agentFilter = document.getElementById('filter-agent');
                    if (agentFilter && agentFilter.value.trim()) {{
                        // For agents page, redirect to specific agent endpoint
                        window.location.href = '/api/agents/' + encodeURIComponent(agentFilter.value.trim());
                        return;
                    }}
                }} else if (endpoint === '/api/history') {{
                    const agentFilter = document.getElementById('filter-agent');
                    const eventTypeFilter = document.getElementById('filter-event-type');
                    const lastFilter = document.getElementById('filter-last');
                    const afterSeqFilter = document.getElementById('filter-after-seq');
                    
                    if (agentFilter && agentFilter.value.trim()) {{
                        params.set('agent', agentFilter.value.trim());
                    }}
                    if (eventTypeFilter && eventTypeFilter.value) {{
                        params.set('event_type', eventTypeFilter.value);
                    }}
                    if (lastFilter && lastFilter.value) {{
                        params.set('last', lastFilter.value);
                    }}
                    if (afterSeqFilter && afterSeqFilter.value) {{
                        params.set('after_seq', afterSeqFilter.value);
                    }}
                }}
                
                // Apply filters by updating URL
                const newUrl = currentUrl.pathname + (params.toString() ? '?' + params.toString() : '');
                window.location.href = newUrl;
            }}
            
            function clearFilters() {{
                const currentUrl = new URL(window.location);
                window.location.href = currentUrl.pathname;
            }}
            
            // Setup auto-refresh for stats page
            {f'''
            const autoRefreshCheckbox = document.getElementById('auto-refresh');
            const intervalInput = document.getElementById('refresh-interval');
            
            if (autoRefreshCheckbox && intervalInput) {{
                function toggleAutoRefresh() {{
                    if (autoRefreshCheckbox.checked) {{
                        startAutoRefresh();
                    }} else {{
                        stopAutoRefresh();
                    }}
                }}
                
                autoRefreshCheckbox.addEventListener('change', toggleAutoRefresh);
                intervalInput.addEventListener('change', function() {{
                    if (autoRefreshCheckbox.checked) {{
                        stopAutoRefresh();
                        startAutoRefresh();
                    }}
                }});
                
                if (autoRefreshCheckbox.checked) {{
                    startAutoRefresh();
                }}
            }}
            ''' if is_stats else ''}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


class PyOrchestrateWebServer:
    """Main web server class."""

    def __init__(self, config: WebServerConfig):
        self.config = config
        self.app = FastAPI(
            title="PyOrchestrate Web Interface",
            description="Read-only web interface for PyOrchestrate orchestrator monitoring",
            version="0.2.0",
        )
        self.orchestrator_client = OrchestratorClient(config.socket_path)
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """Setup CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["GET"],  # Only read operations
            allow_headers=["*"],
        )

    def _setup_auth(self):
        """Setup authentication if enabled."""
        if not self.config.enable_auth:
            return None

        security = HTTPBearer()

        def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
            if credentials.credentials != self.config.auth_token:
                raise HTTPException(
                    status_code=401, detail="Invalid authentication token"
                )
            return credentials.credentials

        return verify_token

    def _setup_routes(self):
        """Setup API routes."""
        auth_dependency = self._setup_auth()

        @self.app.get("/")
        async def root():
            """Root endpoint redirects to orchestrator status."""
            return HTMLResponse(
                """
            <!DOCTYPE html>
            <html>
            <head>
                <title>PyOrchestrate Web Interface</title>
                <meta http-equiv="refresh" content="0; url=/api/orchestrator/status">
            </head>
            <body>
                <p>Redirecting to <a href="/api/orchestrator/status">PyOrchestrate Status</a>...</p>
            </body>
            </html>
            """
            )

        @self.app.get("/api/health")
        async def health_check(
            request: Request,
            format: Optional[str] = None,
            token: Optional[str] = (
                Depends(auth_dependency) if auth_dependency else None
            ),
        ):
            """Health check endpoint."""
            data = {"status": "healthy", "service": "pyorchestrate-web"}

            if format == "json" or "application/json" in request.headers.get(
                "accept", ""
            ):
                return create_pretty_json_response(data)
            else:
                return create_html_response("Health Check", data, "/api/health")

        @self.app.get("/api/orchestrator/status")
        async def get_orchestrator_status(
            request: Request,
            format: Optional[str] = None,
            token: Optional[str] = (
                Depends(auth_dependency) if auth_dependency else None
            ),
        ):
            """Get orchestrator status."""
            response = self.orchestrator_client.send_command("status")

            if format == "json" or "application/json" in request.headers.get(
                "accept", ""
            ):
                return create_pretty_json_response(response)
            else:
                return create_html_response(
                    "Orchestrator Status", response, "/api/orchestrator/status"
                )

        @self.app.get("/api/agents")
        async def list_agents(
            request: Request,
            format: Optional[str] = None,
            token: Optional[str] = (
                Depends(auth_dependency) if auth_dependency else None
            ),
        ):
            """List all agents and their status."""
            response = self.orchestrator_client.send_command("ps")

            if format == "json" or "application/json" in request.headers.get(
                "accept", ""
            ):
                return create_pretty_json_response(response)
            else:
                return create_html_response(
                    "Agents List", response, "/api/agents", show_filters=True
                )

        @self.app.get("/api/agents/{agent_name}")
        async def get_agent_status(
            agent_name: str,
            request: Request,
            format: Optional[str] = None,
            token: Optional[str] = (
                Depends(auth_dependency) if auth_dependency else None
            ),
        ):
            """Get status of a specific agent."""
            response = self.orchestrator_client.send_command("status", [agent_name])

            if format == "json" or "application/json" in request.headers.get(
                "accept", ""
            ):
                return create_pretty_json_response(response)
            else:
                return create_html_response(
                    f"Agent: {agent_name}", response, f"/api/agents/{agent_name}"
                )

        @self.app.get("/api/orchestrator/dependencies")
        async def get_dependencies(
            request: Request,
            format: Optional[str] = None,
            token: Optional[str] = (
                Depends(auth_dependency) if auth_dependency else None
            ),
        ):
            """Get agent dependencies."""
            response = self.orchestrator_client.send_command("dependencies")

            if format == "json" or "application/json" in request.headers.get(
                "accept", ""
            ):
                return create_pretty_json_response(response)
            else:
                return create_html_response(
                    "Dependencies", response, "/api/orchestrator/dependencies"
                )

        @self.app.get("/api/orchestrator/report")
        async def get_full_report(
            request: Request,
            format: Optional[str] = None,
            token: Optional[str] = (
                Depends(auth_dependency) if auth_dependency else None
            ),
        ):
            """Get full orchestrator report."""
            response = self.orchestrator_client.send_command("report")

            if format == "json" or "application/json" in request.headers.get(
                "accept", ""
            ):
                return create_pretty_json_response(response)
            else:
                return create_html_response(
                    "Full Report", response, "/api/orchestrator/report"
                )

        @self.app.get("/api/orchestrator/stats")
        async def get_stats(
            request: Request,
            format: Optional[str] = None,
            token: Optional[str] = (
                Depends(auth_dependency) if auth_dependency else None
            ),
        ):
            """Get real-time orchestrator and agent statistics."""
            response = self.orchestrator_client.send_command("stats")

            if format == "json" or "application/json" in request.headers.get(
                "accept", ""
            ):
                return create_pretty_json_response(response)
            else:
                return create_html_response(
                    "Real-time Stats",
                    response,
                    "/api/orchestrator/stats",
                    is_stats=True,
                )

        @self.app.get("/api/history")
        async def get_event_history(
            request: Request,
            last: Optional[int] = None,
            agent: Optional[str] = None,
            event_type: Optional[str] = None,
            after_seq: Optional[int] = None,
            format: Optional[str] = None,
            token: Optional[str] = (
                Depends(auth_dependency) if auth_dependency else None
            ),
        ):
            """Get event history with optional filtering."""
            params = {}
            if last is not None:
                params["last"] = last
            if agent is not None:
                params["agent"] = agent
            if event_type is not None:
                params["type"] = event_type
            if after_seq is not None:
                params["after_seq"] = after_seq

            args = [json.dumps(params)] if params else []
            response = self.orchestrator_client.send_command("history", args)

            if format == "json" or "application/json" in request.headers.get(
                "accept", ""
            ):
                return create_pretty_json_response(response)
            else:
                current_params = {}
                if last is not None:
                    current_params["last"] = last
                if agent is not None:
                    current_params["agent"] = agent
                if event_type is not None:
                    current_params["event_type"] = event_type
                if after_seq is not None:
                    current_params["after_seq"] = after_seq

                return create_html_response(
                    "Event History",
                    response,
                    "/api/history",
                    show_filters=True,
                    current_params=current_params,
                )

        @self.app.get("/api/history/stats")
        async def get_history_stats(
            request: Request,
            agent: Optional[str] = None,
            format: Optional[str] = None,
            token: Optional[str] = (
                Depends(auth_dependency) if auth_dependency else None
            ),
        ):
            """Get aggregated event statistics."""
            params = {}
            if agent is not None:
                params["agent"] = agent

            args = [json.dumps(params)] if params else []
            response = self.orchestrator_client.send_command("history-stats", args)

            if format == "json" or "application/json" in request.headers.get(
                "accept", ""
            ):
                return create_pretty_json_response(response)
            else:
                return create_html_response(
                    "History Statistics", response, "/api/history/stats"
                )

    def run(self):
        """Run the web server."""
        uvicorn.run(
            self.app, host=self.config.host, port=self.config.port, log_level="info"
        )


def create_app(config: WebServerConfig) -> FastAPI:
    """Factory function to create the FastAPI app."""
    server = PyOrchestrateWebServer(config)
    return server.app


def main():
    """Entry point for the web server."""
    import argparse

    parser = argparse.ArgumentParser(description="PyOrchestrate Web Interface")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument(
        "--socket",
        default=CLIConstants.DEFAULT_SOCKET_PATH,
        help="Path to orchestrator Unix socket",
    )
    parser.add_argument(
        "--enable-auth", action="store_true", help="Enable token-based authentication"
    )
    parser.add_argument(
        "--auth-token", help="Authentication token (required if --enable-auth)"
    )

    args = parser.parse_args()

    if args.enable_auth and not args.auth_token:
        parser.error("--auth-token is required when --enable-auth is used")

    config = WebServerConfig(
        host=args.host,
        port=args.port,
        socket_path=args.socket,
        enable_auth=args.enable_auth,
        auth_token=args.auth_token,
    )

    server = PyOrchestrateWebServer(config)

    print(f"Starting PyOrchestrate Web Interface on {config.host}:{config.port}")
    print(f"Connecting to orchestrator at: {config.socket_path}")
    if config.enable_auth:
        print("Authentication: ENABLED")

    try:
        server.run()
    except KeyboardInterrupt:
        print("\nShutting down web server...")


if __name__ == "__main__":
    main()
