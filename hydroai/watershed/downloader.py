"""
Download automático de DEM (Digital Elevation Model)
Obtém dados SRTM a partir de coordenadas lat/lon via Google Earth Engine
"""
from pathlib import Path
from typing import Tuple, Optional
import logging
import ee

class DEMDownloader:
    """
    Baixa imagens DEM automaticamente
    
    Suporta:
    - SRTM 30m (via USGS)
    - SRTM 90m (via CGIAR)
    - MERIT Hydro
    - Copernicus DEM
    
    Exemplo de uso:
    ---------------
    downloader = DEMDownloader()
    dem_path = downloader.download_dem(
        lat=-29.409,
        lon=-56.737,
        buffer_km=50,
        output_dir=Path('data/dem'),
        dem_type='SRTM30'
    )
    """
    
    def __init__(self):
        """Inicializa downloader"""
        self.logger = logging.getLogger(__name__)
        
        try:
            ee.Initialize()
            self.logger.info("Google Earth Engine inicializado")
        except Exception as e:
            self.logger.warning(f"GEE não disponível: {e}. Use download_dem_usgs().")
    
    def download_dem(
        self,
        lat: float,
        lon: float,
        buffer_km: float = 50,
        output_dir: Path = None,
        dem_type: str = 'SRTM30',
        scale: int = 30
    ) -> Path:
        """
        Baixa DEM para uma região especificada
        
        Parameters:
        -----------
        lat, lon : float
            Coordenadas do ponto central (graus decimais)
        buffer_km : float
            Raio da área a baixar em km
            Exemplo: 50km = área 100km x 100km
        output_dir : Path
            Diretório para salvar o DEM
        dem_type : str
            Tipo de DEM:
            - 'SRTM30': SRTM 30m (recomendado)
            - 'SRTM90': SRTM 90m (mais rápido, menos detalhe)
            - 'MERIT': MERIT Hydro (melhor para hidrologia)
            - 'COPERNICUS': Copernicus DEM 30m
        scale : int
            Escala em metros (30, 90, etc)
            
        Returns:
        --------
        Path
            Caminho do arquivo DEM baixado
        """
        if output_dir is None:
            output_dir = Path('data/dem')
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Baixando DEM {dem_type}...")
        self.logger.info(f"  Coordenadas: ({lat}, {lon})")
        self.logger.info(f"  Buffer: {buffer_km}km")
        self.logger.info(f"  Tipo: {dem_type}")
        
        try:
            # Cria geometria (ponto + buffer)
            point = ee.Geometry.Point([lon, lat])
            roi = point.buffer(buffer_km * 1000)  # Converte km para metros
            
            # Seleciona dataset conforme tipo
            if dem_type == 'SRTM30':
                dem_image = ee.Image('USGS/SRTMGL1_Ellip/SRTMGL1_Ellip_srtm')
                
            elif dem_type == 'SRTM90':
                dem_image = ee.Image('CGIAR/SRTM90_V4')
                
            elif dem_type == 'MERIT':
                dem_image = ee.Image('MERIT/Hydro/v1_0_1').select('elv')
                
            elif dem_type == 'COPERNICUS':
                dem_image = ee.Image('COPERNICUS/DEM/GLO30')
                
            else:
                raise ValueError(f"Tipo DEM desconhecido: {dem_type}")
            
            # Recorta para área de interesse
            dem_clipped = dem_image.clip(roi)
            
            # Prepara download
            filename = f"dem_{dem_type}_{lat:.2f}_{lon:.2f}.tif"
            output_path = output_dir / filename
            
            self.logger.info(f"Iniciando export para Google Drive...")
            self.logger.info(f"  Arquivo: {filename}")
            self.logger.info(f"  Resolução: {scale}m")
            
            # Cria tarefa de export
            task = ee.batch.Export.image.toDrive(
                image=dem_clipped,
                description=f'HydroAI_DEM_{dem_type}',
                scale=scale,
                region=roi,
                maxPixels=1e13,
                folder='HydroAI_Downloads',
                fileFormat='GeoTIFF'
            )
            
            # Inicia tarefa
            task.start()
            
            self.logger.info("✓ Tarefa de export iniciada!")
            self.logger.info("\n" + "="*60)
            self.logger.info("INSTRUÇÕES:")
            self.logger.info("="*60)
            self.logger.info("1. Acesse: https://code.earthengine.google.com/tasks")
            self.logger.info("2. Verifique o status da tarefa")
            self.logger.info("3. Clique em 'RUN' para iniciar o download")
            self.logger.info("4. Aguarde (pode levar minutos)")
            self.logger.info("5. Arquivo aparecerá em: Google Drive/HydroAI_Downloads/")
            self.logger.info("6. Baixe e salve em: " + str(output_dir))
            self.logger.info("="*60)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erro ao fazer download via GEE: {e}")
            self.logger.warning("Tente usar download_dem_usgs() como alternativa")
            raise
    
    def download_dem_usgs(
        self,
        lat: float,
        lon: float,
        output_dir: Path = None
    ) -> Path:
        """
        Download via USGS OpenTopography (alternativa sem GEE)
        Requer: pip install requests
        
        Parameters:
        -----------
        lat, lon : float
            Coordenadas
        output_dir : Path
            Diretório de saída
            
        Returns:
        --------
        Path
            Caminho do arquivo baixado
        """
        if output_dir is None:
            output_dir = Path('data/dem')
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Baixando SRTM via USGS OpenTopography...")
        
        try:
            import requests
            from io import BytesIO
            import rasterio
            from rasterio.io import MemoryFile
            
            # URL da API USGS OpenTopography
            # Retorna tile SRTM 30m
            url = f"https://cloud.sdsc.edu/v1:AUTH_object_store/Raster/SRTM_GL30/SRTM_GL30_srtm/{self._get_srtm_tile(lat, lon)}.tar.gz"
            
            self.logger.info(f"URL: {url}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            filename = f"srtm_{lat:.2f}_{lon:.2f}.tif"
            output_path = output_dir / filename
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"✓ DEM baixado: {output_path}")
            
            return output_path
            
        except ImportError:
            self.logger.error("requests não instalado. Execute: pip install requests")
            raise
        except Exception as e:
            self.logger.error(f"Erro: {e}")
            raise
    
    def download_from_google_cloud(
        self,
        lat: float,
        lon: float,
        output_dir: Path = None,
        dem_type: str = 'SRTM30'
    ) -> Path:
        """
        Download direto de Google Cloud Storage (mais rápido)
        Usa rasterio virtual file system
        
        Parameters:
        -----------
        lat, lon : float
            Coordenadas
        output_dir : Path
            Diretório de saída
        dem_type : str
            Tipo de DEM disponível no GCS
            
        Returns:
        --------
        Path
            Caminho do arquivo baixado
        """
        if output_dir is None:
            output_dir = Path('data/dem')
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Baixando {dem_type} de Google Cloud Storage...")
        
        try:
            import rasterio
            from rasterio.vrt import WarpedVRT
            from rasterio.io import MemoryFile
            import numpy as np
            
            # URLs dos arquivos no GCS
            gcs_urls = {
                'SRTM30': '/vsicurl_streaming/https://storage.googleapis.com/dem_tiles/srtm30m/{z}/{x}/{y}.tif',
                'GEBCO': '/vsicurl_streaming/https://storage.googleapis.com/dem_tiles/gebco/{z}/{x}/{y}.tif',
            }
            
            # Calcula tile
            tile_x, tile_y = self._lat_lon_to_tile(lat, lon, zoom=7)
            
            url = gcs_urls[dem_type].format(z=7, x=tile_x, y=tile_y)
            
            self.logger.info(f"URL: {url}")
            
            # Lê diretamente do GCS
            with rasterio.open(url) as src:
                data = src.read()
                profile = src.profile
                
                filename = f"{dem_type}_{lat:.2f}_{lon:.2f}.tif"
                output_path = output_dir / filename
                
                # Salva localmente
                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(data)
            
            self.logger.info(f"✓ DEM baixado: {output_path}")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erro: {e}")
            raise
    
    def _get_srtm_tile(self, lat: float, lon: float) -> str:
        """
        Obtém nome do tile SRTM para coordenadas
        
        SRTM é organizado em tiles de 5°x5°
        Nomes: srtm_XX_YY onde XX=longitude+180, YY=latitude+60
        """
        x = int((lon + 180) / 5)
        y = int((lat + 60) / 5)
        
        return f"srtm_{x:02d}_{y:02d}"
    
    def _lat_lon_to_tile(
        self,
        lat: float,
        lon: float,
        zoom: int
    ) -> Tuple[int, int]:
        """Converte lat/lon para tile x,y (Web Mercator)"""
        import math
        
        n = 2.0 ** zoom
        x = int((lon + 180.0) / 360.0 * n)
        
        lat_rad = math.radians(lat)
        y = int((1.0 - math.log(
            math.tan(lat_rad) + 1.0 / math.cos(lat_rad)
        ) / math.pi) / 2.0 * n)
        
        return x, y
    
    def get_available_dem_types(self) -> dict:
        """Retorna tipos de DEM disponíveis"""
        return {
            'SRTM30': {
                'description': 'SRTM 30m (NASA/USGS)',
                'resolution': 30,
                'coverage': 'Global',
                'year': 2000,
                'recommended': True
            },
            'SRTM90': {
                'description': 'SRTM 90m (CGIAR)',
                'resolution': 90,
                'coverage': 'Global',
                'year': 2000,
                'fast': True
            },
            'MERIT': {
                'description': 'MERIT Hydro (optimizado para hidrologia)',
                'resolution': 90,
                'coverage': 'Global',
                'year': 2015,
                'recommended_for_hydrology': True
            },
            'COPERNICUS': {
                'description': 'Copernicus DEM 30m (ESA)',
                'resolution': 30,
                'coverage': 'Global',
                'year': 2021,
            }
        }
