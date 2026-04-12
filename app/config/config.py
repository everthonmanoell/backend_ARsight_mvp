"""
Configuration Loader
Carrega configurações do arquivo YAML
"""

import yaml
import os
import platform
from pathlib import Path
from typing import Dict, Any
import torch

# classe de configurações, responsável por carregar e fornecer acesso às configurações do sistema, como thresholds do rule engine e parâmetros dos modelos
class Config:
    """
    Carrega e gerencia configurações do sistema
    """
    
    _instance = None # Singleton instance
    _config = None   # Dicionário com as configurações carregadas
    
    # método que garante que apenas uma instância de Config seja criada (Singleton pattern)
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método de inicialização que chama o carregamento do arquivo YAML
    def __init__(self):
        if self._config is None:
            self.load_config()

    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método que carrega o arquivo YAML e armazena as configurações em um dicionário
    def load_config(self, config_path: str = None):
        """
        Carrega configurações do YAML
        
        Args:
            config_path: Caminho customizado (opcional)
        """
        # usando caminho customizado se fornecido, senão procura arquivo padrão
        if config_path is None:
            # Permite sobrescrever o arquivo de config via variável de ambiente
            # Ex: export AR_CONFIG_FILE=/path/to/thresholds.yaml
            env_config = os.environ.get('AR_CONFIG_FILE')
            if env_config:
                config_path = Path(env_config)
            else:
                # Usa thresholds.yaml padrão (edite conforme o ambiente: Jetson, Desktop, etc)
                current_dir = Path(__file__).parent
                config_path = current_dir / 'thresholds.yaml'
        
        with open(config_path, 'r', encoding='utf-8') as f:  # Carrega o arquivo YAML
            self._config = yaml.safe_load(f)               # Armazena as configurações em um dicionário

    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para acessar valores de configuração usando chaves hierárquicas (ex: 'models.default')
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração
        
        Args:
            key: Chave no formato 'section.subsection.key'
            default: Valor padrão se não encontrado
        
        Returns:
            Valor da configuração
        """
        # Divide a chave hierárquica em partes
        keys = key.split('.') 

        # Começa com o dicionário completo
        value = self._config  
        
        # Navega pelo dicionário usando as partes da chave
        for k in keys:
            # Verifica se a chave existe no nível atual do dicionário
            if isinstance(value, dict) and k in value: 
                # Move para o próximo nível do dicionário
                value = value[k]    
            # Se a chave não for encontrada, retorna o valor padrão                   
            else: 
                return default
            
        # Retorna o valor encontrado após navegar por toda a hierarquia
        return value 
    
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para acessar thresholds do rule engine
    def get_rule_thresholds(self) -> Dict:
        return self.get('rule_engine', {})
    
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------    
    # método para acessar configuração específica do modelo (qwen ou phi)
    def get_model_config(self, model_name: str = None) -> Dict:

        # verifica se o nome do modelo foi fornecido, se não, usa o modelo padrão definido em thresholds.yaml
        if model_name is None:
            model_name = self.get('models.default', 'qwen') 
        
        # Retorna a configuração específica do modelo solicitado
        return self.get(f'models.{model_name}', {})  
    
    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # método para retornar todas as configurações (útil para debug)
    def get_all(self) -> Dict:
        return self._config if self._config else {}

    #------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# Instância global das configurações, pode ser importada e usada em todo o sistema
config = Config()

# ================================================================================================
# 🎯 FP16 / Precision Configuration para Jetson Orin
# ================================================================================================

# Detecta se está em Jetson Orin (aarch64)
PLATFORM = "jetson" if platform.machine() == "aarch64" else "desktop"

# Lê variável de ambiente (padrão: fp16 em Jetson, fp32 em Desktop)
PRECISION = os.getenv("MODEL_PRECISION", "fp16" if PLATFORM == "jetson" else "fp32").lower()

# Define torch dtype baseado na precisão
TORCH_DTYPE = torch.float16 if PRECISION == "fp16" else torch.float32

# Device (GPU ou CPU)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Log para debug
print(f"🎯 ML Config: Platform={PLATFORM}, Precision={PRECISION.upper()}, Device={DEVICE.upper()}, DType={TORCH_DTYPE}")
