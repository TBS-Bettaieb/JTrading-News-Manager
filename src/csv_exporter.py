"""
CSV exporter for economic events
"""

import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports economic events to CSV format"""
    
    def __init__(self, output_path: str = "output/economic_events.csv"):
        self.output_path = output_path
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """Ensure the output directory exists"""
        output_dir = os.path.dirname(self.output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
    
    def export_events(self, events: List[Dict], mode: str = 'w') -> bool:
        """
        Export economic events to CSV file
        
        Args:
            events: List of event dictionaries
            mode: Write mode ('w' for overwrite, 'a' for append)
            
        Returns:
            True if successful, False otherwise
        """
        if not events:
            logger.warning("No events to export")
            return False
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(events)
            
            # Ensure required columns exist
            required_columns = [
                'DateTime', 'Event', 'Country', 'Impact', 
                'Currency', 'Actual', 'Forecast', 'Previous', 'AffectedPairs'
            ]
            
            # Add missing columns with default values
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 'N/A'
                    logger.warning(f"Missing column {col}, filled with 'N/A'")
            
            # Reorder columns to match expected format
            df = df[required_columns]
            
            # Convert DateTime to string format for CSV and validate
            if 'DateTime' in df.columns:
                df['DateTime'] = pd.to_datetime(df['DateTime']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Validate data quality
            self._validate_data_quality(df)
            
            # Handle existing file for append mode
            if mode == 'a' and os.path.exists(self.output_path):
                existing_df = pd.read_csv(self.output_path)
                df = pd.concat([existing_df, df], ignore_index=True)
                # Remove duplicates based on DateTime, Event, and Currency
                df = self._remove_duplicates(df)
                mode = 'w'  # Now we need to overwrite the complete file
            
            # Write to CSV
            df.to_csv(self.output_path, index=False, mode=mode)
            
            logger.info(f"Exported {len(df)} events to {self.output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export events: {e}")
            return False
    
    def _validate_data_quality(self, df: pd.DataFrame) -> None:
        """
        Validate data quality and log statistics
        
        Args:
            df: DataFrame to validate
        """
        if df.empty:
            logger.warning("No data to validate")
            return
        
        try:
            total_events = len(df)
            
            # Check for missing critical data
            missing_event_names = df['Event'].isna().sum()
            missing_currencies = df['Currency'].isna().sum()
            missing_dates = df['DateTime'].isna().sum()
            
            # Check data quality metrics
            events_with_actual = (df['Actual'] != 'N/A').sum()
            events_with_forecast = (df['Forecast'] != 'N/A').sum()
            events_with_previous = (df['Previous'] != 'N/A').sum()
            
            # Count by impact level
            impact_counts = df['Impact'].value_counts().to_dict()
            
            # Count by currency
            currency_counts = df['Currency'].value_counts().head(10).to_dict()
            
            logger.info("=" * 50)
            logger.info("DATA QUALITY VALIDATION REPORT")
            logger.info("=" * 50)
            logger.info(f"[STATS] Total events: {total_events}")
            logger.info(f"[CHECK] Missing Event names: {missing_event_names}")
            logger.info(f"[CURRENCY] Missing Currencies: {missing_currencies}")
            logger.info(f"[DATE] Missing Dates: {missing_dates}")
            logger.info(f"[ACTUAL] Events with Actual values: {events_with_actual} ({events_with_actual/total_events*100:.1f}%)")
            logger.info(f"[FORECAST] Events with Forecast values: {events_with_forecast} ({events_with_forecast/total_events*100:.1f}%)")
            logger.info(f"[PREVIOUS] Events with Previous values: {events_with_previous} ({events_with_previous/total_events*100:.1f}%)")
            
            logger.info("Impact Distribution:")
            for impact, count in impact_counts.items():
                logger.info(f"  {impact}: {count} ({count/total_events*100:.1f}%)")
            
            logger.info("Top Currencies:")
            for currency, count in currency_counts.items():
                logger.info(f"  {currency}: {count}")
            
            logger.info("=" * 50)
            
        except Exception as e:
            logger.warning(f"Error during data validation: {e}")
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate events based on DateTime, Event, and Currency
        
        Args:
            df: DataFrame to deduplicate
            
        Returns:
            Deduplicated DataFrame
        """
        if df.empty:
            return df
        
        # Sort by DateTime to keep the most recent version
        df = df.sort_values('DateTime', ascending=False)
        
        # Remove duplicates keeping the first occurrence (most recent)
        df = df.drop_duplicates(
            subset=['DateTime', 'Event', 'Currency'], 
            keep='first'
        )
        
        # Sort back by DateTime ascending
        df = df.sort_values('DateTime', ascending=True)
        
        return df
    
    def append_events(self, events: List[Dict]) -> bool:
        """
        Append events to existing CSV file
        
        Args:
            events: List of event dictionaries to append
            
        Returns:
            True if successful, False otherwise
        """
        return self.export_events(events, mode='a')
    
    def get_existing_events(self) -> Optional[pd.DataFrame]:
        """
        Load existing events from CSV file
        
        Returns:
            DataFrame of existing events or None if file doesn't exist
        """
        try:
            if os.path.exists(self.output_path):
                df = pd.read_csv(self.output_path)
                # Convert DateTime back to datetime
                if 'DateTime' in df.columns:
                    df['DateTime'] = pd.to_datetime(df['DateTime'])
                return df
            else:
                logger.info(f"Output file {self.output_path} does not exist")
                return None
        except Exception as e:
            logger.error(f"Failed to read existing events: {e}")
            return None
    
    def backup_existing_file(self) -> bool:
        """
        Create a backup of the existing CSV file
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.output_path):
            logger.info("No existing file to backup")
            return True
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.output_path}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(self.output_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def get_file_info(self) -> Dict[str, str]:
        """
        Get information about the output file
        
        Returns:
            Dictionary with file information
        """
        info = {
            'path': self.output_path,
            'exists': str(os.path.exists(self.output_path)),
            'size': '0 bytes'
        }
        
        try:
            if os.path.exists(self.output_path):
                size_bytes = os.path.getsize(self.output_path)
                info['size'] = f"{size_bytes} bytes"
                info['last_modified'] = str(datetime.fromtimestamp(os.path.getmtime(self.output_path)))
        except Exception as e:
            logger.warning(f"Could not get file info: {e}")
        
        return info
