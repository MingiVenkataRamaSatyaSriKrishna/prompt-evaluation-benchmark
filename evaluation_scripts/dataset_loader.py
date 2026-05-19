"""
Dataset loading utilities for various file formats.

Supports CSV, JSON, TXT, and Excel files.
"""

from pathlib import Path
from typing import List, Dict, Any, Union, Callable
import json
import logging

logger = logging.getLogger(__name__)


class DatasetLoader:
    """
    Utility class for loading datasets from various formats.
    
    Supported formats:
    - CSV (.csv)
    - JSON (.json)
    - Text (.txt)
    - Excel (.xlsx, .xls)
    """
    
    # Format loaders
    _loaders: Dict[str, Callable] = {}
    
    @classmethod
    def _register_loader(cls, extension: str, loader_func: Callable):
        """Register a file format loader"""
        cls._loaders[extension.lower()] = loader_func
    
    @classmethod
    def load(cls, file_path: Union[str, Path], column: str = None) -> List[str]:
        """Load dataset from file
        
        Args:
            file_path: Path to the dataset file
            column: Column name to extract (for CSV/Excel with multiple columns)
            
        Returns:
            List of data items (prompts, etc.)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If format is not supported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = file_path.suffix[1:].lower()  # Remove leading dot
        
        if ext not in cls._loaders:
            raise ValueError(f"Unsupported file format: {ext}")
        
        logger.info(f"Loading dataset from {file_path}")
        return cls._loaders[ext](file_path, column)
    
    @staticmethod
    def load_csv(file_path: Path, column: str = None) -> List[str]:
        """Load from CSV file
        
        Args:
            file_path: Path to CSV file
            column: Column name to extract (defaults to first column)
            
        Returns:
            List of items from the specified column
        """
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            
            if column:
                if column not in df.columns:
                    raise ValueError(f"Column '{column}' not found in CSV")
                return df[column].astype(str).tolist()
            else:
                # Use first column
                return df.iloc[:, 0].astype(str).tolist()
        except ImportError:
            raise ImportError("pandas required for CSV support. Install with: pip install pandas")
    
    @staticmethod
    def load_json(file_path: Path, column: str = None) -> List[str]:
        """Load from JSON file
        
        Args:
            file_path: Path to JSON file
            column: Key to extract (for objects) or index (for arrays)
            
        Returns:
            List of items
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle array of strings
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], str):
            return data
        
        # Handle array of objects
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            if column:
                return [item.get(column, str(item)) for item in data]
            else:
                # Use first key
                first_key = list(data[0].keys())[0]
                return [item.get(first_key, str(item)) for item in data]
        
        # Handle single object
        if isinstance(data, dict):
            if column:
                return [str(data.get(column, ""))]
            else:
                return [str(v) for v in data.values()]
        
        raise ValueError("Unsupported JSON structure")
    
    @staticmethod
    def load_txt(file_path: Path, column: str = None) -> List[str]:
        """Load from text file (one item per line)
        
        Args:
            file_path: Path to text file
            column: Ignored for text files
            
        Returns:
            List of lines (non-empty)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines()]
        
        # Filter empty lines
        return [line for line in lines if line]
    
    @staticmethod
    def load_excel(file_path: Path, column: str = None) -> List[str]:
        """Load from Excel file
        
        Args:
            file_path: Path to Excel file
            column: Column name or index
            
        Returns:
            List of items from the specified column
        """
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            
            if column:
                if column in df.columns:
                    return df[column].astype(str).tolist()
                else:
                    # Try as integer index
                    try:
                        col_idx = int(column)
                        return df.iloc[:, col_idx].astype(str).tolist()
                    except (ValueError, IndexError):
                        raise ValueError(f"Column '{column}' not found in Excel")
            else:
                # Use first column
                return df.iloc[:, 0].astype(str).tolist()
        except ImportError:
            raise ImportError("pandas and openpyxl required for Excel support. Install with: pip install pandas openpyxl")
    
    @classmethod
    def register_custom_loader(cls, extension: str, loader_func: Callable):
        """Register a custom file format loader
        
        Args:
            extension: File extension (without dot)
            loader_func: Function that takes (file_path: Path, column: str) and returns List[str]
        """
        cls._register_loader(extension, loader_func)
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """Get list of supported file formats"""
        return list(cls._loaders.keys())


# Register default loaders
DatasetLoader._register_loader('csv', DatasetLoader.load_csv)
DatasetLoader._register_loader('json', DatasetLoader.load_json)
DatasetLoader._register_loader('txt', DatasetLoader.load_txt)
DatasetLoader._register_loader('xlsx', DatasetLoader.load_excel)
DatasetLoader._register_loader('xls', DatasetLoader.load_excel)
