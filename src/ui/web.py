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