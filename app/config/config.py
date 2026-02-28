"""
Configuration Loader
Carrega configurações do arquivo YAML
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """
    Carrega e gerencia configurações do sistema
    """
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa e carrega configurações"""
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: str = None):
        """
        Carrega configurações do YAML
        
        Args:
            config_path: Caminho customizado (opcional)
        """
        if config_path is None:
            # Procura arquivo padrão
            current_dir = Path(__file__).parent
            config_path = current_dir / 'thresholds.yaml'
        
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração
        
        Args:
            key: Chave no formato 'section.subsection.key'
            default: Valor padrão se não encontrado
        
        Returns:
            Valor da configuração
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_rule_thresholds(self) -> Dict:
        """Retorna thresholds do rule engine"""
        return self.get('rule_engine', {})
    
    def get_model_config(self, model_name: str = None) -> Dict:
        """
        Retorna configuração do modelo
        
        Args:
            model_name: 'qwen' ou 'phi' (usa default se None)
        """
        if model_name is None:
            model_name = self.get('models.default', 'qwen')
        
        return self.get(f'models.{model_name}', {})
    
    def get_all(self) -> Dict:
        """Retorna todas as configurações"""
        return self._config if self._config else {}


# Instância global
config = Config()
