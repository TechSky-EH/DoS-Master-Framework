#!/usr/bin/env python3
"""
DoS Master Framework - Input Validation Module
Comprehensive input validation and sanitization
"""

import re
import socket
import ipaddress
from urllib.parse import urlparse
from typing import Any, Dict, List, Union

def validate_target(target: str) -> bool:
    """Validate target IP address or URL"""
    if not target or not isinstance(target, str):
        return False
    
    target = target.strip()
    
    # Check for blocked targets
    blocked_targets = [
        '8.8.8.8', '8.8.4.4',          # Google DNS
        '1.1.1.1', '1.0.0.1',          # Cloudflare DNS
        '208.67.222.222', '208.67.220.220',  # OpenDNS
        'google.com', 'facebook.com', 'amazon.com',
        'cloudflare.com', 'microsoft.com'
    ]
    
    if target.lower() in [t.lower() for t in blocked_targets]:
        return False
    
    # Validate as URL
    if target.startswith(('http://', 'https://')):
        return validate_url(target)
    
    # Validate as IP address
    return validate_ip_address(target)

def validate_ip_address(ip: str) -> bool:
    """Validate IP address"""
    try:
        # Parse as IP address
        ip_obj = ipaddress.ip_address(ip)
        
        # Block private and reserved addresses in production
        if ip_obj.is_private or ip_obj.is_reserved or ip_obj.is_loopback:
            # Allow private IPs for lab testing
            return True
        
        # Block multicast and unspecified
        if ip_obj.is_multicast or ip_obj.is_unspecified:
            return False
        
        return True
        
    except (ipaddress.AddressValueError, ValueError):
        return False

def validate_url(url: str) -> bool:
    """Validate URL"""
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
        
        # Try to resolve hostname to IP and validate
        try:
            ip = socket.gethostbyname(hostname)
            return validate_ip_address(ip)
        except socket.gaierror:
            return False
            
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
    """Validate attack parameters"""
    try:
        # Required parameters
        if 'target' not in params:
            return False
        
        if not validate_target(params['target']):
            return False
        
        # Duration validation
        duration = params.get('duration', 60)
        if not isinstance(duration, (int, float)) or duration <= 0 or duration > 3600:
            return False
        
        # Threads validation
        threads = params.get('threads', 10)
        if not isinstance(threads, int) or threads <= 0 or threads > 200:
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
        
        # Rate validation
        rate = params.get('rate', 0)
        if not isinstance(rate, (int, float)) or rate < 0:
            return False
        
        # Packet size validation
        packet_size = params.get('payload_size', 1024)
        if not isinstance(packet_size, int) or packet_size < 1 or packet_size > 65507:
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