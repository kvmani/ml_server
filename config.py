import os
import logging
import json

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)
            
        # Setup logging based on debug mode
        self._setup_logging()
    
    def _setup_logging(self):
        log_level = logging.DEBUG if self.config.get('debug', False) else logging.INFO
        
        # Create logs directory if it doesn't exist
        log_dir = self.config['logging']['log_dir']
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format=self.config['logging']['format'],
            filename=os.path.join(log_dir, self.config['logging']['log_file'])
        )
    
    @property
    def debug(self):
        return self.config.get('debug', False)
    
    @property
    def super_resolution_extensions(self):
        return set(self.config['super_resolution']['allowed_extensions'])
    
    @property
    def ebsd_extensions(self):
        return set(self.config['ebsd_cleanup']['allowed_extensions'])
    
    @property
    def ml_model_url(self):
        return self.config['super_resolution']['ml_model']['url']
    
    @property
    def ml_model_health_url(self):
        return self.config['super_resolution']['ml_model']['health_url'] 