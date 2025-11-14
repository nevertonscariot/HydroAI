"""
HydroAI - Sistema Inteligente de Análise de Bacias Hidrográficas
Ponto de entrada principal da aplicação
"""
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Adiciona diretório raiz ao path para importar hydroai
sys.path.insert(0, str(Path(__file__).parent))

from hydroai.gui.main_window import MainWindow
from hydroai.utils.logger import setup_logging

def main():
    """
    Função principal - inicializa a aplicação HydroAI
    """
    # Configura logging
    setup_logging()
    
    # Ativa High DPI scaling para melhor resolução em telas modernas
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Cria aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("HydroAI")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("HydroAI Lab")
    app.setOrganizationDomain("hydroai.com")
    
    # Cria e exibe janela principal
    window = MainWindow()
    window.show()
    
    # Executa loop de eventos (aplicação fica aberta)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()