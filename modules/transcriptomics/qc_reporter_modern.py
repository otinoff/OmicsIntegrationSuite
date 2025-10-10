# -*- coding: utf-8 -*-
import sys

# Исправление кодировки для Windows терминала
if sys.platform == 'win32':
    import codecs
    try:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, OSError):
        pass  # Кодировка уже настроена правильно

import os
import json
import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

class ModernTranscriptomicsQCReporter:
    """
    Современный репортер для QC отчетов по транскриптомике
    в стиле MultiQC/10x Genomics с темно-синим header и боковой навигацией
    """
    
    def __init__(self):
        self.report_data = {}
        self.qc_thresholds = {
            'bulk_rna_seq': {
                'alignment_rate': {'pass': 80, 'warn': 60},
                'rrna_rate': {'pass': 5, 'warn': 10},
                'duplication_rate': {'pass': 20, 'warn': 40},
                'gc_content': {'pass_min': 40, 'pass_max': 60, 'warn_min': 35, 'warn_max': 65}
            },
            'scrna_seq': {
                'mean_reads_per_cell': {'pass': 20000, 'warn': 10000},
                'median_genes_per_cell': {'pass': 2000, 'warn': 1000},
                'valid_barcodes': {'pass': 75, 'warn': 50},
                'cells_detected': {'pass': 1000, 'warn': 500}
            }
        }
        
    def _get_qc_status(self, value, metric, data_type):
        """Определение статуса QC (pass/warn/fail)"""
        if data_type not in self.qc_thresholds:
            return 'unknown'
            
        thresholds = self.qc_thresholds[data_type].get(metric, {})
        
        if not thresholds:
            return 'unknown'
            
        if 'pass' in thresholds and 'warn' in thresholds:
            if metric in ['rrna_rate', 'duplication_rate']:  # Обратная логика для негативных метрик
                if value <= thresholds['pass']:
                    return 'pass'
                elif value <= thresholds['warn']:
                    return 'warn'
                else:
                    return 'fail'
            else:  # Прямая логика для позитивных метрик
                if value >= thresholds['pass']:
                    return 'pass'
                elif value >= thresholds['warn']:
                    return 'warn'
                else:
                    return 'fail'
        elif 'pass_min' in thresholds:  # Для метрик с диапазоном (GC content)
            if thresholds['pass_min'] <= value <= thresholds['pass_max']:
                return 'pass'
            elif thresholds['warn_min'] <= value <= thresholds['warn_max']:
                return 'warn'
            else:
                return 'fail'
                
        return 'unknown'
    
    def _get_status_color(self, status):
        """Получение цвета для статуса"""
        colors = {
            'pass': '#28a745',    # Зеленый
            'warn': '#ffc107',    # Желтый
            'fail': '#dc3545',    # Красный
            'unknown': '#6c757d'  # Серый
        }
        return colors.get(status, '#6c757d')
    
    def _get_status_icon(self, status):
        """Получение иконки для статуса"""
        icons = {
            'pass': '✓',
            'warn': '⚠',
            'fail': '✗',
            'unknown': '?'
        }
        return icons.get(status, '?')
    
    def _create_metric_card(self, title, value, unit='', status='unknown', description=''):
        """Создание карточки метрики"""
        color = self._get_status_color(status)
        icon = self._get_status_icon(status)
        
        return f"""
        <div class="metric-card" style="border-left: 4px solid {color};">
            <div class="metric-header">
                <span class="metric-icon" style="color: {color};">{icon}</span>
                <span class="metric-title">{title}</span>
            </div>
            <div class="metric-value">{value}{unit}</div>
            {f'<div class="metric-description">{description}</div>' if description else ''}
        </div>
        """
    
    def _create_summary_table(self, df, data_type):
        """Создание таблицы общей статистики"""
        if df.empty:
            return "<p>Нет данных для отображения</p>"
        
        # Подготовка данных для таблицы
        table_rows = []
        for _, row in df.iterrows():
            sample = row.get('sample', 'Unknown')
            
            cells = []
            cells.append(f'<td class="sample-name">{sample}</td>')
            
            # Определяем метрики в зависимости от типа данных
            if data_type == 'bulk_rna_seq':
                metrics = ['total_reads', 'alignment_rate', 'rrna_rate', 'duplication_rate', 'gc_content']
                for metric in metrics:
                    if metric in row:
                        value = row[metric]
                        if pd.isna(value):
                            cells.append('<td>N/A</td>')
                        else:
                            status = self._get_qc_status(value, metric, data_type)
                            color = self._get_status_color(status)
                            
                            if metric == 'total_reads':
                                formatted_value = f"{value/1e6:.1f}M"
                            elif metric in ['alignment_rate', 'rrna_rate', 'duplication_rate', 'gc_content']:
                                formatted_value = f"{value:.1f}%"
                            else:
                                formatted_value = str(value)
                                
                            cells.append(f'<td style="color: {color}; font-weight: bold;">{formatted_value}</td>')
                    else:
                        cells.append('<td>N/A</td>')
            
            elif data_type == 'scrna_seq':
                metrics = ['estimated_cells', 'mean_reads_per_cell', 'median_genes_per_cell', 'valid_barcodes']
                for metric in metrics:
                    if metric in row:
                        value = row[metric]
                        if pd.isna(value):
                            cells.append('<td>N/A</td>')
                        else:
                            status = self._get_qc_status(value, metric, data_type)
                            color = self._get_status_color(status)
                            
                            if metric == 'estimated_cells':
                                formatted_value = f"{int(value):,}"
                            elif metric in ['mean_reads_per_cell', 'median_genes_per_cell']:
                                formatted_value = f"{int(value):,}"
                            elif metric == 'valid_barcodes':
                                formatted_value = f"{value:.1f}%"
                            else:
                                formatted_value = str(value)
                                
                            cells.append(f'<td style="color: {color}; font-weight: bold;">{formatted_value}</td>')
                    else:
                        cells.append('<td>N/A</td>')
            
            table_rows.append('<tr>' + ''.join(cells) + '</tr>')
        
        # Заголовки таблицы
        if data_type == 'bulk_rna_seq':
            headers = ['Sample', 'Total Reads', 'Alignment Rate', 'rRNA Rate', 'Duplication Rate', 'GC Content']
        elif data_type == 'scrna_seq':
            headers = ['Sample', 'Estimated Cells', 'Reads/Cell', 'Genes/Cell', 'Valid Barcodes']
        else:
            headers = ['Sample']
        
        header_html = '<tr>' + ''.join([f'<th>{h}</th>' for h in headers]) + '</tr>'
        
        return f"""
        <div class="table-container">
            <table class="summary-table">
                <thead>{header_html}</thead>
                <tbody>{''.join(table_rows)}</tbody>
            </table>
        </div>
        """
    
    def _create_modern_plot(self, fig, plot_id):
        """Создание современного интерактивного графика"""
        # Применяем современную тему
        fig.update_layout(
            template='plotly_white',
            font=dict(family="Segoe UI, Arial, sans-serif", size=12),
            title_font=dict(size=16, color='#2c3e50'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=60, r=60, t=80, b=60),
            hovermode='closest'
        )
        
        # Обновляем оси
        fig.update_xaxes(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            showline=True,
            linecolor='rgba(0,0,0,0.2)'
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            showline=True,
            linecolor='rgba(0,0,0,0.2)'
        )
        
        # Конвертируем в HTML
        plot_html = pio.to_html(fig, include_plotlyjs=False, div_id=plot_id)
        
        return f"""
        <div class="plot-container" id="{plot_id}_container">
            {plot_html}
        </div>
        """
    
    def _create_bulk_rnaseq_plots(self, bulk_data):
        """Создание графиков для bulk RNA-seq"""
        plots_html = []
        
        if bulk_data.empty:
            return ["<p>Нет данных для создания графиков bulk RNA-seq</p>"]
        
        try:
            # 1. Alignment Rate Bar Plot
            fig = go.Figure()
            
            colors = [self._get_status_color(self._get_qc_status(rate, 'alignment_rate', 'bulk_rna_seq')) 
                     for rate in bulk_data['alignment_rate']]
            
            fig.add_trace(go.Bar(
                x=bulk_data['sample'],
                y=bulk_data['alignment_rate'],
                marker_color=colors,
                hovertemplate='Sample: %{x}<br>Alignment Rate: %{y:.1f}%<extra></extra>',
                name='Alignment Rate'
            ))
            
            fig.update_layout(
                title='Alignment Rate per Sample',
                xaxis_title='Sample',
                yaxis_title='Alignment Rate (%)',
                yaxis=dict(range=[0, 100])
            )
            
            # Добавляем линии пороговых значений
            fig.add_hline(y=80, line_dash="dash", line_color="green", 
                         annotation_text="Pass Threshold (80%)")
            fig.add_hline(y=60, line_dash="dash", line_color="orange", 
                         annotation_text="Warning Threshold (60%)")
            
            plots_html.append(self._create_modern_plot(fig, 'alignment_rate_plot'))
            
            # 2. rRNA Contamination Plot
            fig = go.Figure()
            
            colors = [self._get_status_color(self._get_qc_status(rate, 'rrna_rate', 'bulk_rna_seq')) 
                     for rate in bulk_data['rrna_rate']]
            
            fig.add_trace(go.Bar(
                x=bulk_data['sample'],
                y=bulk_data['rrna_rate'],
                marker_color=colors,
                hovertemplate='Sample: %{x}<br>rRNA Rate: %{y:.1f}%<extra></extra>',
                name='rRNA Rate'
            ))
            
            fig.update_layout(
                title='rRNA Contamination per Sample',
                xaxis_title='Sample',
                yaxis_title='rRNA Rate (%)'
            )
            
            fig.add_hline(y=5, line_dash="dash", line_color="green", 
                         annotation_text="Pass Threshold (≤5%)")
            fig.add_hline(y=10, line_dash="dash", line_color="orange", 
                         annotation_text="Warning Threshold (≤10%)")
            
            plots_html.append(self._create_modern_plot(fig, 'rrna_rate_plot'))
            
            # 3. GC Content Distribution
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=bulk_data['gc_content'],
                nbinsx=20,
                marker_color='rgba(58, 71, 80, 0.6)',
                name='GC Content Distribution'
            ))
            
            fig.update_layout(
                title='GC Content Distribution',
                xaxis_title='GC Content (%)',
                yaxis_title='Frequency'
            )
            
            # Добавляем вертикальные линии для нормального диапазона
            fig.add_vline(x=40, line_dash="dash", line_color="green", 
                         annotation_text="Normal Range Start (40%)")
            fig.add_vline(x=60, line_dash="dash", line_color="green", 
                         annotation_text="Normal Range End (60%)")
            
            plots_html.append(self._create_modern_plot(fig, 'gc_content_plot'))
            
            # 4. Sample Correlation Heatmap
            if len(bulk_data) > 1:
                # Создаем корреляционную матрицу на основе метрик
                metrics_for_corr = ['alignment_rate', 'rrna_rate', 'duplication_rate', 'gc_content']
                available_metrics = [m for m in metrics_for_corr if m in bulk_data.columns]
                
                if len(available_metrics) >= 2:
                    corr_data = bulk_data[available_metrics].corr()
                    
                    fig = go.Figure(data=go.Heatmap(
                        z=corr_data.values,
                        x=corr_data.columns,
                        y=corr_data.columns,
                        colorscale='RdBu',
                        zmid=0,
                        text=corr_data.values,
                        texttemplate="%{text:.2f}",
                        hovertemplate='X: %{x}<br>Y: %{y}<br>Correlation: %{z:.2f}<extra></extra>'
                    ))
                    
                    fig.update_layout(
                        title='QC Metrics Correlation Matrix',
                        width=500,
                        height=500
                    )
                    
                    plots_html.append(self._create_modern_plot(fig, 'correlation_heatmap'))
            
        except Exception as e:
            plots_html.append(f"<p>Ошибка создания графиков: {str(e)}</p>")
        
        return plots_html
    
    def _create_scrna_plots(self, scrna_data):
        """Создание графиков для scRNA-seq"""
        plots_html = []
        
        if scrna_data.empty:
            return ["<p>Нет данных для создания графиков scRNA-seq</p>"]
        
        try:
            # 1. Cells Detected
            fig = go.Figure()
            
            colors = [self._get_status_color(self._get_qc_status(cells, 'cells_detected', 'scrna_seq')) 
                     for cells in scrna_data['estimated_cells']]
            
            fig.add_trace(go.Bar(
                x=scrna_data['sample'],
                y=scrna_data['estimated_cells'],
                marker_color=colors,
                hovertemplate='Sample: %{x}<br>Estimated Cells: %{y:,.0f}<extra></extra>',
                name='Estimated Cells'
            ))
            
            fig.update_layout(
                title='Estimated Number of Cells',
                xaxis_title='Sample',
                yaxis_title='Number of Cells'
            )
            
            fig.add_hline(y=1000, line_dash="dash", line_color="green", 
                         annotation_text="Pass Threshold (≥1,000)")
            fig.add_hline(y=500, line_dash="dash", line_color="orange", 
                         annotation_text="Warning Threshold (≥500)")
            
            plots_html.append(self._create_modern_plot(fig, 'cells_detected_plot'))
            
            # 2. Reads per Cell vs Genes per Cell Scatter
            if 'mean_reads_per_cell' in scrna_data.columns and 'median_genes_per_cell' in scrna_data.columns:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=scrna_data['mean_reads_per_cell'],
                    y=scrna_data['median_genes_per_cell'],
                    mode='markers',
                    marker=dict(
                        size=12,
                        color=scrna_data['valid_barcodes'] if 'valid_barcodes' in scrna_data.columns else 'blue',
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Valid Barcodes (%)")
                    ),
                    text=scrna_data['sample'],
                    hovertemplate='Sample: %{text}<br>Reads/Cell: %{x:,.0f}<br>Genes/Cell: %{y:,.0f}<extra></extra>',
                    name='Samples'
                ))
                
                fig.update_layout(
                    title='Reads per Cell vs Genes per Cell',
                    xaxis_title='Mean Reads per Cell',
                    yaxis_title='Median Genes per Cell'
                )
                
                plots_html.append(self._create_modern_plot(fig, 'reads_vs_genes_plot'))
            
            # 3. Valid Barcodes Distribution
            if 'valid_barcodes' in scrna_data.columns:
                fig = go.Figure()
                
                colors = [self._get_status_color(self._get_qc_status(vb, 'valid_barcodes', 'scrna_seq')) 
                         for vb in scrna_data['valid_barcodes']]
                
                fig.add_trace(go.Bar(
                    x=scrna_data['sample'],
                    y=scrna_data['valid_barcodes'],
                    marker_color=colors,
                    hovertemplate='Sample: %{x}<br>Valid Barcodes: %{y:.1f}%<extra></extra>',
                    name='Valid Barcodes'
                ))
                
                fig.update_layout(
                    title='Valid Barcodes Percentage',
                    xaxis_title='Sample',
                    yaxis_title='Valid Barcodes (%)',
                    yaxis=dict(range=[0, 100])
                )
                
                fig.add_hline(y=75, line_dash="dash", line_color="green", 
                             annotation_text="Pass Threshold (≥75%)")
                fig.add_hline(y=50, line_dash="dash", line_color="orange", 
                             annotation_text="Warning Threshold (≥50%)")
                
                plots_html.append(self._create_modern_plot(fig, 'valid_barcodes_plot'))
            
        except Exception as e:
            plots_html.append(f"<p>Ошибка создания графиков scRNA-seq: {str(e)}</p>")
        
        return plots_html
    
    def generate_modern_report(self, bulk_data=None, scrna_data=None, output_path="modern_qc_report.html"):
        """Генерация современного отчета QC"""
        
        # Подготовка данных
        if bulk_data is None:
            bulk_data = pd.DataFrame()
        if scrna_data is None:
            scrna_data = pd.DataFrame()
        
        # Создание графиков
        bulk_plots = self._create_bulk_rnaseq_plots(bulk_data) if not bulk_data.empty else []
        scrna_plots = self._create_scrna_plots(scrna_data) if not scrna_data.empty else []
        
        # Создание summary карточек
        summary_cards = []
        
        if not bulk_data.empty:
            avg_alignment = bulk_data['alignment_rate'].mean()
            avg_rrna = bulk_data['rrna_rate'].mean()
            total_samples_bulk = len(bulk_data)
            
            summary_cards.extend([
                self._create_metric_card(
                    "Bulk RNA-seq Samples", 
                    total_samples_bulk, 
                    status='pass'
                ),
                self._create_metric_card(
                    "Avg Alignment Rate", 
                    f"{avg_alignment:.1f}", 
                    "%",
                    self._get_qc_status(avg_alignment, 'alignment_rate', 'bulk_rna_seq')
                ),
                self._create_metric_card(
                    "Avg rRNA Rate", 
                    f"{avg_rrna:.1f}", 
                    "%",
                    self._get_qc_status(avg_rrna, 'rrna_rate', 'bulk_rna_seq')
                )
            ])
        
        if not scrna_data.empty:
            avg_cells = scrna_data['estimated_cells'].mean()
            avg_reads = scrna_data['mean_reads_per_cell'].mean()
            total_samples_scrna = len(scrna_data)
            
            summary_cards.extend([
                self._create_metric_card(
                    "scRNA-seq Samples", 
                    total_samples_scrna, 
                    status='pass'
                ),
                self._create_metric_card(
                    "Avg Estimated Cells", 
                    f"{avg_cells:,.0f}", 
                    "",
                    self._get_qc_status(avg_cells, 'cells_detected', 'scrna_seq')
                ),
                self._create_metric_card(
                    "Avg Reads/Cell", 
                    f"{avg_reads:,.0f}", 
                    "",
                    self._get_qc_status(avg_reads, 'mean_reads_per_cell', 'scrna_seq')
                )
            ])
        
        # HTML шаблон с современным дизайном
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RNA-seq Quality Control Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            color: #333;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 20px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            height: 80px;
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        
        .header .subtitle {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .container {{
            display: flex;
            margin-top: 80px;
            min-height: calc(100vh - 80px);
        }}
        
        .sidebar {{
            width: 280px;
            background: white;
            border-right: 1px solid #e9ecef;
            padding: 20px 0;
            position: fixed;
            height: calc(100vh - 80px);
            overflow-y: auto;
        }}
        
        .sidebar ul {{
            list-style: none;
        }}
        
        .sidebar li {{
            margin: 0;
        }}
        
        .sidebar a {{
            display: block;
            padding: 12px 25px;
            color: #495057;
            text-decoration: none;
            border-left: 3px solid transparent;
            transition: all 0.3s ease;
        }}
        
        .sidebar a:hover {{
            background-color: #f8f9fa;
            border-left-color: #3498db;
            color: #2c3e50;
        }}
        
        .sidebar a.active {{
            background-color: #e3f2fd;
            border-left-color: #2196f3;
            color: #1976d2;
            font-weight: 500;
        }}
        
        .content {{
            flex: 1;
            margin-left: 280px;
            padding: 30px;
            background: white;
            min-height: calc(100vh - 80px);
        }}
        
        .section {{
            margin-bottom: 40px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            overflow: hidden;
        }}
        
        .section-header {{
            background: #f8f9fa;
            padding: 20px 25px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .section-header h2 {{
            color: #2c3e50;
            font-size: 20px;
            font-weight: 600;
            margin: 0;
        }}
        
        .section-content {{
            padding: 25px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .metric-header {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .metric-icon {{
            font-size: 18px;
            margin-right: 8px;
            font-weight: bold;
        }}
        
        .metric-title {{
            font-size: 14px;
            color: #6c757d;
            font-weight: 500;
        }}
        
        .metric-value {{
            font-size: 28px;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .metric-description {{
            font-size: 12px;
            color: #6c757d;
        }}
        
        .table-container {{
            overflow-x: auto;
            margin-top: 20px;
        }}
        
        .summary-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .summary-table th {{
            background: #f8f9fa;
            color: #495057;
            font-weight: 600;
            padding: 15px 12px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
        }}
        
        .summary-table td {{
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .summary-table tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .sample-name {{
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .plot-container {{
            background: white;
            border-radius: 8px;
            margin: 20px 0;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .alert {{
            padding: 15px;
            margin: 20px 0;
            border-radius: 6px;
            border-left: 4px solid;
        }}
        
        .alert-info {{
            background-color: #e3f2fd;
            border-left-color: #2196f3;
            color: #1976d2;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #6c757d;
            font-size: 14px;
            border-top: 1px solid #e9ecef;
            margin-top: 40px;
        }}
        
        @media (max-width: 768px) {{
            .sidebar {{
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }}
            
            .content {{
                margin-left: 0;
            }}
            
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>RNA-seq Quality Control Report</h1>
        <div class="subtitle">Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Pipeline Version 1.0</div>
    </div>
    
    <div class="container">
        <nav class="sidebar">
            <ul>
                <li><a href="#summary" class="active">General Statistics</a></li>
                {'<li><a href="#bulk-rnaseq">Bulk RNA-seq QC</a></li>' if not bulk_data.empty else ''}
                {'<li><a href="#scrna-seq">scRNA-seq QC</a></li>' if not scrna_data.empty else ''}
                <li><a href="#export">Export Data</a></li>
            </ul>
        </nav>
        
        <main class="content">
            <!-- Summary Section -->
            <section id="summary" class="section">
                <div class="section-header">
                    <h2>General Statistics</h2>
                </div>
                <div class="section-content">
                    <div class="metrics-grid">
                        {''.join(summary_cards) if summary_cards else '<p>Нет данных для отображения</p>'}
                    </div>
                </div>
            </section>
            
            {f'''
            <!-- Bulk RNA-seq Section -->
            <section id="bulk-rnaseq" class="section">
                <div class="section-header">
                    <h2>Bulk RNA-seq Quality Control</h2>
                </div>
                <div class="section-content">
                    <h3>Sample Summary</h3>
                    {self._create_summary_table(bulk_data, 'bulk_rna_seq')}
                    
                    <h3>Quality Control Plots</h3>
                    {''.join(bulk_plots)}
                </div>
            </section>
            ''' if not bulk_data.empty else ''}
            
            {f'''
            <!-- scRNA-seq Section -->
            <section id="scrna-seq" class="section">
                <div class="section-header">
                    <h2>scRNA-seq Quality Control</h2>
                </div>
                <div class="section-content">
                    <h3>Sample Summary</h3>
                    {self._create_summary_table(scrna_data, 'scrna_seq')}
                    
                    <h3>Quality Control Plots</h3>
                    {''.join(scrna_plots)}
                </div>
            </section>
            ''' if not scrna_data.empty else ''}
            
            <!-- Export Section -->
            <section id="export" class="section">
                <div class="section-header">
                    <h2>Export Data</h2>
                </div>
                <div class="section-content">
                    <div class="alert alert-info">
                        <strong>Data Export:</strong> Use the browser's save function to export this report as PDF, 
                        or use the plot export buttons for individual visualizations.
                    </div>
                </div>
            </section>
        </main>
    </div>
    
    <div class="footer">
        <p>Generated by OmicsIntegrationSuite | Modern Transcriptomics QC Reporter v1.0</p>
    </div>
    
    <script>
        // Smooth scrolling for navigation links
        document.querySelectorAll('.sidebar a').forEach(link => {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth' }});
                    
                    // Update active link
                    document.querySelectorAll('.sidebar a').forEach(l => l.classList.remove('active'));
                    this.classList.add('active');
                }}
            }});
        }});
        
        // Update active link on scroll
        window.addEventListener('scroll', function() {{
            const sections = document.querySelectorAll('.section');
            const navLinks = document.querySelectorAll('.sidebar a');
            
            let current = '';
            sections.forEach(section => {{
                const sectionTop = section.offsetTop - 100;
                if (pageYOffset >= sectionTop) {{
                    current = section.getAttribute('id');
                }}
            }});
            
            navLinks.forEach(link => {{
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {{
                    link.classList.add('active');
                }}
            }});
        }});
    </script>
</body>
</html>
        """
        
        # Сохранение отчета
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Сохранение метаданных
        metadata = {
            'report_type': 'modern_transcriptomics_qc',
            'generated_at': datetime.datetime.now().isoformat(),
            'bulk_samples': len(bulk_data) if not bulk_data.empty else 0,
            'scrna_samples': len(scrna_data) if not scrna_data.empty else 0,
            'compliance_standards': ['MultiQC', '10x_Genomics', 'ENCODE'],
            'file_size_bytes': os.path.getsize(output_path)
        }
        
        metadata_path = output_path.replace('.html', '_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return {
            'html_path': output_path,
            'metadata_path': metadata_path,
            'file_size': os.path.getsize(output_path),
            'bulk_samples': len(bulk_data) if not bulk_data.empty else 0,
            'scrna_samples': len(scrna_data) if not scrna_data.empty else 0
        }