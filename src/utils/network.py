#!/usr/bin/env python3
"""
DoS Master Framework - Network Utilities
Network-related utility functions and helpers
"""

import socket
import struct
import subprocess
import psutil
import netifaces
from typing import List, Dict, Optional, Tuple
import ipaddress

class NetworkUtils:
    """Network utility functions"""
    
    @staticmethod
    def get_local_ip() -> str:
        """Get local IP address"""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                return s.getsockname()[0]
        except Exception:
            return '127.0.0.1'
    
    @staticmethod
    def get_network_interfaces() -> Dict[str, Dict]:
        """Get all network interfaces and their details"""
        interfaces = {}
        
        try:
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                
                interface_info = {
                    'name': interface,
                    'ipv4': [],
                    'ipv6': [],
                    'mac': None,
                    'status': 'unknown'
                }
                
                # IPv4 addresses
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        interface_info['ipv4'].append({
                            'addr': addr.get('addr'),
                            'netmask': addr.get('netmask'),
                            'broadcast': addr.get('broadcast')
                        })
                
                # IPv6 addresses
                if netifaces.AF_INET6 in addrs:
                    for addr in addrs[netifaces.AF_INET6]:
                        interface_info['ipv6'].append({
                            'addr': addr.get('addr'),
                            'netmask': addr.get('netmask')
                        })
                
                # MAC address
                if netifaces.AF_LINK in addrs:
                    link_addrs = addrs[netifaces.AF_LINK]
                    if link_addrs:
                        interface_info['mac'] = link_addrs[0].get('addr')
                
                # Interface status
                try:
                    stats = psutil.net_if_stats()[interface]
                    interface_info['status'] = 'up' if stats.isup else 'down'
                    interface_info['speed'] = stats.speed
                    interface_info['mtu'] = stats.mtu
                except:
                    pass
                
                interfaces[interface] = interface_info
                
        except Exception as e:
           print(f"Error getting network interfaces: {e}")
       
       return interfaces
   
   @staticmethod
   def get_default_interface() -> Optional[str]:
       """Get default network interface"""
       try:
           # Try to get default route interface
           result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                 capture_output=True, text=True)
           
           if result.returncode == 0:
               for line in result.stdout.split('\n'):
                   if 'dev' in line:
                       parts = line.split()
                       dev_index = parts.index('dev')
                       if dev_index + 1 < len(parts):
                           return parts[dev_index + 1]
           
           # Fallback: find first non-loopback interface that's up
           interfaces = NetworkUtils.get_network_interfaces()
           for name, info in interfaces.items():
               if (name != 'lo' and 
                   info['status'] == 'up' and 
                   info['ipv4']):
                   return name
           
           return None
           
       except Exception:
           return None
   
   @staticmethod
   def ping_host(host: str, count: int = 1, timeout: int = 5) -> Dict:
       """Ping a host and return results"""
       try:
           result = subprocess.run([
               'ping', '-c', str(count), '-W', str(timeout), host
           ], capture_output=True, text=True)
           
           ping_result = {
               'host': host,
               'success': result.returncode == 0,
               'packets_sent': count,
               'packets_received': 0,
               'packet_loss': 100.0,
               'avg_time': 0.0,
               'min_time': 0.0,
               'max_time': 0.0
           }
           
           if result.returncode == 0:
               # Parse ping output
               lines = result.stdout.split('\n')
               
               # Find statistics line
               for line in lines:
                   if 'packets transmitted' in line:
                       parts = line.split()
                       if len(parts) >= 6:
                           ping_result['packets_received'] = int(parts[3])
                           loss_str = parts[5].rstrip('%')
                           ping_result['packet_loss'] = float(loss_str)
                   
                   elif 'min/avg/max' in line or 'rtt' in line:
                       # Extract timing information
                       time_part = line.split('=')[-1].strip()
                       times = time_part.split('/')
                       if len(times) >= 3:
                           ping_result['min_time'] = float(times[0])
                           ping_result['avg_time'] = float(times[1])
                           ping_result['max_time'] = float(times[2])
           
           return ping_result
           
       except Exception as e:
           return {
               'host': host,
               'success': False,
               'error': str(e),
               'packets_sent': count,
               'packets_received': 0,
               'packet_loss': 100.0
           }
   
   @staticmethod
   def port_scan(host: str, ports: List[int], timeout: int = 3) -> Dict[int, bool]:
       """Simple port scan"""
       results = {}
       
       for port in ports:
           try:
               sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
               sock.settimeout(timeout)
               result = sock.connect_ex((host, port))
               results[port] = result == 0
               sock.close()
           except Exception:
               results[port] = False
       
       return results
   
   @staticmethod
   def resolve_hostname(hostname: str) -> Optional[str]:
       """Resolve hostname to IP address"""
       try:
           return socket.gethostbyname(hostname)
       except socket.gaierror:
           return None
   
   @staticmethod
   def reverse_dns(ip: str) -> Optional[str]:
       """Reverse DNS lookup"""
       try:
           return socket.gethostbyaddr(ip)[0]
       except socket.herror:
           return None
   
   @staticmethod
   def get_network_stats(interface: str = None) -> Dict:
       """Get network interface statistics"""
       try:
           if interface:
               net_io = psutil.net_io_counters(pernic=True)
               if interface in net_io:
                   stats = net_io[interface]
                   return {
                       'interface': interface,
                       'bytes_sent': stats.bytes_sent,
                       'bytes_recv': stats.bytes_recv,
                       'packets_sent': stats.packets_sent,
                       'packets_recv': stats.packets_recv,
                       'errin': stats.errin,
                       'errout': stats.errout,
                       'dropin': stats.dropin,
                       'dropout': stats.dropout
                   }
           else:
               # Get system-wide statistics
               stats = psutil.net_io_counters()
               return {
                   'bytes_sent': stats.bytes_sent,
                   'bytes_recv': stats.bytes_recv,
                   'packets_sent': stats.packets_sent,
                   'packets_recv': stats.packets_recv,
                   'errin': stats.errin,
                   'errout': stats.errout,
                   'dropin': stats.dropin,
                   'dropout': stats.dropout
               }
       except Exception:
           return {}
   
   @staticmethod
   def check_connectivity(host: str = '8.8.8.8', port: int = 53) -> bool:
       """Check internet connectivity"""
       try:
           sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
           sock.settimeout(5)
           result = sock.connect_ex((host, port))
           sock.close()
           return result == 0
       except Exception:
           return False
   
   @staticmethod
   def get_subnet_info(ip: str, netmask: str) -> Dict:
       """Get subnet information"""
       try:
           network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
           
           return {
               'network_address': str(network.network_address),
               'broadcast_address': str(network.broadcast_address),
               'netmask': str(network.netmask),
               'prefix_length': network.prefixlen,
               'num_addresses': network.num_addresses,
               'hosts': [str(host) for host in network.hosts()],
               'is_private': network.is_private,
               'is_loopback': network.is_loopback,
               'is_multicast': network.is_multicast
           }
       except Exception as e:
           return {'error': str(e)}
   
   @staticmethod
   def calculate_bandwidth(bytes_transferred: int, duration: float) -> Dict:
       """Calculate bandwidth metrics"""
       if duration <= 0:
           return {'error': 'Invalid duration'}
       
       bytes_per_second = bytes_transferred / duration
       
       return {
           'bytes_per_second': bytes_per_second,
           'kilobytes_per_second': bytes_per_second / 1024,
           'megabytes_per_second': bytes_per_second / (1024 * 1024),
           'megabits_per_second': (bytes_per_second * 8) / (1024 * 1024),
           'duration': duration,
           'total_bytes': bytes_transferred
       }
   
   @staticmethod
   def is_port_open(host: str, port: int, timeout: int = 3) -> bool:
       """Check if a specific port is open"""
       try:
           sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
           sock.settimeout(timeout)
           result = sock.connect_ex((host, port))
           sock.close()
           return result == 0
       except Exception:
           return False
   
   @staticmethod
   def get_mac_address(interface: str) -> Optional[str]:
       """Get MAC address of network interface"""
       try:
           addrs = netifaces.ifaddresses(interface)
           if netifaces.AF_LINK in addrs:
               link_addrs = addrs[netifaces.AF_LINK]
               if link_addrs:
                   return link_addrs[0].get('addr')
       except Exception:
           pass
       return None
   
   @staticmethod
   def create_raw_socket() -> Optional[socket.socket]:
       """Create raw socket for packet crafting"""
       try:
           sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
           return sock
       except PermissionError:
           print("Error: Raw socket creation requires root privileges")
           return None
       except Exception as e:
           print(f"Error creating raw socket: {e}")
           return None
   
   @staticmethod
   def format_bytes(bytes_value: int) -> str:
       """Format bytes into human readable format"""
       for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
           if bytes_value < 1024.0:
               return f"{bytes_value:.2f} {unit}"
           bytes_value /= 1024.0
       return f"{bytes_value:.2f} PB"
   
   @staticmethod
   def validate_cidr(cidr: str) -> bool:
       """Validate CIDR notation"""
       try:
           ipaddress.IPv4Network(cidr, strict=False)
           return True
       except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
           return False