"""
Модуль генерации отчетов QC для транскриптомных данных
Создает HTML, PDF и интерактивные отчеты
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime
import json

# Визуализация
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

# Импорты для работы с scRNA-seq данными
try:
    import scanpy as sc
    import anndata as ad
    SCANPY_AVAILABLE = True
except ImportError:
    SCANPY_AVAILABLE = False

# Настройка логирования
logger = logging.getLogger(__name__)

# Настройка стилей
plt.style.use('default')
sns.set_palette("husl")


class TranscriptomicsQCReporter:
    """
    Класс для генерации QC отчетов по транскриптомным данным
    """
    
    def __init__(self, output_dir: Union[str, Path] = "qc_reports"):
        """
        Инициализация генератора отчетов
        
        Args:
            output_dir: Директория для сохранения отчетов
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.bulk_metrics = None
        self.scrna_metrics = None
        self.doublet_results = None
        self.normalization_comparison = None
        
        # Настройка Plotly для веб-приложений (без notebook mode)
        # pyo.init_notebook_mode(connected=False)  # Отключено для Streamlit
        
    def set_bulk_rnaseq_metrics(self, metrics: Dict[str, Any]):
        """Установка метрик bulk RNA-seq"""
        self.bulk_metrics = metrics
        
    def set_scrna_seq_metrics(self, metrics: Any, adata: Optional[ad.AnnData] = None):
        """Установка метрик scRNA-seq"""
        self.scrna_metrics = metrics
        self.scrna_adata = adata
        
    def set_doublet_results(self, results: Dict[str, Any]):
        """Установка результатов детекции дублетов"""
        self.doublet_results = results
        
    def set_normalization_comparison(self, comparison: pd.DataFrame):
        """Установка сравнения методов нормализации"""
        self.normalization_comparison = comparison
        
    def create_bulk_rnaseq_plots(self) -> Dict[str, go.Figure]:
        """
        Создание графиков для bulk RNA-seq
        
        Returns:
            Dict: Словарь с фигурами Plotly
        """
        if self.bulk_metrics is None:
            return {}
        
        plots = {}
        
        # Подготовка данных
        samples = []
        total_genes = []
        detected_genes = []
        library_sizes = []
        median_expressions = []
        qc_status = []
        
        for sample_name, metrics in self.bulk_metrics.items():
            samples.append(sample_name)
            total_genes.append(metrics.total_genes)
            detected_genes.append(metrics.detected_genes)
            library_sizes.append(metrics.library_size)
            median_expressions.append(metrics.median_expression)
            qc_status.append('Passed' if metrics.qc_passed else 'Failed')
        
        # График 1: Детектируемые гены
        plots['detected_genes'] = px.bar(
            x=samples, y=detected_genes,
            title='Детектируемые гены по образцам',
            labels={'x': 'Образцы', 'y': 'Количество генов'},
            color=qc_status,
            color_discrete_map={'Passed': 'green', 'Failed': 'red'}
        )
        
        # График 2: Библиотечная глубина
        plots['library_depth'] = px.bar(
            x=samples, y=library_sizes,
            title='Глубина секвенирования',
            labels={'x': 'Образцы', 'y': 'Общее количество ридов'},
            color=qc_status,
            color_discrete_map={'Passed': 'green', 'Failed': 'red'}
        )
        
        # График 3: Корреляция детектируемых генов и глубины
        plots['genes_vs_depth'] = px.scatter(
            x=library_sizes, y=detected_genes,
            hover_name=samples,
            title='Корреляция: гены vs глубина секвенирования',
            labels={'x': 'Глубина секвенирования', 'y': 'Детектируемые гены'},
            color=qc_status,
            color_discrete_map={'Passed': 'green', 'Failed': 'red'}
        )
        
        # График 4: Медианная экспрессия
        plots['median_expression'] = px.bar(
            x=samples, y=median_expressions,
            title='Медианная экспрессия по образцам',
            labels={'x': 'Образцы', 'y': 'Медианная экспрессия'},
            color=qc_status,
            color_discrete_map={'Passed': 'green', 'Failed': 'red'}
        )
        
        return plots
    
    def create_scrna_seq_plots(self) -> Dict[str, go.Figure]:
        """
        Создание графиков для scRNA-seq (аналог VlnPlot в Seurat)
        
        Returns:
            Dict: Словарь с фигурами Plotly
        """
        if self.scrna_adata is None:
            return {}
        
        plots = {}
        adata = self.scrna_adata
        
        # График 1: Violin plot - UMI на клетку (nCount_RNA в Seurat)
        if 'n_counts' in adata.obs:
            plots['umi_per_cell'] = px.violin(
                y=adata.obs['n_counts'],
                title='UMI counts per cell',
                labels={'y': 'UMI counts'},
                box=True
            )
        
        # График 2: Violin plot - Гены на клетку (nFeature_RNA в Seurat)
        if 'n_genes' in adata.obs:
            plots['genes_per_cell'] = px.violin(
                y=adata.obs['n_genes'],
                title='Genes per cell',
                labels={'y': 'Number of genes'},
                box=True
            )
        
        # График 3: Violin plot - Процент митохондриальных генов (percent.mt в Seurat)
        if 'percent_mito' in adata.obs:
            plots['mito_percent'] = px.violin(
                y=adata.obs['percent_mito'],
                title='Mitochondrial genes percentage',
                labels={'y': 'Mitochondrial %'},
                box=True
            )
        
        # График 4: Scatter plot - UMI vs Гены (как в Seurat)
        if 'n_counts' in adata.obs and 'n_genes' in adata.obs:
            color_col = 'percent_mito' if 'percent_mito' in adata.obs else None
            
            plots['umi_vs_genes'] = px.scatter(
                x=adata.obs['n_counts'], 
                y=adata.obs['n_genes'],
                color=adata.obs[color_col] if color_col else None,
                title='UMI counts vs Genes detected',
                labels={'x': 'UMI counts', 'y': 'Genes detected'},
                opacity=0.6
            )
        
        # График 5: Scatter plot - UMI vs Митохондриальные %
        if 'n_counts' in adata.obs and 'percent_mito' in adata.obs:
            plots['umi_vs_mito'] = px.scatter(
                x=adata.obs['n_counts'],
                y=adata.obs['percent_mito'],
                title='UMI counts vs Mitochondrial %',
                labels={'x': 'UMI counts', 'y': 'Mitochondrial %'},
                opacity=0.6
            )
        
        # График 6: Гистограммы распределений
        if 'n_counts' in adata.obs:
            plots['umi_distribution'] = px.histogram(
                x=adata.obs['n_counts'],
                nbins=50,
                title='Distribution of UMI counts',
                labels={'x': 'UMI counts', 'y': 'Number of cells'}
            )
        
        return plots
    
    def create_doublet_plots(self) -> Dict[str, go.Figure]:
        """
        Создание графиков для анализа дублетов
        
        Returns:
            Dict: Словарь с фигурами Plotly
        """
        if self.doublet_results is None:
            return {}
        
        plots = {}
        
        # График 1: Сравнение методов детекции дублетов
        methods = []
        n_doublets = []
        percentages = []
        
        for method_name, results in self.doublet_results.items():
            methods.append(results.method)
            n_doublets.append(results.n_doublets)
            percentages.append(results.percent_doublets)
        
        plots['doublet_comparison'] = px.bar(
            x=methods, y=percentages,
            title='Сравнение методов детекции дублетов',
            labels={'x': 'Метод', 'y': 'Процент дублетов (%)'},
            text=n_doublets
        )
        
        # График 2: Распределение Scrublet scores
        if 'scrublet' in self.doublet_results:
            scrublet_results = self.doublet_results['scrublet']
            
            plots['scrublet_scores'] = px.histogram(
                x=scrublet_results.doublet_scores,
                nbins=50,
                title='Распределение Scrublet doublet scores',
                labels={'x': 'Doublet score', 'y': 'Количество клеток'}
            )
            
            # Добавление линии порога
            fig = plots['scrublet_scores']
            fig.add_vline(
                x=scrublet_results.doublet_threshold,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Threshold: {scrublet_results.doublet_threshold:.3f}"
            )
        
        # График 3: Корреляция между методами (если есть несколько)
        if len(self.doublet_results) >= 2:
            method_names = list(self.doublet_results.keys())
            if len(method_names) >= 2:
                method1, method2 = method_names[0], method_names[1]
                scores1 = self.doublet_results[method1].doublet_scores
                scores2 = self.doublet_results[method2].doublet_scores
                
                plots['methods_correlation'] = px.scatter(
                    x=scores1, y=scores2,
                    title=f'Корреляция: {method1} vs {method2}',
                    labels={'x': f'{method1} scores', 'y': f'{method2} scores'},
                    opacity=0.6
                )
        
        return plots
    
    def create_normalization_plots(self) -> Dict[str, go.Figure]:
        """
        Создание графиков сравнения методов нормализации
        
        Returns:
            Dict: Словарь с фигурами Plotly
        """
        if self.normalization_comparison is None:
            return {}
        
        plots = {}
        df = self.normalization_comparison
        
        # График 1: Сравнение средних значений
        plots['mean_comparison'] = px.bar(
            x=df['Method'], y=df['Mean'],
            title='Сравнение средних значений после нормализации',
            labels={'x': 'Метод нормализации', 'y': 'Среднее значение'}
        )
        
        # График 2: Сравнение стандартных отклонений
        plots['std_comparison'] = px.bar(
            x=df['Method'], y=df['Std'],
            title='Сравнение стандартных отклонений',
            labels={'x': 'Метод нормализации', 'y': 'Стандартное отклонение'}
        )
        
        # График 3: Диапазон значений (Min-Max)
        plots['range_comparison'] = go.Figure()
        
        for _, row in df.iterrows():
            plots['range_comparison'].add_trace(go.Scatter(
                x=[row['Method'], row['Method']],
                y=[row['Min'], row['Max']],
                mode='lines+markers',
                name=row['Method'],
                line=dict(width=3),
                marker=dict(size=8)
            ))
        
        plots['range_comparison'].update_layout(
            title='Диапазон значений после нормализации',
            xaxis_title='Метод нормализации',
            yaxis_title='Значение'
        )
        
        return plots
    
    def generate_html_report(self, 
                           data_type: str = 'both',
                           include_plots: bool = True) -> str:
        """
        Генерация HTML отчета
        
        Args:
            data_type: Тип данных ('bulk', 'scrna', 'both')
            include_plots: Включать ли интерактивные графики
            
        Returns:
            str: Путь к созданному HTML файлу
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"transcriptomics_qc_report_{timestamp}.html"
        
        html_content = [
            "<!DOCTYPE html>",
            "<html lang='ru'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "    <title>Transcriptomics QC Report</title>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; }",
            "        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }",
            "        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }",
            "        .metrics-table { width: 100%; border-collapse: collapse; }",
            "        .metrics-table th, .metrics-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "        .metrics-table th { background-color: #f2f2f2; }",
            "        .plot-container { margin: 20px 0; }",
            "        .status-passed { color: green; font-weight: bold; }",
            "        .status-failed { color: red; font-weight: bold; }",
            "        .warning { color: orange; }",
            "        .error { color: red; }",
            "    </style>",
            "    <script src='https://cdn.plot.ly/plotly-latest.min.js'></script>",
            "</head>",
            "<body>",
            "",
            "<div class='header'>",
            f"    <h1>Отчет контроля качества транскриптомных данных</h1>",
            f"    <p>Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>",
            "</div>"
        ]
        
        # Bulk RNA-seq секция
        if data_type in ['bulk', 'both'] and self.bulk_metrics:
            html_content.extend([
                "",
                "<div class='section'>",
                "    <h2>Bulk RNA-seq Quality Control</h2>",
                "    <h3>Сводная таблица образцов</h3>",
                "    <table class='metrics-table'>",
                "        <tr>",
                "            <th>Образец</th>",
                "            <th>Общее количество генов</th>",
                "            <th>Детектируемые гены</th>",
                "            <th>Глубина библиотеки</th>",
                "            <th>Медианная экспрессия</th>",
                "            <th>QC статус</th>",
                "        </tr>"
            ])
            
            for sample_name, metrics in self.bulk_metrics.items():
                status_class = 'status-passed' if metrics.qc_passed else 'status-failed'
                status_text = 'Passed' if metrics.qc_passed else 'Failed'
                
                html_content.append(
                    f"        <tr>"
                    f"<td>{sample_name}</td>"
                    f"<td>{metrics.total_genes:,}</td>"
                    f"<td>{metrics.detected_genes:,}</td>"
                    f"<td>{metrics.library_size:,}</td>"
                    f"<td>{metrics.median_expression:.2f}</td>"
                    f"<td class='{status_class}'>{status_text}</td>"
                    f"</tr>"
                )
            
            html_content.extend([
                "    </table>",
                "</div>"
            ])
        
        # scRNA-seq секция
        if data_type in ['scrna', 'both'] and self.scrna_metrics:
            html_content.extend([
                "",
                "<div class='section'>",
                "    <h2>Single-cell RNA-seq Quality Control</h2>",
                "    <h3>Общая статистика</h3>",
                "    <table class='metrics-table'>",
                "        <tr><td><strong>Всего клеток:</strong></td>",
                f"        <td>{self.scrna_metrics.n_cells:,}</td></tr>",
                "        <tr><td><strong>Всего генов:</strong></td>",
                f"        <td>{self.scrna_metrics.n_genes:,}</td></tr>",
                "        <tr><td><strong>Среднее UMI на клетку:</strong></td>",
                f"        <td>{self.scrna_metrics.mean_counts_per_cell:,.0f}</td></tr>",
                "        <tr><td><strong>Среднее генов на клетку:</strong></td>",
                f"        <td>{self.scrna_metrics.mean_genes_per_cell:,.0f}</td></tr>",
                "        <tr><td><strong>Средний % митохондриальных генов:</strong></td>",
                f"        <td>{self.scrna_metrics.mean_percent_mito:.2f}%</td></tr>",
                "        <tr><td><strong>Предсказанные дублеты:</strong></td>",
                f"        <td>{self.scrna_metrics.n_doublets} ({self.scrna_metrics.percent_doublets:.2f}%)</td></tr>",
                "    </table>",
                "</div>"
            ])
        
        # Графики
        if include_plots:
            plot_id = 0
            
            # Bulk RNA-seq графики
            if data_type in ['bulk', 'both']:
                bulk_plots = self.create_bulk_rnaseq_plots()
                if bulk_plots:
                    html_content.append("<div class='section'><h2>Bulk RNA-seq Графики</h2>")
                    for plot_name, fig in bulk_plots.items():
                        plot_id += 1
                        html_content.extend([
                            f"<div class='plot-container' id='plot_{plot_id}'></div>",
                            "<script>",
                            f"Plotly.newPlot('plot_{plot_id}', {fig.to_json()});",
                            "</script>"
                        ])
                    html_content.append("</div>")
            
            # scRNA-seq графики
            if data_type in ['scrna', 'both']:
                scrna_plots = self.create_scrna_seq_plots()
                if scrna_plots:
                    html_content.append("<div class='section'><h2>Single-cell RNA-seq Графики</h2>")
                    for plot_name, fig in scrna_plots.items():
                        plot_id += 1
                        html_content.extend([
                            f"<div class='plot-container' id='plot_{plot_id}'></div>",
                            "<script>",
                            f"Plotly.newPlot('plot_{plot_id}', {fig.to_json()});",
                            "</script>"
                        ])
                    html_content.append("</div>")
            
            # Графики дублетов
            doublet_plots = self.create_doublet_plots()
            if doublet_plots:
                html_content.append("<div class='section'><h2>Анализ дублетов</h2>")
                for plot_name, fig in doublet_plots.items():
                    plot_id += 1
                    html_content.extend([
                        f"<div class='plot-container' id='plot_{plot_id}'></div>",
                        "<script>",
                        f"Plotly.newPlot('plot_{plot_id}', {fig.to_json()});",
                        "</script>"
                    ])
                html_content.append("</div>")
            
            # Графики нормализации
            norm_plots = self.create_normalization_plots()
            if norm_plots:
                html_content.append("<div class='section'><h2>Сравнение методов нормализации</h2>")
                for plot_name, fig in norm_plots.items():
                    plot_id += 1
                    html_content.extend([
                        f"<div class='plot-container' id='plot_{plot_id}'></div>",
                        "<script>",
                        f"Plotly.newPlot('plot_{plot_id}', {fig.to_json()});",
                        "</script>"
                    ])
                html_content.append("</div>")
        
        html_content.extend([
            "",
            "</body>",
            "</html>"
        ])
        
        # Сохранение HTML файла
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
        
        logger.info(f"HTML отчет сохранен: {output_file}")
        return str(output_file)
    
    def generate_summary_json(self) -> str:
        """
        Генерация JSON файла с сводной информацией
        
        Returns:
            str: Путь к созданному JSON файлу
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"transcriptomics_qc_summary_{timestamp}.json"
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "bulk_rnaseq": {},
            "scrna_seq": {},
            "doublet_detection": {},
            "normalization": {}
        }
        
        # Bulk RNA-seq summary
        if self.bulk_metrics:
            bulk_summary = {
                "n_samples": len(self.bulk_metrics),
                "samples_passed_qc": sum(1 for m in self.bulk_metrics.values() if m.qc_passed),
                "total_genes_range": [
                    min(m.total_genes for m in self.bulk_metrics.values()),
                    max(m.total_genes for m in self.bulk_metrics.values())
                ],
                "library_size_range": [
                    min(m.library_size for m in self.bulk_metrics.values()),
                    max(m.library_size for m in self.bulk_metrics.values())
                ]
            }
            summary["bulk_rnaseq"] = bulk_summary
        
        # scRNA-seq summary
        if self.scrna_metrics:
            scrna_summary = {
                "n_cells": self.scrna_metrics.n_cells,
                "n_genes": self.scrna_metrics.n_genes,
                "mean_umi_per_cell": self.scrna_metrics.mean_counts_per_cell,
                "mean_genes_per_cell": self.scrna_metrics.mean_genes_per_cell,
                "mean_mito_percent": self.scrna_metrics.mean_percent_mito,
                "n_doublets": self.scrna_metrics.n_doublets,
                "percent_doublets": self.scrna_metrics.percent_doublets,
                "qc_passed": self.scrna_metrics.qc_passed
            }
            summary["scrna_seq"] = scrna_summary
        
        # Doublet detection summary
        if self.doublet_results:
            doublet_summary = {}
            for method_name, results in self.doublet_results.items():
                doublet_summary[method_name] = {
                    "n_doublets": results.n_doublets,
                    "percent_doublets": results.percent_doublets,
                    "threshold": results.doublet_threshold
                }
            summary["doublet_detection"] = doublet_summary
        
        # Normalization summary
        if self.normalization_comparison is not None:
            summary["normalization"] = self.normalization_comparison.to_dict('records')
        
        # Сохранение JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON сводка сохранена: {output_file}")
        return str(output_file)
    
    def generate_comprehensive_report(self, 
                                    data_type: str = 'both',
                                    include_interactive: bool = True) -> Dict[str, str]:
        """
        Генерация комплексного отчета (HTML + JSON + статические графики)
        
        Args:
            data_type: Тип данных для включения в отчет
            include_interactive: Включать ли интерактивные элементы
            
        Returns:
            Dict: Пути к созданным файлам
        """
        output_files = {}
        
        # HTML отчет
        html_file = self.generate_html_report(data_type, include_interactive)
        output_files['html'] = html_file
        
        # JSON сводка
        json_file = self.generate_summary_json()
        output_files['json'] = json_file
        
        # Сохранение статических графиков
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plots_dir = self.output_dir / f"plots_{timestamp}"
        plots_dir.mkdir(exist_ok=True)
        
        # Bulk RNA-seq графики
        if data_type in ['bulk', 'both']:
            bulk_plots = self.create_bulk_rnaseq_plots()
            for plot_name, fig in bulk_plots.items():
                plot_file = plots_dir / f"bulk_{plot_name}.png"
                fig.write_image(str(plot_file), width=800, height=600)
        
        # scRNA-seq графики
        if data_type in ['scrna', 'both']:
            scrna_plots = self.create_scrna_seq_plots()
            for plot_name, fig in scrna_plots.items():
                plot_file = plots_dir / f"scrna_{plot_name}.png"
                fig.write_image(str(plot_file), width=800, height=600)
        
        # Графики дублетов
        doublet_plots = self.create_doublet_plots()
        for plot_name, fig in doublet_plots.items():
            plot_file = plots_dir / f"doublet_{plot_name}.png"
            fig.write_image(str(plot_file), width=800, height=600)
        
        output_files['plots_dir'] = str(plots_dir)
        
        logger.info(f"Комплексный отчет создан в {self.output_dir}")
        return output_files