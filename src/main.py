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


def run_pipeline(config: Dict, scrape_only: bool = False) -> bool:
    """
    Run the complete pipeline: scrape -> map -> export
    
    Args:
        config: Configuration dictionary
        scrape_only: If True, only scrape and return events without exporting
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize components
        scraping_config = config.get('scraping', {})
        output_config = config.get('output', {})
        
        scraper = ForexFactoryScraper(
            base_url=scraping_config.get('base_url', 'https://www.forexfactory.com/calendar'),
            timeout=scraping_config.get('timeout', 30),
            retry_attempts=scraping_config.get('retry_attempts', 3)
        )
        
        symbol_mapper = SymbolMapper()
        csv_output_path = resolve_path(output_config.get('csv_path', 'output/economic_events.csv'))
        csv_exporter = CSVExporter(csv_output_path)
        
        # Calculate date range
        days_back = scraping_config.get('days_back', 90)
        days_forward = scraping_config.get('days_forward', 90)
        
        end_date = datetime.now() + timedelta(days=days_forward)
        start_date = datetime.now() - timedelta(days=days_back)
        
        logger.info(f"Scraping events from {start_date.date()} to {end_date.date()}")
        
        # Scrape events
        logger.info("Starting data scraping...")
        events = scraper.scrape_date_range(start_date, end_date)
        logger.info(f"Scraped {len(events)} events")
        
        if not events:
            logger.warning("No events scraped - this may indicate an issue with the scraper or no events in the date range")
            # Don't fail immediately, continue with empty dataset to see if it's a real issue
            events = []
        
        # Map events to trading pairs
        logger.info("Mapping events to trading pairs...")
        mapped_events = symbol_mapper.map_events_to_pairs(events)
        logger.info(f"Mapped {len(mapped_events)} events with trading pairs")
        
        if scrape_only:
            logger.info("Scrape-only mode: not exporting to CSV")
            logger.info(f"Pipeline completed successfully with {len(mapped_events)} events processed")
            return True
        
        # Export to CSV
        logger.info("Exporting events to CSV...")
        try:
            success = csv_exporter.export_events(mapped_events)
            
            if success:
                logger.info("Pipeline completed successfully")
                logger.info(f"Exported {len(mapped_events)} events to CSV")
                return True
            else:
                logger.error("Pipeline failed at export stage")
                return False
        except Exception as export_error:
            logger.error(f"CSV export failed with error: {export_error}")
            return False
            
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
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    # Test mode adjustment
    if args.test:
        config['scraping']['days_back'] = 7
        config['scraping']['days_forward'] = 7
        logger.info("Test mode enabled: fetching 7 days back and forward")
    
    logger.info("Starting Economic News Manager Pipeline")
    
    # Run pipeline
    success = run_pipeline(config, scrape_only=args.scrape_only)
    
    if success:
        logger.info("Economic News Manager completed successfully")
        sys.exit(0)
    else:
        logger.error("Economic News Manager failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
