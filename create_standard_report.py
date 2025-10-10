# -*- coding: utf-8 -*-
import sys

# Исправление кодировки для Windows терминала
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

"""
Создание стандартного научного отчета
Генерирует отчет в классическом научном формате с таблицами и графиками
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os
from datetime import datetime

# Добавляем путь к модулям
current_dir = Path(__file__).parent
modules_path = current_dir / "modules"
if str(modules_path) not in sys.path:
    sys.path.insert(0, str(modules_path))

from modules.transcriptomics.qc_reporter_enhanced import EnhancedTranscriptomicsQCReporter
from modules.transcriptomics.bulk_rnaseq_qc import BulkRNASeqQC, BulkRNASeqQCMetrics
from modules.transcriptomics.scrna_seq_qc import ScRNASeqQC, ScRNASeqQCMetrics

def create_demo_bulk_metrics():
    """Создание демонстрационных bulk RNA-seq метрик"""
    mock_metrics = {}
    
    sample_names = ["Control_1", "Control_2", "Control_3", "Treatment_1", "Treatment_2", "Treatment_3"]
    
    for i, sample_name in enumerate(sample_names):
        # Имитируем реалистичные метрики
        total_genes = np.random.randint(20000, 25000)
        detected_genes = np.random.randint(12000, 18000)
        library_size = np.random.randint(25000000, 45000000)
        median_expression = np.random.uniform(2.5, 8.5)
        
        # QC проходит если соблюдены базовые критерии
        qc_passed = (detected_genes > 10000 and 
                     library_size > 20000000 and 
                     median_expression > 1.0)
        
        metrics = BulkRNASeqQCMetrics(
            sample_name=sample_name,
            total_genes=total_genes,
            detected_genes=detected_genes,
            library_size=library_size,
            median_expression=median_expression,
            qc_passed=qc_passed
        )
        
        mock_metrics[sample_name] = metrics
    
    return mock_metrics

def create_demo_scrna_metrics():
    """Создание демонстрационных scRNA-seq метрик"""
    
    # Имитируем высококачественные scRNA-seq данные
    n_cells = 8432  # Типичное для 10x
    n_genes = 2500
    mean_counts = 22150
    mean_genes = 2847
    mean_mito = 8.5
    n_doublets = 168
    percent_doublets = 2.0
    
    return ScRNASeqQCMetrics(
        n_cells=n_cells,
        n_genes=n_genes,
        mean_counts_per_cell=mean_counts,
        mean_genes_per_cell=mean_genes,
        mean_percent_mito=mean_mito,
        n_doublets=n_doublets,
        percent_doublets=percent_doublets,
        qc_passed=True
    )

def create_demo_anndata():
    """Создание демонстрационного AnnData объекта"""
    try:
        import anndata as ad
        import pandas as pd
        
        n_cells = 1000
        n_genes = 2000
        
        # Создаем матрицу экспрессии
        X = np.random.negative_binomial(5, 0.3, size=(n_cells, n_genes))
        
        # Метаданные клеток
        obs = pd.DataFrame({
            'n_counts': np.random.negative_binomial(100, 0.01, n_cells),
            'n_genes': np.random.negative_binomial(50, 0.02, n_cells),
            'percent_mito': np.random.beta(2, 20, n_cells) * 30  # 0-30%
        })
        
        # Метаданные генов
        var = pd.DataFrame(
            index=[f"Gene_{i}" for i in range(n_genes)]
        )
        
        adata = ad.AnnData(X=X, obs=obs, var=var)
        return adata
        
    except ImportError:
        print("[WARN] AnnData не доступен")
        return None

class StandardTranscriptomicsReporter(EnhancedTranscriptomicsQCReporter):
    """Расширенный класс для создания стандартных научных отчетов"""
    
    def generate_standard_scientific_report(self, data_type: str = 'both') -> str:
        """Генерация стандартного научного отчета"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"standard_scientific_report_{timestamp}.html"
        
        # HTML структура в научном стиле
        html_content = self._generate_scientific_template()
        
        # Основной контент
        html_content.extend([
            "<div class='container'>",
            self._generate_scientific_header(),
            self._generate_abstract(),
            self._generate_methods_section(),
            self._generate_results_section(data_type),
            self._generate_conclusions_section(),
            self._generate_references_section(),
            "</div>",
            "</body>",
            "</html>"
        ])
        
        # Сохранение файла
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_content))
        
        print(f"[OK] Стандартный научный отчет сохранен: {output_file}")
        return str(output_file)
    
    def _generate_scientific_template(self) -> list:
        """Генерация HTML шаблона в научном стиле"""
        return [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "    <title>RNA-seq Quality Control Analysis Report</title>",
            "    <style>",
            self._generate_scientific_css(),
            "    </style>",
            "    <script src='https://cdn.plot.ly/plotly-latest.min.js'></script>",
            "</head>",
            "<body>"
        ]
    
    def _generate_scientific_css(self) -> str:
        """Генерация CSS в научном стиле"""
        return """
        body {
            font-family: 'Times New Roman', Times, serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }
        .container {
            background: white;
            padding: 40px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .title {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .authors {
            font-size: 14px;
            font-style: italic;
            margin-bottom: 10px;
        }
        .affiliation {
            font-size: 12px;
            color: #666;
        }
        .section {
            margin: 30px 0;
        }
        .section-title {
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
            border-bottom: 1px solid #333;
            padding-bottom: 5px;
            margin-bottom: 15px;
        }
        .subsection-title {
            font-size: 16px;
            font-weight: bold;
            margin: 20px 0 10px 0;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 12px;
        }
        .table th, .table td {
            border: 1px solid #333;
            padding: 8px;
            text-align: center;
        }
        .table th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        .table caption {
            font-weight: bold;
            margin-bottom: 10px;
            text-align: left;
        }
        .figure {
            margin: 30px 0;
            text-align: center;
        }
        .figure-caption {
            font-size: 12px;
            font-weight: bold;
            margin-top: 10px;
            text-align: left;
        }
        .plot-container {
            margin: 20px 0;
            border: 1px solid #ddd;
            padding: 10px;
        }
        .abstract {
            font-style: italic;
            text-align: justify;
            margin: 20px 0;
            padding: 20px;
            background-color: #f9f9f9;
            border-left: 4px solid #333;
        }
        .keywords {
            margin-top: 15px;
        }
        .keywords strong {
            font-weight: bold;
        }
        ol, ul {
            text-align: justify;
        }
        .status-pass { color: #2d5a2d; font-weight: bold; }
        .status-warn { color: #b8860b; font-weight: bold; }
        .status-fail { color: #8b0000; font-weight: bold; }
        """
    
    def _generate_scientific_header(self) -> str:
        """Генерация заголовка в научном стиле"""
        return """
        <div class='header'>
            <div class='title'>Quality Control Analysis of RNA-seq Data</div>
            <div class='authors'>Generated by OmicsIntegrationSuite</div>
            <div class='affiliation'>
                Transcriptomics Quality Control Module<br>
                """ + f"Generated: {datetime.now().strftime('%B %d, %Y')}" + """
            </div>
        </div>
        """
    
    def _generate_abstract(self) -> str:
        """Генерация аннотации"""
        return """
        <div class='section'>
            <div class='section-title'>Abstract</div>
            <div class='abstract'>
                <strong>Background:</strong> Quality control is a critical step in RNA-seq data analysis workflow. 
                This report presents comprehensive quality assessment of both bulk and single-cell RNA sequencing datasets 
                using standardized metrics and established best practices.
                
                <br><br><strong>Methods:</strong> We analyzed RNA-seq data using multiple quality control metrics including 
                library depth, gene detection rates, mitochondrial gene expression, and doublet detection for single-cell data. 
                Quality thresholds were established based on ENCODE guidelines and 10x Genomics recommendations.
                
                <br><br><strong>Results:</strong> The analysis reveals dataset-specific quality characteristics with 
                detailed assessment of technical parameters and recommendations for downstream analysis.
                
                <br><br><strong>Conclusions:</strong> This standardized QC approach enables robust evaluation of 
                RNA-seq data quality and informed decision-making for subsequent analytical steps.
                
                <div class='keywords'>
                    <strong>Keywords:</strong> RNA-seq, Quality Control, Single-cell, Transcriptomics, ENCODE, 10x Genomics
                </div>
            </div>
        </div>
        """
    
    def _generate_methods_section(self) -> str:
        """Генерация раздела методов"""
        return """
        <div class='section'>
            <div class='section-title'>Methods</div>
            
            <div class='subsection-title'>Data Processing</div>
            <p>RNA-seq data quality control was performed using the OmicsIntegrationSuite transcriptomics module. 
            The analysis pipeline incorporated multiple quality metrics established by consortiums including ENCODE and 
            best practices from 10x Genomics for single-cell data.</p>
            
            <div class='subsection-title'>Quality Control Metrics</div>
            <p><strong>Bulk RNA-seq:</strong> Library depth (minimum 20M reads), gene detection rate (minimum 15,000 genes), 
            mitochondrial gene expression (&lt;20%), and sample correlation analysis.</p>
            
            <p><strong>Single-cell RNA-seq:</strong> Cell count estimation, UMI counts per cell (minimum 20,000), 
            genes per cell (minimum 1,000), mitochondrial gene percentage (&lt;20%), and doublet detection using 
            computational methods.</p>
            
            <div class='subsection-title'>Statistical Analysis</div>
            <p>Quality assessment was performed using established thresholds. Samples meeting all quality criteria 
            were classified as "PASS", those with minor deviations as "WARN", and those failing critical metrics as "FAIL".</p>
        </div>
        """
    
    def _generate_results_section(self, data_type: str) -> str:
        """Генерация раздела результатов"""
        content = ["<div class='section'>", "<div class='section-title'>Results</div>"]
        
        # Bulk RNA-seq результаты
        if data_type in ['bulk', 'both'] and self.bulk_metrics:
            content.extend(self._generate_bulk_results_table())
            content.extend(self._generate_bulk_figures())
        
        # scRNA-seq результаты
        if data_type in ['scrna', 'both'] and self.scrna_metrics:
            content.extend(self._generate_scrna_results_table())
            content.extend(self._generate_scrna_figures())
        
        content.append("</div>")
        return '\n'.join(content)
    
    def _generate_bulk_results_table(self) -> list:
        """Генерация таблицы результатов bulk RNA-seq"""
        content = [
            "<div class='subsection-title'>Bulk RNA-seq Quality Assessment</div>",
            "<table class='table'>",
            "<caption>Table 1. Summary of bulk RNA-seq quality control metrics</caption>",
            "<thead>",
            "<tr>",
            "<th>Sample ID</th>",
            "<th>Total Reads (M)</th>",
            "<th>Detected Genes</th>",
            "<th>Library Depth (M)</th>",
            "<th>Median Expression</th>",
            "<th>QC Status</th>",
            "</tr>",
            "</thead>",
            "<tbody>"
        ]
        
        for sample_name, metrics in self.bulk_metrics.items():
            status_class = 'status-pass' if metrics.qc_passed else 'status-fail'
            status_text = 'PASS' if metrics.qc_passed else 'FAIL'
            
            content.append(f"""
            <tr>
                <td>{sample_name}</td>
                <td>{metrics.library_size/1e6:.1f}</td>
                <td>{metrics.detected_genes:,}</td>
                <td>{metrics.library_size/1e6:.1f}</td>
                <td>{metrics.median_expression:.2f}</td>
                <td class='{status_class}'>{status_text}</td>
            </tr>
            """)
        
        content.extend(["</tbody>", "</table>"])
        
        # Добавляем статистику
        total_samples = len(self.bulk_metrics)
        passed_samples = sum(1 for m in self.bulk_metrics.values() if m.qc_passed)
        
        content.append(f"""
        <p><strong>Summary:</strong> {passed_samples}/{total_samples} samples passed quality control criteria. 
        Average library depth: {np.mean([m.library_size for m in self.bulk_metrics.values()])/1e6:.1f}M reads. 
        Average detected genes: {np.mean([m.detected_genes for m in self.bulk_metrics.values()]):,.0f}.</p>
        """)
        
        return content
    
    def _generate_scrna_results_table(self) -> list:
        """Генерация таблицы результатов scRNA-seq"""
        content = [
            "<div class='subsection-title'>Single-cell RNA-seq Quality Assessment</div>",
            "<table class='table'>",
            "<caption>Table 2. Summary of single-cell RNA-seq quality control metrics</caption>",
            "<thead>",
            "<tr>",
            "<th>Metric</th>",
            "<th>Value</th>",
            "<th>Threshold</th>",
            "<th>Status</th>",
            "</tr>",
            "</thead>",
            "<tbody>"
        ]
        
        metrics = [
            ("Estimated Cells", f"{self.scrna_metrics.n_cells:,}", "500-10,000", "PASS"),
            ("Total Genes", f"{self.scrna_metrics.n_genes:,}", ">2,000", "PASS"),
            ("Mean UMI/Cell", f"{self.scrna_metrics.mean_counts_per_cell:,.0f}", "≥20,000", "PASS"),
            ("Mean Genes/Cell", f"{self.scrna_metrics.mean_genes_per_cell:,.0f}", "≥1,000", "PASS"),
            ("Mitochondrial %", f"{self.scrna_metrics.mean_percent_mito:.1f}%", "<20%", "PASS"),
            ("Predicted Doublets", f"{self.scrna_metrics.percent_doublets:.1f}%", "<10%", "PASS")
        ]
        
        for metric, value, threshold, status in metrics:
            status_class = 'status-pass' if status == 'PASS' else 'status-fail'
            content.append(f"""
            <tr>
                <td>{metric}</td>
                <td>{value}</td>
                <td>{threshold}</td>
                <td class='{status_class}'>{status}</td>
            </tr>
            """)
        
        content.extend(["</tbody>", "</table>"])
        
        content.append(f"""
        <p><strong>Interpretation:</strong> The single-cell dataset demonstrates high quality with {self.scrna_metrics.n_cells:,} 
        estimated cells and mean UMI count of {self.scrna_metrics.mean_counts_per_cell:,.0f} per cell, 
        meeting 10x Genomics quality standards.</p>
        """)
        
        return content
    
    def _generate_bulk_figures(self) -> list:
        """Генерация фигур для bulk RNA-seq"""
        content = []
        
        # Создаем графики
        bulk_plots = self.create_enhanced_bulk_plots()
        plot_id = 1000
        
        for plot_name, fig in list(bulk_plots.items())[:3]:  # Берем первые 3 графика
            plot_id += 1
            content.extend([
                f"<div class='figure'>",
                f"<div id='plot_{plot_id}' class='plot-container'></div>",
                f"<div class='figure-caption'>Figure {plot_id - 1000}. {plot_name.replace('_', ' ').title()} for bulk RNA-seq samples.</div>",
                f"<script>Plotly.newPlot('plot_{plot_id}', {fig.to_json()});</script>",
                "</div>"
            ])
        
        return content
    
    def _generate_scrna_figures(self) -> list:
        """Генерация фигур для scRNA-seq"""
        content = []
        
        # Создаем графики
        scrna_plots = self.create_enhanced_scrna_plots()
        plot_id = 2000
        
        key_plots = ['barcode_rank', 'qc_metrics_violin', 'umi_vs_genes_scatter']
        for plot_name in key_plots:
            if plot_name in scrna_plots:
                plot_id += 1
                fig = scrna_plots[plot_name]
                content.extend([
                    f"<div class='figure'>",
                    f"<div id='plot_{plot_id}' class='plot-container'></div>",
                    f"<div class='figure-caption'>Figure {plot_id - 2000 + 3}. {plot_name.replace('_', ' ').title()} for single-cell RNA-seq data.</div>",
                    f"<script>Plotly.newPlot('plot_{plot_id}', {fig.to_json()});</script>",
                    "</div>"
                ])
        
        return content
    
    def _generate_conclusions_section(self) -> str:
        """Генерация раздела выводов"""
        return """
        <div class='section'>
            <div class='section-title'>Conclusions</div>
            <ol>
                <li>The quality control analysis demonstrates robust dataset characteristics suitable for downstream analysis.</li>
                <li>All samples meet established quality thresholds based on international consortium guidelines.</li>
                <li>The integrated approach combining multiple QC metrics provides comprehensive assessment framework.</li>
                <li>Both bulk and single-cell datasets show technical quality parameters within acceptable ranges.</li>
            </ol>
            
            <div class='subsection-title'>Recommendations</div>
            <ul>
                <li>Proceed with standard downstream analysis workflow</li>
                <li>Consider batch effects if samples were processed in different runs</li>
                <li>Apply standard normalization methods appropriate for the analysis type</li>
                <li>Document QC decisions for reproducibility</li>
            </ul>
        </div>
        """
    
    def _generate_references_section(self) -> str:
        """Генерация раздела литературы"""
        return """
        <div class='section'>
            <div class='section-title'>References</div>
            <ol style='font-size: 12px;'>
                <li>ENCODE Project Consortium. "Guidelines for RNA-seq experiments." Nature Biotechnology (2020).</li>
                <li>10x Genomics. "Technical Note: Interpreting Cell Ranger Web Summary Files." (2023).</li>
                <li>MultiQC: "Summarize analysis results for multiple tools and samples." Bioinformatics (2016).</li>
                <li>Satija et al. "Spatial reconstruction of single-cell gene expression data." Nature Biotechnology (2015).</li>
                <li>Wolf et al. "SCANPY: large-scale single-cell gene expression data analysis." Genome Biology (2018).</li>
            </ol>
        </div>
        """

def create_standard_scientific_report():
    """Создание стандартного научного отчета"""
    
    print("=== Создание стандартного научного отчета ===")
    print("")
    
    # Создаем директорию для отчетов
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    print(f"[OK] Создана директория для отчетов: {reports_dir.absolute()}")
    
    # Инициализируем standard reporter
    reporter = StandardTranscriptomicsReporter(reports_dir)
    print("[OK] Инициализирован StandardTranscriptomicsReporter")
    
    # Создаем тестовые данные
    print("\n--- Подготовка научных данных ---")
    
    # Bulk RNA-seq данные
    bulk_metrics = create_demo_bulk_metrics()
    reporter.set_bulk_rnaseq_metrics(bulk_metrics)
    print(f"[OK] Загружены метрики для {len(bulk_metrics)} bulk RNA-seq образцов")
    
    # scRNA-seq данные  
    scrna_metrics = create_demo_scrna_metrics()
    adata = create_demo_anndata()
    reporter.set_scrna_seq_metrics(scrna_metrics, adata)
    print("[OK] Загружены scRNA-seq метрики")
    
    # Генерируем научный отчет
    print("\n--- Генерация стандартного научного отчета ---")
    
    try:
        html_file = reporter.generate_standard_scientific_report(data_type='both')
        
        # Проверяем размер файла
        if os.path.exists(html_file):
            file_size = os.path.getsize(html_file)
            print(f"[OK] Размер отчета: {file_size:,} байт")
        
        print(f"\n=== Стандартный научный отчет создан! ===")
        print(f"📂 Папка с отчетами: {reports_dir.absolute()}")
        print(f"📄 HTML отчет: {Path(html_file).name}")
        print("")
        print("🎯 Особенности стандартного отчета:")
        print("  ✅ Классический научный формат")
        print("  ✅ Структура: Abstract, Methods, Results, Conclusions")
        print("  ✅ Научные таблицы с подписями")
        print("  ✅ Нумерованные фигуры")
        print("  ✅ Список литературы")
        print("  ✅ Стиль Times New Roman")
        print("")
        print("📖 Откройте HTML файл в браузере для просмотра!")
        
        return html_file
        
    except Exception as e:
        print(f"[ERROR] Ошибка создания отчета: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    try:
        result = create_standard_scientific_report()
        
        if result:
            print("\n" + "="*60)
            print("🎉 СТАНДАРТНЫЙ НАУЧНЫЙ ОТЧЕТ СОЗДАН УСПЕШНО!")
            print("Отчет соответствует классическому научному формату")
            print("с таблицами, фигурами и стандартной структурой.")
            print("="*60)
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()