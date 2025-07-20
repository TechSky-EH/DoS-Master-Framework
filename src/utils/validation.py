#!/usr/bin/env python3
"""
DoS Master Framework - Input Validation Module - FIXED VERSION
Comprehensive input validation and sanitization with updated safety checks
"""

import re
import socket
import ipaddress
from urllib.parse import urlparse
from typing import Any, Dict, List, Union

def validate_target(target: str) -> bool:
    """Validate target IP address or URL - UPDATED"""
    if not target or not isinstance(target, str):
        return False
    
    target = target.strip()
    
    # Updated blocked targets list - more comprehensive
    blocked_targets = [
        # DNS servers
        '8.8.8.8', '8.8.4.4',          # Google DNS
        '1.1.1.1', '1.0.0.1',          # Cloudflare DNS
        '208.67.222.222', '208.67.220.220',  # OpenDNS
        '9.9.9.9', '149.112.112.112',  # Quad9 DNS
        
        # Major infrastructure
        'google.com', 'facebook.com', 'amazon.com', 'amazonaws.com',
        'cloudflare.com', 'microsoft.com', 'apple.com',
        'twitter.com', 'github.com', 'reddit.com',
        'youtube.com', 'instagram.com', 'linkedin.com',
        
        # Government and critical infrastructure
        'gov', '.gov', 'mil', '.mil', 'edu', '.edu',
        'whitehouse.gov', 'pentagon.mil', 'nasa.gov',
        
        # Localhost variants - REMOVED for VM testing
        # Note: Allowing localhost variants for educational VM environments
    ]
    
    # Check against blocked targets
    target_lower = target.lower()
    for blocked in blocked_targets:
        if blocked in target_lower:
            return False
    
    # Validate as URL
    if target.startswith(('http://', 'https://')):
        return validate_url(target)
    
    # Validate as IP address
    return validate_ip_address(target)

def validate_ip_address(ip: str) -> bool:
    """Validate IP address - UPDATED"""
    try:
        # Parse as IP address
        ip_obj = ipaddress.ip_address(ip)
        
        # Allow private IPs for lab testing (common in VMs)
        if ip_obj.is_private:
            return True
        
        # Block dangerous public ranges
        if ip_obj.is_reserved or ip_obj.is_loopback:
            # Allow loopback for educational purposes in VMs
            if ip_obj.is_loopback:
                return True
            return False
        
        # Block multicast and unspecified
        if ip_obj.is_multicast or ip_obj.is_unspecified:
            return False
        
        # Additional safety checks for public IPs
        if not ip_obj.is_private:
            # Block known dangerous ranges
            dangerous_ranges = [
                '0.0.0.0/8',      # "This" network
                '10.0.0.0/8',     # Private (but we allow this above)
                '127.0.0.0/8',    # Loopback (but we allow this above)
                '169.254.0.0/16', # Link-local
                '172.16.0.0/12',  # Private (but we allow this above)
                '192.168.0.0/16', # Private (but we allow this above)
                '224.0.0.0/4',    # Multicast
                '240.0.0.0/4',    # Reserved
            ]
            
            for dangerous_range in dangerous_ranges:
                if ip_obj in ipaddress.ip_network(dangerous_range, strict=False):
                    # Allow private ranges for lab testing
                    if dangerous_range in ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '127.0.0.0/8']:
                        return True
                    return False
        
        return True
        
    except (ipaddress.AddressValueError, ValueError):
        return False

def validate_url(url: str) -> bool:
    """Validate URL - UPDATED"""
    try:
        parsed = urlparse(url)
        
        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Only allow HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Validate hostname/IP
        hostname = parsed.hostname
        if not hostname:
            return False
        
        # Check against blocked domains
        blocked_domains = [
            'google.com', 'facebook.com', 'amazon.com', 'amazonaws.com',
            'cloudflare.com', 'microsoft.com', 'apple.com',
            'twitter.com', 'github.com', 'reddit.com',
            'youtube.com', 'instagram.com', 'linkedin.com',
            'gov', 'mil', 'edu'  # TLD blocks
        ]
        
        hostname_lower = hostname.lower()
        for blocked in blocked_domains:
            if blocked in hostname_lower:
                return False
        
        # Try to resolve hostname to IP and validate
        try:
            ip = socket.gethostbyname(hostname)
            return validate_ip_address(ip)
        except socket.gaierror:
            # If we can't resolve, allow it (might be local)
            return True
            
    except Exception:
        return False

def validate_port(port: Union[int, str]) -> bool:
    """Validate port number"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False

def validate_attack_params(params: Dict[str, Any]) -> bool:
    """Validate attack parameters - ENHANCED"""
    try:
        # Required parameters
        if 'target' not in params:
            return False
        
        if not validate_target(params['target']):
            return False
        
        # Duration validation - more flexible for testing
        duration = params.get('duration', 60)
        if not isinstance(duration, (int, float)) or duration <= 0 or duration > 7200:  # Allow up to 2 hours
            return False
        
        # Threads validation - increased limit for testing
        threads = params.get('threads', 10)
        if not isinstance(threads, int) or threads <= 0 or threads > 500:  # Increased from 200
            return False
        
        # Port validation (if specified)
        if 'port' in params:
            if not validate_port(params['port']):
                return False
        
        # Ports validation (if specified)
        if 'ports' in params:
            ports = params['ports']
            if not isinstance(ports, list) or len(ports) == 0:
                return False
            
            for port in ports:
                if not validate_port(port):
                    return False
        
        # Rate validation - more flexible
        rate = params.get('rate', 0)
        if not isinstance(rate, (int, float)) or rate < 0 or rate > 100000:  # Increased limit
            return False
        
        # Packet size validation
        packet_size = params.get('payload_size', 1024)
        if not isinstance(packet_size, int) or packet_size < 1 or packet_size > 65507:
            return False
        
        # Profile validation
        profile = params.get('profile', 'moderate')
        if profile not in ['stealth', 'moderate', 'aggressive']:
            return False
        
        return True
        
    except Exception:
        return False

def validate_profile(profile: str) -> bool:
    """Validate attack profile"""
    valid_profiles = ['stealth', 'moderate', 'aggressive']
    return profile in valid_profiles

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove path separators and dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    
    # Ensure not empty
    if not sanitized:
        sanitized = 'unnamed'
    
    return sanitized

def validate_file_path(file_path: str) -> bool:
    """Validate file path for security"""
    try:
        # Check for path traversal attempts
        if '..' in file_path or file_path.startswith('/'):
            return False
        
        # Check for dangerous characters
        if any(char in file_path for char in '<>:"|?*'):
            return False
        
        return True
        
    except Exception:
        return False

def validate_regex_pattern(pattern: str) -> bool:
    """Validate regex pattern"""
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False

def validate_network_interface(interface: str) -> bool:
    """Validate network interface name"""
    try:
        import psutil
        interfaces = psutil.net_if_addrs()
        return interface in interfaces
    except Exception:
        return False

def validate_json_data(data: Any) -> bool:
    """Validate JSON data structure"""
    try:
        import json
        json.dumps(data)
        return True
    except (TypeError, ValueError):
        return False

def validate_yaml_data(data: str) -> bool:
    """Validate YAML data"""
    try:
        import yaml
        yaml.safe_load(data)
        return True
    except yaml.YAMLError:
        return False

def validate_email(email: str) -> bool:
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_domain_name(domain: str) -> bool:
    """Validate domain name"""
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, domain)) and len(domain) <= 253

def is_safe_target(target: str) -> bool:
    """Additional safety check for targets"""
    if not target:
        return False
    
    # Allow VM and lab environments
    safe_patterns = [
        r'^10\.',           # 10.x.x.x (VM NAT networks)
        r'^192\.168\.',     # 192.168.x.x (VM/lab networks)
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',  # 172.16-31.x.x (VM networks)
        r'^127\.',          # Localhost (for educational purposes)
        r'\.local$',        # .local domains
        r'^test\.',         # test domains
    ]
    
    for pattern in safe_patterns:
        if re.match(pattern, target, re.IGNORECASE):
            return True
    
    return False

def get_target_risk_level(target: str) -> str:
    """Assess risk level of target"""
    if not target:
        return "UNKNOWN"
    
    # Very safe targets
    if is_safe_target(target):
        return "SAFE"
    
    # Check for dangerous patterns
    dangerous_patterns = [
        'google', 'facebook', 'amazon', 'microsoft', 'apple',
        'gov', 'mil', 'edu', 'cloudflare', 'twitter'
    ]
    
    target_lower = target.lower()
    for pattern in dangerous_patterns:
        if pattern in target_lower:
            return "DANGEROUS"
    
    return "MEDIUM"