#!/usr/bin/env python3
"""
DoS Master Framework - Real-time Monitoring Module
Comprehensive attack monitoring and analysis
"""

import threading
import time
import psutil
import subprocess
import socket
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

class Monitor:
    """Real-time DoS attack monitoring system"""
    
    def __init__(self, target: str, logger, config: Dict = None):
        self.target = target
        self.logger = logger
        self.config = config or {}
        
        self.monitoring = False
        self.start_time = None
        self.monitor_thread = None
        
        # Monitoring data storage
        self.metrics = {
            'network': deque(maxlen=1000),
            'connections': deque(maxlen=1000),
            'system': deque(maxlen=1000),
            'response_times': deque(maxlen=1000),
            'errors': deque(maxlen=1000),
            'attacks_detected': deque(maxlen=100)
        }
        
        # Network interface tracking
        self.interface = self._detect_interface()
        self.baseline_metrics = {}
        
        # Alert thresholds
        self.thresholds = {
            'syn_recv_count': 100,
            'connection_rate': 500,
            'error_rate': 10,
            'response_time': 5.0,
            'cpu_usage': 80,
            'memory_usage': 85,
            'bandwidth_mbps': 100
        }
        
    def _detect_interface(self) -> str:
        """Detect primary network interface"""
        try:
            # Get default route interface
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'dev' in line:
                        parts = line.split()
                        dev_index = parts.index('dev')
                        if dev_index + 1 < len(parts):
                            return parts[dev_index + 1]
            
            # Fallback to first non-loopback interface
            interfaces = psutil.net_if_stats()
            for interface, stats in interfaces.items():
                if interface != 'lo' and stats.isup:
                    return interface
                    
            return 'eth0'  # Final fallback
            
        except Exception as e:
            self.logger.debug(f"Interface detection failed: {e}")
            return 'eth0'
    
    def start(self):
        """Start monitoring"""
        if self.monitoring:
            return
            
        self.logger.info(f"Starting monitoring for target {self.target}")
        self.monitoring = True
        self.start_time = time.time()
        
        # Establish baseline
        self._establish_baseline()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop(self):
        """Stop monitoring"""
        if not self.monitoring:
            return
            
        self.logger.info("Stopping monitoring")
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
    def _establish_baseline(self):
        """Establish baseline metrics"""
        self.logger.info("Establishing baseline metrics...")
        
        baseline_samples = []
        for _ in range(10):
            sample = {
                'network': self._get_network_stats(),
                'connections': self._get_connection_stats(),
                'system': self._get_system_stats(),
                'response_time': self._test_response_time()
            }
            baseline_samples.append(sample)
            time.sleep(1)
        
        # Calculate baseline averages
        self.baseline_metrics = self._calculate_baseline_averages(baseline_samples)
        self.logger.info("Baseline metrics established")
        
    def _calculate_baseline_averages(self, samples: List[Dict]) -> Dict:
        """Calculate average baseline metrics"""
        baseline = {}
        
        # Network metrics
        network_metrics = [s['network'] for s in samples if s['network']]
        if network_metrics:
            baseline['bytes_recv_rate'] = sum(m.get('bytes_recv_rate', 0) for m in network_metrics) / len(network_metrics)
            baseline['packets_recv_rate'] = sum(m.get('packets_recv_rate', 0) for m in network_metrics) / len(network_metrics)
        
        # Connection metrics
        conn_metrics = [s['connections'] for s in samples if s['connections']]
        if conn_metrics:
            baseline['established_connections'] = sum(m.get('established', 0) for m in conn_metrics) / len(conn_metrics)
            baseline['total_connections'] = sum(m.get('total', 0) for m in conn_metrics) / len(conn_metrics)
        
        # System metrics
        system_metrics = [s['system'] for s in samples if s['system']]
        if system_metrics:
            baseline['cpu_usage'] = sum(m.get('cpu_percent', 0) for m in system_metrics) / len(system_metrics)
            baseline['memory_usage'] = sum(m.get('memory_percent', 0) for m in system_metrics) / len(system_metrics)
        
        # Response time
        response_times = [s['response_time'] for s in samples if s['response_time'] is not None]
        if response_times:
            baseline['response_time'] = sum(response_times) / len(response_times)
        
        return baseline
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        last_network_stats = None
        
        while self.monitoring:
            try:
                timestamp = datetime.now()
                
                # Collect metrics
                network_stats = self._get_network_stats()
                connection_stats = self._get_connection_stats()
                system_stats = self._get_system_stats()
                response_time = self._test_response_time()
                
                # Calculate rates for network stats
                if last_network_stats and network_stats:
                    time_delta = 5.0  # 5 second monitoring interval
                    network_stats['bytes_recv_rate'] = (network_stats['bytes_recv'] - last_network_stats['bytes_recv']) / time_delta
                    network_stats['packets_recv_rate'] = (network_stats['packets_recv'] - last_network_stats['packets_recv']) / time_delta
                
                # Store metrics with timestamps
                self.metrics['network'].append({
                    'timestamp': timestamp,
                    'data': network_stats
                })
                
                self.metrics['connections'].append({
                    'timestamp': timestamp,
                    'data': connection_stats
                })
                
                self.metrics['system'].append({
                    'timestamp': timestamp,
                    'data': system_stats
                })
                
                if response_time is not None:
                    self.metrics['response_times'].append({
                        'timestamp': timestamp,
                        'data': response_time
                    })
                
                # Detect anomalies and attacks
                alerts = self._detect_anomalies(network_stats, connection_stats, system_stats, response_time)
                for alert in alerts:
                    self.metrics['attacks_detected'].append({
                        'timestamp': timestamp,
                        'alert': alert
                    })
                    self.logger.warning(f"ALERT: {alert}")
                
                # Log status
                self._log_status(network_stats, connection_stats, system_stats, response_time)
                
                last_network_stats = network_stats
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                self.metrics['errors'].append({
                    'timestamp': timestamp,
                    'error': str(e)
                })
            
            time.sleep(5)  # 5-second monitoring interval
    
    def _get_network_stats(self) -> Optional[Dict]:
        """Get network interface statistics"""
        try:
            net_io = psutil.net_io_counters(pernic=True)
            if self.interface in net_io:
                stats = net_io[self.interface]
                return {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv,
                    'errin': stats.errin,
                    'errout': stats.errout,
                    'dropin': stats.dropin,
                    'dropout': stats.dropout
                }
            return None
        except Exception as e:
            self.logger.debug(f"Network stats error: {e}")
            return None
    
    def _get_connection_stats(self) -> Optional[Dict]:
        """Get connection statistics"""
        try:
            # Use ss command for detailed connection stats
            result = subprocess.run(['ss', '-tan'], capture_output=True, text=True)
            if result.returncode != 0:
                return None
                
            lines = result.stdout.split('\n')
            
            stats = {
                'established': 0,
                'syn_recv': 0,
                'time_wait': 0,
                'close_wait': 0,
                'fin_wait': 0,
                'total': 0,
                'port_80_connections': 0,
                'port_443_connections': 0
            }
            
            for line in lines:
                if not line.strip() or line.startswith('State'):
                    continue
                    
                parts = line.split()
                if len(parts) < 2:
                    continue
                    
                state = parts[0]
                local_addr = parts[3] if len(parts) > 3 else ""
                
                stats['total'] += 1
                
                # Count by connection state
                if state == 'ESTAB':
                    stats['established'] += 1
                elif state == 'SYN-RECV':
                    stats['syn_recv'] += 1
                elif state == 'TIME-WAIT':
                    stats['time_wait'] += 1
                elif state == 'CLOSE-WAIT':
                    stats['close_wait'] += 1
                elif 'FIN-WAIT' in state:
                    stats['fin_wait'] += 1
                
                # Count by port
                if ':80' in local_addr:
                    stats['port_80_connections'] += 1
                elif ':443' in local_addr:
                    stats['port_443_connections'] += 1
            
            return stats
            
        except Exception as e:
            self.logger.debug(f"Connection stats error: {e}")
            return None
    
    def _get_system_stats(self) -> Optional[Dict]:
        """Get system resource statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Load average
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                # getloadavg not available on all platforms
                load_avg = (0, 0, 0)
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'memory_used': memory.used,
                'load_avg_1min': load_avg[0],
                'load_avg_5min': load_avg[1],
                'load_avg_15min': load_avg[2],
                'disk_read_bytes': disk_io.read_bytes if disk_io else 0,
                'disk_write_bytes': disk_io.write_bytes if disk_io else 0
            }
            
        except Exception as e:
            self.logger.debug(f"System stats error: {e}")
            return None
    
    def _test_response_time(self) -> Optional[float]:
        """Test response time to target"""
        try:
            # Parse target to determine test method
            if self.target.startswith('http'):
                return self._test_http_response_time()
            else:
                return self._test_ping_response_time()
                
        except Exception as e:
            self.logger.debug(f"Response time test error: {e}")
            return None
    
    def _test_http_response_time(self) -> Optional[float]:
        """Test HTTP response time"""
        try:
            import requests
            start_time = time.time()
            response = requests.get(self.target, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                return end_time - start_time
            else:
                return None
                
        except Exception:
            return None
    
    def _test_ping_response_time(self) -> Optional[float]:
        """Test ping response time"""
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '5', self.target], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse ping output for response time
                for line in result.stdout.split('\n'):
                    if 'time=' in line:
                        time_part = line.split('time=')[1].split()[0]
                        return float(time_part) / 1000.0  # Convert ms to seconds
            
            return None
            
        except Exception:
            return None
    
    def _detect_anomalies(self, network_stats: Dict, connection_stats: Dict, 
                         system_stats: Dict, response_time: float) -> List[str]:
        """Detect attack patterns and anomalies"""
        alerts = []
        
        if not network_stats or not connection_stats or not system_stats:
            return alerts
        
        # SYN flood detection
        syn_recv_count = connection_stats.get('syn_recv', 0)
        if syn_recv_count > self.thresholds['syn_recv_count']:
            alerts.append(f"SYN flood detected: {syn_recv_count} SYN_RECV connections")
        
        # Connection rate anomaly
        total_connections = connection_stats.get('total', 0)
        baseline_connections = self.baseline_metrics.get('total_connections', 0)
        if baseline_connections > 0 and total_connections > baseline_connections * 3:
            alerts.append(f"High connection rate: {total_connections} (baseline: {baseline_connections:.0f})")
        
        # Response time degradation
        if response_time and response_time > self.thresholds['response_time']:
            baseline_rt = self.baseline_metrics.get('response_time', 1.0)
            if response_time > baseline_rt * 5:
                alerts.append(f"Severe response time degradation: {response_time:.2f}s (baseline: {baseline_rt:.2f}s)")
        
        # System resource exhaustion
        cpu_usage = system_stats.get('cpu_percent', 0)
        if cpu_usage > self.thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {cpu_usage:.1f}%")
        
        memory_usage = system_stats.get('memory_percent', 0)
        if memory_usage > self.thresholds['memory_usage']:
            alerts.append(f"High memory usage: {memory_usage:.1f}%")
        
        # Network bandwidth anomaly
        if 'bytes_recv_rate' in network_stats:
            bandwidth_mbps = (network_stats['bytes_recv_rate'] * 8) / (1024 * 1024)
            if bandwidth_mbps > self.thresholds['bandwidth_mbps']:
                alerts.append(f"High incoming bandwidth: {bandwidth_mbps:.1f} Mbps")
        
        # Connection state anomalies
        time_wait_count = connection_stats.get('time_wait', 0)
        if time_wait_count > 1000:
            alerts.append(f"High TIME_WAIT connections: {time_wait_count}")
        
        return alerts
    
    def _log_status(self, network_stats: Dict, connection_stats: Dict, 
                   system_stats: Dict, response_time: float):
        """Log current monitoring status"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        # Network info
        net_info = ""
        if network_stats and 'bytes_recv_rate' in network_stats:
            bandwidth_mbps = (network_stats['bytes_recv_rate'] * 8) / (1024 * 1024)
            packet_rate = network_stats.get('packets_recv_rate', 0)
            net_info = f"BW: {bandwidth_mbps:.1f}Mbps, PPS: {packet_rate:.0f}"
        
        # Connection info
        conn_info = ""
        if connection_stats:
            estab = connection_stats.get('established', 0)
            syn_recv = connection_stats.get('syn_recv', 0)
            conn_info = f"Conn: {estab} estab, {syn_recv} syn_recv"
        
        # System info
        sys_info = ""
        if system_stats:
            cpu = system_stats.get('cpu_percent', 0)
            mem = system_stats.get('memory_percent', 0)
            sys_info = f"CPU: {cpu:.1f}%, Mem: {mem:.1f}%"
        
        # Response time info
        rt_info = f"RT: {response_time:.3f}s" if response_time else "RT: N/A"
        
        self.logger.info(f"Monitor [{elapsed:.0f}s]: {net_info} | {conn_info} | {sys_info} | {rt_info}")
    
    def get_metrics(self, metric_type: str = None, since: datetime = None) -> Dict:
        """Get monitoring metrics"""
        if metric_type and metric_type in self.metrics:
            data = list(self.metrics[metric_type])
        else:
            data = {k: list(v) for k, v in self.metrics.items()}
        
        # Filter by time if specified
        if since:
            if metric_type:
                data = [item for item in data if item['timestamp'] >= since]
            else:
                for key in data:
                    data[key] = [item for item in data[key] if item['timestamp'] >= since]
        
        return data
    
    def get_summary(self) -> Dict:
        """Get monitoring summary"""
        current_time = datetime.now()
        elapsed = (current_time - datetime.fromtimestamp(self.start_time)).total_seconds() if self.start_time else 0
        
        # Get latest metrics
        latest_network = self.metrics['network'][-1]['data'] if self.metrics['network'] else {}
        latest_connections = self.metrics['connections'][-1]['data'] if self.metrics['connections'] else {}
        latest_system = self.metrics['system'][-1]['data'] if self.metrics['system'] else {}
        latest_response = self.metrics['response_times'][-1]['data'] if self.metrics['response_times'] else None
        
        # Count alerts
        recent_alerts = [alert for alert in self.metrics['attacks_detected'] 
                        if (current_time - alert['timestamp']).total_seconds() < 300]  # Last 5 minutes
        
        return {
            'monitoring_duration': elapsed,
            'target': self.target,
            'interface': self.interface,
            'baseline_metrics': self.baseline_metrics,
            'current_metrics': {
                'network': latest_network,
                'connections': latest_connections,
                'system': latest_system,
                'response_time': latest_response
            },
            'recent_alerts': len(recent_alerts),
            'total_data_points': {
                'network': len(self.metrics['network']),
                'connections': len(self.metrics['connections']),
                'system': len(self.metrics['system']),
                'response_times': len(self.metrics['response_times'])
            }
        }
    
    def export_data(self, filename: str, format: str = 'json'):
        """Export monitoring data"""
        data = {
            'target': self.target,
            'start_time': self.start_time,
            'baseline_metrics': self.baseline_metrics,
            'metrics': {k: list(v) for k, v in self.metrics.items()},
            'export_time': datetime.now().isoformat()
        }
        
        if format.lower() == 'json':
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        self.logger.info(f"Monitoring data exported to {filename}")