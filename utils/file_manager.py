# -*- coding: utf-8 -*-
"""
Менеджер файлов для сохранения загруженных данных и отчетов
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """
    Класс для управления загруженными файлами и отчетами
    """
    
    def __init__(self, base_dir: Union[str, Path] = "data_storage"):
        """
        Инициализация файлового менеджера
        
        Args:
            base_dir: Базовая директория для хранения файлов
        """
        self.base_dir = Path(base_dir)
        self.uploaded_files_dir = self.base_dir / "uploaded_files"
        self.reports_dir = self.base_dir / "reports"
        self.metadata_file = self.base_dir / "file_metadata.json"
        
        # Создание необходимых директорий
        self.uploaded_files_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Загрузка метаданных
        self.metadata = self._load_metadata()
        
    def _load_metadata(self) -> Dict:
        """Загрузка метаданных файлов"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Не удалось загрузить метаданные: {e}")
        
        return {
            "uploaded_files": {},
            "reports": {}
        }
    
    def _save_metadata(self):
        """Сохранение метаданных файлов"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных: {e}")
    
    def save_uploaded_file(self, file_content: bytes, original_filename: str, 
                          data_type: str, description: str = "") -> str:
        """
        Сохранение загруженного файла
        
        Args:
            file_content: Содержимое файла
            original_filename: Исходное имя файла
            data_type: Тип данных (bulk_rnaseq, scrna_seq)
            description: Описание файла
            
        Returns:
            str: Уникальный ID сохраненного файла
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = f"{data_type}_{timestamp}"
        
        # Определение расширения файла
        file_ext = Path(original_filename).suffix
        saved_filename = f"{file_id}{file_ext}"
        saved_path = self.uploaded_files_dir / saved_filename
        
        # Сохранение файла
        try:
            with open(saved_path, 'wb') as f:
                f.write(file_content)
            
            # Обновление метаданных
            self.metadata["uploaded_files"][file_id] = {
                "original_filename": original_filename,
                "saved_filename": saved_filename,
                "saved_path": str(saved_path),
                "data_type": data_type,
                "description": description,
                "upload_timestamp": datetime.now().isoformat(),
                "file_size": len(file_content)
            }
            
            self._save_metadata()
            logger.info(f"Файл сохранен: {file_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения файла: {e}")
            raise
    
    def get_uploaded_files(self, data_type: Optional[str] = None) -> List[Dict]:
        """
        Получение списка загруженных файлов
        
        Args:
            data_type: Фильтр по типу данных
            
        Returns:
            List[Dict]: Список файлов с метаданными
        """
        files = []
        for file_id, metadata in self.metadata["uploaded_files"].items():
            if data_type is None or metadata["data_type"] == data_type:
                file_info = metadata.copy()
                file_info["file_id"] = file_id
                file_info["exists"] = Path(metadata["saved_path"]).exists()
                files.append(file_info)
        
        # Сортировка по времени загрузки (новые первыми)
        files.sort(key=lambda x: x["upload_timestamp"], reverse=True)
        return files
    
    def get_file_path(self, file_id: str) -> Optional[str]:
        """
        Получение пути к сохраненному файлу
        
        Args:
            file_id: ID файла
            
        Returns:
            Optional[str]: Путь к файлу или None
        """
        if file_id in self.metadata["uploaded_files"]:
            file_path = self.metadata["uploaded_files"][file_id]["saved_path"]
            if Path(file_path).exists():
                return file_path
        return None
    
    def delete_uploaded_file(self, file_id: str) -> bool:
        """
        Удаление загруженного файла
        
        Args:
            file_id: ID файла
            
        Returns:
            bool: True если файл удален успешно
        """
        if file_id not in self.metadata["uploaded_files"]:
            return False
        
        try:
            file_path = Path(self.metadata["uploaded_files"][file_id]["saved_path"])
            if file_path.exists():
                file_path.unlink()
            
            del self.metadata["uploaded_files"][file_id]
            self._save_metadata()
            logger.info(f"Файл удален: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления файла {file_id}: {e}")
            return False
    
    def save_report(self, report_files: Dict[str, str], analysis_type: str,
                   source_file_id: str, description: str = "") -> str:
        """
        Сохранение отчета
        
        Args:
            report_files: Словарь путей к файлам отчета
            analysis_type: Тип анализа
            source_file_id: ID исходного файла
            description: Описание отчета
            
        Returns:
            str: Уникальный ID отчета
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_id = f"report_{analysis_type}_{timestamp}"
        
        # Создание директории для отчета
        report_dir = self.reports_dir / report_id
        report_dir.mkdir(exist_ok=True)
        
        saved_files = {}
        
        try:
            # Копирование файлов отчета
            for file_type, source_path in report_files.items():
                if Path(source_path).exists():
                    if Path(source_path).is_file():
                        # Обычный файл
                        dest_path = report_dir / Path(source_path).name
                        shutil.copy2(source_path, dest_path)
                        saved_files[file_type] = str(dest_path)
                    elif Path(source_path).is_dir():
                        # Директория (например, plots)
                        dest_dir = report_dir / Path(source_path).name
                        shutil.copytree(source_path, dest_dir, dirs_exist_ok=True)
                        saved_files[file_type] = str(dest_dir)
            
            # Обновление метаданных
            self.metadata["reports"][report_id] = {
                "analysis_type": analysis_type,
                "source_file_id": source_file_id,
                "description": description,
                "report_dir": str(report_dir),
                "files": saved_files,
                "creation_timestamp": datetime.now().isoformat()
            }
            
            self._save_metadata()
            logger.info(f"Отчет сохранен: {report_id}")
            return report_id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения отчета: {e}")
            # Попытка очистки при ошибке
            if report_dir.exists():
                shutil.rmtree(report_dir, ignore_errors=True)
            raise
    
    def get_reports(self, analysis_type: Optional[str] = None) -> List[Dict]:
        """
        Получение списка отчетов
        
        Args:
            analysis_type: Фильтр по типу анализа
            
        Returns:
            List[Dict]: Список отчетов с метаданными
        """
        reports = []
        for report_id, metadata in self.metadata["reports"].items():
            if analysis_type is None or metadata["analysis_type"] == analysis_type:
                report_info = metadata.copy()
                report_info["report_id"] = report_id
                report_info["exists"] = Path(metadata["report_dir"]).exists()
                
                # Информация об исходном файле
                source_file_id = metadata.get("source_file_id")
                if source_file_id and source_file_id in self.metadata["uploaded_files"]:
                    report_info["source_filename"] = self.metadata["uploaded_files"][source_file_id]["original_filename"]
                else:
                    report_info["source_filename"] = "Неизвестно"
                
                reports.append(report_info)
        
        # Сортировка по времени создания (новые первыми)
        reports.sort(key=lambda x: x["creation_timestamp"], reverse=True)
        return reports
    
    def get_report_files(self, report_id: str) -> Optional[Dict[str, str]]:
        """
        Получение путей к файлам отчета
        
        Args:
            report_id: ID отчета
            
        Returns:
            Optional[Dict[str, str]]: Словарь файлов отчета или None
        """
        if report_id in self.metadata["reports"]:
            return self.metadata["reports"][report_id]["files"]
        return None
    
    def delete_report(self, report_id: str) -> bool:
        """
        Удаление отчета
        
        Args:
            report_id: ID отчета
            
        Returns:
            bool: True если отчет удален успешно
        """
        if report_id not in self.metadata["reports"]:
            return False
        
        try:
            report_dir = Path(self.metadata["reports"][report_id]["report_dir"])
            if report_dir.exists():
                shutil.rmtree(report_dir)
            
            del self.metadata["reports"][report_id]
            self._save_metadata()
            logger.info(f"Отчет удален: {report_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления отчета {report_id}: {e}")
            return False
    
    def get_storage_info(self) -> Dict:
        """
        Получение информации о хранилище
        
        Returns:
            Dict: Статистика хранилища
        """
        uploaded_files_count = len(self.metadata["uploaded_files"])
        reports_count = len(self.metadata["reports"])
        
        # Расчет размера
        total_size = 0
        for file_info in self.metadata["uploaded_files"].values():
            total_size += file_info.get("file_size", 0)
        
        return {
            "uploaded_files_count": uploaded_files_count,
            "reports_count": reports_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "base_dir": str(self.base_dir)
        }