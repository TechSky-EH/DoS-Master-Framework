#!/usr/bin/env python3
"""
DoS Master Framework - Web Interface
Modern web-based interface for DoS testing
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
import threading
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any
import secrets

# Import framework components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.engine import DoSEngine
from src.core.monitor import Monitor
from src.utils.validation import validate_target, validate_attack_params
from src.utils.config import load_config
from src.utils.logger import setup_logger

def create_app(config=None):
    """Create Flask application"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Configuration
    app.config['SECRET_KEY'] = config.get('web_interface', {}).get('secret_key', secrets.token_hex(16))
    app.config['DEBUG'] = config.get('web_interface', {}).get('debug', False)
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Global variables
    app.dos_engine = None
    app.monitor = None
    app.active_attacks = {}
    app.config_data = config or load_config()
    app.logger_instance = setup_logger()
    
    @app.route('/')
    def index():
        """Main dashboard"""
        return render_template('index.html')
    
    @app.route('/attack')
    def attack_page():
        """Attack configuration page"""
        attack_types = ['icmp_flood', 'udp_flood', 'syn_flood', 'http_flood', 'slowloris', 'multi_vector']
        profiles = ['stealth', 'moderate', 'aggressive']
        return render_template('attack.html', attack_types=attack_types, profiles=profiles)
    
    @app.route('/monitor')
    def monitor_page():
        """Monitoring dashboard"""
        return render_template('monitor.html')
    
    @app.route('/reports')
    def reports_page():
        """Reports and history"""
        return render_template('reports.html')
    
    @app.route('/api/attacks', methods=['GET'])
    def get_attack_types():
        """Get available attack types"""
        attacks = {
            'icmp_flood': {
                'name': 'ICMP Flood',
                'description': 'Bandwidth exhaustion using ICMP packets',
                'parameters': ['threads', 'duration', 'packet_size', 'rate']
            },
            'udp_flood': {
                'name': 'UDP Flood',
                'description': 'Connectionless flooding attack',
                'parameters': ['threads', 'duration', 'packet_size', 'ports', 'rate']
            },
            'syn_flood': {
                'name': 'SYN Flood',
                'description': 'TCP connection exhaustion',
                'parameters': ['threads', 'duration', 'port', 'spoof_ips']
            },
            'http_flood': {
                'name': 'HTTP Flood',
                'description': 'Application layer flooding',
                'parameters': ['threads', 'duration', 'target_paths', 'user_agents']
            },
            'slowloris': {
                'name': 'Slowloris',
                'description': 'Connection holding attack',
                'parameters': ['connections', 'duration', 'keep_alive_interval']
            },
            'multi_vector': {
                'name': 'Multi-Vector',
               'description': 'Coordinated multi-attack campaign',
               'parameters': ['vectors', 'duration', 'stagger_delay']
           }
       }
       return jsonify(attacks)
   
   @app.route('/api/attack/start', methods=['POST'])
   def start_attack():
       """Start DoS attack"""
       try:
           data = request.get_json()
           
           # Validate input
           if not data or 'target' not in data or 'attack_type' not in data:
               return jsonify({'error': 'Missing required parameters'}), 400
           
           target = data['target']
           attack_type = data['attack_type']
           
           # Validate target
           if not validate_target(target):
               return jsonify({'error': 'Invalid target'}), 400
           
           # Check if attack is already running
           if app.active_attacks:
               return jsonify({'error': 'Attack already in progress'}), 409
           
           # Prepare attack configuration
           attack_config = {
               'target': target,
               'attack_type': attack_type,
               'duration': data.get('duration', 60),
               'threads': data.get('threads', 10),
               'port': data.get('port', 80),
               'packet_size': data.get('packet_size', 1024),
               'rate': data.get('rate', 0),
               'profile': data.get('profile', 'moderate'),
               'dry_run': data.get('dry_run', False)
           }
           
           # Add attack-specific parameters
           if attack_type == 'udp_flood':
               attack_config['ports'] = data.get('ports', [53, 80, 123])
           elif attack_type == 'syn_flood':
               attack_config['spoof_ips'] = data.get('spoof_ips', True)
           elif attack_type == 'http_flood':
               attack_config['target_paths'] = data.get('target_paths', ['/'])
           elif attack_type == 'slowloris':
               attack_config['connections'] = data.get('connections', 200)
               attack_config['keep_alive_interval'] = data.get('keep_alive_interval', 15)
           elif attack_type == 'multi_vector':
               attack_config['vectors'] = data.get('vectors', ['icmp_flood', 'udp_flood'])
               attack_config['stagger_delay'] = data.get('stagger_delay', 30)
           
           # Validate attack parameters
           if not validate_attack_params(attack_config):
               return jsonify({'error': 'Invalid attack parameters'}), 400
           
           # Create engine and start attack in thread
           app.dos_engine = DoSEngine(app.config_data, app.logger_instance)
           
           attack_id = f"{attack_type}_{int(time.time())}"
           app.active_attacks[attack_id] = {
               'config': attack_config,
               'start_time': time.time(),
               'status': 'starting'
           }
           
           def run_attack():
               try:
                   app.active_attacks[attack_id]['status'] = 'running'
                   socketio.emit('attack_status', {
                       'attack_id': attack_id,
                       'status': 'running',
                       'message': f'Attack {attack_type} started'
                   })
                   
                   result = app.dos_engine.execute_attack(attack_type, attack_config)
                   
                   app.active_attacks[attack_id]['status'] = 'completed'
                   app.active_attacks[attack_id]['result'] = result
                   
                   socketio.emit('attack_completed', {
                       'attack_id': attack_id,
                       'result': result
                   })
                   
               except Exception as e:
                   app.active_attacks[attack_id]['status'] = 'failed'
                   app.active_attacks[attack_id]['error'] = str(e)
                   
                   socketio.emit('attack_failed', {
                       'attack_id': attack_id,
                       'error': str(e)
                   })
               finally:
                   # Clean up after delay
                   time.sleep(10)
                   if attack_id in app.active_attacks:
                       del app.active_attacks[attack_id]
           
           attack_thread = threading.Thread(target=run_attack)
           attack_thread.daemon = True
           attack_thread.start()
           
           return jsonify({
               'success': True,
               'attack_id': attack_id,
               'message': f'Attack {attack_type} started against {target}'
           })
           
       except Exception as e:
           app.logger_instance.error(f"Attack start failed: {e}")
           return jsonify({'error': str(e)}), 500
   
   @app.route('/api/attack/stop', methods=['POST'])
   def stop_attack():
       """Stop active attack"""
       try:
           data = request.get_json()
           attack_id = data.get('attack_id') if data else None
           
           if not attack_id or attack_id not in app.active_attacks:
               return jsonify({'error': 'No active attack found'}), 404
           
           # Stop the attack
           if app.dos_engine:
               app.dos_engine.stop_all_attacks()
           
           # Update status
           app.active_attacks[attack_id]['status'] = 'stopped'
           
           socketio.emit('attack_status', {
               'attack_id': attack_id,
               'status': 'stopped',
               'message': 'Attack stopped by user'
           })
           
           return jsonify({
               'success': True,
               'message': 'Attack stopped'
           })
           
       except Exception as e:
           return jsonify({'error': str(e)}), 500
   
   @app.route('/api/attack/status')
   def get_attack_status():
       """Get current attack status"""
       if not app.active_attacks:
           return jsonify({'active': False})
       
       status_data = {}
       for attack_id, attack_info in app.active_attacks.items():
           elapsed = time.time() - attack_info['start_time']
           
           status_data[attack_id] = {
               'config': attack_info['config'],
               'status': attack_info['status'],
               'elapsed_time': elapsed,
               'result': attack_info.get('result'),
               'error': attack_info.get('error')
           }
           
           # Get live stats if engine is available
           if app.dos_engine and attack_info['status'] == 'running':
               live_status = app.dos_engine.get_attack_status(attack_id)
               if live_status:
                   status_data[attack_id]['live_stats'] = live_status
       
       return jsonify({
           'active': True,
           'attacks': status_data
       })
   
   @app.route('/api/monitor/start', methods=['POST'])
   def start_monitoring():
       """Start monitoring"""
       try:
           data = request.get_json()
           target = data.get('target') if data else None
           
           if not target:
               return jsonify({'error': 'Target required'}), 400
           
           if not validate_target(target):
               return jsonify({'error': 'Invalid target'}), 400
           
           if app.monitor and app.monitor.monitoring:
               return jsonify({'error': 'Monitoring already active'}), 409
           
           # Start monitoring
           app.monitor = Monitor(target, app.logger_instance, app.config_data)
           app.monitor.start()
           
           return jsonify({
               'success': True,
               'message': f'Monitoring started for {target}'
           })
           
       except Exception as e:
           return jsonify({'error': str(e)}), 500
   
   @app.route('/api/monitor/stop', methods=['POST'])
   def stop_monitoring():
       """Stop monitoring"""
       try:
           if app.monitor:
               app.monitor.stop()
               app.monitor = None
           
           return jsonify({
               'success': True,
               'message': 'Monitoring stopped'
           })
           
       except Exception as e:
           return jsonify({'error': str(e)}), 500
   
   @app.route('/api/monitor/data')
   def get_monitor_data():
       """Get monitoring data"""
       if not app.monitor or not app.monitor.monitoring:
           return jsonify({'monitoring': False})
       
       try:
           # Get recent data (last 5 minutes)
           since = datetime.now() - timedelta(minutes=5)
           metrics = app.monitor.get_metrics(since=since)
           summary = app.monitor.get_summary()
           
           return jsonify({
               'monitoring': True,
               'summary': summary,
               'metrics': metrics
           })
           
       except Exception as e:
           return jsonify({'error': str(e)}), 500
   
   @app.route('/api/templates')
   def get_attack_templates():
       """Get attack templates"""
       try:
           templates_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'attacks.yaml')
           
           if os.path.exists(templates_file):
               import yaml
               with open(templates_file, 'r') as f:
                   templates = yaml.safe_load(f)
               return jsonify(templates.get('templates', {}))
           else:
               return jsonify({})
               
       except Exception as e:
           return jsonify({'error': str(e)}), 500
   
   @app.route('/api/system/info')
   def get_system_info():
       """Get system information"""
       try:
           import psutil
           import platform
           
           info = {
               'platform': platform.platform(),
               'python_version': platform.python_version(),
               'cpu_count': psutil.cpu_count(),
               'memory_total': psutil.virtual_memory().total,
               'disk_free': psutil.disk_usage('/').free,
               'network_interfaces': list(psutil.net_if_addrs().keys()),
               'framework_version': '2.0'
           }
           
           return jsonify(info)
           
       except Exception as e:
           return jsonify({'error': str(e)}), 500
   
   # WebSocket events
   @socketio.on('connect')
   def handle_connect():
       """Handle client connection"""
       emit('connected', {'message': 'Connected to DoS Master Framework'})
   
   @socketio.on('disconnect')
   def handle_disconnect():
       """Handle client disconnection"""
       pass
   
   @socketio.on('subscribe_monitoring')
   def handle_subscribe_monitoring():
       """Subscribe to monitoring updates"""
       def send_monitoring_updates():
           while app.monitor and app.monitor.monitoring:
               try:
                   summary = app.monitor.get_summary()
                   socketio.emit('monitoring_update', summary)
                   time.sleep(2)  # Update every 2 seconds
               except:
                   break
       
       if app.monitor and app.monitor.monitoring:
           monitor_thread = threading.Thread(target=send_monitoring_updates)
           monitor_thread.daemon = True
           monitor_thread.start()
   
   # Error handlers
   @app.errorhandler(404)
   def not_found(error):
       return render_template('error.html', 
                            error_code=404, 
                            error_message="Page not found"), 404
   
   @app.errorhandler(500)
   def internal_error(error):
       return render_template('error.html', 
                            error_code=500, 
                            error_message="Internal server error"), 500
   
   return app, socketio

# HTML Templates

# Base template (`templates/base.html`)
BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
   <meta charset="UTF-8">
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   <title>{% block title %}DoS Master Framework{% endblock %}</title>
   
   <!-- Bootstrap CSS -->
   <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
   
   <!-- Chart.js -->
   <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   
   <!-- Socket.IO -->
   <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
   
   <!-- Custom CSS -->
   <style>
       .navbar-brand {
           font-weight: bold;
       }
       .card {
           margin-bottom: 20px;
       }
       .status-indicator {
           width: 12px;
           height: 12px;
           border-radius: 50%;
           display: inline-block;
           margin-right: 8px;
       }
       .status-active { background-color: #28a745; }
       .status-inactive { background-color: #6c757d; }
       .status-warning { background-color: #ffc107; }
       .status-danger { background-color: #dc3545; }
       
       .metric-card {
           text-align: center;
           padding: 20px;
       }
       .metric-value {
           font-size: 2rem;
           font-weight: bold;
       }
       .metric-label {
           color: #6c757d;
           text-transform: uppercase;
           font-size: 0.8rem;
       }
       
       .log-container {
           height: 300px;
           overflow-y: auto;
           background-color: #f8f9fa;
           border: 1px solid #dee2e6;
           padding: 10px;
           font-family: monospace;
           font-size: 0.9rem;
       }
       
       .attack-form {
           background-color: #f8f9fa;
           padding: 20px;
           border-radius: 8px;
       }
       
       .legal-warning {
           background-color: #fff3cd;
           border: 1px solid #ffeaa7;
           border-radius: 8px;
           padding: 15px;
           margin-bottom: 20px;
       }
   </style>
</head>
<body>
   <!-- Navigation -->
   <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
       <div class="container">
           <a class="navbar-brand" href="{{ url_for('index') }}">
               🛡️ DoS Master Framework
           </a>
           
           <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
               <span class="navbar-toggler-icon"></span>
           </button>
           
           <div class="collapse navbar-collapse" id="navbarNav">
               <ul class="navbar-nav me-auto">
                   <li class="nav-item">
                       <a class="nav-link" href="{{ url_for('index') }}">Dashboard</a>
                   </li>
                   <li class="nav-item">
                       <a class="nav-link" href="{{ url_for('attack_page') }}">Attack</a>
                   </li>
                   <li class="nav-item">
                       <a class="nav-link" href="{{ url_for('monitor_page') }}">Monitor</a>
                   </li>
                   <li class="nav-item">
                       <a class="nav-link" href="{{ url_for('reports_page') }}">Reports</a>
                   </li>
               </ul>
               
               <span class="navbar-text">
                   <span id="status-indicator" class="status-indicator status-inactive"></span>
                   <span id="status-text">Ready</span>
               </span>
           </div>
       </div>
   </nav>

   <!-- Main Content -->
   <div class="container mt-4">
       {% block content %}{% endblock %}
   </div>

   <!-- Bootstrap JS -->
   <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
   
   <!-- Socket.IO Connection -->
   <script>
       const socket = io();
       
       socket.on('connect', function() {
           updateStatus('connected', 'Connected');
       });
       
       socket.on('disconnect', function() {
           updateStatus('inactive', 'Disconnected');
       });
       
       socket.on('attack_status', function(data) {
           updateStatus('warning', `Attack ${data.status}`);
           showNotification(data.message, 'info');
       });
       
       socket.on('attack_completed', function(data) {
           updateStatus('inactive', 'Ready');
           showNotification('Attack completed', 'success');
       });
       
       socket.on('attack_failed', function(data) {
           updateStatus('danger', 'Error');
           showNotification(`Attack failed: ${data.error}`, 'danger');
       });
       
       function updateStatus(status, text) {
           const indicator = document.getElementById('status-indicator');
           const statusText = document.getElementById('status-text');
           
           indicator.className = `status-indicator status-${status}`;
           statusText.textContent = text;
       }
       
       function showNotification(message, type) {
           // Create notification element
           const notification = document.createElement('div');
           notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
           notification.style.top = '20px';
           notification.style.right = '20px';
           notification.style.zIndex = '9999';
           notification.innerHTML = `
               ${message}
               <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
           `;
           
           document.body.appendChild(notification);
           
           // Auto remove after 5 seconds
           setTimeout(() => {
               notification.remove();
           }, 5000);
       }
   </script>
   
   {% block scripts %}{% endblock %}
</body>
</html>'''

# Dashboard template (`templates/index.html`)
DASHBOARD_TEMPLATE = '''{% extends "base.html" %}

{% block title %}Dashboard - DoS Master Framework{% endblock %}

{% block content %}
<div class="row">
   <div class="col-12">
       <h1>DoS Master Framework Dashboard</h1>
       
       <!-- Legal Warning -->
       <div class="legal-warning">
           <h5>⚠️ Legal Notice</h5>
           <p class="mb-0">
               This framework is designed for <strong>authorized security testing only</strong>. 
               Unauthorized use against systems you do not own is illegal and may result in 
               criminal prosecution. Always obtain written permission before testing any systems.
           </p>
       </div>
   </div>
</div>

<div class="row">
   <!-- System Status -->
   <div class="col-lg-3 col-md-6">
       <div class="card">
           <div class="card-body metric-card">
               <div class="metric-value text-primary" id="cpu-usage">--</div>
               <div class="metric-label">CPU Usage</div>
           </div>
       </div>
   </div>
   
   <div class="col-lg-3 col-md-6">
       <div class="card">
           <div class="card-body metric-card">
               <div class="metric-value text-success" id="memory-usage">--</div>
               <div class="metric-label">Memory Usage</div>
           </div>
       </div>
   </div>
   
   <div class="col-lg-3 col-md-6">
       <div class="card">
           <div class="card-body metric-card">
               <div class="metric-value text-info" id="network-traffic">--</div>
               <div class="metric-label">Network Traffic</div>
           </div>
       </div>
   </div>
   
   <div class="col-lg-3 col-md-6">
       <div class="card">
           <div class="card-body metric-card">
               <div class="metric-value text-warning" id="active-attacks">0</div>
               <div class="metric-label">Active Attacks</div>
           </div>
       </div>
   </div>
</div>

<div class="row">
   <!-- Quick Actions -->
   <div class="col-lg-6">
       <div class="card">
           <div class="card-header">
               <h5>Quick Actions</h5>
           </div>
           <div class="card-body">
               <div class="d-grid gap-2">
                   <a href="{{ url_for('attack_page') }}" class="btn btn-primary">
                       🚀 Launch Attack
                   </a>
                   <a href="{{ url_for('monitor_page') }}" class="btn btn-info">
                       📊 Start Monitoring
                   </a>
                   <a href="{{ url_for('reports_page') }}" class="btn btn-secondary">
                       📋 View Reports
                   </a>
               </div>
           </div>
       </div>
   </div>
   
   <!-- Recent Activity -->
   <div class="col-lg-6">
       <div class="card">
           <div class="card-header">
               <h5>Recent Activity</h5>
           </div>
           <div class="card-body">
               <div id="activity-log" class="log-container">
                   <div class="text-muted">No recent activity</div>
               </div>
           </div>
       </div>
   </div>
</div>

<div class="row">
   <!-- System Information -->
   <div class="col-12">
       <div class="card">
           <div class="card-header">
               <h5>System Information</h5>
           </div>
           <div class="card-body">
               <div class="row">
                   <div class="col-md-4">
                       <strong>Framework Version:</strong> <span id="framework-version">2.0</span>
                   </div>
                   <div class="col-md-4">
                       <strong>Platform:</strong> <span id="platform">--</span>
                   </div>
                   <div class="col-md-4">
                       <strong>Python Version:</strong> <span id="python-version">--</span>
                   </div>
               </div>
               <div class="row mt-2">
                   <div class="col-md-4">
                       <strong>CPU Cores:</strong> <span id="cpu-cores">--</span>
                   </div>
                   <div class="col-md-4">
                       <strong>Total Memory:</strong> <span id="total-memory">--</span>
                   </div>
                   <div class="col-md-4">
                       <strong>Free Disk:</strong> <span id="free-disk">--</span>
                   </div>
               </div>
           </div>
       </div>
   </div>
</div>
{% endblock %}

{% block scripts %}
<script>
   // Load system information
   function loadSystemInfo() {
       fetch('/api/system/info')
           .then(response => response.json())
           .then(data => {
               if (!data.error) {
                   document.getElementById('framework-version').textContent = data.framework_version;
                   document.getElementById('platform').textContent = data.platform;
                   document.getElementById('python-version').textContent = data.python_version;
                   document.getElementById('cpu-cores').textContent = data.cpu_count;
                   document.getElementById('total-memory').textContent = formatBytes(data.memory_total);
                   document.getElementById('free-disk').textContent = formatBytes(data.disk_free);
               }
           })
           .catch(error => console.error('Error loading system info:', error));
   }
   
   // Update dashboard metrics
   function updateMetrics() {
       // Update system metrics
       fetch('/api/monitor/data')
           .then(response => response.json())
           .then(data => {
               if (data.monitoring && data.summary && data.summary.current_metrics) {
                   const metrics = data.summary.current_metrics;
                   
                   if (metrics.system) {
                       document.getElementById('cpu-usage').textContent = 
                           metrics.system.cpu_percent ? `${metrics.system.cpu_percent.toFixed(1)}%` : '--';
                       document.getElementById('memory-usage').textContent = 
                           metrics.system.memory_percent ? `${metrics.system.memory_percent.toFixed(1)}%` : '--';
                   }
                   
                   if (metrics.network && metrics.network.bytes_recv_rate) {
                       const mbps = (metrics.network.bytes_recv_rate * 8) / (1024 * 1024);
                       document.getElementById('network-traffic').textContent = `${mbps.toFixed(1)} Mbps`;
                   }
               }
           })
           .catch(error => console.error('Error updating metrics:', error));
       
       // Update active attacks count
       fetch('/api/attack/status')
           .then(response => response.json())
           .then(data => {
               const count = data.active ? Object.keys(data.attacks).length : 0;
               document.getElementById('active-attacks').textContent = count;
           })
           .catch(error => console.error('Error updating attack status:', error));
   }
   
   // Utility function to format bytes
   function formatBytes(bytes) {
       if (bytes === 0) return '0 B';
       const k = 1024;
       const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
       const i = Math.floor(Math.log(bytes) / Math.log(k));
       return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
   }
   
   // Activity log
   function addActivity(message, type = 'info') {
       const log = document.getElementById('activity-log');
       const timestamp = new Date().toLocaleTimeString();
       const entry = document.createElement('div');
       entry.className = `text-${type}`;
       entry.innerHTML = `[${timestamp}] ${message}`;
       
       // Remove "No recent activity" message
       if (log.querySelector('.text-muted')) {
           log.innerHTML = '';
       }
       
       log.appendChild(entry);
       log.scrollTop = log.scrollHeight;
       
       // Keep only last 50 entries
       while (log.children.length > 50) {
           log.removeChild(log.firstChild);
       }
   }
   
   // Socket event handlers
   socket.on('attack_status', function(data) {
       addActivity(`Attack ${data.status}: ${data.message}`, 'warning');
   });
   
   socket.on('attack_completed', function(data) {
       addActivity('Attack completed successfully', 'success');
   });
   
   socket.on('attack_failed', function(data) {
       addActivity(`Attack failed: ${data.error}`, 'danger');
   });
   
   // Initialize dashboard
   document.addEventListener('DOMContentLoaded', function() {
       loadSystemInfo();
       updateMetrics();
       
       // Update metrics every 5 seconds
       setInterval(updateMetrics, 5000);
       
       addActivity('Dashboard loaded', 'success');
   });
</script>
{% endblock %}'''

if __name__ == '__main__':
   # Standalone web server
   config = load_config()
   app, socketio = create_app(config)
   
   host = config.get('web_interface', {}).get('host', '0.0.0.0')
   port = config.get('web_interface', {}).get('port', 8080)
   
   print(f"Starting DoS Master Framework Web Interface")
   print(f"Access at: http://localhost:{port}")
   print("Press Ctrl+C to stop")
   
   socketio.run(app, host=host, port=port, debug=False)