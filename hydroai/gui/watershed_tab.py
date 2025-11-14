"""
Aba para delimitação de bacia hidrográfica
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QProgressBar, QComboBox
)
from PyQt5.QtCore import QThread, pyqtSignal
from pathlib import Path
from hydroai.watershed import WatershedDelineator

class WatershedWorker(QThread):
    """Thread para executar delimitação sem travar GUI"""
    
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, dem_path, lat, lon):
        super().__init__()
        self.dem_path = dem_path
        self.lat = lat
        self.lon = lon
    
    def run(self):
        try:
            self.progress.emit(25)
            
            delineator = WatershedDelineator()
            
            self.progress.emit(50)
            
            watershed_gdf = delineator.delineate(
                self.lat, self.lon,
                dem_path=self.dem_path,
                output_dir=Path('results/bacia')
            )
            
            self.progress.emit(75)
            
            stats = delineator.get_stats(watershed_gdf)
            
            self.progress.emit(100)
            self.finished.emit((watershed_gdf, stats))
            
        except Exception as e:
            self.error.emit(str(e))

class WatershedTab(QWidget):
    """
    Aba para gerenciar delimitação de bacia
    """
    
    def __init__(self, parent):
        super().__init__()
        self.parent_window = parent
        self.dem_path = None
        self.worker = None
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Status
        layout.addWidget(QLabel("Status: Aguardando..."))
        
        # Progress bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        layout.addStretch()
    
    def delineate(self, lat, lon, dem_path=None):
        """Inicia delimitação"""
        if dem_path is None:
            dem_path = Path('data/dem/dem_SRTM30_-29.41_-56.74.tif')
        
        if not Path(dem_path).exists():
            QMessageBox.critical(
                self,
                "Erro",
                f"DEM não encontrado: {dem_path}\nBaixe o DEM primeiro"
            )
            return
        
        # Thread worker
        self.worker = WatershedWorker(dem_path, lat, lon)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()
    
    def _on_progress(self, value):
        self.progress.setValue(value)
    
    def _on_finished(self, result):
        watershed_gdf, stats = result
        
        self.parent_window.watershed_gdf = watershed_gdf
        self.parent_window._log(f"✓ Bacia delimitada!")
        self.parent_window._log(f"  Área: {stats['area_km2']:.2f} km²")
        
        # Adiciona ao mapa
        geojson = watershed_gdf.__geo_interface__
        self.parent_window.map_widget.add_polygon(geojson, "Bacia")
    
    def _on_error(self, error):
        QMessageBox.critical(self, "Erro", f"Erro: {error}")
