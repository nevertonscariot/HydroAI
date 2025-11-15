"""
Wrapper para PySheds - Delimitação de bacias hidrográficas
Integra PySheds ao HydroAI com interface simples
"""
from pathlib import Path
from typing import Tuple, Optional
import logging
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
import rasterio
from rasterio.transform import Affine
from pysheds.grid import Grid
import tempfile
import os

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
        self.dem_path = None
        
    def load_dem(self, dem_path: Path) -> Grid:
        """
        Carrega DEM (Digital Elevation Model)
        
        Parameters:
        -----------
        dem_path : Path
            Caminho para arquivo DEM (GeoTIFF)
            
        Returns:
        --------
        Grid
            Grid object do PySheds
        """
        dem_path = Path(dem_path)
        
        if not dem_path.exists():
            raise FileNotFoundError(f"DEM não encontrado: {dem_path}")
        
        self.logger.info(f"Carregando DEM: {dem_path}")
        self.dem_path = dem_path
        
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
        
        Returns:
        --------
        ndarray
            DEM processado
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
        """
        self.logger.info("Calculando direção de fluxo...")
        
        try:
            # Routing D8 (8 direções)
            fdir = self.grid.flowdir(dem_conditioned, routing='d8')
            # Converte para numpy array
            self.fdir = np.asarray(fdir)
            
            self.logger.info("Direção de fluxo calculada")
            
            return self.fdir
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular direção: {e}")
            raise
    
    def calculate_flow_accumulation(self) -> np.ndarray:
        """
        Calcula acumulação de fluxo (Flow Accumulation)
        
        Returns:
        --------
        ndarray
            Matriz de acumulação
        """
        if self.fdir is None:
            raise ValueError("Calcule direção de fluxo primeiro")
        
        self.logger.info("Calculando acumulação de fluxo...")
        
        try:
            acc = self.grid.accumulation(self.fdir, routing='d8')
            # Converte para numpy array
            self.acc = np.asarray(acc)
            
            self.logger.info("Acumulação calculada")
            self.logger.info(f"  - Valor máximo: {np.nanmax(self.acc)}")
            self.logger.info(f"  - Valor mínimo: {np.nanmin(self.acc)}")
            
            return self.acc
            
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
            Diretório para salvar shapefiles
            
        Returns:
        --------
        GeoDataFrame
            Polígono da bacia delimitada
        """
        self.logger.info(f"Delimitando bacia para ponto: ({lat}, {lon})")
        
        temp_file = None
        
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
                xytype='index'
            )
            
            # 6. Salva catch em arquivo temporário PRIMEIRO
            self.logger.info("Salvando resultado intermediário...")
            
            # Cria arquivo temporário
            fd, temp_file = tempfile.mkstemp(suffix='.tif')
            os.close(fd)
            
            # Converte catch para numpy array
            catch_array = np.asarray(catch, dtype=np.float32)
            
            
            # Obtém metadados do DEM original
            with rasterio.open(str(dem_path)) as src:
                transform = src.transform
                crs = src.crs
                profile = src.profile
            
            # Atualiza profile para o resultado
            profile.update({
                'dtype': rasterio.float32,
                'count': 1,
                'compress': 'deflate',
                'nodata': None  # Remove nodata value
            })

            
            # Salva array temporário
            with rasterio.open(temp_file, 'w', **profile) as dst:
                dst.write(catch_array, 1)
            
            self.logger.info(f"  - Arquivo temporário: {temp_file}")
            
            # 7. Lê arquivo temporário e vectoriza
            self.logger.info("Extraindo geometria...")
            
            import rasterio.features
            
            with rasterio.open(temp_file) as src:
                catch_data = src.read(1)
                transform = src.transform
                crs = src.crs
            
            # Cria máscara (apenas valores > 0)
            catch_mask = (catch_data > 0).astype(np.uint8)
            
            self.logger.info(f"  - Máscara criada: {catch_mask.shape}")
            self.logger.info(f"  - Pixels da bacia: {np.sum(catch_mask)}")
            
            # Vectoriza
            shapes_list = list(rasterio.features.shapes(
                catch_mask,
                transform=transform
            ))
            
            if not shapes_list:
                raise ValueError("Nenhuma geometria foi criada")
            
            self.logger.info(f"  - {len(shapes_list)} shapes encontrados")
            
            # 8. Filtra apenas polígonos válidos
            valid_shapes = []
            for geom, value in shapes_list:
                if value == 1:
                    try:
                        geom_obj = shape(geom)
                        if geom_obj.is_valid and geom_obj.area > 0:
                            valid_shapes.append(geom_obj)
                    except Exception as e:
                        self.logger.warning(f"  - Shape inválido: {e}")
            
            if not valid_shapes:
                raise ValueError("Nenhum polígono válido encontrado")
            
            self.logger.info(f"  - {len(valid_shapes)} polígonos válidos")
            
            # 9. Combina polígonos
            from shapely.ops import unary_union
            if len(valid_shapes) == 1:
                final_geom = valid_shapes[0]
            else:
                final_geom = unary_union(valid_shapes)
            
            # 10. Cria GeoDataFrame
            watershed_gdf = gpd.GeoDataFrame(
                [{'id': 1}],
                geometry=[final_geom],
                crs=crs
            )
            
            # 11. Calcula estatísticas
            area_m2 = watershed_gdf.geometry.area.sum()
            area_km2 = area_m2 / 1_000_000
            
            self.logger.info("=" * 70)
            self.logger.info(f"✓ BACIA DELIMITADA COM SUCESSO!")
            self.logger.info("=" * 70)
            self.logger.info(f"  Área: {area_km2:.2f} km²")
            self.logger.info(f"  Área: {area_m2/10000:.2f} ha")
            self.logger.info(f"  CRS: {crs}")
            self.logger.info("=" * 70)
            
            # 12. Salva resultado se solicitado
            if output_path:
                output_path = Path(output_path)
                output_path.mkdir(parents=True, exist_ok=True)
                
                try:
                    shapefile_path = output_path / 'watershed.shp'
                    watershed_gdf.to_file(shapefile_path)
                    self.logger.info(f"✓ Shapefile salvo: {shapefile_path}")
                except Exception as e:
                    self.logger.warning(f"Erro ao salvar shapefile: {e}")
                
                try:
                    gpkg_path = output_path / 'watershed.gpkg'
                    watershed_gdf.to_file(gpkg_path, driver='GPKG')
                    self.logger.info(f"✓ GeoPackage salvo: {gpkg_path}")
                except Exception as e:
                    self.logger.warning(f"Erro ao salvar GeoPackage: {e}")
                
                try:
                    geojson_path = output_path / 'watershed.geojson'
                    watershed_gdf.to_file(geojson_path, driver='GeoJSON')
                    self.logger.info(f"✓ GeoJSON salvo: {geojson_path}")
                except Exception as e:
                    self.logger.warning(f"Erro ao salvar GeoJSON: {e}")
            
            return watershed_gdf
            
        except Exception as e:
            self.logger.error("=" * 70)
            self.logger.error(f"❌ ERRO AO DELIMITAR BACIA")
            self.logger.error("=" * 70)
            self.logger.error(f"Erro: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.logger.error("=" * 70)
            raise
        
        finally:
            # Limpa arquivo temporário
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    self.logger.info("Arquivo temporário removido")
                except:
                    pass
    
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
            'bounds': watershed_gdf.total_bounds,
            'crs': watershed_gdf.crs
        }
        
        return stats
