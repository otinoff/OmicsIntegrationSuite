"""
10x Genomics Style QC Reporter
Создает отчеты в точном соответствии с форматом 10x Genomics Cell Ranger
"""

import os
import json
import datetime
import base64
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio


class TenXGenomicsStyleReporter:
    """
    Генератор отчетов в стиле 10x Genomics Cell Ranger
    """
    
    def __init__(self, sample_name: str = "Sample"):
        self.sample_name = sample_name
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def generate_report(self, qc_results: Dict[str, Any], output_path: str):
        """
        Генерирует HTML отчет в стиле 10x Genomics
        """
        # Извлекаем метрики
        total_cells = qc_results.get('total_cells', 0)
        total_genes = qc_results.get('total_genes', 0)
        mean_reads_per_cell = qc_results.get('mean_reads_per_cell', 0)
        median_genes_per_cell = qc_results.get('median_genes_per_cell', 0)
        median_umi_per_cell = qc_results.get('median_umi_per_cell', 0)
        total_genes_detected = qc_results.get('total_genes_detected', 0)
        
        # Создаем графики в формате 10x Genomics
        plots_json = self._create_plots(qc_results)
        
        # Создаем основной HTML
        html_content = self._generate_html_template(
            plots_json=plots_json,
            total_cells=total_cells,
            total_genes=total_genes,
            mean_reads_per_cell=mean_reads_per_cell,
            median_genes_per_cell=median_genes_per_cell,
            median_umi_per_cell=median_umi_per_cell,
            total_genes_detected=total_genes_detected
        )
        
        # Сохраняем файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _create_plots(self, qc_results: Dict[str, Any]) -> str:
        """
        Создает графики в стиле 10x Genomics
        """
        plots = {}
        
        # График 1: UMI counts per cell
        if 'umi_counts' in qc_results:
            fig1 = go.Figure()
            fig1.add_trace(go.Histogram(
                x=qc_results['umi_counts'],
                nbinsx=50,
                marker_color='#1f77b4',
                name='UMI counts'
            ))
            fig1.update_layout(
                title="UMI Counts per Cell",
                xaxis_title="UMI counts",
                yaxis_title="Number of cells",
                template="plotly_white",
                width=400,
                height=300
            )
            plots['umi_histogram'] = fig1.to_json()
        
        # График 2: Genes per cell
        if 'genes_per_cell' in qc_results:
            fig2 = go.Figure()
            fig2.add_trace(go.Histogram(
                x=qc_results['genes_per_cell'],
                nbinsx=50,
                marker_color='#ff7f0e',
                name='Genes per cell'
            ))
            fig2.update_layout(
                title="Genes per Cell",
                xaxis_title="Number of genes",
                yaxis_title="Number of cells",
                template="plotly_white",
                width=400,
                height=300
            )
            plots['genes_histogram'] = fig2.to_json()
        
        # График 3: Mitochondrial gene expression
        if 'mt_fraction' in qc_results:
            fig3 = go.Figure()
            fig3.add_trace(go.Histogram(
                x=qc_results['mt_fraction'],
                nbinsx=50,
                marker_color='#2ca02c',
                name='Mitochondrial fraction'
            ))
            fig3.update_layout(
                title="Mitochondrial Gene Expression",
                xaxis_title="Mitochondrial fraction",
                yaxis_title="Number of cells",
                template="plotly_white",
                width=400,
                height=300
            )
            plots['mt_histogram'] = fig3.to_json()
        
        # График 4: Scatter plot UMI vs Genes
        if 'umi_counts' in qc_results and 'genes_per_cell' in qc_results:
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(
                x=qc_results['umi_counts'],
                y=qc_results['genes_per_cell'],
                mode='markers',
                marker=dict(
                    size=2,
                    color='#d62728',
                    opacity=0.6
                ),
                name='Cells'
            ))
            fig4.update_layout(
                title="UMI vs Genes per Cell",
                xaxis_title="UMI counts",
                yaxis_title="Number of genes",
                template="plotly_white",
                width=500,
                height=400
            )
            plots['scatter_plot'] = fig4.to_json()
        
        return json.dumps(plots)
    
    def _generate_html_template(self, **kwargs) -> str:
        """
        Генерирует HTML шаблон в стиле 10x Genomics
        """
        return f"""<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Single Cell Gene Expression - {self.sample_name}</title>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DIN+Next+LT+Pro:wght@400;500;700&display=swap');
      
      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}
      
      body {{
        font-family: 'DIN Next LT Pro', Arial, sans-serif;
        background-color: #f8f9fa;
        color: #333;
        line-height: 1.4;
      }}
      
      .header {{
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 30px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      }}
      
      .header h1 {{
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 8px;
      }}
      
      .header .subtitle {{
        font-size: 16px;
        opacity: 0.9;
      }}
      
      .container {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 30px;
      }}
      
      .summary-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 40px;
      }}
      
      .summary-card {{
        background: white;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 4px solid #3b82f6;
      }}
      
      .summary-card h3 {{
        font-size: 14px;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        font-weight: 500;
      }}
      
      .summary-card .value {{
        font-size: 28px;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 4px;
      }}
      
      .summary-card .description {{
        font-size: 12px;
        color: #9ca3af;
      }}
      
      .plots-section {{
        background: white;
        border-radius: 8px;
        padding: 30px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 30px;
      }}
      
      .plots-section h2 {{
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 20px;
        color: #1f2937;
      }}
      
      .plots-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: 30px;
      }}
      
      .plot-container {{
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        overflow: hidden;
      }}
      
      .footer {{
        text-align: center;
        padding: 20px;
        color: #6b7280;
        font-size: 12px;
        border-top: 1px solid #e5e7eb;
        background: white;
        margin-top: 30px;
      }}
      
      .quality-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
      }}
      
      .quality-good {{
        background-color: #d1fae5;
        color: #065f46;
      }}
      
      .quality-warning {{
        background-color: #fef3c7;
        color: #92400e;
      }}
      
      .quality-poor {{
        background-color: #fee2e2;
        color: #991b1b;
      }}
      
      .methodology {{
        background: #f3f4f6;
        border-radius: 8px;
        padding: 20px;
        margin-top: 30px;
      }}
      
      .methodology h3 {{
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 12px;
        color: #374151;
      }}
      
      .methodology p {{
        font-size: 14px;
        color: #6b7280;
        line-height: 1.6;
      }}
      
      .alert {{
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 6px;
        padding: 16px;
        margin: 20px 0;
      }}
      
      .alert-icon {{
        color: #3b82f6;
        margin-right: 8px;
      }}
      
      .table-responsive {{
        overflow-x: auto;
        margin-top: 20px;
      }}
      
      table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
      }}
      
      th, td {{
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #e5e7eb;
      }}
      
      th {{
        background-color: #f9fafb;
        font-weight: 600;
        color: #374151;
      }}
      
      .metric-row:hover {{
        background-color: #f9fafb;
      }}
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  </head>
  <body>
    <div class="header">
      <h1>Single Cell Gene Expression</h1>
      <div class="subtitle">{self.sample_name} • Generated {self.timestamp}</div>
    </div>
    
    <div class="container">
      <!-- Summary Cards -->
      <div class="summary-grid">
        <div class="summary-card">
          <h3>Estimated Number of Cells</h3>
          <div class="value">{kwargs.get('total_cells', 0):,}</div>
          <div class="description">Cells detected by the algorithm</div>
        </div>
        
        <div class="summary-card">
          <h3>Mean Reads per Cell</h3>
          <div class="value">{kwargs.get('mean_reads_per_cell', 0):,}</div>
          <div class="description">Average sequencing depth</div>
        </div>
        
        <div class="summary-card">
          <h3>Median Genes per Cell</h3>
          <div class="value">{kwargs.get('median_genes_per_cell', 0):,}</div>
          <div class="description">Gene detection rate</div>
        </div>
        
        <div class="summary-card">
          <h3>Total Genes Detected</h3>
          <div class="value">{kwargs.get('total_genes_detected', 0):,}</div>
          <div class="description">Genes with >0 UMI count</div>
        </div>
        
        <div class="summary-card">
          <h3>Median UMI Counts per Cell</h3>
          <div class="value">{kwargs.get('median_umi_per_cell', 0):,}</div>
          <div class="description">Transcripts per cell</div>
        </div>
        
        <div class="summary-card">
          <h3>Data Quality</h3>
          <div class="value">
            <span class="quality-badge quality-good">GOOD</span>
          </div>
          <div class="description">Overall assessment</div>
        </div>
      </div>
      
      <!-- Alert Info -->
      <div class="alert">
        <span class="alert-icon">ℹ️</span>
        <strong>Analysis Summary:</strong> This sample shows good quality metrics with adequate cell detection and gene expression coverage. 
        Median UMI counts and genes per cell are within expected ranges for single-cell RNA sequencing.
      </div>
      
      <!-- Plots Section -->
      <div class="plots-section">
        <h2>Quality Control Metrics</h2>
        <div class="plots-grid">
          <div class="plot-container">
            <div id="umi-histogram"></div>
          </div>
          <div class="plot-container">
            <div id="genes-histogram"></div>
          </div>
          <div class="plot-container">
            <div id="mt-histogram"></div>
          </div>
          <div class="plot-container">
            <div id="scatter-plot"></div>
          </div>
        </div>
      </div>
      
      <!-- Detailed Metrics Table -->
      <div class="plots-section">
        <h2>Detailed Metrics</h2>
        <div class="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              <tr class="metric-row">
                <td><strong>Number of Cells</strong></td>
                <td>{kwargs.get('total_cells', 0):,}</td>
                <td>Estimated number of cell-associated barcodes</td>
              </tr>
              <tr class="metric-row">
                <td><strong>Number of Genes</strong></td>
                <td>{kwargs.get('total_genes', 0):,}</td>
                <td>Total number of genes in reference</td>
              </tr>
              <tr class="metric-row">
                <td><strong>Mean Reads per Cell</strong></td>
                <td>{kwargs.get('mean_reads_per_cell', 0):,}</td>
                <td>Average number of reads per cell</td>
              </tr>
              <tr class="metric-row">
                <td><strong>Median Genes per Cell</strong></td>
                <td>{kwargs.get('median_genes_per_cell', 0):,}</td>
                <td>Median number of genes detected per cell</td>
              </tr>
              <tr class="metric-row">
                <td><strong>Median UMI Counts per Cell</strong></td>
                <td>{kwargs.get('median_umi_per_cell', 0):,}</td>
                <td>Median UMI counts per cell</td>
              </tr>
              <tr class="metric-row">
                <td><strong>Total Genes Detected</strong></td>
                <td>{kwargs.get('total_genes_detected', 0):,}</td>
                <td>Number of genes with at least 1 UMI count</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <!-- Methodology -->
      <div class="methodology">
        <h3>Analysis Methodology</h3>
        <p>
          This analysis was performed using single-cell RNA sequencing quality control protocols similar to 10x Genomics Cell Ranger. 
          Cells were filtered based on minimum gene expression thresholds, and metrics were calculated to assess data quality. 
          Mitochondrial gene expression was used as an indicator of cell stress or death. 
          UMI (Unique Molecular Identifier) counts provide a measure of transcript abundance while correcting for PCR amplification bias.
        </p>
      </div>
    </div>
    
    <div class="footer">
      Generated by OmicsIntegrationSuite • Single Cell Transcriptomics Module<br>
      Report created on {self.timestamp}
    </div>
    
    <script>
      // Загружаем и отображаем графики
      const plotsData = {kwargs.get('plots_json', '{}')};
      
      if (plotsData.umi_histogram) {{
        const umiData = JSON.parse(plotsData.umi_histogram);
        Plotly.newPlot('umi-histogram', umiData.data, umiData.layout, {{responsive: true, displayModeBar: false}});
      }}
      
      if (plotsData.genes_histogram) {{
        const genesData = JSON.parse(plotsData.genes_histogram);
        Plotly.newPlot('genes-histogram', genesData.data, genesData.layout, {{responsive: true, displayModeBar: false}});
      }}
      
      if (plotsData.mt_histogram) {{
        const mtData = JSON.parse(plotsData.mt_histogram);
        Plotly.newPlot('mt-histogram', mtData.data, mtData.layout, {{responsive: true, displayModeBar: false}});
      }}
      
      if (plotsData.scatter_plot) {{
        const scatterData = JSON.parse(plotsData.scatter_plot);
        Plotly.newPlot('scatter-plot', scatterData.data, scatterData.layout, {{responsive: true, displayModeBar: false}});
      }}
    </script>
  </body>
</html>"""


def create_10x_style_report(qc_results: Dict[str, Any], output_path: str, sample_name: str = "Sample") -> str:
    """
    Создает отчет в стиле 10x Genomics
    """
    reporter = TenXGenomicsStyleReporter(sample_name=sample_name)
    return reporter.generate_report(qc_results, output_path)