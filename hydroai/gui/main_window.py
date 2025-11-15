"""
Janela principal da aplicação HydroAI
Interface completa com abas para diferentes análises
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QFileDialog, QMessageBox, QProgressBar, QTextEdit, QGroupBox,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor
from pathlib import Path
import logging

from hydroai.gui.map_widget import MapWidget
from hydroai.gui.watershed_tab import WatershedTab
from hydroai.gui.analysis_tab import AnalysisTab

class MainWindow(QMainWindow):
    """
    Janela principal do HydroAI
    
    Componentes:
    - Menu superior com ações
    - Painel lateral com controles
    - Mapa interativo
    - Abas de análise
    - Status bar com progresso
    """
    
    def __init__(self):
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.current_project = None
        self.watershed_gdf = None
        
        # Configuração da janela
        self.setWindowTitle("HydroAI - Sistema de Análise de Bacias Hidrográficas")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet(self._get_stylesheet())
        
        # Inicializa UI
        self._init_ui()
        
        self.logger.info("HydroAI inicializado com sucesso")
    
    def _init_ui(self):
        """Inicializa interface"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # ========== PAINEL LATERAL ESQUERDO ==========
        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel, stretch=1)
        
        # ========== ÁREA CENTRAL ==========
        center_widget = QWidget()
        center_layout = QVBoxLayout()
        center_widget.setLayout(center_layout)
        
        # Mapa interativo
        self.map_widget = MapWidget()
        center_layout.addWidget(self.map_widget, stretch=2)
        
        # Abas de análise
        self.tabs = QTabWidget()
        self.watershed_tab = WatershedTab(self)
        self.analysis_tab = AnalysisTab(self)
        
        self.tabs.addTab(self.watershed_tab, "🗺️ Bacia Hidrográfica")
        self.tabs.addTab(self.analysis_tab, "📊 Análises")
        
        center_layout.addWidget(self.tabs, stretch=1)
        
        main_layout.addWidget(center_widget, stretch=3)
        
        # ========== PAINEL DIREITO ==========
        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel, stretch=1)
        
        # Status bar
        self._create_status_bar()
    
    def _create_left_panel(self) -> QWidget:
        """Cria painel lateral esquerdo"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Título
        title = QLabel("HydroAI")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Seção: Projeto
        layout.addWidget(self._create_group_projeto())
        
        # Seção: Coordenadas
        layout.addWidget(self._create_group_coordenadas())
        
        # Seção: DEM
        layout.addWidget(self._create_group_dem())
        
        # Botões de ação
        layout.addWidget(self._create_group_acoes())
        
        # Espaço vazio
        layout.addStretch()
        
        return panel
    
    def _create_group_projeto(self) -> QGroupBox:
        """Grupo: Gerenciamento de projetos"""
        group = QGroupBox("📁 Projeto")
        layout = QVBoxLayout()
        group.setLayout(layout)
        
        # Nome do projeto
        layout.addWidget(QLabel("Nome do Projeto:"))
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("Ex: Bacia do Rio Pardo")
        layout.addWidget(self.project_name_input)
        
        # Botões
        btn_new = QPushButton("🆕 Novo Projeto")
        btn_new.clicked.connect(self.create_new_project)
        layout.addWidget(btn_new)
        
        btn_open = QPushButton("📂 Abrir Projeto")
        btn_open.clicked.connect(self.open_project)
        layout.addWidget(btn_open)
        
        return group
    
    def _create_group_coordenadas(self) -> QGroupBox:
        """Grupo: Entrada de coordenadas"""
        group = QGroupBox("📍 Coordenadas do Exutório")
        layout = QGridLayout()
        group.setLayout(layout)
        
        # Latitude
        layout.addWidget(QLabel("Latitude:"), 0, 0)
        self.lat_input = QDoubleSpinBox()
        self.lat_input.setRange(-90, 90)
        self.lat_input.setValue(-29.409)
        self.lat_input.setDecimals(6)
        layout.addWidget(self.lat_input, 0, 1)
        
        # Longitude
        layout.addWidget(QLabel("Longitude:"), 1, 0)
        self.lon_input = QDoubleSpinBox()
        self.lon_input.setRange(-180, 180)
        self.lon_input.setValue(-56.737)
        self.lon_input.setDecimals(6)
        layout.addWidget(self.lon_input, 1, 1)
        
        # Botão: Ir para coordenadas
        btn_go = QPushButton("🎯 Ir para Local")
        btn_go.clicked.connect(self.go_to_coordinates)
        layout.addWidget(btn_go, 2, 0, 1, 2)
        
        return group
    
    def _create_group_dem(self) -> QGroupBox:
        """Grupo: Seleção de DEM"""
        group = QGroupBox("🏔️ Digital Elevation Model (DEM)")
        layout = QVBoxLayout()
        group.setLayout(layout)
        
        # Tipo de DEM
        layout.addWidget(QLabel("Tipo de DEM:"))
        self.dem_type = QComboBox()
        self.dem_type.addItems([
            "SRTM 30m (Recomendado)",
            "SRTM 90m (Rápido)",
            "MERIT Hydro (Hidrologia)",
            "Copernicus 30m"
        ])
        layout.addWidget(self.dem_type)
        
        # Buffer
        layout.addWidget(QLabel("Buffer (km):"))
        self.buffer_spinbox = QSpinBox()
        self.buffer_spinbox.setRange(10, 200)
        self.buffer_spinbox.setValue(50)
        layout.addWidget(self.buffer_spinbox)
        
        # Botões
        btn_download = QPushButton("⬇️ Baixar DEM")
        btn_download.clicked.connect(self.download_dem)
        layout.addWidget(btn_download)
        
        btn_local = QPushButton("📂 Usar DEM Local")
        btn_local.clicked.connect(self.load_dem_local)
        layout.addWidget(btn_local)
        
        return group
    
    def _create_group_acoes(self) -> QGroupBox:
        """Grupo: Botões de ação principais"""
        group = QGroupBox("⚙️ Ações")
        layout = QVBoxLayout()
        group.setLayout(layout)
        
        # Delimitar bacia
        btn_delineate = QPushButton("🔴 Delimitar Bacia")
        btn_delineate.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        btn_delineate.clicked.connect(self.delineate_watershed)
        layout.addWidget(btn_delineate)
        
        # Analisar
        btn_analyze = QPushButton("📊 Analisar")
        btn_analyze.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        btn_analyze.clicked.connect(self.run_analysis)
        layout.addWidget(btn_analyze)
        
        # Gerar relatório
        btn_report = QPushButton("📄 Gerar Relatório")
        btn_report.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 10px;")
        btn_report.clicked.connect(self.generate_report)
        layout.addWidget(btn_report)
        
        return group
    
    def _create_right_panel(self) -> QWidget:
        """Cria painel direito com informações"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Título
        title = QLabel("📋 Informações")
        title_font = QFont()
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Area de log/status
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")
        layout.addWidget(self.info_text)
        
        # Tabela de estatísticas
        layout.addWidget(QLabel("📊 Estatísticas:"))
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Métrica", "Valor"])
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.stats_table)
        
        return panel
    
    def _create_status_bar(self):
        """Cria barra de status com progresso"""
        self.statusBar().showMessage("Pronto")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.statusBar().addPermanentWidget(self.progress_bar)
    
    # ============================================
    # MÉTODOS DE AÇÃO
    # ============================================
    
    def create_new_project(self):
        """Cria novo projeto"""
        name = self.project_name_input.text()
        
        if not name:
            QMessageBox.warning(self, "Aviso", "Digite um nome para o projeto")
            return
        
        from hydroai.core.project_manager import ProjectManager
        
        try:
            pm = ProjectManager(Path('data/projects'))
            lat = self.lat_input.value()
            lon = self.lon_input.value()
            
            self.current_project = pm.create_project(name, lat, lon)
            
            self._log(f"✓ Projeto criado: {name}")
            self._log(f"  Local: {self.current_project}")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar projeto: {e}")
    
    def go_to_coordinates(self):
        """Move mapa para as coordenadas"""
        lat = self.lat_input.value()
        lon = self.lon_input.value()
        
        self.map_widget.set_center(lat, lon)
        self._log(f"Mapa movido para: ({lat}, {lon})")
    
    def download_dem(self):
        """Baixa DEM automaticamente"""
        from hydroai.watershed.downloader import DEMDownloader
        
    def download_dem(self):
        """Baixa DEM com suporte a OpenTopography"""
        from hydroai.watershed.dem_downloader import DEMDownloader
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox, QSpinBox, QHBoxLayout
        
        # Dialog para configurar download
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurar Download de DEM")
        dialog.setGeometry(200, 200, 500, 300)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # Título
        title = QLabel("⚙️ Configurar Download de DEM")
        title_font = title.font()
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Dataset
        layout.addWidget(QLabel("Dataset:"))
        combo_dataset = QComboBox()
        combo_dataset.addItems(['SRTMGL1 (30m) ⭐', 'SRTMGL3 (90m)', 'ASTER (30m)', 'ALOS (30m)'])
        layout.addWidget(combo_dataset)
        
        # Buffer
        layout.addWidget(QLabel("Área de Download (buffer em km):"))
        spin_buffer = QSpinBox()
        spin_buffer.setRange(5, 100)
        spin_buffer.setValue(25)
        layout.addWidget(spin_buffer)
        
        # Info
        info_text = QLabel(
            "ℹ️ IMPORTANTE:\n"
            "• Com API Key: Download direto e rápido\n"
            "• Sem API Key: Usa OpenElevation (mais lento)\n\n"
            "Obtenha sua API Key em:\n"
            "https://portal.opentopography.org/myot"
        )
        info_text.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_text)
        
        # Botão de download
        def do_download():
            datasets = ['SRTMGL1', 'SRTMGL3', 'ASTER', 'AW3D30']
            dataset = datasets[combo_dataset.currentIndex()]
            buffer_km = spin_buffer.value()
            
            lat = self.lat_input.value()
            lon = self.lon_input.value()
            output_dir = Path('data/dem')
            
            self._log(f"🔄 Iniciando download...")
            self._log(f"  Dataset: {dataset}")
            self._log(f"  Coordenadas: ({lat}, {lon})")
            self._log(f"  Buffer: {buffer_km}km")
            self.progress_bar.setValue(25)
            
            try:
                downloader = DEMDownloader()
                
                self._log(f"Conectando ao servidor...")
                dem_path = downloader.download_dem(
                    lat, lon, output_dir,
                    buffer_km=buffer_km,
                    dataset=dataset
                )
                
                self._log(f"✓ Download concluído com sucesso!")
                self._log(f"  Arquivo: {dem_path.name}")
                self.current_dem_path = dem_path
                self.progress_bar.setValue(100)
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, 
                    "✓ Sucesso", 
                    f"DEM baixado com sucesso!\n\n{dem_path}"
                )
                
                dialog.accept()
                
            except Exception as e:
                self._log(f"❌ Erro: {str(e)}")
                self.progress_bar.setValue(0)
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "❌ Erro", f"Erro ao baixar:\n{e}")
        
        btn_download = QPushButton("⬇️ Baixar Agora")
        btn_download.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        btn_download.clicked.connect(do_download)
        layout.addWidget(btn_download)
        
        layout.addStretch()
        
        dialog.exec_()

    
    def load_dem_local(self):
        """Carrega DEM local"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar DEM",
            str(Path('data/dem')),
            "GeoTIFF (*.tif *.tiff);;Todos (*.*)"
        )
        
        if file_path:
            self._log(f"DEM carregado: {file_path}")
    
    def delineate_watershed(self):
        """Delimita bacia hidrográfica"""
        if not self.current_project:
            QMessageBox.warning(self, "Aviso", "Crie ou abra um projeto primeiro")
            return
        
        # Abre aba de bacia
        self.tabs.setCurrentWidget(self.watershed_tab)
        
        self._log("Iniciando delimitação de bacia...")
        self.progress_bar.setValue(25)
        
        # Passa controle para a aba
        self.watershed_tab.delineate(
            self.lat_input.value(),
            self.lon_input.value()
        )
    
    def run_analysis(self):
        """Executa análises"""
        if self.watershed_gdf is None:
            QMessageBox.warning(self, "Aviso", "Delimite uma bacia primeiro")
            return
        
        self.tabs.setCurrentWidget(self.analysis_tab)
        self._log("Iniciando análises...")
    
    def generate_report(self):
        """Gera relatório"""
        QMessageBox.information(self, "Relatório", "Recurso em desenvolvimento")
    
    def open_project(self):
        """Abre projeto existente"""
        QMessageBox.information(self, "Abrir Projeto", "Recurso em desenvolvimento")
    
    # ============================================
    # UTILIDADES
    # ============================================
    
    def _log(self, message: str):
        """Adiciona mensagem ao log"""
        current_text = self.info_text.toPlainText()
        self.info_text.setText(f"{current_text}\n{message}")
        # Scroll para o final
        self.info_text.verticalScrollBar().setValue(
            self.info_text.verticalScrollBar().maximum()
        )
    
    def _get_stylesheet(self) -> str:
        """Retorna stylesheet da aplicação"""
        return """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
        }
        
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #bbb;
            border-radius: 4px;
            padding: 8px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
        
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            border: 1px solid #bbb;
            border-radius: 4px;
            padding: 5px;
            background-color: white;
        }
        """
