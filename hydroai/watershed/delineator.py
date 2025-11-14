"""
Interface principal para delimitação de bacias
Usa PySheds internamente
"""
from pathlib import Path
from typing import Optional
import logging
import geopandas as gpd

from hydroai.watershed.pysheds_wrapper import PySheksWrapper

class WatershedDelineator:
    """
    Delimitador de bacias hidrográficas usando PySheds
    
    Workflow:
    1. Carrega DEM
    2. Pré-processa (preenche depressões)
    3. Calcula fluxo
    4. Delimita bacia para ponto de exutório
    """
    
    def __init__(self):
        """Inicializa delimitador"""
        self.logger = logging.getLogger(__name__)
        self.pysheds = PySheksWrapper()
    
    def delineate(
        self,
        lat: float,
        lon: float,
        dem_path: Path,
        output_dir: Optional[Path] = None
    ) -> gpd.GeoDataFrame:
        """
        Delimita bacia hidrográfica
        
        Parameters:
        -----------
        lat, lon : float
            Coordenadas do ponto de exutório (graus decimais)
        dem_path : Path
            Caminho para arquivo DEM (GeoTIFF)
            Recomendações:
            - SRTM 30m: https://earthexplorer.usgs.gov
            - MERIT Hydro: http://hydro.iis.u-tokyo.ac.jp
            - GEBCO: https://www.gebco.net
        output_dir : Path, optional
            Diretório para salvar resultados
            
        Returns:
        --------
        GeoDataFrame
            Geometria da bacia delimitada
        """
        try:
            watershed_gdf = self.pysheds.delineate_watershed(
                lat=lat,
                lon=lon,
                dem_path=dem_path,
                output_path=output_dir
            )
            
            return watershed_gdf
            
        except Exception as e:
            self.logger.error(f"Erro ao delimitar bacia: {e}")
            raise
    
    def get_stats(self, watershed_gdf: gpd.GeoDataFrame) -> dict:
        """
        Retorna estatísticas da bacia
        
        Returns:
        --------
        dict
            Área, perímetro, CRS, bounds
        """
        return self.pysheds.get_watershed_stats(watershed_gdf)
