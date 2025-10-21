"""
Scheduler for daily economic news fetching
"""

import schedule
import time
import logging
import sys
import os
import signal
from datetime import datetime
import json

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import load_config, setup_logging, run_pipeline


class NewsScheduler:
    """Scheduler for running economic news pipeline daily"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.config = None
        self.logger = logging.getLogger(__name__)
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received {signal_name} signal. Initiating graceful shutdown...")
        self.running = False
        
    def _load_and_setup(self):
        """Load config and setup logging"""
        try:
            self.config = load_config(self.config_path)
            setup_logging(self.config)
            self.logger = logging.getLogger(__name__)
            return True
        except Exception as e:
            print(f"Failed to load configuration: {e}")
            return False
    
    def _scheduled_job(self):
        """Job to run the economic news pipeline"""
        self.logger.info("=" * 50)
        self.logger.info(f"Scheduled job started at {datetime.now()}")
        
        try:
            success = run_pipeline(self.config, scrape_only=False)
            
            if success:
                self.logger.info("Scheduled job completed successfully")
            else:
                self.logger.error("Scheduled job failed")
                
        except Exception as e:
            self.logger.error(f"Scheduled job failed with exception: {e}")
        
        self.logger.info(f"Scheduled job finished at {datetime.now()}")
        self.logger.info("=" * 50)
    
    def start_scheduler(self):
        """Start the scheduler"""
        if not self._load_and_setup():
            print("Failed to setup scheduler. Exiting.")
            sys.exit(1)
        
        scheduler_config = self.config.get('scheduler', {})
        run_time = scheduler_config.get('run_time', '06:00')
        timezone = scheduler_config.get('timezone', 'local')
        
        self.logger.info(f"Setting up scheduled job for daily execution at {run_time}")
        
        # Schedule the job
        schedule.every().day.at(run_time).do(self._scheduled_job)
        
        self.logger.info("Scheduler started. Waiting for next execution...")
        
        # Log next run time
        next_run = schedule.next_run()
        self.logger.info(f"Next scheduled run: {next_run}")
        
        self.running = True
        
        try:
            while self.running:
                schedule.run_pending()
                # Check every minute or until shutdown signal
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)  # Check every second for shutdown signal
                
                # Log status periodically
                if self.running and schedule.next_run():
                    self.logger.debug(f"Next scheduled run: {schedule.next_run()}")
                
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user (Ctrl+C)")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
        finally:
            self.logger.info("Scheduler shutdown complete")
            self.running = False
    
    def run_once_now(self):
        """Run the job once immediately"""
        if not self._load_and_setup():
            print("Failed to setup scheduler. Exiting.")
            sys.exit(1)
        
        self.logger.info("Running job once immediately...")
        self._scheduled_job()
    
    def get_next_run_time(self):
        """Get the next scheduled run time"""
        if schedule.jobs:
            return schedule.next_run()
        return None


def main():
    """Main entry point for scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Economic News Scheduler')
    parser.add_argument('--config', default='config/config.json',
                       help='Path to configuration file')
    parser.add_argument('--run-once', action='store_true',
                       help='Run the job once immediately instead of scheduling')
    
    args = parser.parse_args()
    
    scheduler = NewsScheduler(args.config)
    
    if args.run_once:
        scheduler.run_once_now()
    else:
        scheduler.start_scheduler()


if __name__ == "__main__":
    main()
