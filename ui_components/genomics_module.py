"""
Genomics Module Component for OmicsIntegrationSuite
Enhanced with QualityControlSuite FASTQ analysis capabilities

Integrated from: QualityControlSuite (https://github.com/otinoff/QualityControlSuite)
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import random
from pathlib import Path
import sys
import os
from datetime import datetime
import json
import uuid

# Add modules path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import genomics QC functions
try:
    from modules.genomics.quality_control import run_advanced_fastq_qc
    from modules.genomics.logging_system import get_logger
    QC_AVAILABLE = True
except ImportError as e:
    QC_AVAILABLE = False
    print(f"Warning: QC module not available: {e}")

# Constants
DATA_DIR = Path("data/genomics_qc")
UPLOADED_FILES_DIR = DATA_DIR / "uploaded_files"
REPORTS_DIR = DATA_DIR / "reports"
METADATA_FILE = DATA_DIR / "metadata.json"


def init_directories():
    """Initialize directories"""
    UPLOADED_FILES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_metadata():
    """Load metadata"""
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"files": {}, "reports": {}}
    return {"files": {}, "reports": {}}


def save_metadata(metadata):
    """Save metadata"""
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, default=str)


def init_session_state():
    """Initialize session state"""
    if 'genomics_metadata' not in st.session_state:
        st.session_state.genomics_metadata = load_metadata()


def render_genomics_module():
    """Отображение модуля геномики с интеграцией QualityControlSuite"""

    # Initialize
    init_directories()
    init_session_state()

    st.header("🧬 Модуль обработки геномных данных")

    # Создаем табы с иконками
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Новый анализ",
        "📁 История файлов",
        "📊 Реестр отчетов",
        "⚙️ Настройки"
    ])

    # Tab 1: Новый анализ
    with tab1:
        st.subheader("📤 Загрузка и анализ FASTQ файлов")

        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_file = st.file_uploader(
                "Загрузите FASTQ файл",
                type=['fastq', 'fq', 'gz'],
                help="Поддерживаемые форматы: .fastq, .fq, .fastq.gz, .fq.gz"
            )

            if uploaded_file:
                file_size_mb = uploaded_file.size / 1024 / 1024
                st.info(f"📁 **{uploaded_file.name}** ({file_size_mb:.2f} MB)")

                # Sample size slider
                sample_size = st.slider(
                    "Количество ридов для анализа",
                    min_value=1000,
                    max_value=100000,
                    value=10000,
                    step=1000,
                    help="Для больших файлов рекомендуется 10000-50000 ридов"
                )

                if st.button("🚀 Запустить анализ", type="primary"):
                    # Check if QC module is available
                    if not QC_AVAILABLE:
                        st.error("❌ QC модуль недоступен. Проверьте установку зависимостей.")
                        st.info("Убедитесь, что модули genomics установлены корректно.")
                        st.stop()

                    # Save uploaded file
                    file_id = str(uuid.uuid4())
                    file_path = UPLOADED_FILES_DIR / f"{file_id}_{uploaded_file.name}"

                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())

                    # Create progress indicators
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    try:
                        # Step 1: Validation
                        status_text.info("🔍 Валидация файла...")
                        progress_bar.progress(20)

                        # Step 2: Analysis
                        status_text.info(f"⚙️ Анализ {sample_size:,} ридов...")
                        progress_bar.progress(40)

                        # Run advanced QC
                        qc_results = run_advanced_fastq_qc(
                            str(file_path),
                            REPORTS_DIR,
                            sample_size=sample_size
                        )

                        progress_bar.progress(80)

                        if qc_results:
                            # Update metadata
                            metadata = st.session_state.genomics_metadata

                            # Add file info
                            metadata['files'][file_id] = {
                                'original_name': uploaded_file.name,
                                'file_path': str(file_path),
                                'size_mb': file_size_mb,
                                'upload_timestamp': datetime.now().isoformat(),
                                'sample_size': sample_size
                            }

                            # Add report info
                            report_id = str(uuid.uuid4())
                            metadata['reports'][report_id] = {
                                'file_id': file_id,
                                'file_name': uploaded_file.name,
                                'html_report': qc_results['html_report'],
                                'json_metrics': qc_results['json_metrics'],
                                'status': qc_results['status'],
                                'metrics': qc_results['metrics'],
                                'timestamp': datetime.now().isoformat()
                            }

                            save_metadata(metadata)
                            st.session_state.genomics_metadata = metadata

                            progress_bar.progress(100)
                            status_text.success("✅ Анализ завершен!")

                            # Display results
                            st.markdown("---")
                            st.markdown("### 📊 Результаты анализа")

                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                st.metric(
                                    "Всего ридов",
                                    f"{qc_results['metrics']['total_reads']:,}"
                                )

                            with col2:
                                q30 = qc_results['metrics']['q30_percentage']
                                st.metric(
                                    "Q30 %",
                                    f"{q30:.1f}%",
                                    delta="PASS" if q30 >= 80 else "WARNING"
                                )

                            with col3:
                                st.metric(
                                    "GC %",
                                    f"{qc_results['metrics']['gc_content']:.1f}%"
                                )

                            with col4:
                                status = qc_results['status']
                                status_icon = "✅" if status == "PASS" else "⚠️" if status == "WARNING" else "❌"
                                st.metric("Статус", f"{status_icon} {status}")

                            # Download buttons
                            st.markdown("### 📥 Скачать отчеты")
                            col1, col2 = st.columns(2)

                            with col1:
                                with open(qc_results['html_report'], 'r', encoding='utf-8') as f:
                                    html_content = f.read()
                                st.download_button(
                                    "📄 HTML отчет",
                                    html_content,
                                    file_name=f"{uploaded_file.name}_report.html",
                                    mime="text/html"
                                )

                            with col2:
                                with open(qc_results['json_metrics'], 'r', encoding='utf-8') as f:
                                    json_content = f.read()
                                st.download_button(
                                    "📊 JSON метрики",
                                    json_content,
                                    file_name=f"{uploaded_file.name}_metrics.json",
                                    mime="application/json"
                                )

                            st.balloons()

                        else:
                            status_text.error("❌ Ошибка анализа")
                            st.error("Не удалось выполнить анализ. Проверьте формат файла.")

                    except Exception as e:
                        status_text.error(f"❌ Ошибка: {e}")
                        st.error(f"Произошла ошибка: {str(e)}")

                    finally:
                        progress_bar.empty()

        with col2:
            st.markdown("### 📋 Информация")
            st.markdown("""
            **Поддерживаемые форматы:**
            - `.fastq`, `.fq`
            - `.fastq.gz`, `.fq.gz`

            **Метрики анализа:**
            - Количество ридов
            - Q20/Q30 проценты
            - GC-содержание
            - Средняя длина ридов
            - Процент N-оснований

            **Требования:**
            - Illumina/PacBio/Nanopore
            - Корректный FASTQ формат
            """)

            if QC_AVAILABLE:
                st.success("✅ QC модуль активен")
            else:
                st.warning("⚠️ QC модуль недоступен")

    # Tab 2: История файлов
    with tab2:
        st.subheader("📁 Загруженные файлы")

        metadata = st.session_state.genomics_metadata

        if metadata['files']:
            files_df = pd.DataFrame([
                {
                    'ID': file_id[:8],
                    'Имя файла': info['original_name'],
                    'Размер (MB)': f"{info['size_mb']:.2f}",
                    'Дата загрузки': info['upload_timestamp'][:19].replace('T', ' '),
                    'Sample size': f"{info['sample_size']:,}"
                }
                for file_id, info in metadata['files'].items()
            ])

            st.dataframe(files_df, use_container_width=True, hide_index=True)

            st.info(f"📊 Всего файлов: {len(metadata['files'])}")

        else:
            st.info("Нет загруженных файлов. Загрузите файл во вкладке 'Новый анализ'.")

    # Tab 3: Реестр отчетов
    with tab3:
        st.subheader("📊 Созданные отчеты")

        metadata = st.session_state.genomics_metadata

        if metadata['reports']:
            for report_id, report_info in sorted(
                metadata['reports'].items(),
                key=lambda x: x[1]['timestamp'],
                reverse=True
            ):
                with st.expander(
                    f"📄 {report_info['file_name']} - {report_info['timestamp'][:19].replace('T', ' ')}",
                    expanded=False
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Всего ридов",
                            f"{report_info['metrics']['total_reads']:,}"
                        )

                    with col2:
                        st.metric(
                            "Q30 %",
                            f"{report_info['metrics']['q30_percentage']:.1f}%"
                        )

                    with col3:
                        status = report_info['status']
                        status_icon = "✅" if status == "PASS" else "⚠️" if status == "WARNING" else "❌"
                        st.metric("Статус", f"{status_icon} {status}")

                    # View and download buttons
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button(f"👁️ Просмотр", key=f"view_{report_id}"):
                            with open(report_info['html_report'], 'r', encoding='utf-8') as f:
                                html_content = f.read()
                            components.html(html_content, height=800, scrolling=True)

                    with col2:
                        with open(report_info['html_report'], 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        st.download_button(
                            "📥 HTML",
                            html_content,
                            file_name=f"{report_info['file_name']}_report.html",
                            mime="text/html",
                            key=f"dl_html_{report_id}"
                        )

                    with col3:
                        with open(report_info['json_metrics'], 'r', encoding='utf-8') as f:
                            json_content = f.read()
                        st.download_button(
                            "📥 JSON",
                            json_content,
                            file_name=f"{report_info['file_name']}_metrics.json",
                            mime="application/json",
                            key=f"dl_json_{report_id}"
                        )

            st.info(f"📊 Всего отчетов: {len(metadata['reports'])}")

        else:
            st.info("Нет созданных отчетов. Выполните анализ во вкладке 'Новый анализ'.")

    # Tab 4: Настройки
    with tab4:
        st.subheader("⚙️ Настройки и статистика")

        metadata = st.session_state.genomics_metadata

        # Statistics
        st.markdown("### 📈 Статистика")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📁 Файлов", len(metadata['files']))

        with col2:
            st.metric("📊 Отчетов", len(metadata['reports']))

        with col3:
            total_size = sum(f['size_mb'] for f in metadata['files'].values())
            st.metric("💾 Всего данных", f"{total_size:.1f} MB")

        st.markdown("---")

        # Data management
        st.markdown("### 🗂️ Управление данными")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Очистить историю файлов", type="secondary"):
                if st.session_state.get('confirm_clear_files', False):
                    metadata['files'] = {}
                    save_metadata(metadata)
                    st.session_state.genomics_metadata = metadata
                    st.session_state.confirm_clear_files = False
                    st.success("✅ История файлов очищена")
                    st.rerun()
                else:
                    st.session_state.confirm_clear_files = True
                    st.warning("⚠️ Нажмите еще раз для подтверждения")

        with col2:
            if st.button("🗑️ Очистить все отчеты", type="secondary"):
                if st.session_state.get('confirm_clear_reports', False):
                    metadata['reports'] = {}
                    save_metadata(metadata)
                    st.session_state.genomics_metadata = metadata
                    st.session_state.confirm_clear_reports = False
                    st.success("✅ Отчеты очищены")
                    st.rerun()
                else:
                    st.session_state.confirm_clear_reports = True
                    st.warning("⚠️ Нажмите еще раз для подтверждения")

        st.markdown("---")

        # System info
        st.markdown("### 🔧 Информация о системе")
        st.markdown(f"""
        - **QC модуль:** {'✅ Активен' if QC_AVAILABLE else '❌ Недоступен'}
        - **Директория данных:** `{DATA_DIR}`
        - **Директория отчетов:** `{REPORTS_DIR}`
        - **Метаданные:** `{METADATA_FILE}`
        """)

if __name__ == "__main__":
    render_genomics_module()