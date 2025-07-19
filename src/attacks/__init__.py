#!/usr/bin/env python3
"""
DoS Master Framework - Attack Modules
Implementation of various DoS attack types
"""

from .icmp_flood import ICMPFlood
from .udp_flood import UDPFlood
from .syn_flood import SYNFlood
from .http_flood import HTTPFlood
from .slowloris import Slowloris

# Attack registry for dynamic loading
ATTACK_REGISTRY = {
    'icmp_flood': ICMPFlood,
    'udp_flood': UDPFlood,
    'syn_flood': SYNFlood,
    'http_flood': HTTPFlood,
    'slowloris': Slowloris
}

def get_attack_class(attack_type: str):
    """Get attack class by type name"""
    return ATTACK_REGISTRY.get(attack_type)

def list_available_attacks():
    """List all available attack types"""
    return list(ATTACK_REGISTRY.keys())

def register_attack(name: str, attack_class):
    """Register a new attack type"""
    ATTACK_REGISTRY[name] = attack_class

__all__ = [
    'ICMPFlood',
    'UDPFlood', 
    'SYNFlood',
    'HTTPFlood',
    'Slowloris',
    'ATTACK_REGISTRY',
    'get_attack_class',
    'list_available_attacks',
    'register_attack'
]