"""
Aba para executar análises
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class AnalysisTab(QWidget):
    """
    Aba com análises disponíveis
    """
    
    def __init__(self, parent):
        super().__init__()
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(QLabel("📊 Análises Disponíveis:"))
        
        # Botões de análise
        analyses = [
            "🌍 LULC (Mudança de Uso da Terra)",
            "⛰️ Topografia (DEM)",
            "🌱 Solos",
            "💧 Hidrologia",
            "☁️ Clima"
        ]
        
        for analysis in analyses:
            btn = QPushButton(analysis)
            btn.clicked.connect(lambda checked, a=analysis: self._run_analysis(a))
            layout.addWidget(btn)
        
        layout.addStretch()
    
    def _run_analysis(self, analysis_name):
        print(f"Executando: {analysis_name}")
