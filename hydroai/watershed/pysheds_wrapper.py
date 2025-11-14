"""
Wrapper para PySheds - Delimitação de bacias hidrográficas
Integra PySheds ao HydroAI com interface simples
"""
from pathlib import Path
from typing import Tuple, Optional
import logging
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.plot import show
from pysheds.grid import Grid

class PySheksWrapper:
    """
    Interface para PySheds dentro do HydroAI
    Realiza delimitação de bacias a partir de um DEM (Digital Elevation Model)
    """
    
    def __init__(self):
        """Inicializa wrapper do PySheds"""
        self.logger = logging.getLogger(__name__)
        self.grid = None
        self.dem = None
        self.fdir = None
        self.acc = None
        
    def load_dem(self, dem_path: Path) -> Grid:
        """
        Carrega DEM (Digital Elevation Model)
        
        Parameters:
        -----------
        dem_path : Path
            Caminho para arquivo DEM (GeoTIFF)
            Pode ser: SRTM, MERIT, GEBCO, etc
            
        Returns:
        --------
        Grid
            Grid object do PySheds
            
        Exemplo:
        --------
        wrapper = PySheksWrapper()
        grid = wrapper.load_dem(Path('data/srtm_30s.tif'))
        """
        dem_path = Path(dem_path)
        
        if not dem_path.exists():
            raise FileNotFoundError(f"DEM não encontrado: {dem_path}")
        
        self.logger.info(f"Carregando DEM: {dem_path}")
        
        try:
            # Carrega grid a partir do DEM
            self.grid = Grid.from_raster(str(dem_path))
            self.dem = self.grid.read_raster(str(dem_path))
            
            self.logger.info(f"DEM carregado com sucesso")
            self.logger.info(f"  - Dimensões: {self.dem.shape}")
            self.logger.info(f"  - CRS: {self.grid.crs}")
            
            return self.grid
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar DEM: {e}")
            raise
    
    def preprocess_dem(self) -> np.ndarray:
        """
        Pré-processa DEM (preenche depressões, etc)
        Etapa essencial para melhorar delimitação
        
        Returns:
        --------
        ndarray
            DEM processado
            
        Explicação:
        -----------
        1. fill_pits: Remove poços (depressões pequenas)
        2. fill_depressions: Remove depressões maiores
        3. resolve_flats: Resolve áreas planas
        """
        if self.dem is None:
            raise ValueError("Carregue DEM primeiro com load_dem()")
        
        self.logger.info("Pré-processando DEM...")
        
        try:
            # 1. Preenche depressões pequenas
            self.logger.info("  1. Preenchendo poços...")
            dem_filled = self.grid.fill_pits(self.dem)
            
            # 2. Preenche depressões maiores
            self.logger.info("  2. Preenchendo depressões...")
            dem_flooded = self.grid.fill_depressions(dem_filled)
            
            # 3. Resolve áreas planas
            self.logger.info("  3. Resolvendo áreas planas...")
            dem_conditioned = self.grid.resolve_flats(dem_flooded)
            
            self.logger.info("DEM pré-processado com sucesso")
            
            return dem_conditioned
            
        except Exception as e:
            self.logger.error(f"Erro no pré-processamento: {e}")
            raise
    
    def calculate_flow_direction(self, dem_conditioned: np.ndarray) -> np.ndarray:
        """
        Calcula direção de fluxo (Flow Direction)
        
        Parameters:
        -----------
        dem_conditioned : ndarray
            DEM pré-processado
            
        Returns:
        --------
        ndarray
            Matriz de direção de fluxo (D8 routing)
            
        Valores (D8):
        - 1: direita
        - 2: diagonal inferior-direita
        - 4: inferior
        - 8: diagonal inferior-esquerda
        - 16: esquerda
        - 32: diagonal superior-esquerda
        - 64: superior
        - 128: diagonal superior-direita
        """
        self.logger.info("Calculando direção de fluxo...")
        
        try:
            # Routing D8 (8 direções)
            fdir = self.grid.flowdir(dem_conditioned, routing='d8')
            self.fdir = fdir
            
            self.logger.info("Direção de fluxo calculada")
            
            return fdir
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular direção: {e}")
            raise
    
    def calculate_flow_accumulation(self) -> np.ndarray:
        """
        Calcula acumulação de fluxo (Flow Accumulation)
        Número de células que drenam para cada célula
        
        Returns:
        --------
        ndarray
            Matriz de acumulação (quanto maior, mais concentrado o fluxo)
        """
        if self.fdir is None:
            raise ValueError("Calcule direção de fluxo primeiro")
        
        self.logger.info("Calculando acumulação de fluxo...")
        
        try:
            acc = self.grid.accumulation(self.fdir, routing='d8')
            self.acc = acc
            
            self.logger.info("Acumulação calculada")
            self.logger.info(f"  - Valor máximo: {np.nanmax(acc)}")
            self.logger.info(f"  - Valor mínimo: {np.nanmin(acc)}")
            
            return acc
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular acumulação: {e}")
            raise
    
    def delineate_watershed(
        self,
        lat: float,
        lon: float,
        dem_path: Path,
        output_path: Optional[Path] = None
    ) -> gpd.GeoDataFrame:
        """
        Delimita bacia hidrográfica para um ponto de exutório
        
        Parameters:
        -----------
        lat, lon : float
            Coordenadas geográficas (WGS84) do ponto de exutório
        dem_path : Path
            Caminho para arquivo DEM
        output_path : Path, optional
            Diretório para salvar shapefile da bacia
            
        Returns:
        --------
        GeoDataFrame
            Polígono da bacia delimitada
            
        Exemplo:
        --------
        wrapper = PySheksWrapper()
        watershed = wrapper.delineate_watershed(
            lat=-29.409,
            lon=-56.737,
            dem_path=Path('data/srtm.tif'),
            output_path=Path('results/bacia')
        )
        """
        self.logger.info(f"Delimitando bacia para ponto: ({lat}, {lon})")
        
        try:
            # 1. Carrega DEM
            self.load_dem(dem_path)
            
            # 2. Pré-processa
            dem_conditioned = self.preprocess_dem()
            
            # 3. Calcula fluxo
            self.calculate_flow_direction(dem_conditioned)
            self.calculate_flow_accumulation()
            
            # 4. Converte coordenadas geográficas para índices da grid
            self.logger.info("Convertendo coordenadas...")
            col, row = self.grid.nearest_cell(lon, lat)
            self.logger.info(f"  - Índices da grid: col={col}, row={row}")
            
            # 5. Delimita bacia (watershed catchment)
            self.logger.info("Delimitando bacia...")
            catch = self.grid.catchment(
                x=col, 
                y=row,
                fdir=self.fdir,
                routing='d8',
                xytype='index'  # Usando índices
            )
            
            # 6. Extrai polígono
            self.logger.info("Extraindo geometria...")
            self.grid.clip_to(catch)
            clipped_catch = self.grid.view(catch)
            
            # 7. Converte para GeoDataFrame
            shapes = self.grid.polygonize(clipped_catch > 0)
            watershed_gdf = gpd.GeoDataFrame(
                [1],
                geometry=[shapes[0]],
                crs=self.grid.crs,
                columns=['id']
            )
            
            # 8. Calcula estatísticas
            area_m2 = watershed_gdf.geometry.area.sum()
            area_km2 = area_m2 / 1_000_000
            
            self.logger.info(f"✓ Bacia delimitada com sucesso!")
            self.logger.info(f"  - Área: {area_km2:.2f} km²")
            self.logger.info(f"  - CRS: {watershed_gdf.crs}")
            
            # 9. Salva resultado se solicitado
            if output_path:
                output_path = Path(output_path)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Salva como shapefile
                shapefile_path = output_path / 'watershed.shp'
                watershed_gdf.to_file(shapefile_path)
                self.logger.info(f"Shapefile salvo: {shapefile_path}")
                
                # Salva como GeoPackage
                gpkg_path = output_path / 'watershed.gpkg'
                watershed_gdf.to_file(gpkg_path, driver='GPKG')
                self.logger.info(f"GeoPackage salvo: {gpkg_path}")
                
                # Salva como GeoJSON
                geojson_path = output_path / 'watershed.geojson'
                watershed_gdf.to_file(geojson_path, driver='GeoJSON')
                self.logger.info(f"GeoJSON salvo: {geojson_path}")
            
            return watershed_gdf
            
        except Exception as e:
            self.logger.error(f"Erro ao delimitar bacia: {e}")
            raise
    
    def get_watershed_stats(self, watershed_gdf: gpd.GeoDataFrame) -> dict:
        """
        Calcula estatísticas da bacia
        
        Returns:
        --------
        dict
            Dicionário com estatísticas
        """
        area_m2 = watershed_gdf.geometry.area.sum()
        perimeter_m = watershed_gdf.geometry.length.sum()
        
        stats = {
            'area_m2': area_m2,
            'area_ha': area_m2 / 10_000,
            'area_km2': area_m2 / 1_000_000,
            'perimeter_m': perimeter_m,
            'perimeter_km': perimeter_m / 1_000,
            'bounds': watershed_gdf.total_bounds,  # [minx, miny, maxx, maxy]
            'crs': watershed_gdf.crs
        }
        
        return stats
