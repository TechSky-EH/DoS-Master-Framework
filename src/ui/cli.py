#!/usr/bin/env python3
"""
DoS Master Framework - Command Line Interface - ROBUST VERSION
Professional DoS Testing Framework for Authorized Testing Only

Author: Tech Sky
License: MIT
"""

import argparse
import sys
import os
import signal
import time
from datetime import datetime
from pathlib import Path

# Robust path handling for imports
def setup_python_path():
    """Setup Python path for reliable imports"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Possible paths to add
    paths_to_add = [
        os.path.dirname(current_dir),  # src directory
        os.path.dirname(os.path.dirname(current_dir)),  # framework root
        current_dir,  # current directory
        '/opt/dos-master-framework',  # default install location
        '/opt/dos-master-framework/src',  # default src location
    ]
    
    for path in paths_to_add:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)

# Setup paths first
setup_python_path()

# Import framework components with comprehensive error handling
IMPORTS_OK = True
IMPORT_ERRORS = []
MISSING_MODULES = []

def safe_import(module_name, from_module=None, fallback_name=None):
    """Safely import a module with fallback options"""
    try:
        if from_module:
            module = __import__(from_module, fromlist=[module_name])
            return getattr(module, module_name)
        else:
            return __import__(module_name)
    except ImportError as e:
        IMPORT_ERRORS.append(f"{module_name}: {str(e)}")
        MISSING_MODULES.append(module_name)
        return None

# Try multiple import strategies
def import_framework_components():
    """Import framework components with multiple fallback strategies"""
    global IMPORTS_OK
    
    components = {}
    
    # Strategy 1: Relative imports
    try:
        from core.engine import DoSEngine
        from core.monitor import Monitor
        from core.analyzer import TrafficAnalyzer
        from core.reporter import ReportGenerator
        from utils.validation import validate_target, validate_attack_params
        from utils.logger import setup_logger
        from utils.config import load_config
        
        components.update({
            'DoSEngine': DoSEngine,
            'Monitor': Monitor,
            'TrafficAnalyzer': TrafficAnalyzer,
            'ReportGenerator': ReportGenerator,
            'validate_target': validate_target,
            'validate_attack_params': validate_attack_params,
            'setup_logger': setup_logger,
            'load_config': load_config
        })
        return components
        
    except ImportError:
        pass
    
    # Strategy 2: Absolute imports
    try:
        import core.engine
        import core.monitor
        import core.analyzer
        import core.reporter
        import utils.validation
        import utils.logger
        import utils.config
        
        components.update({
            'DoSEngine': core.engine.DoSEngine,
            'Monitor': core.monitor.Monitor,
            'TrafficAnalyzer': core.analyzer.TrafficAnalyzer,
            'ReportGenerator': core.reporter.ReportGenerator,
            'validate_target': utils.validation.validate_target,
            'validate_attack_params': utils.validation.validate_attack_params,
            'setup_logger': utils.logger.setup_logger,
            'load_config': utils.config.load_config
        })
        return components
        
    except ImportError:
        pass
    
    # Strategy 3: Direct file imports
    try:
        framework_paths = [
            '/opt/dos-master-framework/src',
            os.path.join(os.path.dirname(__file__), '..'),
            os.path.dirname(os.path.dirname(__file__)),
        ]
        
        for base_path in framework_paths:
            if os.path.exists(base_path):
                sys.path.insert(0, base_path)
                try:
                    import core.engine
                    components['DoSEngine'] = core.engine.DoSEngine
                    break
                except ImportError:
                    continue
        
        if components:
            return components
            
    except ImportError:
        pass
    
    # If all strategies fail, create fallback implementations
    IMPORTS_OK = False
    return create_fallback_components()

def create_fallback_components():
    """Create fallback components when imports fail"""
    import logging
    
    # Fallback logger
    def setup_logger():
        logger = logging.getLogger('dmf')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    # Fallback config
    def load_config():
        return {
            'framework': {'name': 'DoS Master Framework', 'version': '2.0'},
            'global': {'log_level': 'INFO', 'max_threads': 50},
            'safety': {'dry_run': True, 'require_confirmation': True}
        }
    
    # Fallback validation
    def validate_target(target):
        import re
        if not target or not isinstance(target, str):
            return False
        # Basic IP validation
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_pattern, target):
            # Check for dangerous IPs
            dangerous_ips = ['8.8.8.8', '1.1.1.1', '127.0.0.1', 'localhost']
            return target not in dangerous_ips
        # Basic hostname validation
        return '.' in target and len(target) > 3
    
    def validate_attack_params(params):
        return isinstance(params, dict) and 'target' in params
    
    # Fallback engine
    class FallbackDoSEngine:
        def __init__(self, config, logger):
            self.config = config
            self.logger = logger
            
        def execute_attack(self, attack_type, config):
            self.logger.info(f"SIMULATION: {attack_type} attack against {config.get('target', 'unknown')}")
            self.logger.info("Running in fallback mode - limited functionality")
            
            # Simulate attack
            duration = config.get('duration', 10)
            threads = config.get('threads', 5)
            
            time.sleep(min(duration, 5))  # Simulate for max 5 seconds
            
            return {
                'attack_type': attack_type,
                'target': config.get('target', 'unknown'),
                'packets_sent': threads * 100 * duration,
                'success_rate': 95.0,
                'avg_rate': threads * 100,
                'duration': duration,
                'fallback_mode': True,
                'timestamp': datetime.now().isoformat()
            }
        
        def stop_all_attacks(self):
            pass
        
        def cleanup(self):
            pass
    
    # Fallback monitor and other components
    class FallbackComponent:
        def __init__(self, *args, **kwargs):
            pass
        def start(self): pass
        def stop(self): pass
        def cleanup(self): pass
    
    return {
        'DoSEngine': FallbackDoSEngine,
        'Monitor': FallbackComponent,
        'TrafficAnalyzer': FallbackComponent,
        'ReportGenerator': FallbackComponent,
        'validate_target': validate_target,
        'validate_attack_params': validate_attack_params,
        'setup_logger': setup_logger,
        'load_config': load_config
    }

# Import components
components = import_framework_components()

# Extract components
DoSEngine = components['DoSEngine']
Monitor = components['Monitor']
TrafficAnalyzer = components['TrafficAnalyzer']
ReportGenerator = components['ReportGenerator']
validate_target = components['validate_target']
validate_attack_params = components['validate_attack_params']
setup_logger = components['setup_logger']
load_config = components['load_config']

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
        
        # Show import status
        if not IMPORTS_OK:
            print("⚠️  WARNING: Running in limited mode (some modules unavailable)")
            print("   Framework functionality may be reduced")
            print("   Consider reinstalling or checking dependencies")
            print()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n[!] Received signal {signum}, stopping attacks...")
            if self.engine and hasattr(self.engine, 'stop_all_attacks'):
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
  # Simple ICMP flood (dry run - ALWAYS START WITH THIS)
  dmf --target 192.168.1.100 --attack icmp_flood --duration 60 --dry-run
  
  # SYN flood with custom parameters  
  dmf --target 192.168.1.100 --attack syn_flood --port 80 --threads 10 --dry-run
  
  # List available attacks
  dmf --list-attacks
  
  # Show version
  dmf --version
  
  # Start web interface
  dmf --web-ui --port 8080

⚠️  IMPORTANT: 
  - Always use --dry-run first to test without sending actual packets
  - Only test systems you own or have explicit written permission to test
  - Unauthorized DoS attacks are illegal and punishable by law
            """
        )
        
        # Target specification
        parser.add_argument('--target', '-t', 
                          help='Target IP address or URL')
        
        # Attack specification
        parser.add_argument('--attack', '-a', 
                          choices=['icmp_flood', 'udp_flood', 'syn_flood', 
                                 'http_flood', 'slowloris', 'amplification', 
                                 'multi_vector'],
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
        
        # Safety options
        parser.add_argument('--dry-run', action='store_true',
                          help='Simulate attack without sending packets (STRONGLY RECOMMENDED)')
        
        parser.add_argument('--profile',
                          choices=['stealth', 'moderate', 'aggressive'],
                          default='moderate',
                          help='Attack profile (default: moderate)')
        
        # Information
        parser.add_argument('--list-attacks', action='store_true',
                          help='List available attack types')
        
        parser.add_argument('--version', action='version', 
                          version='DoS Master Framework 2.0.0')
        
        parser.add_argument('--validate', action='store_true',
                          help='Validate installation and show status')
        
        # Web interface
        parser.add_argument('--web-ui', action='store_true',
                          help='Start web interface')
        
        parser.add_argument('--web-port', type=int, default=8080,
                          help='Web interface port (default: 8080)')
        
        # Monitoring
        parser.add_argument('--monitor', '-m', action='store_true',
                          help='Enable real-time monitoring')
        
        # Verbosity
        parser.add_argument('--verbose', '-v', action='count', default=0,
                          help='Increase verbosity (-v, -vv, -vvv)')
        
        parser.add_argument('--debug', action='store_true',
                          help='Enable debug mode')
        
        return parser
    
    def validate_environment(self):
        """Validate execution environment"""
        issues = []
        
        # Check if running as root
        if os.geteuid() != 0:
            issues.append("Some attacks require root privileges (consider using sudo)")
        
        # Check required tools
        required_tools = ['hping3', 'nmap', 'tcpdump']
        missing_tools = []
        
        for tool in required_tools:
            if os.system(f"which {tool} > /dev/null 2>&1") != 0:
                missing_tools.append(tool)
        
        if missing_tools:
            issues.append(f"Missing tools: {', '.join(missing_tools)}")
        
        # Check framework imports
        if not IMPORTS_OK:
            issues.append("Framework modules not fully available")
        
        if issues:
            print("⚠️  Environment Issues:")
            for issue in issues:
                print(f"   - {issue}")
            print()
        
        return len(issues) == 0
    
    def validate_installation(self):
        """Validate framework installation"""
        print("\n📋 Installation Validation Report")
        print("=" * 50)
        
        checks = []
        
        # Check Python version
        python_version = sys.version.split()[0]
        checks.append(("Python Version", python_version, "✅" if sys.version_info >= (3, 7) else "❌"))
        
        # Check import status
        checks.append(("Framework Imports", "Available" if IMPORTS_OK else "Limited", "✅" if IMPORTS_OK else "⚠️"))
        
        # Check tools
        tools = ['hping3', 'nmap', 'tcpdump', 'curl']
        for tool in tools:
            available = os.system(f"which {tool} > /dev/null 2>&1") == 0
            checks.append((f"Tool: {tool}", "Available" if available else "Missing", "✅" if available else "❌"))
        
        # Check permissions
        is_root = os.geteuid() == 0
        checks.append(("Root Access", "Yes" if is_root else "No", "✅" if is_root else "⚠️"))
        
        # Display results
        for check_name, status, icon in checks:
            print(f"  {icon} {check_name:<20}: {status}")
        
        print("\n💡 Recommendations:")
        if not IMPORTS_OK:
            print("  - Reinstall framework: Run installation script again")
            print("  - Check Python dependencies: pip install -r requirements.txt")
        
        if os.geteuid() != 0:
            print("  - For full functionality, run with sudo for certain attacks")
        
        print("\n📖 For help: dmf --help")
        print("🌐 Web interface: dmf --web-ui")
        print("🔍 List attacks: dmf --list-attacks")
    
    def list_attacks(self):
        """List available attack types"""
        attacks = {
            'icmp_flood': 'ICMP flood attack (ping flood)',
            'udp_flood': 'UDP flood attack (connectionless flooding)', 
            'syn_flood': 'TCP SYN flood attack (connection exhaustion)',
            'http_flood': 'HTTP flood attack (application layer)',
            'slowloris': 'Slowloris attack (connection holding)',
            'amplification': 'DNS/NTP amplification attacks',
            'multi_vector': 'Combined multi-vector attack'
        }
        
        print("\nAvailable Attack Types:")
        print("=" * 60)
        for attack, description in attacks.items():
            status = "✅" if IMPORTS_OK else "⚠️"
            print(f"  {status} {attack:<15} - {description}")
        print()
        
        if not IMPORTS_OK:
            print("⚠️  Note: Running in limited mode - some attacks may have reduced functionality")
            print("   Consider running installation validation: dmf --validate")
        
        print("\n🔒 Security Notice:")
        print("   • ALWAYS use --dry-run first")
        print("   • Only test systems you own or have permission to test")
        print("   • Unauthorized DoS attacks are illegal")
        print("   • Example: dmf --target 192.168.1.100 --attack icmp_flood --dry-run")
    
    def confirm_attack(self, args):
        """Confirm attack parameters with user"""
        if args.dry_run:
            print("\n✅ DRY RUN MODE - No actual packets will be sent")
            print("   This is safe and recommended for testing")
            return True
            
        print(f"\n⚠️  LIVE ATTACK CONFIRMATION")
        print(f"    Target: {args.target}")
        print(f"    Attack: {args.attack}")
        print(f"    Duration: {args.duration} seconds")
        print(f"    Threads: {args.threads}")
        print(f"    Profile: {args.profile}")
        print()
        print("🚨 WARNING: This will launch a REAL DoS attack against the target.")
        print("   • Ensure you have explicit written authorization")
        print("   • Verify this is a test environment")
        print("   • Consider liability and legal implications")
        print()
        
        # Additional safety checks
        dangerous_patterns = ['google', 'facebook', 'cloudflare', 'amazonaws', 'microsoft']
        target_lower = args.target.lower()
        if any(pattern in target_lower for pattern in dangerous_patterns):
            print("🛑 DANGER: Target appears to be a major service provider")
            print("   This type of target should NEVER be attacked")
            return False
        
        while True:
            response = input("Type 'I UNDERSTAND THE RISKS' to continue with LIVE attack: ").strip()
            if response == 'I UNDERSTAND THE RISKS':
                print("⚠️  Proceeding with live attack...")
                return True
            elif response.lower() in ['n', 'no', 'cancel', 'exit', '']:
                return False
            else:
                print("Please type exactly 'I UNDERSTAND THE RISKS' or press Enter to cancel")
    
    def run_attack(self, args):
        """Execute the specified attack"""
        try:
            # Validate target
            if not validate_target(args.target):
                print(f"❌ Invalid target: {args.target}")
                print("   Target must be a valid IP address or hostname")
                return
            
            # Check for dangerous targets
            dangerous_targets = [
                'localhost', '127.0.0.1', '0.0.0.0', 
                'google.com', 'facebook.com', 'cloudflare.com',
                'amazonaws.com', 'microsoft.com', 'apple.com'
            ]
            if any(dangerous in args.target.lower() for dangerous in dangerous_targets):
                print(f"🛑 Cannot target {args.target} - blocked for safety")
                print("   This target is not appropriate for testing")
                return
            
            # Confirm attack
            if not self.confirm_attack(args):
                print("❌ Attack cancelled by user")
                return
            
            # Initialize components
            self.engine = DoSEngine(self.config, self.logger)
            
            if args.monitor and IMPORTS_OK:
                try:
                    self.monitor = Monitor(args.target, self.logger)
                    self.monitor.start()
                    print("📊 Monitoring started")
                except Exception as e:
                    print(f"⚠️  Monitoring failed to start: {e}")
            
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
            
            # Validate attack parameters
            if not validate_attack_params(attack_config):
                print("❌ Invalid attack parameters")
                return
            
            print(f"\n🚀 {'Simulating' if args.dry_run else 'Starting'} {args.attack} attack")
            print(f"    Target: {args.target}")
            print(f"    Duration: {args.duration} seconds")
            print(f"    Threads: {args.threads}")
            print(f"    Profile: {args.profile}")
            
            if args.dry_run:
                print("    Mode: 🛡️  DRY RUN (simulation only)")
            else:
                print("    Mode: ⚠️  LIVE ATTACK")
            
            print("\n" + "=" * 60)
            
            # Execute attack
            start_time = time.time()
            result = self.engine.execute_attack(args.attack, attack_config)
            end_time = time.time()
            
            print("\n" + "=" * 60)
            print(f"✅ Attack {'simulation' if args.dry_run else 'execution'} completed")
            print(f"    Total time: {end_time - start_time:.2f} seconds")
            
            if isinstance(result, dict):
                print(f"    Packets sent: {result.get('packets_sent', 'N/A'):,}")
                print(f"    Success rate: {result.get('success_rate', 'N/A'):.1f}%")
                print(f"    Average rate: {result.get('avg_rate', 'N/A'):.0f} pps")
                
                if result.get('fallback_mode'):
                    print("    ℹ️  Ran in fallback/simulation mode")
                elif args.dry_run:
                    print("    ✅ Simulation completed successfully")
                else:
                    print("    ✅ Live attack completed")
            
            return result
            
        except KeyboardInterrupt:
            print("\n❌ Attack interrupted by user")
        except Exception as e:
            print(f"\n❌ Attack failed: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
        finally:
            # Cleanup
            if self.engine and hasattr(self.engine, 'cleanup'):
                self.engine.cleanup()
            if self.monitor and hasattr(self.monitor, 'stop'):
                self.monitor.stop()
                print("📊 Monitoring stopped")
    
    def start_web_ui(self, port):
        """Start web interface"""
        try:
            print(f"\n🌐 Starting web interface on port {port}")
            print(f"    Access at: http://localhost:{port}")
            print("    Press Ctrl+C to stop")
            print()
            
            if IMPORTS_OK:
                try:
                    from ui.web import create_app
                    app, socketio = create_app(self.config)
                    socketio.run(app, host='0.0.0.0', port=port, debug=False)
                except ImportError:
                    print("⚠️  Advanced web interface not available")
                    self._start_simple_web_server(port)
            else:
                self._start_simple_web_server(port)
                
        except Exception as e:
            print(f"❌ Failed to start web interface: {e}")
    
    def _start_simple_web_server(self, port):
        """Start simple fallback web server"""
        try:
            import http.server
            import socketserver
            
            class CustomHandler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/':
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        html = """
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>DoS Master Framework</title>
                            <style>
                                body { font-family: Arial, sans-serif; margin: 40px; }
                                .warning { background: #fff3cd; padding: 20px; border: 1px solid #ffeaa7; border-radius: 8px; }
                                .info { background: #d1ecf1; padding: 20px; border: 1px solid #bee5eb; border-radius: 8px; margin-top: 20px; }
                            </style>
                        </head>
                        <body>
                            <h1>🛡️ DoS Master Framework</h1>
                            <div class="warning">
                                <h3>⚠️ Limited Mode</h3>
                                <p>The web interface is running in basic mode due to missing dependencies.</p>
                            </div>
                            <div class="info">
                                <h3>💡 For Full Functionality</h3>
                                <p>Use the command line interface:</p>
                                <ul>
                                    <li><code>dmf --help</code> - Show help</li>
                                    <li><code>dmf --list-attacks</code> - List available attacks</li>
                                    <li><code>dmf --validate</code> - Check installation</li>
                                    <li><code>dmf --target IP --attack TYPE --dry-run</code> - Safe testing</li>
                                </ul>
                            </div>
                            <div class="warning">
                                <h3>🔒 Legal Notice</h3>
                                <p><strong>For authorized testing only.</strong> Unauthorized use is illegal.</p>
                            </div>
                        </body>
                        </html>
                        """
                        self.wfile.write(html.encode())
                    else:
                        super().do_GET()
            
            with socketserver.TCPServer(("", port), CustomHandler) as httpd:
                print(f"    Serving basic interface at port {port}")
                httpd.serve_forever()
                
        except Exception as e:
            print(f"❌ Simple web server failed: {e}")
    
    def main(self):
        """Main entry point"""
        self.setup_signal_handlers()
        
        parser = self.create_parser()
        args = parser.parse_args()
        
        # Handle debug mode
        if args.debug:
            print("🔧 Debug mode enabled")
            if not IMPORTS_OK:
                print("Import errors:")
                for i, error in enumerate(IMPORT_ERRORS, 1):
                    print(f"  {i}. {error}")
            print(f"Python path: {sys.path[:3]}...")  # Show first 3 paths
            print()
        
        # Display banner unless minimal output requested
        if not any([args.list_attacks, args.validate, args.version]):
            self.display_banner()
        
        # Handle validation
        if args.validate:
            self.validate_installation()
            return
        
        # Handle information requests
        if args.list_attacks:
            self.list_attacks()
            return
        
        # Handle web UI
        if args.web_ui:
            self.start_web_ui(args.web_port)
            return
        
        # Validate environment for attacks
        env_ok = self.validate_environment()
        
        # Handle attacks
        if args.attack:
            if not args.target:
                print("❌ Target is required for attack operations")
                print("💡 Example: dmf --target 192.168.1.100 --attack icmp_flood --dry-run")
                parser.print_help()
                return
            
            self.run_attack(args)
        else:
            # Show help if no specific action
            parser.print_help()

def main():
    """Entry point for dmf command"""
    try:
        cli = DoSMasterCLI()
        cli.main()
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()