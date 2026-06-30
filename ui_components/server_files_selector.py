"""
Universal Server Files Selector Component
Iteration 068 - Radio button pattern for single file selection

Created: 2025-11-21
Author: Claude Code
"""

import streamlit as st
from pathlib import Path
from typing import List, Dict, Optional


def render_server_files_selector(
    files: List[Dict],
    session_key: str,
    title: str = "Файлы на сервере"
) -> Optional[Dict]:
    """
    Universal server files selector with radio buttons (single selection)

    Shows individual file sizes (verbose, appropriate for 7-10 files prototype).
    Uses radio buttons for clean single-selection UX.

    Args:
        files: List of file dicts [{'name': str, 'path': Path/str, 'size_mb': float}]
        session_key: Module-specific session state key (e.g., "genomics_selected_file")
        title: Display title (default: "Файлы на сервере")

    Returns:
        Selected file dict or None if no files

    Examples:
        >>> # Genomics module
        >>> server_files = scan_server_files()
        >>> selected = render_server_files_selector(
        ...     files=server_files,
        ...     session_key="genomics_selected_file",
        ...     title="Файлы геномики"
        ... )

        >>> # miRNA module
        >>> existing_files = scan_existing_files()
        >>> selected = render_server_files_selector(
        ...     files=existing_files,
        ...     session_key="mirna_selected_file",
        ...     title="Файлы miRNA"
        ... )
    """

    if not files:
        # Empty state
        st.info(f"📁 {title} не найдены")
        st.markdown("""
        Загрузите файл через форму выше, чтобы начать работу.
        """)
        return None

    # Header
    st.markdown(f"💾 **{title}**")

    # File count with Russian pluralization
    file_count = len(files)
    if file_count == 1:
        files_text = "файл"
    elif file_count in [2, 3, 4]:
        files_text = "файла"
    else:
        files_text = "файлов"

    # Success message
    st.success(f"✅ Найдено {file_count} {files_text} на сервере")

    # Radio button selector
    # Convert file dict to index for st.radio (it needs hashable options)
    file_options = list(range(len(files)))

    selected_index = st.radio(
        "Выберите файл для обработки:",
        options=file_options,
        format_func=lambda idx: f"📄 {files[idx]['name']} ({files[idx]['size_mb']:.1f} MB)",
        key=f"{session_key}_radio"
    )

    # Get selected file
    selected_file = files[selected_index] if selected_index is not None else None

    if selected_file:
        # Save to session state
        st.session_state[session_key] = selected_file

        # Navigation hint
        st.info("→ Перейдите на вкладку '⚙️ Обработка' для анализа")

    return selected_file


def get_russian_pluralization(count: int) -> str:
    """
    Helper function for Russian pluralization

    Args:
        count: Number of items

    Returns:
        Correct Russian word form for 'файл'

    Examples:
        >>> get_russian_pluralization(1)
        'файл'
        >>> get_russian_pluralization(3)
        'файла'
        >>> get_russian_pluralization(7)
        'файлов'
    """
    if count == 1:
        return "файл"
    elif count in [2, 3, 4]:
        return "файла"
    else:
        return "файлов"
