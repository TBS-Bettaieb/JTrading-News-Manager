"""
Main pipeline for economic news manager
"""

import json
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict
import argparse
import pandas as pd

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import ForexFactoryScraper
from symbol_mapper import SymbolMapper
from csv_exporter import CSVExporter


def resolve_path(relative_path: str) -> str:
    """Resolve relative path to absolute path relative to project root"""
    if os.path.isabs(relative_path):
        return relative_path
    
    # Get the directory containing this script (src/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to get project root
    project_root = os.path.dirname(script_dir)
    # Combine with relative path
    return os.path.join(project_root, relative_path)


def setup_logging(config: Dict) -> None:
    """Setup logging configuration"""
    log_config = config.get('logging', {})
    
    # Resolve log file path relative to project root
    log_file = log_config.get('file', 'logs/app.log')
    full_log_path = resolve_path(log_file)
    
    # Ensure the log directory exists
    log_dir = os.path.dirname(full_log_path)
    os.makedirs(log_dir, exist_ok=True)
    
    # Create handlers with proper encoding to avoid Unicode issues
    file_handler = logging.FileHandler(full_log_path, encoding='utf-8')
    console_handler = logging.StreamHandler(sys.stdout)
    
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[file_handler, console_handler]
    )


def load_config(config_path: str = "config/config.json") -> Dict:
    """Load configuration from JSON file"""
    # Resolve config path relative to project root
    full_config_path = resolve_path(config_path)
    
    try:
        with open(full_config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Use print since logging is not set up yet
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        print(f"ERROR: Config file not found: {full_config_path}")
        print(f"Original path: {config_path}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Script directory: {script_dir}")
        print(f"Project root: {project_root}")
        print(f"Looking for config at: {full_config_path}")
        # Also try to log if logging is available
        try:
            logging.error(f"Config file not found: {full_config_path} (original path: {config_path})")
        except:
            pass  # Logging not set up yet, ignore
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config file: {e}")
        try:
            logging.error(f"Invalid JSON in config file: {e}")
        except:
            pass  # Logging not set up yet, ignore
        sys.exit(1)


def run_pipeline(config: Dict, mode: str = 'range', target_date: datetime = None, scrape_only: bool = False) -> bool:
    """
    Run the complete pipeline: scrape -> map -> export
    
    Args:
        config: Configuration dictionary
        mode: Scraping mode ('daily' or 'range')
        target_date: Target date for daily mode (required if mode='daily')
        scrape_only: If True, only scrape and return events without exporting
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize components
        scraping_config = config.get('scraping', {})
        output_config = config.get('output', {})
        
        symbol_mapper = SymbolMapper()
        csv_output_path = resolve_path(output_config.get('csv_path', 'output/economic_events.csv'))
        csv_exporter = CSVExporter(csv_output_path)
        
        # Initialize scraper with CSV exporter and symbol mapper for immediate saving
        scraper = ForexFactoryScraper(
            base_url=scraping_config.get('base_url', 'https://www.forexfactory.com/calendar'),
            timeout=scraping_config.get('timeout', 30),
            retry_attempts=scraping_config.get('retry_attempts', 3),
            csv_exporter=csv_exporter,
            symbol_mapper=symbol_mapper,
            headless=scraping_config.get('headless', True)  # Default to headless mode
        )
        
        if mode == 'daily':
            # Daily mode: scrape single date
            if target_date is None:
                logger.error("Target date is required for daily mode")
                return False
            
            logger.info(f"Daily mode: scraping events for {target_date.date()}")
            
            # For daily mode, don't clear CSV - use append mode
            if not scrape_only and csv_exporter:
                logger.info("Daily mode: appending to existing CSV file")
            
            # Scrape single day
            events = scraper.scrape_single_day(target_date)
            logger.info(f"Daily scrape completed: {len(events)} events found")
            
        else:
            # Range mode: scrape date range
            # Calculate date range using months instead of days
            months_back = scraping_config.get('months_back', 3)
            months_forward = scraping_config.get('months_forward', 3)
            
            # Convert months to approximate days for calculation (using 30 days per month)
            days_back = months_back * 30
            days_forward = months_forward * 30
            
            end_date = datetime.now() + timedelta(days=days_forward)
            start_date = datetime.now() - timedelta(days=days_back)
            
            logger.info(f"Range mode: scraping events from {start_date.date()} to {end_date.date()}")
            
            # Note: CSV file will be managed by deduplication logic in per-day saving
            # No need to clear existing data - deduplication will handle it
            
            # Scrape events (data will be saved to CSV after each page)
            logger.info("Starting range data scraping...")
            events = scraper.scrape_date_range(start_date, end_date)
            logger.info(f"Range scrape completed: {len(events)} events found")
        
        if not events:
            logger.warning("No events scraped - this may indicate an issue with the scraper or no events in the date range")
            # Don't fail immediately, continue with empty dataset to see if it's a real issue
            events = []
        
        if scrape_only:
            logger.info("Scrape-only mode: not exporting to CSV")
            # Map events for final count even in scrape-only mode
            mapped_events = symbol_mapper.map_events_to_pairs(events)
            logger.info(f"Pipeline completed successfully with {len(mapped_events)} events processed")
            return True
        
        # Save events to CSV (different handling for daily vs range mode)
        if events and csv_exporter:
            try:
                # Map events to trading pairs before saving
                mapped_events = symbol_mapper.map_events_to_pairs(events)
                
                if mode == 'daily':
                    # Daily mode: append to existing CSV
                    success = csv_exporter.append_events(mapped_events)
                    if success:
                        logger.info(f"Daily mode: appended {len(mapped_events)} events to CSV")
                    else:
                        logger.warning("Daily mode: failed to append events to CSV")
                else:
                    # Range mode: data should already be saved incrementally, but verify
                    logger.info("Range mode: data has been saved incrementally during scraping")
                
                # Get final file info to confirm everything was saved
                file_info = csv_exporter.get_file_info()
                logger.info(f"Final CSV file: {file_info['path']} (size: {file_info['size']})")
                
                # Load and verify the final CSV file
                try:
                    final_events_df = csv_exporter.get_existing_events()
                    if final_events_df is not None:
                        logger.info(f"Pipeline completed successfully. Final CSV contains {len(final_events_df)} events")
                        return True
                    else:
                        logger.warning("Could not verify final CSV file state")
                        return True  # Still consider it successful since saves happened
                except Exception as verify_error:
                    logger.error(f"Error verifying final CSV file: {verify_error}")
                    return True  # Still consider it successful since saves happened
                    
            except Exception as save_error:
                logger.error(f"Error saving events to CSV: {save_error}")
                return False
        else:
            logger.info("No events to save or no CSV exporter available")
            return True
            
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Economic News Manager')
    parser.add_argument('--config', default='config/config.json',
                       help='Path to configuration file')
    parser.add_argument('--scrape-only', action='store_true',
                       help='Only scrape data without exporting to CSV')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: scrape only last 7 days')
    parser.add_argument('--no-headless', action='store_true',
                       help='Disable headless mode (show browser window)')
    parser.add_argument('--mode', choices=['daily', 'range'], 
                       default=None, help='Scraping mode (overrides config)')
    parser.add_argument('--date', type=str, 
                       help='Target date for daily mode (YYYY-MM-DD, default: today)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    # Determine scraping mode (CLI overrides config)
    mode = args.mode or config.get('scraping', {}).get('default_mode', 'range')
    
    # Parse target date for daily mode
    target_date = None
    if mode == 'daily':
        if args.date:
            try:
                target_date = datetime.strptime(args.date, '%Y-%m-%d')
            except ValueError:
                logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD format.")
                sys.exit(1)
        else:
            target_date = datetime.now()
        logger.info(f"Daily mode: targeting date {target_date.date()}")
    else:
        logger.info(f"Range mode: using config date range")
    
    # Test mode adjustment
    if args.test:
        # Use approximately 1 month for test mode instead of 7 days
        config['scraping']['months_back'] = 1
        config['scraping']['months_forward'] = 1
        logger.info("Test mode enabled: fetching 1 month back and forward")
    
    # Headless mode adjustment
    if args.no_headless:
        config['scraping']['headless'] = False
        logger.info("Headless mode disabled: browser window will be visible")
    
    logger.info("Starting Economic News Manager Pipeline")
    
    # Run pipeline
    success = run_pipeline(config, mode=mode, target_date=target_date, scrape_only=args.scrape_only)
    
    if success:
        logger.info("Economic News Manager completed successfully")
        sys.exit(0)
    else:
        logger.error("Economic News Manager failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
