#!/usr/bin/env python3
"""
Data validation script for Sharp Agents.
Validates database integrity, price data quality, and market consistency.
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append('.')

from utils.config import get_config
from utils.logger import get_logger
from database.models import Market, MarketPrice
from utils.config import get_config


class DataValidator:
    """Comprehensive data validation for the Sharp Agents database."""
    
    def __init__(self):
        """Initialize the data validator."""
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.session = None
        self.issues = []
        self.warnings = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/data_validation.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def _print_header(self):
        """Print validation header."""
        print("\n" + "="*80)
        print("🔍 SHARP AGENTS - DATA VALIDATION REPORT")
        print("="*80)
        print(f"Validation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    
    def _print_summary(self, total_issues: int, total_warnings: int):
        """Print validation summary."""
        print("\n" + "="*80)
        print("📊 VALIDATION SUMMARY")
        print("="*80)
        print(f"🔴 Total Issues: {total_issues}")
        print(f"🟡 Total Warnings: {total_warnings}")
        
        if total_issues == 0 and total_warnings == 0:
            print("✅ Database is healthy - no issues found!")
            print("🎯 Exit code: 0 (Success)")
        elif total_issues == 0:
            print("⚠️  Database has warnings but no critical issues")
            print("🎯 Exit code: 0 (Success)")
        else:
            print("❌ Database has critical issues that need attention")
            print("🎯 Exit code: 1 (Issues found)")
        
        print("="*80 + "\n")
    
    def initialize_database(self) -> bool:
        """Initialize database connection."""
        try:
            # Create database connection
            database_url = self.config.get_database_url()
            engine = create_engine(database_url, echo=False)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.session = SessionLocal()
            
            self.logger.info("Database connection established successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            self.issues.append(f"Database connection failed: {e}")
            return False
    
    def check_markets_exist(self) -> bool:
        """Check if database has markets."""
        try:
            market_count = self.session.query(Market).count()
            
            if market_count == 0:
                self.issues.append("No markets found in database")
                return False
            
            self.logger.info(f"Found {market_count} markets in database")
            
            # Check for markets with basic required fields
            valid_markets = self.session.query(Market).filter(
                and_(
                    Market.platform.isnot(None),
                    Market.market_id.isnot(None)
                )
            ).count()
            
            if valid_markets < market_count:
                self.warnings.append(f"{market_count - valid_markets} markets missing required fields")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking markets: {e}")
            self.issues.append(f"Error checking markets: {e}")
            return False
    
    def check_recent_prices(self) -> bool:
        """Check if prices are recent (< 10 minutes old)."""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=10)
            
            # Get markets with recent prices
            recent_prices = self.session.query(MarketPrice).filter(
                MarketPrice.timestamp >= cutoff_time
            ).count()
            
            # Get total price records
            total_prices = self.session.query(MarketPrice).count()
            
            if total_prices == 0:
                self.issues.append("No price data found in database")
                return False
            
            # Check percentage of recent prices
            recent_percentage = (recent_prices / total_prices) * 100 if total_prices > 0 else 0
            
            if recent_percentage < 50:
                self.issues.append(f"Only {recent_percentage:.1f}% of prices are recent (< 10 minutes old)")
                return False
            elif recent_percentage < 80:
                self.warnings.append(f"Only {recent_percentage:.1f}% of prices are recent (< 10 minutes old)")
            
            self.logger.info(f"Price freshness: {recent_percentage:.1f}% recent out of {total_prices} total")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking recent prices: {e}")
            self.issues.append(f"Error checking recent prices: {e}")
            return False
    
    def validate_price_data(self) -> bool:
        """Validate that price data makes sense."""
        try:
            # Get all price records with bid/ask data
            prices = self.session.query(MarketPrice).filter(
                and_(
                    MarketPrice.yes_bid.isnot(None),
                    MarketPrice.yes_ask.isnot(None),
                    MarketPrice.no_bid.isnot(None),
                    MarketPrice.no_ask.isnot(None)
                )
            ).all()
            
            if not prices:
                self.warnings.append("No price records with complete bid/ask data found")
                return True
            
            validation_issues = 0
            validation_warnings = 0
            
            for price in prices:
                # Check bid < ask
                if price.yes_bid >= price.yes_ask:
                    validation_issues += 1
                    self.issues.append(f"Market {price.market_id}: Yes bid ({price.yes_bid}) >= ask ({price.yes_ask})")
                
                if price.no_bid >= price.no_ask:
                    validation_issues += 1
                    self.issues.append(f"Market {price.market_id}: No bid ({price.no_bid}) >= ask ({price.no_ask})")
                
                # Check prices between 0 and 1
                for field, value in [('yes_bid', price.yes_bid), ('yes_ask', price.yes_ask), 
                                   ('no_bid', price.no_bid), ('no_ask', price.no_ask)]:
                    if value < 0 or value > 1:
                        validation_issues += 1
                        self.issues.append(f"Market {price.market_id}: {field} ({value}) outside valid range [0,1]")
                
                # Check Yes + No prices approximately sum to 1
                yes_mid = (price.yes_bid + price.yes_ask) / 2
                no_mid = (price.no_bid + price.no_ask) / 2
                total = yes_mid + no_mid
                
                if abs(total - 1.0) > 0.1:  # Allow 10% tolerance
                    validation_warnings += 1
                    self.warnings.append(f"Market {price.market_id}: Yes+No prices sum to {total:.3f} (expected ~1.0)")
                
                # Check spread reasonableness
                yes_spread = price.yes_ask - price.yes_bid
                no_spread = price.no_ask - price.no_bid
                
                if yes_spread > 0.2:  # 20% spread threshold
                    validation_warnings += 1
                    self.warnings.append(f"Market {price.market_id}: Large Yes spread ({yes_spread:.3f})")
                
                if no_spread > 0.2:
                    validation_warnings += 1
                    self.warnings.append(f"Market {price.market_id}: Large No spread ({no_spread:.3f})")
            
            self.logger.info(f"Price validation: {validation_issues} issues, {validation_warnings} warnings")
            return validation_issues == 0
            
        except Exception as e:
            self.logger.error(f"Error validating price data: {e}")
            self.issues.append(f"Error validating price data: {e}")
            return False
    
    def check_duplicate_markets(self) -> bool:
        """Check for duplicate markets."""
        try:
            # Check for duplicate platform + ticker combinations
            duplicates = self.session.query(
                Market.platform,
                Market.ticker,
                func.count(Market.id).label('count')
            ).filter(
                Market.ticker.isnot(None)
            ).group_by(
                Market.platform,
                Market.ticker
            ).having(
                func.count(Market.id) > 1
            ).all()
            
            if duplicates:
                for dup in duplicates:
                    self.issues.append(f"Duplicate market: {dup.platform}/{dup.ticker} appears {dup.count} times")
                return False
            
            # Check for duplicate market_ids within same platform
            market_id_duplicates = self.session.query(
                Market.platform,
                Market.market_id,
                func.count(Market.id).label('count')
            ).filter(
                Market.market_id.isnot(None)
            ).group_by(
                Market.platform,
                Market.market_id
            ).having(
                func.count(Market.id) > 1
            ).all()
            
            if market_id_duplicates:
                for dup in market_id_duplicates:
                    self.issues.append(f"Duplicate market_id: {dup.platform}/{dup.market_id} appears {dup.count} times")
                return False
            
            self.logger.info("No duplicate markets found")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking for duplicates: {e}")
            self.issues.append(f"Error checking for duplicates: {e}")
            return False
    
    def check_data_consistency(self) -> bool:
        """Check overall data consistency."""
        try:
            # Check for markets without prices
            markets_without_prices = self.session.query(Market).outerjoin(
                MarketPrice
            ).filter(
                MarketPrice.id.is_(None)
            ).count()
            
            if markets_without_prices > 0:
                self.warnings.append(f"{markets_without_prices} markets have no price data")
            
            # Check for orphaned price records
            orphaned_prices = self.session.query(MarketPrice).outerjoin(
                Market
            ).filter(
                Market.id.is_(None)
            ).count()
            
            if orphaned_prices > 0:
                self.issues.append(f"{orphaned_prices} price records reference non-existent markets")
            
            # Check for reasonable volume data
            high_volume_prices = self.session.query(MarketPrice).filter(
                MarketPrice.volume > 1000000  # $1M threshold
            ).count()
            
            if high_volume_prices > 0:
                self.warnings.append(f"{high_volume_prices} price records have unusually high volume (>$1M)")
            
            self.logger.info("Data consistency check completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking data consistency: {e}")
            self.issues.append(f"Error checking data consistency: {e}")
            return False
    
    def print_issues_report(self):
        """Print detailed issues report."""
        if not self.issues and not self.warnings:
            print("✅ No issues or warnings found!")
            return
        
        if self.issues:
            print("🔴 CRITICAL ISSUES:")
            print("-" * 40)
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")
            print()
        
        if self.warnings:
            print("🟡 WARNINGS:")
            print("-" * 40)
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {warning}")
            print()
    
    def run_validation(self) -> bool:
        """Run all validation checks."""
        try:
            self._print_header()
            
            # Initialize database
            if not self.initialize_database():
                return False
            
            print("🔍 Running validation checks...\n")
            
            # Run all validation checks
            checks = [
                ("Markets exist", self.check_markets_exist),
                ("Recent prices", self.check_recent_prices),
                ("Price data validation", self.validate_price_data),
                ("Duplicate markets", self.check_duplicate_markets),
                ("Data consistency", self.check_data_consistency)
            ]
            
            all_passed = True
            for check_name, check_func in checks:
                print(f"🔍 Checking: {check_name}...")
                try:
                    if check_func():
                        print(f"   ✅ {check_name}: PASSED")
                    else:
                        print(f"   ❌ {check_name}: FAILED")
                        all_passed = False
                except Exception as e:
                    print(f"   ❌ {check_name}: ERROR - {e}")
                    all_passed = False
                print()
            
            # Print issues report
            if self.issues or self.warnings:
                self.print_issues_report()
            
            # Print summary
            self._print_summary(len(self.issues), len(self.warnings))
            
            return all_passed and len(self.issues) == 0
            
        except Exception as e:
            self.logger.error(f"Validation failed with error: {e}")
            print(f"❌ Validation failed: {e}")
            return False
        finally:
            if self.session:
                self.session.close()


def main():
    """Main entry point for data validation."""
    print("🔍 Sharp Agents - Data Validation")
    print("Starting validation process...\n")
    
    # Create and run validator
    validator = DataValidator()
    success = validator.run_validation()
    
    # Exit with appropriate code
    if success:
        print("✅ Validation completed successfully!")
        sys.exit(0)
    else:
        print("❌ Validation found issues!")
        sys.exit(1)


if __name__ == "__main__":
    main()
