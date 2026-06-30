"""
Genomics Module Component for OmicsIntegrationSuite
Enhanced with QualityControlSuite FASTQ analysis capabilities

Version: 1.1 - 3-Tab Architecture (Iteration 064)
Refactored from 4 tabs → 3 tabs following mirna pattern

Integrated from: QualityControlSuite (https://github.com/otinoff/QualityControlSuite)
nVERSION = "1.1.1"  # Version with fixed paths and defensive .get()
"""

import streamlit as st
from modules.shared.ui_components.file_upload_display import show_uploaded_file_info
from ui_components.server_files_selector import render_server_files_selector
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
DATA_DIR = Path("data/genomics")
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

    # Initialize state for data flow between tabs
    if 'selected_file_path' not in st.session_state:
        st.session_state.selected_file_path = None
    if 'file_id' not in st.session_state:
        st.session_state.file_id = None
    if 'file_metadata' not in st.session_state:
        st.session_state.file_metadata = None
    if 'qc_results' not in st.session_state:
        st.session_state.qc_results = None

    # ✅ NEW (Iteration_066): Processing state (miRNA pattern)
    if "genomics_processing_complete" not in st.session_state:
        st.session_state.genomics_processing_complete = False
    if "genomics_qc_results" not in st.session_state:
        st.session_state.genomics_qc_results = None
    if "genomics_selected_file" not in st.session_state:
        st.session_state.genomics_selected_file = None


def scan_server_files():
    """Scan server for previously uploaded files (like mirna pattern)"""
    server_files = []

    if UPLOADED_FILES_DIR.exists():
        for file_path in UPLOADED_FILES_DIR.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.fastq', '.fq', '.gz']:
                try:
                    stats = file_path.stat()
                    server_files.append({
                        'path': file_path,
                        'name': file_path.name,
                        'size_mb': stats.st_size / (1024 * 1024),
                        'modified': datetime.fromtimestamp(stats.st_mtime)
                    })
                except Exception as e:
                    continue

    return sorted(server_files, key=lambda x: x['modified'], reverse=True)


def render_genomics_module():
    """Отображение модуля геномики с 3-tab архитектурой"""

    # Initialize
    init_directories()
    init_session_state()

    st.header("🧬 Модуль обработки геномных данных")

    # 3-TAB STRUCTURE (Upload → Process → Results)
    tab1, tab2, tab3 = st.tabs([
        "📤 Загрузка данных",
        "⚙️ Обработка",
        "📊 Результаты"
    ])

    # ========================================================================
    # TAB 1: ЗАГРУЗКА ДАННЫХ (Upload)
    # ========================================================================
    with tab1:
        st.subheader("📤 Загрузка FASTQ файлов")

        col1, col2 = st.columns([2, 1])

        with col1:
            # File uploader
            uploaded_file = st.file_uploader(
                "Загрузите FASTQ файл",
                type=['fastq', 'fq', 'gz'],
                help="Поддерживаемые форматы: .fastq, .fq, .fastq.gz, .fq.gz"
            )

            if uploaded_file:
                # Use unified file display component (Iteration 062)
                file_info = show_uploaded_file_info(uploaded_file, show_preview=False)

                if st.button("💾 Сохранить файл", type="primary"):
                    # Save uploaded file
                    file_id = str(uuid.uuid4())
                    file_path = UPLOADED_FILES_DIR / f"{file_id}_{uploaded_file.name}"

                    file_size_mb = uploaded_file.size / (1024 * 1024)

                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())

                    # Update metadata
                    metadata = st.session_state.genomics_metadata
                    metadata['files'][file_id] = {
                        'original_name': uploaded_file.name,
                        'file_path': str(file_path),
                        'size_mb': file_size_mb,
                        'upload_timestamp': datetime.now().isoformat()
                    }
                    save_metadata(metadata)
                    st.session_state.genomics_metadata = metadata

                    # Set selected file for processing
                    st.session_state.selected_file_path = file_path
                    st.session_state.file_id = file_id
                    st.session_state.file_metadata = metadata['files'][file_id]

                    st.success(f"✅ Файл сохранен: {uploaded_file.name}")
                    st.info("Перейдите на вкладку '⚙️ Обработка' для анализа")

            st.markdown("---")

            # Previously uploaded files (radio button selector - Iteration 068)
            st.markdown("### 📁 Ранее загруженные файлы")

            server_files = scan_server_files()

            # Use shared component with radio buttons
            selected_file = render_server_files_selector(
                files=server_files,
                session_key="genomics_selected_file",
                title="Файлы геномики"
            )

            # Update legacy session state keys for compatibility with Tab 2
            if selected_file:
                st.session_state.selected_file_path = selected_file['path']
                st.session_state.file_id = selected_file['path'].stem
                st.session_state.file_metadata = {
                    'original_name': selected_file['name'],
                    'file_path': str(selected_file['path']),
                    'size_mb': selected_file['size_mb'],
                    'upload_timestamp': datetime.now().isoformat()
                }

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

            # Show current selection
            if st.session_state.selected_file_path:
                st.markdown("---")
                st.success("✅ Файл выбран")
                st.caption(f"📄 {st.session_state.file_metadata['original_name']}")

    # ========================================================================
    # TAB 2: ОБРАБОТКА (Process)
    # ========================================================================
    with tab2:
            st.subheader("⚙️ Параметры обработки")

            # Server files list
            server_files = scan_server_files()

            if not server_files:
                st.warning("⚠️ Нет файлов на сервере. Загрузите файл в разделе 'Загрузка данных'")
                st.button("🚀 Начать анализ", type="primary", disabled=True)
            else:
                # File selection
                st.markdown("### 📁 Выбор файла")
                selected_file = st.selectbox(
                    "Файл для анализа:",
                    options=server_files,
                    format_func=lambda x: f"{x['name']} ({x['size_mb']:.1f} MB)"
                )

                st.markdown("---")

                # Analysis parameters
                st.markdown("### 🔧 Параметры анализа")

                col1, col2 = st.columns(2)

                with col1:
                    sample_size = st.number_input(
                        "Sample size (ридов для анализа)",
                        min_value=1000,
                        max_value=1000000,
                        value=10000,
                        step=1000,
                        help="Количество ридов для QC анализа"
                    )

                with col2:
                    st.info(f"\n\n📊 Будет проанализировано: **{sample_size:,}** ридов")

                st.markdown("---")

                # Processing button
                if st.button("🚀 Начать анализ", type="primary"):
                    if not QC_AVAILABLE:
                        st.error("❌ QC модуль недоступен")
                    else:
                        with st.status("🔄 Обработка...", expanded=True) as status_widget:
                            progress = st.progress(0, text="Инициализация...")

                            # Run QC
                            progress.progress(0.3, text=f"Анализ {selected_file['name']}...")

                            try:
                                qc_results = run_advanced_fastq_qc(
                                    str(selected_file['path']),
                                    sample_size=sample_size
                                )

                                progress.progress(1.0, text="Завершено!")

                                if qc_results and qc_results.get('status') in ['PASS', 'WARNING', 'FAIL']:
                                    # ✅ Save to session_state (miRNA pattern)
                                    st.session_state.genomics_qc_results = qc_results
                                    st.session_state.genomics_processing_complete = True
                                    st.session_state.genomics_selected_file = {
                                        'name': selected_file['name'],
                                        'path': str(selected_file['path']),
                                        'size_mb': selected_file['size_mb']
                                    }

                                    status_widget.update(label="✅ Обработка завершена!", state="complete")

                                    # ✅ Success notification (NO RESULTS HERE!)
                                    st.balloons()
                                    st.success("✅ Обработка завершена успешно!")
                                    st.info("📊 Перейдите на вкладку **'📊 Результаты'** для просмотра отчёта")

                                else:
                                    status_widget.update(label="❌ Ошибка анализа", state="error")
                                    st.error("❌ Ошибка при анализе данных")
                                    st.session_state.genomics_processing_complete = False

                            except Exception as e:
                                progress.progress(0, text="Ошибка!")
                                status_widget.update(label=f"❌ Ошибка: {e}", state="error")
                                st.error(f"❌ Ошибка выполнения QC: {e}")
                                st.session_state.genomics_processing_complete = False
    with tab3:
        st.subheader("📊 Результаты анализа")

        # ✅ Empty state check (miRNA pattern)
        if not st.session_state.genomics_processing_complete:
            st.info("📊 Результаты появятся после обработки данных")
            st.markdown("""
            ### Для получения результатов:
            1. 📤 Загрузите файл в разделе 'Загрузка данных'
            2. ⚙️ Настройте параметры в разделе 'Обработка'
            3. 🚀 Запустите обработку
            """)
            return

        # ✅ Read from session_state
        qc_results = st.session_state.genomics_qc_results
        selected_file = st.session_state.genomics_selected_file

        if not qc_results:
            st.warning("⚠️ Нет данных для отображения")
            return

        # Display file info
        st.info(f"📁 **Файл:** {selected_file['name']} ({selected_file['size_mb']:.1f} MB)")

        st.markdown("---")

        # ✅ Quick Summary (4 metrics)
        st.markdown("### 📊 Результаты анализа (Quick Summary)")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_reads = qc_results['metrics'].get('total_reads', 0)
            st.metric("Всего ридов", f"{total_reads:,}")

        with col2:
            q30_pct = qc_results['metrics'].get('q30_percentage', 0.0)
            status_emoji = "✅" if q30_pct >= 80 else "⚠️"
            st.metric("Q30 %", f"{q30_pct:.1f}% {status_emoji}")

        with col3:
            gc_content = qc_results['metrics'].get('gc_content', 0.0)
            st.metric("GC %", f"{gc_content:.1f}%")

        with col4:
            status = qc_results['metrics'].get('status', 'UNKNOWN')
            status_icons = {'PASS': '✅', 'WARNING': '⚠️', 'FAIL': '❌'}
            status_icon = status_icons.get(status, '❓')
            st.metric("Статус", f"{status_icon} {status}")

        st.markdown("---")

        # ✅ Detailed Summary Table (7 rows)
        st.markdown("### 📋 Детальная сводка (Summary)")

        m = qc_results['metrics']

        # Calculate Q20 reads percentage
        q20_reads_pct = 0.0
        if m.get('total_reads', 0) > 0:
            q20_reads_pct = (m.get('q20_reads', 0) / m.get('total_reads', 1)) * 100

        # Calculate total GC bases and Q20 bases
        total_bases = m.get('total_bases', 0)
        gc_pct = m.get('gc_content', 0.0)
        q20_pct = m.get('q20_percentage', 0.0)

        total_gc_bases = int(total_bases * gc_pct / 100)
        total_q20_bases = int(total_bases * q20_pct / 100)

        summary_data = {
            "Метрика": [
                "Mean length",
                "Length range (min-max)",
                "Total reads",
                "Q20 reads",
                "Total bases",
                "Total GC bases",
                "Q20 bases"
            ],
            "Значение": [
                f"{m.get('avg_read_length', 0):.2f}",
                f"{m.get('min_read_length', 0)} - {m.get('max_read_length', 0)}",
                f"{m.get('total_reads', 0):,}",
                f"{m.get('q20_reads', 0):,}",
                f"{total_bases:,}",
                f"{total_gc_bases:,}",
                f"{total_q20_bases:,}"
            ],
            "Процент": [
                "",
                "",
                "",
                f"{q20_reads_pct:.2f}%",
                "",
                f"{gc_pct:.2f}%",
                f"{q20_pct:.2f}%"
            ]
        }

        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ✅ Download button (ONLY HTML, renamed)
        st.markdown("### 📥 Скачать отчет")

        if qc_results.get('html_report'):
            html_path = Path(qc_results['html_report'])
            if html_path.exists():
                with open(html_path, 'rb') as f:
                    html_bytes = f.read()

                st.download_button(
                    label="📄 Скачать отчёт",
                    data=html_bytes,
                    file_name=html_path.name,
                    mime="text/html",
                    type="primary"
                )
            else:
                st.warning(f"⚠️ HTML отчёт не найден: {html_path.name}")
        else:
            st.warning("⚠️ HTML отчёт не был создан")

        st.markdown("---")

        # ✅ Display HTML report inline
        if qc_results.get('html_report'):
            html_path = Path(qc_results['html_report'])
            if html_path.exists():
                st.markdown("### 📄 Просмотр отчёта")

                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()

                st.components.v1.html(html_content, height=800, scrolling=True)
            else:
                st.info("💡 HTML отчёт будет отображён здесь после успешной обработки")
