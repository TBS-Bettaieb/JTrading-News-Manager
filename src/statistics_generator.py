"""
Generate statistical analysis of cleaned economic events data
"""

import pandas as pd
import logging
from typing import Dict, List
import os

logger = logging.getLogger(__name__)


class EconomicEventsAnalyzer:
    """Analyze economic events data and generate statistics"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load data from CSV file"""
        try:
            self.df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(self.df)} events from {self.csv_path}")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def generate_impact_distribution(self) -> Dict:
        """Generate impact level distribution"""
        impact_counts = self.df['Impact'].value_counts()
        total_events = len(self.df)
        
        distribution = {}
        for impact, count in impact_counts.items():
            percentage = (count / total_events) * 100
            distribution[impact] = {
                'count': count,
                'percentage': percentage
            }
        
        return distribution
    
    def generate_currency_distribution(self, top_n: int = 10) -> Dict:
        """Generate currency distribution"""
        currency_counts = self.df['Currency'].value_counts().head(top_n)
        total_events = len(self.df)
        
        distribution = {}
        for currency, count in currency_counts.items():
            percentage = (count / total_events) * 100
            distribution[currency] = {
                'count': count,
                'percentage': percentage
            }
        
        return distribution
    
    def generate_country_distribution(self, top_n: int = 10) -> Dict:
        """Generate country distribution"""
        country_counts = self.df['Country'].value_counts().head(top_n)
        total_events = len(self.df)
        
        distribution = {}
        for country, count in country_counts.items():
            percentage = (count / total_events) * 100
            distribution[country] = {
                'count': count,
                'percentage': percentage
            }
        
        return distribution
    
    def generate_data_completeness(self) -> Dict:
        """Generate data completeness statistics"""
        total_events = len(self.df)
        
        completeness = {
            'total_events': total_events,
            'actual_values': {
                'count': (self.df['Actual'] != 'N/A').sum(),
                'percentage': ((self.df['Actual'] != 'N/A').sum() / total_events) * 100
            },
            'forecast_values': {
                'count': (self.df['Forecast'] != 'N/A').sum(),
                'percentage': ((self.df['Forecast'] != 'N/A').sum() / total_events) * 100
            },
            'previous_values': {
                'count': (self.df['Previous'] != 'N/A').sum(),
                'percentage': ((self.df['Previous'] != 'N/A').sum() / total_events) * 100
            }
        }
        
        return completeness
    
    def generate_time_analysis(self) -> Dict:
        """Generate time-based analysis"""
        # Convert DateTime to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(self.df['DateTime']):
            self.df['DateTime'] = pd.to_datetime(self.df['DateTime'])
        
        # Add time-based columns
        self.df['Date'] = self.df['DateTime'].dt.date
        self.df['Hour'] = self.df['DateTime'].dt.hour
        self.df['DayOfWeek'] = self.df['DateTime'].dt.day_name()
        
        # Daily events
        daily_events = self.df.groupby('Date').size()
        
        # Hourly events (top 5)
        hourly_events = self.df.groupby('Hour').size().nlargest(5)
        
        # Weekly events
        weekly_events = self.df.groupby('DayOfWeek').size()
        
        time_analysis = {
            'daily_stats': {
                'average_events_per_day': daily_events.mean(),
                'max_events_in_day': daily_events.max(),
                'min_events_in_day': daily_events.min(),
                'total_days': len(daily_events)
            },
            'top_hours': {hour: count for hour, count in hourly_events.items()},
            'weekly_distribution': {day: count for day, count in weekly_events.items()}
        }
        
        return time_analysis
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        logger.info("Generating comprehensive analysis report...")
        
        report = {
            'summary': {
                'total_events': len(self.df),
                'date_range': {
                    'start': self.df['DateTime'].min(),
                    'end': self.df['DateTime'].max()
                },
                'unique_currencies': self.df['Currency'].nunique(),
                'unique_countries': self.df['Country'].nunique()
            },
            'impact_distribution': self.generate_impact_distribution(),
            'currency_distribution': self.generate_currency_distribution(),
            'country_distribution': self.generate_country_distribution(),
            'data_completeness': self.generate_data_completeness(),
            'time_analysis': self.generate_time_analysis()
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted analysis report"""
        print("\n" + "="*60)
        print("STATISTICAL ANALYSIS OF ECONOMIC EVENTS")
        print("="*60)
        
        # Summary
        summary = report['summary']
        print(f"Total Events: {summary['total_events']}")
        print(f"Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"Unique Currencies: {summary['unique_currencies']}")
        print(f"Unique Countries: {summary['unique_countries']}")
        
        # Impact Distribution
        print(f"\nImpact Level Distribution:")
        for impact, data in report['impact_distribution'].items():
            print(f"   {impact:6s}: {data['count']:4d} events ({data['percentage']:5.1f}%)")
        
        # Currency Distribution
        print(f"\nTop 10 Currencies:")
        for currency, data in report['currency_distribution'].items():
            print(f"   {currency:3s}: {data['count']:4d} events ({data['percentage']:5.1f}%)")
        
        # Country Distribution
        print(f"\nTop 10 Countries:")
        for country, data in report['country_distribution'].items():
            print(f"   {country:20s}: {data['count']:4d} events ({data['percentage']:5.1f}%)")
        
        # Data Completeness
        completeness = report['data_completeness']
        print(f"\nData Completeness:")
        print(f"   Events with Actual values: {completeness['actual_values']['count']:4d} ({completeness['actual_values']['percentage']:5.1f}%)")
        print(f"   Events with Forecast values: {completeness['forecast_values']['count']:4d} ({completeness['forecast_values']['percentage']:5.1f}%)")
        print(f"   Events with Previous values: {completeness['previous_values']['count']:4d} ({completeness['previous_values']['percentage']:5.1f}%)")
        
        # Time Analysis
        time_analysis = report['time_analysis']
        daily_stats = time_analysis['daily_stats']
        print(f"\nTime-based Analysis:")
        print(f"   Average events per day: {daily_stats['average_events_per_day']:.1f}")
        print(f"   Max events in a day: {daily_stats['max_events_in_day']}")
        print(f"   Min events in a day: {daily_stats['min_events_in_day']}")
        print(f"   Days with events: {daily_stats['total_days']}")
        
        print(f"\nEvents by Hour (Top 5):")
        for hour, count in time_analysis['top_hours'].items():
            print(f"   {hour:2d}:00 - {count:3d} events")
        
        print(f"\nEvents by Day of Week:")
        for day, count in time_analysis['weekly_distribution'].items():
            print(f"   {day:9s}: {count:3d} events")
        
        print("="*60)


def analyze_economic_events(csv_path: str):
    """
    Analyze economic events CSV file and generate statistics
    
    Args:
        csv_path: Path to CSV file
    """
    try:
        # Initialize analyzer
        analyzer = EconomicEventsAnalyzer(csv_path)
        
        # Generate comprehensive report
        report = analyzer.generate_comprehensive_report()
        
        # Print report
        analyzer.print_report(report)
        
        return report
        
    except Exception as e:
        logger.error(f"Error analyzing data: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python statistics_generator.py <csv_path>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    report = analyze_economic_events(csv_path)
    if report:
        print("\nAnalysis completed successfully!")
    else:
        print("Analysis failed!")
        sys.exit(1)
