"""
配置管理 - 管理智能体的配置
"""
import os
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class AgentConfig:
    """智能体配置"""
    
    # 配置文件路径
    MODELS_CONFIG_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "models_config.json"
    )
    
    # 当前选中的配置
    _current_provider = None
    _current_model = None
    
    # 模型配置缓存
    _models_config = None
    
    @classmethod
    def _load_models_config(cls):
        """加载模型配置"""
        if cls._models_config is None:
            try:
                with open(cls.MODELS_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    cls._models_config = json.load(f)
            except:
                cls._models_config = {
                    "providers": [],
                    "default": {"provider": "SiliconFlow", "model": "Qwen/Qwen2.5-7B-Instruct"}
                }
        return cls._models_config
    
    @classmethod
    def get_available_providers(cls):
        """获取所有可用的模型提供商"""
        config = cls._load_models_config()
        return config.get("providers", [])
    
    @classmethod
    def get_models_by_provider(cls, provider_name):
        """获取指定提供商的所有模型"""
        config = cls._load_models_config()
        providers = config.get("providers", [])
        for provider in providers:
            if provider.get("name") == provider_name:
                return provider.get("models", [])
        return []
    
    @classmethod
    def get_provider_config(cls, provider_name):
        """获取提供商配置"""
        config = cls._load_models_config()
        providers = config.get("providers", [])
        for provider in providers:
            if provider.get("name") == provider_name:
                return provider
        return None
    
    @classmethod
    def get_current_provider(cls):
        """获取当前选中的提供商"""
        if cls._current_provider is None:
            config = cls._load_models_config()
            cls._current_provider = config.get("default", {}).get("provider", "SiliconFlow")
        return cls._current_provider
    
    @classmethod
    def get_current_model(cls):
        """获取当前选中的模型"""
        if cls._current_model is None:
            config = cls._load_models_config()
            cls._current_model = config.get("default", {}).get("model", "Qwen/Qwen2.5-7B-Instruct")
        return cls._current_model
    
    @classmethod
    def set_current_model(cls, provider_name, model_id):
        """设置当前使用的模型"""
        cls._current_provider = provider_name
        cls._current_model = model_id
    
    @classmethod
    def get_api_config(cls):
        """获取当前 API 配置"""
        provider_name = cls.get_current_provider()
        provider_config = cls.get_provider_config(provider_name)
        
        if provider_config:
            api_url = provider_config.get("api_url")
            # 从环境变量获取 API Key
            api_key_env = provider_config.get("api_key_env", "LLM_API_KEY")
            api_key = os.getenv(api_key_env, os.getenv("LLM_API_KEY", ""))
            
            return {
                "api_url": api_url,
                "api_key": api_key,
                "model": cls.get_current_model(),
                "provider": provider_name
            }
        
        # 回退到旧的配置方式
        return {
            "api_url": os.getenv("LLM_API_URL", ""),
            "api_key": os.getenv("LLM_API_KEY", ""),
            "model": os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
            "provider": "Custom"
        }
    
    # 旧配置方式的向后兼容
    @classmethod
    def get_api_url(cls):
        return cls.get_api_config().get("api_url", "")
    
    @classmethod
    def get_api_key(cls):
        return cls.get_api_config().get("api_key", "")
    
    @classmethod
    def get_model_name(cls):
        return cls.get_api_config().get("model", "gpt-3.5-turbo")
    
    # 其他配置
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
    MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))
    
    @classmethod
    def is_api_configured(cls) -> bool:
        """检查 API 是否已配置"""
        config = cls.get_api_config()
        return bool(config.get("api_url") and config.get("api_key"))
