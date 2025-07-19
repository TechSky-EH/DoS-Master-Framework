#!/usr/bin/env python3
"""
DoS Master Framework - Traffic Analysis Module
Advanced packet analysis and pattern detection
"""

import subprocess
import threading
import time
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

class TrafficAnalyzer:
    """Advanced traffic analysis and pattern detection"""
    
    def __init__(self, logger, interface: str = 'eth0'):
        self.logger = logger
        self.interface = interface
        self.capture_active = False
        self.capture_process = None
        self.capture_file = None
        
        # Analysis data
        self.packet_stats = defaultdict(int)
        self.protocol_stats = defaultdict(int)
        self.source_ips = Counter()
        self.destination_ports = Counter()
        self.packet_sizes = []
        self.timestamps = []
        
        # Attack detection patterns
        self.attack_signatures = {
            'syn_flood': {
                'tcp_syn_ratio': 0.8,  # >80% SYN packets
                'unique_sources': 100,  # Many different source IPs
                'packet_rate': 1000     # High packet rate
            },
            'udp_flood': {
                'udp_ratio': 0.9,      # >90% UDP packets
                'packet_rate': 500,     # High packet rate
                'port_concentration': 0.8  # Concentrated on few ports
            },
            'icmp_flood': {
                'icmp_ratio': 0.8,     # >80% ICMP packets
                'packet_rate': 500,     # High packet rate
                'payload_size': 1000    # Large payloads
            }
        }
    
    def start_capture(self, capture_file: Optional[str] = None, duration: int = 0):
        """Start packet capture"""
        if self.capture_active:
            self.logger.warning("Packet capture already active")
            return False
        
        if not capture_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            capture_file = f"traffic_capture_{timestamp}.pcap"
        
        self.capture_file = capture_file
        
        try:
            # Build tcpdump command
            cmd = [
                'tcpdump',
                '-i', self.interface,
                '-w', capture_file,
                '-s', '65535',  # Capture full packets
                '-n'            # Don't resolve hostnames
            ]
            
            if duration > 0:
                cmd.extend(['-G', str(duration), '-W', '1'])
            
            self.logger.info(f"Starting packet capture on {self.interface}")
            self.logger.info(f"Capture file: {capture_file}")
            
            # Start tcpdump process
            self.capture_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            self.capture_active = True
            
            # Start analysis thread
            if duration == 0:  # Continuous capture
                analysis_thread = threading.Thread(target=self._continuous_analysis)
                analysis_thread.daemon = True
                analysis_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start packet capture: {e}")
            return False
    
    def stop_capture(self):
        """Stop packet capture"""
        if not self.capture_active:
            return
        
        self.capture_active = False
        
        if self.capture_process:
            try:
                self.capture_process.terminate()
                self.capture_process.wait(timeout=5)
                self.logger.info("Packet capture stopped")
            except subprocess.TimeoutExpired:
                self.capture_process.kill()
                self.logger.warning("Forced termination of packet capture")
            except Exception as e:
                self.logger.error(f"Error stopping capture: {e}")
    
    def analyze_pcap_file(self, pcap_file: str) -> Dict[str, Any]:
        """Analyze existing PCAP file"""
        if not os.path.exists(pcap_file):
            self.logger.error(f"PCAP file not found: {pcap_file}")
            return {}
        
        self.logger.info(f"Analyzing PCAP file: {pcap_file}")
        
        try:
            # Use tshark for detailed analysis
            analysis_results = {}
            
            # Basic statistics
            analysis_results['basic_stats'] = self._get_basic_stats(pcap_file)
            
            # Protocol distribution
            analysis_results['protocol_stats'] = self._get_protocol_stats(pcap_file)
            
            # Top talkers
            analysis_results['top_sources'] = self._get_top_sources(pcap_file)
            analysis_results['top_destinations'] = self._get_top_destinations(pcap_file)
            
            # Port analysis
            analysis_results['port_stats'] = self._get_port_stats(pcap_file)
            
            # Packet size distribution
            analysis_results['packet_sizes'] = self._get_packet_size_stats(pcap_file)
            
            # Time-based analysis
            analysis_results['time_analysis'] = self._get_time_analysis(pcap_file)
            
            # Attack detection
            analysis_results['attack_detection'] = self._detect_attacks(analysis_results)
            
            # Anomaly detection
            analysis_results['anomalies'] = self._detect_anomalies(analysis_results)
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"PCAP analysis failed: {e}")
            return {}
    
    def _get_basic_stats(self, pcap_file: str) -> Dict[str, Any]:
        """Get basic packet statistics"""
        try:
            # Get packet count
            result = subprocess.run([
                'tshark', '-r', pcap_file, '-q', '-z', 'io,stat,0'
            ], capture_output=True, text=True, timeout=30)
            
            stats = {'total_packets': 0, 'total_bytes': 0, 'duration': 0}
            
            for line in result.stdout.split('\n'):
                if 'Packets' in line and 'Bytes' in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        stats['total_packets'] = int(parts[1])
                        stats['total_bytes'] = int(parts[3])
                elif 'Duration:' in line:
                    duration_str = line.split('Duration:')[1].strip()
                    # Parse duration (format: "XX.XXX seconds")
                    if 'seconds' in duration_str:
                        stats['duration'] = float(duration_str.split()[0])
            
            # Calculate rates
            if stats['duration'] > 0:
                stats['packets_per_second'] = stats['total_packets'] / stats['duration']
                stats['bytes_per_second'] = stats['total_bytes'] / stats['duration']
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get basic stats: {e}")
            return {}
    
    def _get_protocol_stats(self, pcap_file: str) -> Dict[str, int]:
        """Get protocol distribution"""
        try:
            result = subprocess.run([
                'tshark', '-r', pcap_file, '-q', '-z', 'prot,stat'
            ], capture_output=True, text=True, timeout=30)
            
            protocol_stats = {}
            
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('=') and 'Protocol' not in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        protocol = parts[0]
                        count = int(parts[2])
                        protocol_stats[protocol] = count
            
            return protocol_stats
            
        except Exception as e:
            self.logger.error(f"Failed to get protocol stats: {e}")
            return {}
    
    def _get_top_sources(self, pcap_file: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top source IP addresses"""
        try:
            result = subprocess.run([
                'tshark', '-r', pcap_file, '-T', 'fields', '-e', 'ip.src'
            ], capture_output=True, text=True, timeout=30)
            
            source_counter = Counter()
            for line in result.stdout.split('\n'):
                if line.strip():
                    source_counter[line.strip()] += 1
            
            top_sources = []
            for ip, count in source_counter.most_common(top_n):
                top_sources.append({'ip': ip, 'packet_count': count})
            
            return top_sources
            
        except Exception as e:
            self.logger.error(f"Failed to get top sources: {e}")
            return []
    
    def _get_top_destinations(self, pcap_file: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top destination IP addresses"""
        try:
            result = subprocess.run([
                'tshark', '-r', pcap_file, '-T', 'fields', '-e', 'ip.dst'
            ], capture_output=True, text=True, timeout=30)
            
            dest_counter = Counter()
            for line in result.stdout.split('\n'):
                if line.strip():
                    dest_counter[line.strip()] += 1
            
            top_destinations = []
            for ip, count in dest_counter.most_common(top_n):
                top_destinations.append({'ip': ip, 'packet_count': count})
            
            return top_destinations
            
        except Exception as e:
            self.logger.error(f"Failed to get top destinations: {e}")
            return []
    
    def _get_port_stats(self, pcap_file: str) -> Dict[str, Any]:
        """Get port statistics"""
        try:
            # TCP ports
            tcp_result = subprocess.run([
                'tshark', '-r', pcap_file, '-T', 'fields', '-e', 'tcp.dstport'
            ], capture_output=True, text=True, timeout=30)
            
            tcp_ports = Counter()
            for line in tcp_result.stdout.split('\n'):
                if line.strip() and line.strip().isdigit():
                    tcp_ports[int(line.strip())] += 1
            
            # UDP ports
            udp_result = subprocess.run([
                'tshark', '-r', pcap_file, '-T', 'fields', '-e', 'udp.dstport'
            ], capture_output=True, text=True, timeout=30)
            
            udp_ports = Counter()
            for line in udp_result.stdout.split('\n'):
                if line.strip() and line.strip().isdigit():
                    udp_ports[int(line.strip())] += 1
            
            return {
                'tcp_ports': dict(tcp_ports.most_common(10)),
                'udp_ports': dict(udp_ports.most_common(10))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get port stats: {e}")
            return {}
    
    def _get_packet_size_stats(self, pcap_file: str) -> Dict[str, Any]:
        """Get packet size distribution"""
        try:
            result = subprocess.run([
                'tshark', '-r', pcap_file, '-T', 'fields', '-e', 'frame.len'
            ], capture_output=True, text=True, timeout=30)
            
            packet_sizes = []
            for line in result.stdout.split('\n'):
                if line.strip() and line.strip().isdigit():
                    packet_sizes.append(int(line.strip()))
            
            if packet_sizes:
                stats = {
                    'min_size': min(packet_sizes),
                    'max_size': max(packet_sizes),
                    'avg_size': sum(packet_sizes) / len(packet_sizes),
                    'total_packets': len(packet_sizes)
                }
                
                # Size distribution
                size_ranges = {
                    '0-64': 0, '65-128': 0, '129-256': 0, '257-512': 0,
                    '513-1024': 0, '1025-1500': 0, '1501+': 0
                }
                
                for size in packet_sizes:
                    if size <= 64:
                        size_ranges['0-64'] += 1
                    elif size <= 128:
                        size_ranges['65-128'] += 1
                    elif size <= 256:
                        size_ranges['129-256'] += 1
                    elif size <= 512:
                        size_ranges['257-512'] += 1
                    elif size <= 1024:
                        size_ranges['513-1024'] += 1
                    elif size <= 1500:
                        size_ranges['1025-1500'] += 1
                    else:
                        size_ranges['1501+'] += 1
                
                stats['size_distribution'] = size_ranges
                return stats
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get packet size stats: {e}")
            return {}
    
    def _get_time_analysis(self, pcap_file: str) -> Dict[str, Any]:
        """Get time-based analysis"""
        try:
            result = subprocess.run([
                'tshark', '-r', pcap_file, '-T', 'fields', '-e', 'frame.time_epoch'
            ], capture_output=True, text=True, timeout=30)
            
            timestamps = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        timestamps.append(float(line.strip()))
                    except ValueError:
                        continue
            
            if len(timestamps) < 2:
                return {}
            
            timestamps.sort()
            
            # Calculate intervals
            intervals = []
            for i in range(1, len(timestamps)):
                intervals.append(timestamps[i] - timestamps[i-1])
            
            # Time-based statistics
            total_duration = timestamps[-1] - timestamps[0]
            
            # Detect burst patterns
            short_intervals = [i for i in intervals if i < 0.001]  # < 1ms
            burst_ratio = len(short_intervals) / len(intervals) if intervals else 0
            
            return {
                'start_time': timestamps[0],
                'end_time': timestamps[-1],
                'total_duration': total_duration,
                'avg_interval': sum(intervals) / len(intervals) if intervals else 0,
                'min_interval': min(intervals) if intervals else 0,
                'max_interval': max(intervals) if intervals else 0,
                'burst_ratio': burst_ratio
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get time analysis: {e}")
            return {}
    
    def _detect_attacks(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential DoS/DDoS attacks"""
        detected_attacks = {}
        
        basic_stats = analysis_results.get('basic_stats', {})
        protocol_stats = analysis_results.get('protocol_stats', {})
        time_analysis = analysis_results.get('time_analysis', {})
        
        total_packets = basic_stats.get('total_packets', 0)
        packet_rate = basic_stats.get('packets_per_second', 0)
        
        if total_packets == 0:
            return detected_attacks
        
        # Calculate protocol ratios
        tcp_packets = protocol_stats.get('TCP', 0)
        udp_packets = protocol_stats.get('UDP', 0)
        icmp_packets = protocol_stats.get('ICMP', 0)
        
        tcp_ratio = tcp_packets / total_packets
        udp_ratio = udp_packets / total_packets
        icmp_ratio = icmp_packets / total_packets
        
        # SYN flood detection
        if (tcp_ratio > self.attack_signatures['syn_flood']['tcp_syn_ratio'] and
            packet_rate > self.attack_signatures['syn_flood']['packet_rate']):
            detected_attacks['syn_flood'] = {
                'confidence': 0.8,
                'indicators': [
                    f'High TCP ratio: {tcp_ratio:.2f}',
                    f'High packet rate: {packet_rate:.0f} pps'
                ]
            }
        
        # UDP flood detection
        if (udp_ratio > self.attack_signatures['udp_flood']['udp_ratio'] and
            packet_rate > self.attack_signatures['udp_flood']['packet_rate']):
            detected_attacks['udp_flood'] = {
                'confidence': 0.9,
                'indicators': [
                    f'High UDP ratio: {udp_ratio:.2f}',
                    f'High packet rate: {packet_rate:.0f} pps'
                ]
            }
        
        # ICMP flood detection
        if (icmp_ratio > self.attack_signatures['icmp_flood']['icmp_ratio'] and
            packet_rate > self.attack_signatures['icmp_flood']['packet_rate']):
            detected_attacks['icmp_flood'] = {
                'confidence': 0.85,
                'indicators': [
                    f'High ICMP ratio: {icmp_ratio:.2f}',
                    f'High packet rate: {packet_rate:.0f} pps'
                ]
            }
        
        # Burst pattern detection
        burst_ratio = time_analysis.get('burst_ratio', 0)
        if burst_ratio > 0.5:
            detected_attacks['burst_attack'] = {
                'confidence': 0.7,
                'indicators': [
                    f'High burst ratio: {burst_ratio:.2f}',
                    'Packet timing suggests automated tool'
                ]
            }
        
        return detected_attacks
    
    def _detect_anomalies(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect traffic anomalies"""
        anomalies = []
        
        basic_stats = analysis_results.get('basic_stats', {})
        packet_sizes = analysis_results.get('packet_sizes', {})
        
        # High packet rate anomaly
        packet_rate = basic_stats.get('packets_per_second', 0)
        if packet_rate > 10000:
            anomalies.append({
                'type': 'high_packet_rate',
                'severity': 'high',
                'description': f'Extremely high packet rate: {packet_rate:.0f} pps',
                'threshold': 10000
            })
        elif packet_rate > 1000:
            anomalies.append({
                'type': 'elevated_packet_rate',
                'severity': 'medium',
                'description': f'Elevated packet rate: {packet_rate:.0f} pps',
                'threshold': 1000
            })
        
        # Unusual packet sizes
        avg_size = packet_sizes.get('avg_size', 0)
        if avg_size < 50:
            anomalies.append({
                'type': 'small_packets',
                'severity': 'medium',
                'description': f'Unusually small average packet size: {avg_size:.0f} bytes',
                'threshold': 50
            })
        elif avg_size > 1400:
            anomalies.append({
                'type': 'large_packets',
                'severity': 'medium',
                'description': f'Unusually large average packet size: {avg_size:.0f} bytes',
                'threshold': 1400
            })
        
        return anomalies
    
    def _continuous_analysis(self):
        """Continuous analysis during live capture"""
        self.logger.info("Starting continuous traffic analysis")
        
        while self.capture_active:
            try:
                if self.capture_file and os.path.exists(self.capture_file):
                    # Quick analysis of current capture
                    results = self._get_basic_stats(self.capture_file)
                    
                    if results:
                        packet_rate = results.get('packets_per_second', 0)
                        
                        if packet_rate > 1000:
                            self.logger.warning(f"High packet rate detected: {packet_rate:.0f} pps")
                        
                        # Check for attack patterns every 30 seconds
                        if int(time.time()) % 30 == 0:
                           full_analysis = self.analyze_pcap_file(self.capture_file)
                           attacks = full_analysis.get('attack_detection', {})
                           
                           if attacks:
                               self.logger.warning(f"Potential attacks detected: {list(attacks.keys())}")
               
               time.sleep(5)  # Analyze every 5 seconds
               
           except Exception as e:
               self.logger.error(f"Continuous analysis error: {e}")
               time.sleep(10)
   
   def export_analysis(self, analysis_results: Dict[str, Any], export_file: str):
       """Export analysis results to file"""
       try:
           # Add metadata
           export_data = {
               'analysis_timestamp': datetime.now().isoformat(),
               'analyzer_version': '2.0',
               'interface': self.interface,
               'results': analysis_results
           }
           
           with open(export_file, 'w') as f:
               json.dump(export_data, f, indent=2, default=str)
           
           self.logger.info(f"Analysis results exported to {export_file}")
           
       except Exception as e:
           self.logger.error(f"Failed to export analysis: {e}")
   
   def generate_summary_report(self, analysis_results: Dict[str, Any]) -> str:
       """Generate human-readable summary report"""
       try:
           report_lines = []
           report_lines.append("=" * 60)
           report_lines.append("TRAFFIC ANALYSIS SUMMARY REPORT")
           report_lines.append("=" * 60)
           report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
           report_lines.append("")
           
           # Basic statistics
           basic_stats = analysis_results.get('basic_stats', {})
           if basic_stats:
               report_lines.append("BASIC STATISTICS:")
               report_lines.append(f"  Total Packets: {basic_stats.get('total_packets', 0):,}")
               report_lines.append(f"  Total Bytes: {basic_stats.get('total_bytes', 0):,}")
               report_lines.append(f"  Duration: {basic_stats.get('duration', 0):.2f} seconds")
               report_lines.append(f"  Packet Rate: {basic_stats.get('packets_per_second', 0):.0f} pps")
               report_lines.append(f"  Bandwidth: {basic_stats.get('bytes_per_second', 0) * 8 / 1024 / 1024:.2f} Mbps")
               report_lines.append("")
           
           # Protocol distribution
           protocol_stats = analysis_results.get('protocol_stats', {})
           if protocol_stats:
               report_lines.append("PROTOCOL DISTRIBUTION:")
               total_packets = sum(protocol_stats.values())
               for protocol, count in sorted(protocol_stats.items(), key=lambda x: x[1], reverse=True):
                   percentage = (count / total_packets) * 100 if total_packets > 0 else 0
                   report_lines.append(f"  {protocol}: {count:,} packets ({percentage:.1f}%)")
               report_lines.append("")
           
           # Top sources
           top_sources = analysis_results.get('top_sources', [])
           if top_sources:
               report_lines.append("TOP SOURCE IPs:")
               for source in top_sources[:5]:
                   report_lines.append(f"  {source['ip']}: {source['packet_count']:,} packets")
               report_lines.append("")
           
           # Attack detection
           attacks = analysis_results.get('attack_detection', {})
           if attacks:
               report_lines.append("DETECTED ATTACKS:")
               for attack_type, details in attacks.items():
                   confidence = details.get('confidence', 0) * 100
                   report_lines.append(f"  {attack_type.upper()}: {confidence:.0f}% confidence")
                   for indicator in details.get('indicators', []):
                       report_lines.append(f"    - {indicator}")
               report_lines.append("")
           
           # Anomalies
           anomalies = analysis_results.get('anomalies', [])
           if anomalies:
               report_lines.append("DETECTED ANOMALIES:")
               for anomaly in anomalies:
                   severity = anomaly.get('severity', 'unknown').upper()
                   description = anomaly.get('description', 'No description')
                   report_lines.append(f"  [{severity}] {description}")
               report_lines.append("")
           
           report_lines.append("=" * 60)
           
           return "\n".join(report_lines)
           
       except Exception as e:
           self.logger.error(f"Failed to generate summary report: {e}")
           return "Error generating report"
   
   def cleanup(self):
       """Cleanup resources"""
       self.stop_capture()
       
       # Clear analysis data
       self.packet_stats.clear()
       self.protocol_stats.clear()
       self.source_ips.clear()
       self.destination_ports.clear()
       self.packet_sizes.clear()
       self.timestamps.clear()