"""
Configuration loader for entity resolution profiles.
Supports operational, analytics, and default profiles with different thresholds.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class ResolutionConfig:
    """Entity resolution configuration with validation"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.name = config_dict.get('name', 'default')
        self.description = config_dict.get('description', '')
        
        # Core thresholds
        self.merge_threshold = config_dict.get('merge_threshold', 0.5)
        self.min_attribute_match_ratio = config_dict.get('min_attribute_match_ratio', 0.3)
        
        # Hard link tiered thresholds
        self.hard_link_tier1_ratio = config_dict.get('hard_link_tier1_ratio', 0.5)
        self.hard_link_tier2_ratio = config_dict.get('hard_link_tier2_ratio', 0.3)
        self.hard_link_tier3_ratio = config_dict.get('hard_link_tier3_ratio', 0.3)
        
        # Matching rules
        self.allow_soft_matches = config_dict.get('allow_soft_matches', False)
        self.require_business_relationship = config_dict.get('require_business_relationship', False)
        self.min_confidence_for_merge = config_dict.get('min_confidence_for_merge', 0.7)
        
        # Evidence filtering
        self.use_hard_links_only = config_dict.get('use_hard_links_only', False)
        self.ignore_low_quality_evidence = config_dict.get('ignore_low_quality_evidence', False)
        
        # Output settings
        self.output_suffix = config_dict.get('output_suffix', '')
        self.output_description = config_dict.get('output_description', 'Entity Resolution')
        
        self._validate()
    
    def _validate(self):
        """Validate configuration values"""
        assert 0 <= self.merge_threshold <= 1, "merge_threshold must be between 0 and 1"
        assert 0 <= self.min_attribute_match_ratio <= 1, "min_attribute_match_ratio must be between 0 and 1"
        assert 0 <= self.hard_link_tier1_ratio <= 1, "hard_link_tier1_ratio must be between 0 and 1"
        assert 0 <= self.hard_link_tier2_ratio <= 1, "hard_link_tier2_ratio must be between 0 and 1"
        assert 0 <= self.hard_link_tier3_ratio <= 1, "hard_link_tier3_ratio must be between 0 and 1"
        assert self.hard_link_tier1_ratio >= self.hard_link_tier2_ratio >= self.hard_link_tier3_ratio, \
            "Tier ratios must be descending: tier1 >= tier2 >= tier3"
    
    def __str__(self):
        return f"ResolutionConfig(name={self.name}, merge_threshold={self.merge_threshold})"


def load_config(config_name: str = 'default') -> ResolutionConfig:
    """
    Load entity resolution configuration from YAML file.
    
    Args:
        config_name: Name of config profile ('operational', 'analytics', 'default')
    
    Returns:
        ResolutionConfig object with validated parameters
    
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    # Get project root and config path
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / 'config' / f'resolution_{config_name}.yaml'
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Available configs: operational, analytics, default"
        )
    
    # Load YAML
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    # Create and validate config object
    config = ResolutionConfig(config_dict)
    
    return config


def list_available_configs() -> list:
    """List all available configuration profiles"""
    project_root = Path(__file__).parent.parent.parent
    config_dir = project_root / 'config'
    
    if not config_dir.exists():
        return []
    
    configs = []
    for config_file in config_dir.glob('resolution_*.yaml'):
        config_name = config_file.stem.replace('resolution_', '')
        configs.append(config_name)
    
    return sorted(configs)
