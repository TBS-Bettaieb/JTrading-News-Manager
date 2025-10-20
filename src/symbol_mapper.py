"""
Currency to trading symbol mapper
"""

import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class SymbolMapper:
    """Maps currencies to affected trading pairs"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.auto_mapping = {}
        self.custom_overrides = {}
        self._load_config()
    
    def _load_config(self):
        """Load mapping configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            symbol_config = config.get('symbol_mapping', {})
            self.auto_mapping = symbol_config.get('auto_mapping', {})
            self.custom_overrides = symbol_config.get('custom_overrides', {})
            
            logger.info(f"Loaded {len(self.auto_mapping)} auto mappings and {len(self.custom_overrides)} custom overrides")
            
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            self._load_default_mappings()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            self._load_default_mappings()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._load_default_mappings()
    
    def _load_default_mappings(self):
        """Load default mapping if config file is not available"""
        self.auto_mapping = {
            "USD": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD"],
            "EUR": ["EURUSD", "EURGBP", "EURJPY", "EURCHF", "EURAUD"],
            "GBP": ["GBPUSD", "EURGBP", "GBPJPY", "GBPCHF", "GBPAUD"],
            "JPY": ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "NZDJPY"],
            "CHF": ["USDCHF", "EURCHF", "GBPCHF", "CHFJPY"],
            "AUD": ["AUDUSD", "EURAUD", "GBPAUD", "AUDJPY", "AUDNZD"],
            "NZD": ["NZDUSD", "NZDJPY", "AUDNZD"],
            "CAD": ["USDCAD", "CADJPY"]
        }
        self.custom_overrides = {}
        logger.warning("Using default mappings due to config error")
    
    def get_affected_pairs(self, currency: str) -> List[str]:
        """
        Get affected trading pairs for a currency
        
        Args:
            currency: Currency code (e.g., 'USD', 'EUR')
            
        Returns:
            List of affected trading pairs
        """
        # First check custom overrides
        if currency in self.custom_overrides:
            logger.debug(f"Using custom override for {currency}: {self.custom_overrides[currency]}")
            return self.custom_overrides[currency].copy()
        
        # Then check auto mapping
        if currency in self.auto_mapping:
            logger.debug(f"Using auto mapping for {currency}: {self.auto_mapping[currency]}")
            return self.auto_mapping[currency].copy()
        
        # If no mapping found, return empty list
        logger.warning(f"No mapping found for currency: {currency}")
        return []
    
    def map_events_to_pairs(self, events: List[Dict]) -> List[Dict]:
        """
        Add affected trading pairs to economic events
        
        Args:
            events: List of economic event dictionaries
            
        Returns:
            List of events with AffectedPairs field added
        """
        mapped_events = []
        
        for event in events:
            currency = event.get('Currency', '')
            affected_pairs = self.get_affected_pairs(currency)
            
            # Create a copy of the event and add affected pairs
            mapped_event = event.copy()
            mapped_event['AffectedPairs'] = ', '.join(affected_pairs) if affected_pairs else 'N/A'
            
            mapped_events.append(mapped_event)
        
        logger.info(f"Mapped {len(mapped_events)} events with trading pairs")
        return mapped_events
    
    def add_custom_mapping(self, currency: str, pairs: List[str]):
        """
        Add or update custom mapping for a currency
        
        Args:
            currency: Currency code
            pairs: List of trading pairs
        """
        self.custom_overrides[currency] = pairs.copy()
        logger.info(f"Added custom mapping for {currency}: {pairs}")
    
    def remove_custom_mapping(self, currency: str):
        """
        Remove custom mapping for a currency
        
        Args:
            currency: Currency code
        """
        if currency in self.custom_overrides:
            del self.custom_overrides[currency]
            logger.info(f"Removed custom mapping for {currency}")
        else:
            logger.warning(f"No custom mapping found for {currency}")
    
    def get_available_currencies(self) -> List[str]:
        """Get list of all available currencies from mappings"""
        currencies = set(self.auto_mapping.keys())
        currencies.update(self.custom_overrides.keys())
        return sorted(list(currencies))
    
    def get_all_mappings(self) -> Dict[str, List[str]]:
        """
        Get complete mapping (auto + custom, with custom taking precedence)
        
        Returns:
            Dictionary mapping currencies to their trading pairs
        """
        complete_mapping = self.auto_mapping.copy()
        complete_mapping.update(self.custom_overrides)
        return complete_mapping
