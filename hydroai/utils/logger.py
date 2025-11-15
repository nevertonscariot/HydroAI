"""
Sistema de logging do HydroAI
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_file: Path = None, level: str = 'INFO'):
    """
    Configura sistema de logging para toda aplicação
    
    Parameters:
    -----------
    log_file : Path, optional
        Arquivo para salvar logs
    level : str
        Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Formato do log
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove handlers existentes para evitar duplicatas
    root_logger.handlers.clear()
    
    # ============ Handler para CONSOLE ============
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # ============ Handler para ARQUIVO (opcional) ============
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)
    
    root_logger.info("Sistema de logging inicializado")

