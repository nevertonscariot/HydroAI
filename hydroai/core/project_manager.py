"""
Gerenciador de projetos do HydroAI
Cria, carrega e gerencia projetos de análise de bacias
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

class ProjectManager:
    """
    Gerencia projetos de análise de bacias hidrográficas
    
    Estrutura de diretórios do projeto:
    projeto/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── results/
    ├── reports/
    ├── cache/
    └── project.json
    """
    
    def __init__(self, base_dir: Path):
        """
        Inicializa gerenciador de projetos
        
        Parameters:
        -----------
        base_dir : Path
            Diretório base para armazenar projetos
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"ProjectManager inicializado em: {self.base_dir}")
        
    def create_project(
        self, 
        name: str, 
        lat: float, 
        lon: float,
        description: str = ""
    ) -> Path:
        """
        Cria novo projeto
        
        Parameters:
        -----------
        name : str
            Nome do projeto
        lat, lon : float
            Coordenadas do ponto de exutório
        description : str, optional
            Descrição do projeto
            
        Returns:
        --------
        Path
            Caminho do projeto criado
            
        Exemplo:
        --------
        pm = ProjectManager(Path('data/projects'))
        project_path = pm.create_project(
            'Bacia do Rio Pardo',
            lat=-29.409,
            lon=-56.737
        )
        """
        # Nome único com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = self._sanitize_name(name)
        project_name = f"{safe_name}_{timestamp}"
        project_path = self.base_dir / project_name
        
        self.logger.info(f"Criando projeto: {name}")
        
        # Cria estrutura de diretórios
        (project_path / 'data' / 'raw').mkdir(parents=True, exist_ok=True)
        self.logger.info(f"  - Criado: data/raw/")
        
        (project_path / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
        self.logger.info(f"  - Criado: data/processed/")
        
        (project_path / 'results').mkdir(parents=True, exist_ok=True)
        self.logger.info(f"  - Criado: results/")
        
        (project_path / 'reports').mkdir(parents=True, exist_ok=True)
        self.logger.info(f"  - Criado: reports/")
        
        (project_path / 'cache').mkdir(parents=True, exist_ok=True)
        self.logger.info(f"  - Criado: cache/")
        
        # Metadados do projeto
        metadata = {
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat(),
            'outlet': {
                'lat': lat,
                'lon': lon
            },
            'watershed': None,
            'analyzers_run': [],
            'status': 'created',
            'version': '0.1.0'
        }
        
        # Salva metadados
        metadata_file = project_path / 'project.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✓ Projeto criado em: {project_path}")
        
        return project_path
    
    def load_project(self, project_path: Path) -> Dict:
        """
        Carrega projeto existente
        
        Parameters:
        -----------
        project_path : Path
            Caminho do projeto
            
        Returns:
        --------
        dict
            Metadados do projeto
            
        Exemplo:
        --------
        metadata = pm.load_project(Path('data/projects/meu_projeto_20251114_144530'))
        """
        metadata_file = Path(project_path) / 'project.json'
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"Projeto não encontrado: {project_path}")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        self.logger.info(f"✓ Projeto carregado: {metadata['name']}")
        
        return metadata
    
    def update_project(self, project_path: Path, updates: Dict):
        """
        Atualiza metadados do projeto
        
        Parameters:
        -----------
        project_path : Path
            Caminho do projeto
        updates : dict
            Atualizações a aplicar
            
        Exemplo:
        --------
        pm.update_project(
            project_path,
            {'watershed': geom, 'status': 'watershed_delineated'}
        )
        """
        metadata = self.load_project(project_path)
        metadata.update(updates)
        metadata['last_modified'] = datetime.now().isoformat()
        
        metadata_file = Path(project_path) / 'project.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✓ Projeto atualizado")
    
    def list_projects(self) -> List[Dict]:
        """
        Lista todos os projetos
        
        Returns:
        --------
        list
            Lista de metadados dos projetos (ordenada por data de modificação)
            
        Exemplo:
        --------
        projetos = pm.list_projects()
        for p in projetos:
            print(f"{p['name']} - {p['last_modified']}")
        """
        projects = []
        
        for project_dir in self.base_dir.iterdir():
            if project_dir.is_dir():
                metadata_file = project_dir / 'project.json'
                if metadata_file.exists():
                    try:
                        metadata = self.load_project(project_dir)
                        metadata['path'] = str(project_dir)
                        projects.append(metadata)
                    except Exception as e:
                        self.logger.warning(f"Erro ao carregar {project_dir}: {e}")
        
        # Ordena por data de modificação (mais recente primeiro)
        projects.sort(key=lambda x: x['last_modified'], reverse=True)
        
        self.logger.info(f"Total de projetos encontrados: {len(projects)}")
        
        return projects
    
    def delete_project(self, project_path: Path):
        """
        Remove projeto
        
        Parameters:
        -----------
        project_path : Path
            Caminho do projeto
            
        Exemplo:
        --------
        pm.delete_project(Path('data/projects/meu_projeto_20251114_144530'))
        """
        import shutil
        
        project_path = Path(project_path)
        
        if project_path.exists():
            shutil.rmtree(project_path)
            self.logger.info(f"✓ Projeto removido: {project_path}")
        else:
            raise FileNotFoundError(f"Projeto não encontrado: {project_path}")
    
    def get_project_size(self, project_path: Path) -> float:
        """
        Calcula tamanho do projeto em MB
        
        Parameters:
        -----------
        project_path : Path
            Caminho do projeto
            
        Returns:
        --------
        float
            Tamanho em MB
        """
        project_path = Path(project_path)
        
        total_size = 0
        for path in project_path.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        
        size_mb = total_size / (1024 * 1024)
        return size_mb
    
    def _sanitize_name(self, name: str) -> str:
        """
        Remove caracteres inválidos do nome do projeto
        
        Parameters:
        -----------
        name : str
            Nome original
            
        Returns:
        --------
        str
            Nome sanitizado (seguro para usar como nome de diretório)
        """
        import re
        
        # Remove caracteres especiais, mantém apenas alfanuméricos, _ e -
        safe_name = re.sub(r'[^\w\-]', '_', name)
        
        # Limita tamanho
        return safe_name[:50]
