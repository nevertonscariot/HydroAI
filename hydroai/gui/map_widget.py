"""
Widget de mapa interativo com Folium
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
import folium
from folium.plugins import MousePosition, MeasureControl
from io import BytesIO
import base64

class MapWidget(QWidget):
    """
    Mapa interativo usando Folium
    """
    
    def __init__(self, center=[-29.409, -56.737], zoom=10):
        super().__init__()
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Cria mapa
        self.m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        # Adiciona plugins
        MousePosition().add_to(self.m)
        MeasureControl(primary_length_unit='kilometers').add_to(self.m)
        
        # WebView
        self.view = QWebEngineView()
        self.layout.addWidget(self.view)
        
        # Renderiza mapa
        self._render_map()
    
    def _render_map(self):
        """Renderiza mapa no navegador"""
        # Converte para HTML
        data = BytesIO()
        self.m.save(data, close_file=False)
        
        # Encode para Base64
        html_string = data.getvalue().decode('utf-8')
        
        self.view.setHtml(html_string)
    
    def set_center(self, lat, lon):
        """Centraliza mapa em coordenadas"""
        self.m.location = [lat, lon]
        self._render_map()
    
    def add_point(self, lat, lon, popup="Ponto"):
        """Adiciona ponto ao mapa"""
        folium.Marker([lat, lon], popup=popup).add_to(self.m)
        self._render_map()
    
    def add_polygon(self, geojson, name="Polígono"):
        """Adiciona polígono ao mapa"""
        folium.GeoJson(geojson, name=name).add_to(self.m)
        self._render_map()
