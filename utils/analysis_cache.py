# -*- coding: utf-8 -*-
"""
Модуль для кэширования результатов анализа транскриптомики
Обеспечивает постоянное хранение результатов между сессиями
"""

import sys

import json
import pickle
import os
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AnalysisCache:
    """Класс для кэширования результатов анализа"""
    
    def __init__(self, cache_dir: str = "analysis_cache"):
        """
        Инициализация кэша
        
        Args:
            cache_dir: Директория для хранения кэша
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """Загрузка метаданных кэша"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Ошибка загрузки метаданных кэша: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def save_metadata(self):
        """Сохранение метаданных кэша"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных кэша: {e}")
    
    def _generate_cache_key(self, file_path: str, analysis_type: str, parameters: Dict) -> str:
        """Генерация ключа кэша на основе файла и параметров"""
        # Создаем хэш на основе пути к файлу, типа анализа и параметров
        content = f"{file_path}_{analysis_type}_{json.dumps(parameters, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def save_analysis(self, 
                     file_path: str, 
                     analysis_type: str, 
                     parameters: Dict, 
                     results: Any,
                     file_name: str = None) -> str:
        """
        Сохранение результатов анализа
        
        Args:
            file_path: Путь к анализируемому файлу
            analysis_type: Тип анализа (bulk_rnaseq, scrna_seq)
            parameters: Параметры анализа
            results: Результаты анализа
            file_name: Оригинальное имя файла
        
        Returns:
            str: Ключ кэша
        """
        cache_key = self._generate_cache_key(file_path, analysis_type, parameters)
        
        # Сохранение результатов в pickle файл
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(results, f)
            
            # Обновление метаданных
            self.metadata[cache_key] = {
                'file_path': file_path,
                'file_name': file_name or os.path.basename(file_path),
                'analysis_type': analysis_type,
                'parameters': parameters,
                'timestamp': datetime.now().isoformat(),
                'cache_file': str(cache_file)
            }
            
            self.save_metadata()
            
            logger.info(f"Анализ сохранен в кэш: {cache_key}")
            return cache_key
            
        except Exception as e:
            logger.error(f"Ошибка сохранения анализа в кэш: {e}")
            return None
    
    def load_analysis(self, cache_key: str) -> Optional[Any]:
        """
        Загрузка результатов анализа из кэша
        
        Args:
            cache_key: Ключ кэша
        
        Returns:
            Результаты анализа или None
        """
        if cache_key not in self.metadata:
            return None
        
        cache_file = Path(self.metadata[cache_key]['cache_file'])
        
        if not cache_file.exists():
            logger.warning(f"Файл кэша не найден: {cache_file}")
            # Удаляем из метаданных
            del self.metadata[cache_key]
            self.save_metadata()
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                results = pickle.load(f)
            
            logger.info(f"Анализ загружен из кэша: {cache_key}")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка загрузки анализа из кэша: {e}")
            return None
    
    def get_cached_analyses(self) -> List[Dict]:
        """
        Получение списка всех кэшированных анализов
        
        Returns:
            Список метаданных анализов
        """
        cached_analyses = []
        
        for cache_key, metadata in self.metadata.items():
            # Проверяем что файл кэша существует
            cache_file = Path(metadata['cache_file'])
            if cache_file.exists():
                cached_analyses.append({
                    'cache_key': cache_key,
                    **metadata
                })
            else:
                # Помечаем для удаления
                logger.warning(f"Файл кэша не найден: {cache_file}")
        
        # Сортируем по времени (новые первые)
        cached_analyses.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return cached_analyses
    
    def delete_analysis(self, cache_key: str) -> bool:
        """
        Удаление анализа из кэша
        
        Args:
            cache_key: Ключ кэша
        
        Returns:
            bool: Успешность удаления
        """
        if cache_key not in self.metadata:
            return False
        
        try:
            # Удаляем файл кэша
            cache_file = Path(self.metadata[cache_key]['cache_file'])
            if cache_file.exists():
                cache_file.unlink()
            
            # Удаляем из метаданных
            del self.metadata[cache_key]
            self.save_metadata()
            
            logger.info(f"Анализ удален из кэша: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления анализа из кэша: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """
        Очистка всего кэша
        
        Returns:
            bool: Успешность очистки
        """
        try:
            # Удаляем все файлы кэша
            for cache_key in list(self.metadata.keys()):
                self.delete_analysis(cache_key)
            
            logger.info("Кэш полностью очищен")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            return False
    
    def get_cache_size(self) -> Dict[str, Any]:
        """
        Получение размера кэша
        
        Returns:
            Информация о размере кэша
        """
        total_size = 0
        file_count = 0
        
        for cache_key, metadata in self.metadata.items():
            cache_file = Path(metadata['cache_file'])
            if cache_file.exists():
                total_size += cache_file.stat().st_size
                file_count += 1
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'file_count': file_count,
            'analysis_count': len(self.metadata)
        }
    
    def find_analysis(self, 
                     file_path: str = None, 
                     analysis_type: str = None, 
                     parameters: Dict = None) -> Optional[str]:
        """
        Поиск анализа по параметрам
        
        Args:
            file_path: Путь к файлу
            analysis_type: Тип анализа
            parameters: Параметры анализа
        
        Returns:
            Ключ кэша или None
        """
        if file_path and analysis_type and parameters:
            # Точный поиск по всем параметрам
            cache_key = self._generate_cache_key(file_path, analysis_type, parameters)
            if cache_key in self.metadata:
                return cache_key
        
        # Поиск по частичным критериям
        for cache_key, metadata in self.metadata.items():
            match = True
            
            if file_path and metadata.get('file_path') != file_path:
                match = False
            
            if analysis_type and metadata.get('analysis_type') != analysis_type:
                match = False
            
            if parameters and metadata.get('parameters') != parameters:
                match = False
            
            if match:
                return cache_key
        
        return None