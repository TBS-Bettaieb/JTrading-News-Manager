"""
Data cleaning utility for economic events CSV
Fixes impact levels and country mapping issues
"""

import pandas as pd
import logging
from typing import Dict, List
import re

logger = logging.getLogger(__name__)


class EconomicDataCleaner:
    """Clean and fix economic events data"""
    
    def __init__(self):
        # Impact level mapping from CSS classes to readable values
        self.impact_mapping = {
            'Icon--Ff-Impact-Red': 'High',
            'Icon--Ff-Impact-Ora': 'Medium', 
            'Icon--Ff-Impact-Yel': 'Low',
            'Icon--Ff-Impact-Gra': 'Low',
            'High': 'High',
            'Medium': 'Medium',
            'Low': 'Low'
        }
        
        # Enhanced country mapping
        self.country_mapping = {
            'USD': 'United States',
            'EUR': 'Eurozone',
            'GBP': 'United Kingdom',
            'JPY': 'Japan',
            'CHF': 'Switzerland',
            'AUD': 'Australia',
            'NZD': 'New Zealand',
            'CAD': 'Canada',
            'CNY': 'China',
            'CH': 'Switzerland',
            'US': 'United States',
            'GB': 'United Kingdom',
            'UK': 'United Kingdom',
            'JP': 'Japan',
            'AU': 'Australia',
            'NZ': 'New Zealand',
            'CA': 'Canada',
            'CN': 'China',
            'FR': 'France',
            'DE': 'Germany',
            'IT': 'Italy',
            'ES': 'Spain',
            'RU': 'Russia',
            'BR': 'Brazil',
            'IN': 'India',
            'MX': 'Mexico',
            'ZA': 'South Africa'
        }
        
        # Event name to country mapping for better detection
        self.event_country_keywords = {
            'United States': ['US ', 'United States', 'Federal Reserve', 'FOMC', 'Fed', 'Treasury', 'Bureau', 'Department of'],
            'Eurozone': ['EZ ', 'Eurozone', 'European Central Bank', 'ECB', 'European', 'Euro'],
            'United Kingdom': ['UK ', 'United Kingdom', 'Bank of England', 'BOE', 'British', 'MPC'],
            'Japan': ['Japan', 'Bank of Japan', 'BOJ', 'Japanese'],
            'Switzerland': ['CH ', 'Switzerland', 'Swiss National Bank', 'SNB', 'Swiss'],
            'Australia': ['AU ', 'Australia', 'Reserve Bank of Australia', 'RBA', 'Australian'],
            'New Zealand': ['NZ ', 'New Zealand', 'Reserve Bank of New Zealand', 'RBNZ'],
            'Canada': ['CA ', 'Canada', 'Bank of Canada', 'BOC', 'Canadian'],
            'China': ['CN ', 'China', 'People\'s Bank of China', 'PBOC', 'Chinese'],
            'France': ['FR ', 'France', 'French'],
            'Germany': ['DE ', 'Germany', 'German', 'Bundesbank'],
            'Italy': ['IT ', 'Italy', 'Italian'],
            'Spain': ['ES ', 'Spain', 'Spanish'],
            'Russia': ['RU ', 'Russia', 'Russian'],
            'Brazil': ['BR ', 'Brazil', 'Brazilian'],
            'India': ['IN ', 'India', 'Indian', 'Reserve Bank of India', 'RBI'],
            'Mexico': ['MX ', 'Mexico', 'Mexican'],
            'South Africa': ['ZA ', 'South Africa', 'South African']
        }
    
    def clean_impact_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert impact levels from CSS classes to readable values"""
        logger.info("Cleaning impact levels...")
        
        # Count before cleaning
        impact_counts_before = df['Impact'].value_counts()
        logger.info(f"Impact levels before cleaning: {dict(impact_counts_before)}")
        
        # Apply mapping
        df['Impact'] = df['Impact'].map(self.impact_mapping).fillna(df['Impact'])
        
        # Count after cleaning
        impact_counts_after = df['Impact'].value_counts()
        logger.info(f"Impact levels after cleaning: {dict(impact_counts_after)}")
        
        return df
    
    def clean_countries(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and fix country mapping"""
        logger.info("Cleaning country mapping...")
        
        # Count before cleaning
        country_counts_before = df['Country'].value_counts()
        logger.info(f"Countries before cleaning: {dict(country_counts_before.head(10))}")
        
        # Fix countries based on event names and currency
        for idx, row in df.iterrows():
            event_name = str(row['Event'])
            currency = str(row['Currency'])
            current_country = str(row['Country'])
            
            # Skip if already correctly mapped
            if current_country != 'Unknown':
                continue
            
            # Try to detect country from event name
            detected_country = self._detect_country_from_event(event_name)
            if detected_country:
                df.at[idx, 'Country'] = detected_country
                logger.debug(f"Fixed country for '{event_name}': {current_country} -> {detected_country}")
                continue
            
            # Fallback to currency mapping
            if currency in self.country_mapping:
                df.at[idx, 'Country'] = self.country_mapping[currency]
                logger.debug(f"Fixed country for '{event_name}' using currency {currency}: {current_country} -> {self.country_mapping[currency]}")
        
        # Fix currency inconsistencies
        self._fix_currency_inconsistencies(df)
        
        # Count after cleaning
        country_counts_after = df['Country'].value_counts()
        logger.info(f"Countries after cleaning: {dict(country_counts_after.head(10))}")
        
        return df
    
    def _detect_country_from_event(self, event_name: str) -> str:
        """Detect country from event name using keywords"""
        event_name_upper = event_name.upper()
        
        for country, keywords in self.event_country_keywords.items():
            for keyword in keywords:
                if keyword.upper() in event_name_upper:
                    return country
        
        return None
    
    def _fix_currency_inconsistencies(self, df: pd.DataFrame):
        """Fix currency inconsistencies based on country and event name"""
        logger.info("Fixing currency inconsistencies...")
        
        # Country to currency mapping
        country_to_currency = {
            'United States': 'USD',
            'Eurozone': 'EUR',
            'United Kingdom': 'GBP',
            'Japan': 'JPY',
            'Switzerland': 'CHF',
            'Australia': 'AUD',
            'New Zealand': 'NZD',
            'Canada': 'CAD',
            'China': 'CNY',
            'France': 'EUR',
            'Germany': 'EUR',
            'Italy': 'EUR',
            'Spain': 'EUR',
            'Russia': 'RUB',
            'Brazil': 'BRL',
            'India': 'INR',
            'Mexico': 'MXN',
            'South Africa': 'ZAR'
        }
        
        for idx, row in df.iterrows():
            country = str(row['Country'])
            currency = str(row['Currency'])
            event_name = str(row['Event'])
            
            # Fix obvious mismatches
            if country in country_to_currency:
                expected_currency = country_to_currency[country]
                if currency != expected_currency:
                    logger.debug(f"Fixing currency mismatch: '{event_name}' - Country: {country}, Currency: {currency} -> {expected_currency}")
                    df.at[idx, 'Currency'] = expected_currency
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean all data issues"""
        logger.info("Starting data cleaning process...")
        
        # Make a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Clean impact levels
        cleaned_df = self.clean_impact_levels(cleaned_df)
        
        # Clean countries
        cleaned_df = self.clean_countries(cleaned_df)
        
        # Remove duplicates if any
        initial_count = len(cleaned_df)
        cleaned_df = cleaned_df.drop_duplicates(subset=['DateTime', 'Event', 'Currency'])
        final_count = len(cleaned_df)
        
        if initial_count != final_count:
            logger.info(f"Removed {initial_count - final_count} duplicate events")
        
        logger.info("Data cleaning completed successfully")
        return cleaned_df
    
    def generate_cleaning_report(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> Dict:
        """Generate a report of cleaning changes"""
        report = {
            'total_events': len(cleaned_df),
            'impact_changes': {},
            'country_changes': {},
            'currency_changes': {}
        }
        
        # Impact changes
        original_impacts = original_df['Impact'].value_counts()
        cleaned_impacts = cleaned_df['Impact'].value_counts()
        
        for impact in set(list(original_impacts.index) + list(cleaned_impacts.index)):
            original_count = original_impacts.get(impact, 0)
            cleaned_count = cleaned_impacts.get(impact, 0)
            if original_count != cleaned_count:
                report['impact_changes'][impact] = {
                    'before': original_count,
                    'after': cleaned_count,
                    'change': cleaned_count - original_count
                }
        
        # Country changes
        original_countries = original_df['Country'].value_counts()
        cleaned_countries = cleaned_df['Country'].value_counts()
        
        for country in set(list(original_countries.index) + list(cleaned_countries.index)):
            original_count = original_countries.get(country, 0)
            cleaned_count = cleaned_countries.get(country, 0)
            if original_count != cleaned_count:
                report['country_changes'][country] = {
                    'before': original_count,
                    'after': cleaned_count,
                    'change': cleaned_count - original_count
                }
        
        return report


def clean_economic_events_csv(input_path: str, output_path: str = None) -> bool:
    """
    Clean economic events CSV file
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to output CSV file (if None, overwrites input)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Loading data from: {input_path}")
        df = pd.read_csv(input_path)
        
        logger.info(f"Loaded {len(df)} events")
        
        # Initialize cleaner
        cleaner = EconomicDataCleaner()
        
        # Clean data
        cleaned_df = cleaner.clean_data(df)
        
        # Generate report
        report = cleaner.generate_cleaning_report(df, cleaned_df)
        
        # Print report
        print("\n" + "="*60)
        print("DATA CLEANING REPORT")
        print("="*60)
        print(f"Total events: {report['total_events']}")
        
        if report['impact_changes']:
            print(f"\nImpact Level Changes:")
            for impact, change in report['impact_changes'].items():
                print(f"  {impact}: {change['before']} -> {change['after']} ({change['change']:+d})")
        
        if report['country_changes']:
            print(f"\nCountry Changes:")
            for country, change in report['country_changes'].items():
                print(f"  {country}: {change['before']} -> {change['after']} ({change['change']:+d})")
        
        print("="*60)
        
        # Save cleaned data
        output_file = output_path or input_path
        cleaned_df.to_csv(output_file, index=False)
        logger.info(f"Cleaned data saved to: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error cleaning data: {e}")
        return False


if __name__ == "__main__":
    import sys
    import os
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python data_cleaner.py <input_csv_path> [output_csv_path]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    success = clean_economic_events_csv(input_path, output_path)
    if success:
        print("Data cleaning completed successfully!")
    else:
        print("Data cleaning failed!")
        sys.exit(1)
