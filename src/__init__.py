"""
Document Conversion Pipeline - Source Module Initialization
"""

__version__ = "1.0.0"
__author__ = "IKB Project Team"

from .document_extractor import DocumentExtractor
from .ai_processor import AIProcessor
from .template_generator import TemplateGenerator
from .file_manager import FileManager

__all__ = [
    'DocumentExtractor',
    'AIProcessor', 
    'TemplateGenerator',
    'FileManager'
]
