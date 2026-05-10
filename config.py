import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-influenceiq-secret-key-2026')
    DEBUG = False
    TESTING = False
    
    # YouTube API
    YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
    
    # ML Model Configs
    ML_MODEL_PATH = os.environ.get('ML_MODEL_PATH', 'dataset.csv')
    
class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    ENV = 'production'
    # Here you might add strict secure cookie settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True

# Dictionary to easily map environment names to config classes
config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'test': TestingConfig,
    'default': DevelopmentConfig
}
