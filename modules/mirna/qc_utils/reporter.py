#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
miRNA Reporter - HTML report generation for miRNA-seq QC
Generates comprehensive HTML reports with visual metrics and plots
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class MiRNAReporter:
    """Generate HTML reports for miRNA-seq QC pipeline."""

    def generate_html_report(
        self,
        metadata: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        Generate comprehensive HTML report from pipeline metadata

        Args:
            metadata: Pipeline metadata dictionary
            output_path: Path to save HTML report

        Returns:
            str: Path to generated HTML file
        """
        html = self._create_html_template(metadata)
        Path(output_path).write_text(html, encoding='utf-8')
        return output_path

    def _create_html_template(self, metadata: Dict[str, Any]) -> str:
        """
        Create HTML template with miRNA-seq specific metrics

        Args:
            metadata: Pipeline metadata dictionary

        Returns:
            HTML string
        """
        # Extract data
        sample_id = metadata.get('sample_id', 'Unknown')
        status = metadata.get('status', 'unknown')
        stages = metadata.get('stages', {})

        # Determine status color
        status_color = {
            'completed': '#27ae60',
            'warning': '#f39c12',
            'failed': '#e74c3c'
        }.get(status, '#95a5a6')

        # Generate timestamp
        timestamp = metadata.get('end_time', datetime.now().isoformat())

        # Extract stage metrics
        trim_data = stages.get('trimming', {})
        align_data = stages.get('alignment', {})
        count_data = stages.get('counting', {})
        val_data = stages.get('validation', {})

        # Top miRNAs
        top_mirnas = count_data.get('top_mirnas', [])[:10]

        # Create HTML
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>miRNA QC Report - {sample_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
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
        }}
        .metric-card h3 {{
            color: #764ba2;
            font-size: 0.9rem;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-card .value {{
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }}
        .metric-card .label {{
            color: #666;
            font-size: 0.9rem;
            margin-top: 5px;
        }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .section h2 {{
            color: #764ba2;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .pipeline-stage {{
            margin-bottom: 25px;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 5px;
        }}
        .pipeline-stage h3 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        .pipeline-stage .metric {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
        }}
        .pipeline-stage .metric .key {{
            color: #666;
        }}
        .pipeline-stage .metric .value {{
            font-weight: bold;
            color: #333;
        }}
        .mirna-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .mirna-table th,
        .mirna-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .mirna-table th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        .mirna-table tr:hover {{
            background: #f8f9fa;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #ecf0f1;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.3s ease;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9rem;
        }}
        .check-icon {{
            color: #27ae60;
            font-weight: bold;
        }}
        .warning-icon {{
            color: #f39c12;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🧬 miRNA-seq Quality Control Report</h1>
            <p><strong>Sample:</strong> {sample_id}</p>
            <p><strong>Generated:</strong> {timestamp}</p>
            <div class="status">{status.upper()}</div>
        </div>

        <!-- Summary Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Input Reads</h3>
                <div class="value">{trim_data.get('total_reads', 0):,}</div>
                <div class="label">Total FASTQ reads</div>
            </div>
            <div class="metric-card">
                <h3>Filtered Reads</h3>
                <div class="value">{trim_data.get('filtered_reads', 0):,}</div>
                <div class="label">{trim_data.get('percent_kept', 0):.1f}% kept (18-25 nt)</div>
            </div>
            <div class="metric-card">
                <h3>Aligned Reads</h3>
                <div class="value">{align_data.get('aligned_reads', 0):,}</div>
                <div class="label">{align_data.get('alignment_rate', 0):.1f}% to miRBase</div>
            </div>
            <div class="metric-card">
                <h3>Unique miRNAs</h3>
                <div class="value">{count_data.get('unique_mirnas', 0):,}</div>
                <div class="label">Detected species</div>
            </div>
        </div>

        <!-- Pipeline Stages -->
        <div class="section">
            <h2>Pipeline Stages</h2>

            <!-- Stage 1: Trimming -->
            <div class="pipeline-stage">
                <h3><span class="check-icon">✓</span> Stage 1: Adapter Trimming & Filtering</h3>
                <div class="metric">
                    <span class="key">Method:</span>
                    <span class="value">{trim_data.get('method', 'unknown')}</span>
                </div>
                <div class="metric">
                    <span class="key">Total reads:</span>
                    <span class="value">{trim_data.get('total_reads', 0):,}</span>
                </div>
                <div class="metric">
                    <span class="key">Filtered reads (18-25 nt):</span>
                    <span class="value">{trim_data.get('filtered_reads', 0):,}</span>
                </div>
                <div class="metric">
                    <span class="key">Pass rate:</span>
                    <span class="value">{trim_data.get('percent_kept', 0):.1f}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {trim_data.get('percent_kept', 0)}%;">
                        {trim_data.get('percent_kept', 0):.1f}%
                    </div>
                </div>
            </div>

            <!-- Stage 2: Alignment -->
            <div class="pipeline-stage">
                <h3><span class="check-icon">✓</span> Stage 2: Alignment to miRBase</h3>
                <div class="metric">
                    <span class="key">Method:</span>
                    <span class="value">{align_data.get('method', 'unknown')}</span>
                </div>
                <div class="metric">
                    <span class="key">Total reads:</span>
                    <span class="value">{align_data.get('total_reads', 0):,}</span>
                </div>
                <div class="metric">
                    <span class="key">Aligned reads:</span>
                    <span class="value">{align_data.get('aligned_reads', 0):,}</span>
                </div>
                <div class="metric">
                    <span class="key">Alignment rate:</span>
                    <span class="value">{align_data.get('alignment_rate', 0):.1f}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {align_data.get('alignment_rate', 0)}%;">
                        {align_data.get('alignment_rate', 0):.1f}%
                    </div>
                </div>
            </div>

            <!-- Stage 3: Counting -->
            <div class="pipeline-stage">
                <h3><span class="check-icon">✓</span> Stage 3: miRNA Counting</h3>
                <div class="metric">
                    <span class="key">Aligned reads:</span>
                    <span class="value">{count_data.get('aligned_reads', 0):,}</span>
                </div>
                <div class="metric">
                    <span class="key">Unique miRNAs:</span>
                    <span class="value">{count_data.get('unique_mirnas', 0):,}</span>
                </div>
            </div>

            <!-- Stage 4: Validation -->
            {self._generate_validation_html(val_data) if val_data else ''}
        </div>

        <!-- Top miRNAs -->
        {self._generate_top_mirnas_html(top_mirnas, count_data.get('aligned_reads', 0))}

        <!-- Footer -->
        <div class="footer">
            <p>Generated by OmicsIntegrationSuite miRNA QC Pipeline</p>
            <p>ТЗ compliant report per contract requirements (Sections 1.2.4, 1.3.4)</p>
        </div>
    </div>
</body>
</html>"""

    def _generate_validation_html(self, val_data: Dict) -> str:
        """Generate HTML for validation stage"""
        if not val_data:
            return ""

        icon = "check-icon" if val_data.get('validation_rate', 0) == 100 else "warning-icon"
        symbol = "✓" if val_data.get('validation_rate', 0) == 100 else "⚠"

        return f"""
            <div class="pipeline-stage">
                <h3><span class="{icon}">{symbol}</span> Stage 4: ID Validation</h3>
                <div class="metric">
                    <span class="key">Total miRNAs:</span>
                    <span class="value">{val_data.get('total_mirnas', 0):,}</span>
                </div>
                <div class="metric">
                    <span class="key">Valid IDs:</span>
                    <span class="value">{val_data.get('valid_mirnas', 0):,}</span>
                </div>
                <div class="metric">
                    <span class="key">Invalid IDs:</span>
                    <span class="value">{val_data.get('invalid_mirnas', 0):,}</span>
                </div>
                <div class="metric">
                    <span class="key">Validation rate:</span>
                    <span class="value">{val_data.get('validation_rate', 0):.1f}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {val_data.get('validation_rate', 0)}%;">
                        {val_data.get('validation_rate', 0):.1f}%
                    </div>
                </div>
            </div>"""

    def _generate_top_mirnas_html(self, top_mirnas: List, total_reads: int) -> str:
        """Generate HTML table for top abundant miRNAs"""
        if not top_mirnas:
            return ""

        rows = []
        for i, (mirna_id, count) in enumerate(top_mirnas, 1):
            pct = (count / total_reads * 100) if total_reads > 0 else 0
            rows.append(f"""
                <tr>
                    <td>{i}</td>
                    <td>{mirna_id}</td>
                    <td>{count:,}</td>
                    <td>{pct:.2f}%</td>
                </tr>""")

        return f"""
        <div class="section">
            <h2>Top Abundant miRNAs</h2>
            <p>Top 10 most abundant miRNAs detected in this sample:</p>
            <table class="mirna-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>miRNA ID</th>
                        <th>Read Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>"""


def generate_html_report(metadata_file: str, output_file: str) -> str:
    """
    Convenience function to generate HTML report from metadata JSON

    Args:
        metadata_file: Path to metadata JSON file
        output_file: Path to output HTML file

    Returns:
        str: Path to generated HTML file
    """
    # Load metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    # Generate report
    reporter = MiRNAReporter()
    return reporter.generate_html_report(metadata, output_file)


# Test function
if __name__ == "__main__":
    import sys

    print("Testing miRNA Reporter")
    print("=" * 50)

    # Test metadata path
    test_metadata = Path(__file__).parent.parent.parent.parent.parent / \
        "Michael/01_Projects/2025-09-11_Contract_Omics_Platform/iterations" / \
        "Iteration_006_miRNA_Implementation/test_data/pipeline_output/test_pipeline_metadata.json"

    if test_metadata.exists():
        print(f"\n✓ Found test metadata: {test_metadata}")

        # Generate report
        output_html = test_metadata.parent / "test_pipeline_report.html"

        print(f"\nGenerating HTML report...")
        report_path = generate_html_report(str(test_metadata), str(output_html))

        print(f"\n✓ Report generated: {report_path}")
        print(f"  Open in browser to view")

    else:
        print("\n⚠ Test metadata not found. Run test_full_pipeline.py first!")
        print("Ready for report generation!")
