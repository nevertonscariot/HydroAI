"""
Aba para delimitação de bacia hidrográfica
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QProgressBar, QComboBox
)
from PyQt5.QtCore import QThread, pyqtSignal
from pathlib import Path
import logging
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
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        try:
            self.progress.emit(25)
            self.logger.info(f"Iniciando delimitação...")
            self.logger.info(f"  DEM: {self.dem_path}")
            self.logger.info(f"  Coordenadas: ({self.lat}, {self.lon})")
            
            delineator = WatershedDelineator()
            
            self.progress.emit(50)
            self.logger.info("Carregando DEM...")
            
            watershed_gdf = delineator.delineate(
                self.lat, self.lon,
                dem_path=self.dem_path,
                output_dir=Path('results/bacia')
            )
            
            self.progress.emit(75)
            self.logger.info("Calculando estatísticas...")
            
            stats = delineator.get_stats(watershed_gdf)
            
            self.progress.emit(100)
            self.logger.info(f"✓ Bacia delimitada! Área: {stats['area_km2']:.2f} km²")
            
            self.finished.emit((watershed_gdf, stats))
            
        except Exception as e:
            self.logger.error(f"Erro: {str(e)}")
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
        self.logger = logging.getLogger(__name__)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Título
        title = QLabel("🗺️ Delimitação de Bacia Hidrográfica")
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("Status: Aguardando...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        # Log
        self.log_label = QLabel("Logs:")
        layout.addWidget(self.log_label)
        
        from PyQt5.QtWidgets import QTextEdit
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        layout.addStretch()
    
    def delineate(self, lat, lon, dem_path=None):
        """Inicia delimitação"""
        if dem_path is None:
            # Procura por DEM em data/dem/
            dem_dir = Path('data/dem')
            dem_dir.mkdir(parents=True, exist_ok=True)
            
            # Lista TIFs disponíveis
            tif_files = list(dem_dir.glob('*.tif')) + list(dem_dir.glob('*.tiff'))
            
            if not tif_files:
                QMessageBox.critical(
                    self,
                    "Erro",
                    "Nenhum arquivo DEM encontrado em data/dem/\n\n"
                    "Por favor:\n"
                    "1. Baixe um DEM de: https://earthexplorer.usgs.gov\n"
                    "2. Salve em: data/dem/\n"
                    "3. Tente novamente"
                )
                return
            
            # Usa o primeiro encontrado
            dem_path = tif_files[0]
            self._log(f"DEM encontrado: {dem_path.name}")
        
        if not Path(dem_path).exists():
            QMessageBox.critical(
                self,
                "Erro",
                f"DEM não encontrado: {dem_path}"
            )
            return
        
        self._log(f"Iniciando delimitação...")
        self._log(f"Coordenadas: ({lat}, {lon})")
        
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
        
        self._log(f"✓ Bacia delimitada com sucesso!")
        self._log(f"  Área: {stats['area_km2']:.2f} km²")
        self._log(f"  Perímetro: {stats['perimeter_km']:.2f} km")
        self._log(f"  CRS: {stats['crs']}")
        
        # Atualiza tabela de estatísticas
        self.parent_window.stats_table.setRowCount(4)
        self.parent_window.stats_table.setItem(0, 0, 
            self.parent_window.QTableWidgetItem("Área (km²)"))
        self.parent_window.stats_table.setItem(0, 1,
            self.parent_window.QTableWidgetItem(f"{stats['area_km2']:.2f}"))
        self.parent_window.stats_table.setItem(1, 0,
            self.parent_window.QTableWidgetItem("Área (ha)"))
        self.parent_window.stats_table.setItem(1, 1,
            self.parent_window.QTableWidgetItem(f"{stats['area_ha']:.2f}"))
        self.parent_window.stats_table.setItem(2, 0,
            self.parent_window.QTableWidgetItem("Perímetro (km)"))
        self.parent_window.stats_table.setItem(2, 1,
            self.parent_window.QTableWidgetItem(f"{stats['perimeter_km']:.2f}"))
        self.parent_window.stats_table.setItem(3, 0,
            self.parent_window.QTableWidgetItem("CRS"))
        self.parent_window.stats_table.setItem(3, 1,
            self.parent_window.QTableWidgetItem(str(stats['crs'])))
        
        # Adiciona ao mapa
        try:
            geojson = watershed_gdf.__geo_interface__
            self.parent_window.map_widget.add_polygon(geojson, "Bacia Delimitada")
            self._log("✓ Bacia adicionada ao mapa")
        except Exception as e:
            self._log(f"Aviso ao adicionar ao mapa: {e}")
    
    def _on_error(self, error):
        self._log(f"❌ ERRO: {error}")
        QMessageBox.critical(self, "Erro na Delimitação", f"Erro: {error}")
    
    def _log(self, message: str):
        """Adiciona mensagem ao log"""
        current_text = self.log_text.toPlainText()
        self.log_text.setText(f"{current_text}\n{message}")
        # Scroll para o final
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
