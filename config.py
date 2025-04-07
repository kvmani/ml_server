import os
import logging
import json
import subprocess
import time
import requests

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

    def start_ml_model_service(self):
        """Start the ML model service if it's not running"""
        try:
            # Check if service is already running
            response = requests.get(self.config['super_resolution']['ml_model']['health_url'])
            if response.status_code == 200:
                logging.info("ML model service is already running")
                return True
        except requests.exceptions.RequestException:
            logging.info("ML model service not found, attempting to start it...")
            pass

        try:
            # Get the absolute path to fake_ml_model_server.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            ml_server_path = os.path.join(current_dir, 'fake_ml_model_server.py')
            
            # Print the path for debugging
            print(f"Starting ML model server from: {ml_server_path}")
            
            # Start the ML model server
            if os.name == 'nt':  # Windows
                # Use start command to open in new window
                subprocess.Popen(
                    ['start', 'cmd', '/k', 'python', ml_server_path],
                    shell=True
                )
            else:  # Unix/Linux/Mac
                subprocess.Popen(
                    ['python', ml_server_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait for service to start
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    response = requests.get(self.config['super_resolution']['ml_model']['health_url'])
                    if response.status_code == 200:
                        print("ML model server started successfully!")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)  # Wait 1 second before next attempt
                print(f"Waiting for ML model server to start... (Attempt {attempt + 1}/{max_attempts})")
            
            print("Failed to start ML model server")
            return False
            
        except Exception as e:
            print(f"Error starting ML model server: {str(e)}")
            return False 