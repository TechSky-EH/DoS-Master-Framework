#!/usr/bin/env python3
"""
DoS Master Framework - Attack Modules
Implementation of various DoS attack types
"""

# Attack registry for dynamic loading
ATTACK_REGISTRY = {}

try:
    from .icmp_flood import ICMPFlood
    ATTACK_REGISTRY['icmp_flood'] = ICMPFlood
except ImportError:
    pass

try:
    from .udp_flood import UDPFlood
    ATTACK_REGISTRY['udp_flood'] = UDPFlood
except ImportError:
    pass

try:
    from .syn_flood import SYNFlood
    ATTACK_REGISTRY['syn_flood'] = SYNFlood
except ImportError:
    pass

try:
    from .http_flood import HTTPFlood
    ATTACK_REGISTRY['http_flood'] = HTTPFlood
except ImportError:
    pass

try:
    from .slowloris import Slowloris
    ATTACK_REGISTRY['slowloris'] = Slowloris
except ImportError:
    pass

try:
    from .amplification import AmplificationAttack
    ATTACK_REGISTRY['amplification'] = AmplificationAttack
except ImportError:
    pass

def get_attack_class(attack_type: str):
    """Get attack class by type name"""
    return ATTACK_REGISTRY.get(attack_type)

def list_available_attacks():
    """List all available attack types"""
    return list(ATTACK_REGISTRY.keys())

def register_attack(name: str, attack_class):
    """Register a new attack type"""
    ATTACK_REGISTRY[name] = attack_class

__all__ = ['ATTACK_REGISTRY', 'get_attack_class', 'list_available_attacks', 'register_attack'] + list(ATTACK_REGISTRY.keys())