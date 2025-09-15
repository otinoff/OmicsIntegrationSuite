"""
UI Components Package for OmicsIntegrationSuite
Пакет компонентов пользовательского интерфейса
"""

# Инициализация пакета UI компонентов
__version__ = "1.0.0"
__author__ = "OmicsIntegrationSuite Team"

# Экспортируемые модули
from .header import render_header
from .sidebar import render_sidebar
from .footer import render_footer
from .home_page import render_home_page
from .genomics_module import render_genomics_module
from .transcriptomics_module import render_transcriptomics_module
from .mirna_module import render_mirna_module
from .proteomics_module import render_proteomics_module
from .metabolomics_module import render_metabolomics_module
from .integration_module import render_integration_module
from .quality_control_module import render_quality_control_module
from .reporting_module import render_reporting_module

__all__ = [
    'render_header',
    'render_sidebar',
    'render_footer',
    'render_home_page',
    'render_genomics_module',
    'render_transcriptomics_module',
    'render_mirna_module',
    'render_proteomics_module',
    'render_metabolomics_module',
    'render_integration_module',
    'render_quality_control_module',
    'render_reporting_module'
]