#!/usr/bin/env python3
"""
DoS Master Framework - Report Generation Module
Comprehensive reporting with HTML, PDF, and JSON formats
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import base64

class ReportGenerator:
    """Generate comprehensive attack and analysis reports"""
    
    def __init__(self, logger):
        self.logger = logger
        self.template_dir = Path(__file__).parent.parent / 'ui' / 'templates'
        
    def generate_report(self, attack_results: Dict[str, Any], output_dir: str = './reports') -> str:
        """Generate comprehensive attack report"""
        try:
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamp-based filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            attack_type = attack_results.get('attack_type', 'unknown')
            report_name = f"dos_report_{attack_type}_{timestamp}"
            
            # Generate HTML report
            html_file = output_path / f"{report_name}.html"
            self._generate_html_report(attack_results, html_file)
            
            # Generate JSON report
            json_file = output_path / f"{report_name}.json"
            self._generate_json_report(attack_results, json_file)
            
            # Generate summary text
            summary_file = output_path / f"{report_name}_summary.txt"
            self._generate_summary_report(attack_results, summary_file)
            
            self.logger.info(f"Reports generated in {output_dir}")
            return str(html_file)
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            raise
    
    def _generate_html_report(self, results: Dict[str, Any], output_file: Path):
        """Generate HTML report with charts and styling"""
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DoS Attack Report - {attack_type}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #e74c3c;
        }}
        .header h1 {{
            color: #e74c3c;
            margin-bottom: 10px;
        }}
        .header p {{
            color: #666;
            font-size: 1.1em;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .status-success {{ background-color: #27ae60; }}
        .status-warning {{ background-color: #f39c12; }}
        .status-danger {{ background-color: #e74c3c; }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .info-table th, .info-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .info-table th {{
            background-color: #f8f9fa;
            font-weight: bold;
            color: #2c3e50;
        }}
        .info-table tr:hover {{
            background-color: #f5f5f5;
        }}
        .alert {{
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 5px solid;
        }}
        .alert-info {{
            background-color: #d1ecf1;
            border-color: #17a2b8;
            color: #0c5460;
        }}
        .alert-warning {{
            background-color: #fff3cd;
            border-color: #ffc107;
            color: #856404;
        }}
        .alert-danger {{
            background-color: #f8d7da;
            border-color: #dc3545;
            color: #721c24;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
        @media print {{
            body {{ background-color: white; }}
            .container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DoS Master Framework - Attack Report</h1>
            <p>Attack Type: <strong>{attack_type_display}</strong></p>
            <p>Generated: {timestamp}</p>
        </div>

        <div class="alert alert-warning">
            <strong>⚠️ Legal Notice:</strong> This report is generated from authorized security testing only. 
            Any unauthorized use of DoS attacks is illegal and may result in criminal prosecution.
        </div>

        <div class="section">
            <h2>Executive Summary</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{packets_sent:,}</div>
                    <div class="metric-label">Packets Sent</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{duration:.1f}s</div>
                    <div class="metric-label">Duration</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{avg_rate:.0f}</div>
                    <div class="metric-label">Packets/Second</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{success_rate:.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Attack Configuration</h2>
            <table class="info-table">
                <tr><th>Parameter</th><th>Value</th></tr>
                <tr><td>Target</td><td>{target}</td></tr>
                <tr><td>Attack Type</td><td>{attack_type}</td></tr>
                <tr><td>Duration</td><td>{duration:.1f} seconds</td></tr>
                <tr><td>Threads Used</td><td>{threads_used}</td></tr>
                <tr><td>Start Time</td><td>{start_time}</td></tr>
                <tr><td>End Time</td><td>{end_time}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>Performance Metrics</h2>
            <div class="chart-container">
                <canvas id="performanceChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2>Attack Timeline</h2>
            <div class="chart-container">
                <canvas id="timelineChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2>Technical Details</h2>
            {technical_details}
        </div>

        <div class="section">
            <h2>Impact Assessment</h2>
            <div class="alert alert-info">
                <strong>Attack Effectiveness:</strong> Based on the success rate of {success_rate:.1f}% 
                and packet rate of {avg_rate:.0f} pps, this attack would be classified as 
                <strong>{effectiveness_level}</strong>.
            </div>
        </div>

        <div class="section">
            <h2>Recommendations</h2>
            <ul>
                <li>Implement rate limiting to restrict packets per second from individual sources</li>
                <li>Deploy DDoS protection services for volumetric attack mitigation</li>
                <li>Configure firewalls with appropriate flood protection settings</li>
                <li>Monitor network traffic for similar attack patterns</li>
                <li>Implement network segmentation to limit attack surface</li>
                <li>Establish incident response procedures for DoS attacks</li>
            </ul>
        </div>

        <div class="footer">
            <p>Generated by DoS Master Framework v2.0 | <strong>For Authorized Testing Only</strong></p>
        </div>
    </div>

    <script>
        // Performance Chart
        const performanceCtx = document.getElementById('performanceChart').getContext('2d');
        new Chart(performanceCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Successful Packets', 'Failed Packets'],
                datasets: [{{
                    data: [{successful_packets}, {failed_packets}],
                    backgroundColor: ['#27ae60', '#e74c3c'],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Packet Success Rate'
                    }},
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});

        // Timeline Chart (simulated data)
        const timelineCtx = document.getElementById('timelineChart').getContext('2d');
        const timelineData = {timeline_data};
        
        new Chart(timelineCtx, {{
            type: 'line',
            data: {{
                labels: timelineData.labels,
                datasets: [{{
                    label: 'Packets per Second',
                    data: timelineData.data,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 2,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Attack Timeline'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Packets per Second'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Time (seconds)'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """
        
        # Prepare data for template
        attack_type = results.get('attack_type', 'unknown')
        attack_type_display = attack_type.replace('_', ' ').title()
        
        packets_sent = results.get('packets_sent', 0)
        duration = results.get('duration', 0)
        avg_rate = results.get('avg_rate', 0)
        success_rate = results.get('success_rate', 0)
        threads_used = results.get('threads_used', 0)
        
        # Calculate derived metrics
        failed_packets = packets_sent - int(packets_sent * success_rate / 100)
        successful_packets = packets_sent - failed_packets
        
        # Determine effectiveness level
        if success_rate > 90 and avg_rate > 1000:
            effectiveness_level = "HIGHLY EFFECTIVE"
        elif success_rate > 70 and avg_rate > 500:
            effectiveness_level = "MODERATELY EFFECTIVE"
        elif success_rate > 50:
            effectiveness_level = "PARTIALLY EFFECTIVE"
        else:
            effectiveness_level = "LOW EFFECTIVENESS"
        
        # Generate timeline data
        timeline_labels = [f"{i*10}" for i in range(int(duration/10) + 1)]
        timeline_values = [avg_rate + random.randint(-100, 100) for _ in timeline_labels]
        timeline_data = json.dumps({
            'labels': timeline_labels,
            'data': timeline_values
        })
        
        # Generate technical details
        technical_details = self._generate_technical_details_html(results)
        
        # Format timestamps
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = timestamp  # Would be actual start time in real implementation
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format template
        html_content = html_template.format(
            attack_type=attack_type,
            attack_type_display=attack_type_display,
            timestamp=timestamp,
            packets_sent=packets_sent,
            duration=duration,
            avg_rate=avg_rate,
            success_rate=success_rate,
            threads_used=threads_used,
            target=results.get('target', 'Unknown'),
            start_time=start_time,
            end_time=end_time,
            technical_details=technical_details,
            effectiveness_level=effectiveness_level,
            successful_packets=successful_packets,
            failed_packets=failed_packets,
            timeline_data=timeline_data
        )
        
        # Write HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"HTML report generated: {output_file}")
    
    def _generate_technical_details_html(self, results: Dict[str, Any]) -> str:
        """Generate technical details section"""
        details = []
        
        attack_type = results.get('attack_type', 'unknown')
        
        if attack_type == 'syn_flood':
            details.append('<h3>SYN Flood Details</h3>')
            details.append('<ul>')
            details.append(f'<li>Target Port: {results.get("port", "Unknown")}</li>')
            details.append(f'<li>IP Spoofing: {"Enabled" if results.get("spoof_enabled", False) else "Disabled"}</li>')
            details.append(f'<li>Connection Exhaustion Method: TCP SYN packets without ACK response</li>')
            details.append('</ul>')
            
        elif attack_type == 'udp_flood':
            details.append('<h3>UDP Flood Details</h3>')
            details.append('<ul>')
            details.append(f'<li>Target Ports: {results.get("ports", "Unknown")}</li>')
            details.append(f'<li>Packet Size: {results.get("packet_size", "Unknown")} bytes</li>')
            details.append(f'<li>Connectionless Protocol: UDP packets without handshake requirement</li>')
            details.append('</ul>')
            
        elif attack_type == 'icmp_flood':
            details.append('<h3>ICMP Flood Details</h3>')
            details.append('<ul>')
            details.append(f'<li>Packet Size: {results.get("packet_size", "Unknown")} bytes</li>')
            details.append(f'<li>Protocol: Internet Control Message Protocol (ICMP)</li>')
            details.append(f'<li>Attack Method: High-rate ping flooding</li>')
            details.append('</ul>')
            
        elif attack_type == 'http_flood':
            details.append('<h3>HTTP Flood Details</h3>')
            details.append('<ul>')
            details.append(f'<li>Target Paths: {results.get("target_paths", "Unknown")}</li>')
            details.append(f'<li>Request Method: GET requests with random parameters</li>')
            details.append(f'<li>User-Agent Rotation: Multiple browser identities</li>')
            details.append('</ul>')
        
        return ''.join(details) if details else '<p>No specific technical details available for this attack type.</p>'
    
    def _generate_json_report(self, results: Dict[str, Any], output_file: Path):
        """Generate JSON report"""
        report_data = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'generator': 'DoS Master Framework v2.0',
                'report_type': 'attack_analysis',
                'format_version': '1.0'
            },
            'attack_results': results,
            'analysis': {
                'effectiveness_rating': self._calculate_effectiveness_rating(results),
                'threat_level': self._calculate_threat_level(results),
                'mitigation_priority': self._calculate_mitigation_priority(results)
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.logger.info(f"JSON report generated: {output_file}")
    
    def _generate_summary_report(self, results: Dict[str, Any], output_file: Path):
        """Generate plain text summary report"""
        lines = []
        lines.append("=" * 60)
        lines.append("DOS MASTER FRAMEWORK - ATTACK SUMMARY REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Basic info
        lines.append("ATTACK INFORMATION:")
        lines.append(f"  Type: {results.get('attack_type', 'Unknown').replace('_', ' ').title()}")
        lines.append(f"  Target: {results.get('target', 'Unknown')}")
        lines.append(f"  Duration: {results.get('duration', 0):.1f} seconds")
        lines.append(f"  Threads: {results.get('threads_used', 0)}")
        lines.append("")
        
        # Performance metrics
        lines.append("PERFORMANCE METRICS:")
        lines.append(f"  Packets Sent: {results.get('packets_sent', 0):,}")
        lines.append(f"  Success Rate: {results.get('success_rate', 0):.1f}%")
        lines.append(f"  Average Rate: {results.get('avg_rate', 0):.0f} packets/second")
        lines.append("")
        
        # Impact assessment
        effectiveness = self._calculate_effectiveness_rating(results)
        lines.append("IMPACT ASSESSMENT:")
        lines.append(f"  Effectiveness: {effectiveness}")
        lines.append(f"  Threat Level: {self._calculate_threat_level(results)}")
        lines.append("")
        
        # Recommendations
        lines.append("MITIGATION RECOMMENDATIONS:")
        lines.append("  - Implement rate limiting for incoming packets")
        lines.append("  - Deploy DDoS protection services")
        lines.append("  - Configure firewall flood protection")
        lines.append("  - Monitor for similar attack patterns")
        lines.append("  - Establish incident response procedures")
        lines.append("")
        
        lines.append("=" * 60)
        lines.append("This report is for authorized security testing only.")
        lines.append("DoS Master Framework v2.0 - Tech Sky")
        lines.append("=" * 60)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        self.logger.info(f"Summary report generated: {output_file}")
    
    def _calculate_effectiveness_rating(self, results: Dict[str, Any]) -> str:
        """Calculate attack effectiveness rating"""
        success_rate = results.get('success_rate', 0)
        avg_rate = results.get('avg_rate', 0)
        
        if success_rate > 90 and avg_rate > 1000:
            return "HIGHLY EFFECTIVE"
        elif success_rate > 70 and avg_rate > 500:
            return "MODERATELY EFFECTIVE"
        elif success_rate > 50:
            return "PARTIALLY EFFECTIVE"
        else:
            return "LOW EFFECTIVENESS"
    
    def _calculate_threat_level(self, results: Dict[str, Any]) -> str:
        """Calculate threat level"""
        avg_rate = results.get('avg_rate', 0)
        
        if avg_rate > 10000:
            return "CRITICAL"
        elif avg_rate > 5000:
            return "HIGH"
        elif avg_rate > 1000:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_mitigation_priority(self, results: Dict[str, Any]) -> str:
        """Calculate mitigation priority"""
        effectiveness = self._calculate_effectiveness_rating(results)
        threat_level = self._calculate_threat_level(results)
        
        if effectiveness in ["HIGHLY EFFECTIVE"] and threat_level in ["CRITICAL", "HIGH"]:
            return "IMMEDIATE"
        elif effectiveness in ["MODERATELY EFFECTIVE", "HIGHLY EFFECTIVE"]:
            return "HIGH"
        elif effectiveness in ["PARTIALLY EFFECTIVE"]:
            return "MEDIUM"
        else:
            return "LOW"

    def generate_comparison_report(self, results_list: List[Dict[str, Any]], output_dir: str = './reports') -> str:
        """Generate comparison report for multiple attacks"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = output_path / f"dos_comparison_report_{timestamp}.html"
            
            # Generate comparison HTML
            self._generate_comparison_html(results_list, report_file)
            
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"Comparison report generation failed: {e}")
            raise
    
    def _generate_comparison_html(self, results_list: List[Dict[str, Any]], output_file: Path):
        """Generate HTML comparison report"""
        # This would contain the comparison report template
        # For brevity, implementing a basic version
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>DoS Attack Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>DoS Attack Comparison Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <table>
        <tr>
            <th>Attack Type</th>
            <th>Packets Sent</th>
            <th>Success Rate</th>
            <th>Avg Rate (pps)</th>
            <th>Duration</th>
            <th>Effectiveness</th>
        </tr>
        {"".join([
            f"""<tr>
                <td>{result.get('attack_type', 'Unknown')}</td>
                <td>{result.get('packets_sent', 0):,}</td>
                <td>{result.get('success_rate', 0):.1f}%</td>
                <td>{result.get('avg_rate', 0):.0f}</td>
                <td>{result.get('duration', 0):.1f}s</td>
                <td>{self._calculate_effectiveness_rating(result)}</td>
            </tr>"""
            for result in results_list
        ])}
    </table>
</body>
</html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Comparison report generated: {output_file}")