"""
Reporter - Simple report generation for FASTQ analysis
Supports text, JSON, and HTML output formats
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class Reporter:
    """Generate reports in different formats."""
    
    def print_summary(self, metrics: Dict[str, Any], min_q30: float = 80):
        """
        Print summary to console.
        
        Args:
            metrics: Dictionary containing analysis metrics
            min_q30: Minimum Q30 threshold for warnings
        """
        # Status symbols for console output (ASCII-safe for Windows)
        status_symbol = {
            'PASS': '[OK]',
            'WARNING': '[!]',
            'FAIL': '[X]',
            'UNKNOWN': '[?]'
        }.get(metrics.get('status', 'UNKNOWN'), '[?]')
        
        # Print header
        print(f"\n{'=' * 50}")
        print("FASTQ Quality Report")
        print('=' * 50)
        
        # File info
        print(f"File: {metrics.get('filename', 'unknown')}")
        print(f"Size: {metrics.get('file_size_mb', 0):.1f} MB")
        print(f"Status: {status_symbol} {metrics.get('status', 'UNKNOWN')}")
        
        # Quality metrics
        print("\nQuality Metrics:")
        print(f"  Total reads:     {metrics.get('total_reads', 0):,}")
        print(f"  Total bases:     {metrics.get('total_bases', 0):,}")
        print(f"  Avg read length: {metrics.get('avg_read_length', 0):.1f} bp")
        print(f"  Min read length: {metrics.get('min_read_length', 0)} bp")
        print(f"  Max read length: {metrics.get('max_read_length', 0)} bp")
        
        print("\nQuality Scores:")
        print(f"  Avg quality:     {metrics.get('avg_quality_score', 0):.1f}")
        print(f"  Q20 percentage:  {metrics.get('q20_percentage', 0):.1f}%")
        print(f"  Q30 percentage:  {metrics.get('q30_percentage', 0):.1f}%")
        
        print("\nBase Composition:")
        print(f"  GC content:      {metrics.get('gc_content', 0):.1f}%")
        print(f"  N content:       {metrics.get('n_percentage', 0):.3f}%")
        
        # Warnings
        q30 = metrics.get('q30_percentage', 0)
        if q30 < min_q30:
            print(f"\n[!] Warning: Q30 ({q30:.1f}%) is below threshold ({min_q30}%)")
        
        n_percent = metrics.get('n_percentage', 0)
        if n_percent > 5:
            print(f"[!] Warning: High N content ({n_percent:.1f}%)")
        
        print('=' * 50)
    
    def generate_html(self, metrics: Dict[str, Any], output_path: str):
        """
        Generate HTML report.
        
        Args:
            metrics: Dictionary containing analysis metrics
            output_path: Path to save HTML report
        """
        html = self._create_html_template(metrics)
        Path(output_path).write_text(html)
    
    def _create_html_template(self, metrics: Dict[str, Any]) -> str:
        """
        Create HTML template with metrics.
        
        Args:
            metrics: Dictionary containing analysis metrics
            
        Returns:
            HTML string
        """
        # Determine status color
        status_color = {
            'PASS': '#27ae60',
            'WARNING': '#f39c12', 
            'FAIL': '#e74c3c',
            'UNKNOWN': '#95a5a6'
        }.get(metrics.get('status', 'UNKNOWN'), '#95a5a6')
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FASTQ Quality Report - {metrics.get('filename', 'unknown')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f6fa;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        .header p {{
            opacity: 0.9;
            margin: 5px 0;
        }}
        .status {{
            display: inline-block;
            background: {status_color};
            color: white;
            padding: 5px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        .metric-label {{
            color: #7f8c8d;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        .metric-value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #2c3e50;
        }}
        .metric-value.good {{
            color: #27ae60;
        }}
        .metric-value.warning {{
            color: #f39c12;
        }}
        .metric-value.bad {{
            color: #e74c3c;
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .section h2 {{
            color: #34495e;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #7f8c8d;
        }}
        .footer {{
            text-align: center;
            color: #7f8c8d;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>FASTQ Quality Report</h1>
            <p><strong>File:</strong> {metrics.get('filename', 'unknown')}</p>
            <p><strong>Size:</strong> {metrics.get('file_size_mb', 0):.1f} MB</p>
            <p><strong>Analysis Date:</strong> {timestamp}</p>
            <div class="status">{metrics.get('status', 'UNKNOWN')}</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Reads</div>
                <div class="metric-value">{metrics.get('total_reads', 0):,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Average Read Length</div>
                <div class="metric-value">{metrics.get('avg_read_length', 0):.0f} bp</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Q30 Percentage</div>
                <div class="metric-value {self._get_q30_class(metrics.get('q30_percentage', 0))}">{metrics.get('q30_percentage', 0):.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">GC Content</div>
                <div class="metric-value">{metrics.get('gc_content', 0):.1f}%</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Detailed Metrics</h2>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Total Bases</td>
                        <td>{metrics.get('total_bases', 0):,}</td>
                        <td>-</td>
                    </tr>
                    <tr>
                        <td>Average Quality Score</td>
                        <td>{metrics.get('avg_quality_score', 0):.1f}</td>
                        <td>{self._get_status_text(metrics.get('avg_quality_score', 0) >= 20)}</td>
                    </tr>
                    <tr>
                        <td>Q20 Percentage</td>
                        <td>{metrics.get('q20_percentage', 0):.1f}%</td>
                        <td>{self._get_status_text(metrics.get('q20_percentage', 0) >= 90)}</td>
                    </tr>
                    <tr>
                        <td>Q30 Percentage</td>
                        <td>{metrics.get('q30_percentage', 0):.1f}%</td>
                        <td>{self._get_status_text(metrics.get('q30_percentage', 0) >= 80)}</td>
                    </tr>
                    <tr>
                        <td>N Content</td>
                        <td>{metrics.get('n_percentage', 0):.3f}%</td>
                        <td>{self._get_status_text(metrics.get('n_percentage', 0) < 5)}</td>
                    </tr>
                    <tr>
                        <td>Min Read Length</td>
                        <td>{metrics.get('min_read_length', 0)} bp</td>
                        <td>-</td>
                    </tr>
                    <tr>
                        <td>Max Read Length</td>
                        <td>{metrics.get('max_read_length', 0)} bp</td>
                        <td>-</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated by FastQCLI v1.0.0 | {timestamp}</p>
            <p>Minimalist FASTQ Quality Control Tool</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _get_q30_class(self, q30_percentage: float) -> str:
        """Get CSS class for Q30 percentage color."""
        if q30_percentage >= 80:
            return "good"
        elif q30_percentage >= 50:
            return "warning"
        else:
            return "bad"
    
    def _get_status_text(self, passed: bool) -> str:
        """Get status text with color."""
        if passed:
            return '<span style="color: #27ae60;">Pass</span>'
        else:
            return '<span style="color: #e74c3c;">Fail</span>'