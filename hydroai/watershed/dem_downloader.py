"""
Download de DEM com suporte a OpenTopography API
Integrado ao HydroAI
"""
from pathlib import Path
from typing import Optional
import logging
import requests
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

class DEMDownloader:
    """
    Download de DEM com suporte a múltiplas fontes
    Prioridade: OpenTopography > OpenElevation > Local
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa downloader
        
        Parameters:
        -----------
        api_key : str, optional
            Chave da API OpenTopography
            Se não fornecida, tenta carregar de .env ou usa modo público
        """
        self.logger = logging.getLogger(__name__)
        
        # Tenta obter chave de API
        self.api_key = api_key or os.getenv('OPENTOPOGRAPHY_API_KEY', None)
        
        if self.api_key:
            self.logger.info("✓ Chave OpenTopography detectada")
        else:
            self.logger.warning("⚠ Chave OpenTopography não encontrada")
            self.logger.warning("  Para ativar, obtenha em: https://portal.opentopography.org/myot")
        
        self.session = requests.Session()
        self.session.timeout = 60
    
    def download_dem(
        self,
        lat: float,
        lon: float,
        output_path: Path,
        buffer_km: float = 25,
        dataset: str = 'SRTMGL1'
    ) -> Path:
        """
        Baixa DEM com suporte a OpenTopography
        
        Parameters:
        -----------
        lat, lon : float
            Coordenadas do centro
        output_path : Path
            Onde salvar
        buffer_km : float
            Raio em km (padrão: 25km = ~50km x 50km)
        dataset : str
            Dataset a usar:
            - 'SRTMGL1': SRTM 30m (padrão)
            - 'SRTMGL3': SRTM 90m
            - 'ASTER': ASTER GDEM 30m
            - 'AW3D30': ALOS World 3D 30m
            
        Returns:
        --------
        Path
            Caminho do arquivo baixado
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Baixando DEM...")
        self.logger.info(f"  Coordenadas: ({lat}, {lon})")
        self.logger.info(f"  Dataset: {dataset}")
        self.logger.info(f"  Buffer: {buffer_km}km")
        
        # Tenta OpenTopography primeiro (se tem API key)
        if self.api_key:
            try:
                return self._download_from_opentopography(
                    lat, lon, output_path, buffer_km, dataset
                )
            except Exception as e:
                self.logger.warning(f"OpenTopography falhou: {e}")
                self.logger.info("Tentando alternativa...")
        
        # Fallback: OpenElevation
        try:
            return self._download_from_openelevation(lat, lon, output_path)
        except Exception as e:
            self.logger.error(f"Todas as fontes falharam: {e}")
            raise
    
    def _download_from_opentopography(
        self,
        lat: float,
        lon: float,
        output_path: Path,
        buffer_km: float,
        dataset: str
    ) -> Path:
        """
        Download via API OpenTopography
        MELHOR QUALIDADE - Usa quando tem API key
        """
        self.logger.info("📡 Usando OpenTopography API...")
        
        # Converte buffer de km para graus (aproximadamente)
        # 1 grau ≈ 111 km na equador
        buffer_deg = buffer_km / 111.0
        
        # Define bounds (oeste, sul, leste, norte)
        bounds = {
            'west': lon - buffer_deg,
            'south': lat - buffer_deg,
            'east': lon + buffer_deg,
            'north': lat + buffer_deg
        }
        
        self.logger.info(f"  Bounds: W={bounds['west']:.3f}, S={bounds['south']:.3f}, "
                        f"E={bounds['east']:.3f}, N={bounds['north']:.3f}")
        
        # URL da API
        base_url = "https://portal.opentopography.org/API/globaldem"
        
        params = {
            'demtype': dataset,
            'south': bounds['south'],
            'north': bounds['north'],
            'west': bounds['west'],
            'east': bounds['east'],
            'outputFormat': 'GTiff',
            'API_Key': self.api_key
        }
        
        self.logger.info(f"  Enviando requisição para OpenTopography...")
        
        try:
            response = self.session.get(base_url, params=params)
            response.raise_for_status()
            
            # Salva arquivo
            output_file = output_path / f"dem_{dataset}_{lat:.2f}_{lon:.2f}.tif"
            
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            
            self.logger.info(f"✓ Download OpenTopography concluído!")
            self.logger.info(f"  Arquivo: {output_file.name}")
            self.logger.info(f"  Tamanho: {file_size_mb:.2f} MB")
            
            return output_file
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erro HTTP: {response.status_code}")
            self.logger.error(f"Mensagem: {response.text}")
            raise
    
    def _download_from_openelevation(
        self,
        lat: float,
        lon: float,
        output_path: Path
    ) -> Path:
        """
        Fallback: Download via OpenElevation API
        Gratuito, mas mais lento
        """
        self.logger.info("📡 Usando OpenElevation API (gratuito)...")
        
        try:
            import numpy as np
            import rasterio
            from rasterio.transform import Affine
            
            # Define grid
            grid_size = 0.5
            lat_min = lat - grid_size / 2
            lat_max = lat + grid_size / 2
            lon_min = lon - grid_size / 2
            lon_max = lon + grid_size / 2
            
            resolution = 0.01  # ~1km
            
            lats = np.arange(lat_min, lat_max, resolution)
            lons = np.arange(lon_min, lon_max, resolution)
            
            heights_array = np.zeros((len(lats), len(lons)))
            
            self.logger.info(f"  Criando grid: {len(lats)} x {len(lons)} pontos")
            self.logger.info(f"  Baixando altitudes...")
            
            total = len(lats) * len(lons)
            count = 0
            
            for i, lat_i in enumerate(lats):
                for j, lon_j in enumerate(lons):
                    url = "https://api.open-elevation.com/api/v1/lookup"
                    params = {'locations': f'{lat_i},{lon_j}'}
                    
                    response = self.session.get(url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    if data['results']:
                        heights_array[i, j] = data['results'][0]['elevation']
                    
                    count += 1
                    if count % 50 == 0:
                        self.logger.info(f"    {count}/{total} pontos...")
            
            self.logger.info(f"  Salvando como GeoTIFF...")
            
            transform = Affine.translation(lon_min, lat_max) * Affine.scale(
                (lon_max - lon_min) / len(lons),
                -(lat_max - lat_min) / len(lats)
            )
            
            output_file = output_path / f"dem_openelevation_{lat:.2f}_{lon:.2f}.tif"
            
            with rasterio.open(
                output_file,
                'w',
                driver='GTiff',
                height=heights_array.shape[0],
                width=heights_array.shape[1],
                count=1,
                dtype=rasterio.float32,
                crs='EPSG:4326',
                transform=transform,
                compress='deflate'
            ) as dst:
                dst.write(heights_array.astype(rasterio.float32), 1)
            
            self.logger.info(f"✓ Download OpenElevation concluído!")
            self.logger.info(f"  Arquivo: {output_file.name}")
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"Erro OpenElevation: {e}")
            raise
    
    def get_datasets(self) -> dict:
        """Retorna datasets disponíveis no OpenTopography"""
        return {
            'SRTMGL1': {
                'name': 'SRTM 30m Global',
                'resolution': 30,
                'coverage': 'Global (-60° a +60°)',
                'year': 2000,
                'recommended': True
            },
            'SRTMGL3': {
                'name': 'SRTM 90m Global',
                'resolution': 90,
                'coverage': 'Global (-60° a +60°)',
                'year': 2000
            },
            'ASTER': {
                'name': 'ASTER GDEM v3',
                'resolution': 30,
                'coverage': 'Global (-83° a +83°)',
                'year': 2019
            },
            'AW3D30': {
                'name': 'ALOS World 3D 30m',
                'resolution': 30,
                'coverage': 'Global',
                'year': 2021
            }
        }
