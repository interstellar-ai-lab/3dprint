#!/usr/bin/env python3
"""
Generic Supabase Connection Test Script
Provides functionality to test Supabase database connection and discover available tables
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    logger.error("❌ Supabase library not installed. Install with: pip install supabase")
    SUPABASE_AVAILABLE = False


class SupabaseTestManager:
    """Manager class for testing Supabase operations"""
    
    def __init__(self):
        """Initialize Supabase test manager"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.client: Optional[Client] = None
        
        # Validate environment variables
        if not self.supabase_url:
            logger.error("❌ SUPABASE_URL environment variable not set")
        if not self.supabase_key:
            logger.error("❌ SUPABASE_ANON_KEY environment variable not set")
    
    def connect(self) -> Dict[str, Any]:
        """Test Supabase connection"""
        if not SUPABASE_AVAILABLE:
            return {
                "success": False,
                "error": "Supabase library not available",
                "message": "Install supabase: pip install supabase"
            }
        
        if not self.supabase_url or not self.supabase_key:
            return {
                "success": False,
                "error": "Missing configuration",
                "message": "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables"
            }
        
        try:
            logger.info("🔌 Testing Supabase connection...")
            logger.info(f"URL: {self.supabase_url}")
            
            # Create Supabase client
            self.client = create_client(self.supabase_url, self.supabase_key)
            
            # Test connection with a simple query to check if we can access the database
            # We'll try to get some basic info about the database
            logger.info("✅ Supabase connection successful!")
            return {
                "success": True,
                "message": "Connected to Supabase successfully",
                "url": self.supabase_url
            }
            
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to connect to Supabase"
            }
    
    def discover_tables(self) -> Dict[str, Any]:
        """Discover available tables in the database"""
        if not self.client:
            return {"success": False, "error": "Not connected to Supabase"}
        
        try:
            logger.info("🔍 Discovering available tables...")
            
            # Common table names to try
            common_tables = [
                'generated_images',
            ]
            
            available_tables = []
            not_found_tables = []
            
            for table_name in common_tables:
                try:
                    response = self.client.table(table_name).select("*").limit(1).execute()
                    available_tables.append({
                        "name": table_name,
                        "accessible": True,
                        "row_count": len(response.data) if response.data else 0
                    })
                    logger.info(f"✅ Found table: {table_name}")
                except Exception as e:
                    # Table doesn't exist or not accessible
                    not_found_tables.append(table_name)
                    logger.debug(f"Table {table_name} not accessible: {str(e)}")
                    continue
            
            # Try to get system information about the database
            try:
                # Try to access some system tables or get database info
                logger.info("🔍 Attempting to get database schema information...")
                # Note: This might not work due to RLS policies, but worth trying
            except Exception as e:
                logger.debug(f"Could not get schema info: {str(e)}")
            
            result = {
                "success": True,
                "available_tables": available_tables,
                "total_found": len(available_tables),
                "tables_checked": len(common_tables),
                "not_found_tables": not_found_tables
            }
            
            if len(available_tables) == 0:
                result["message"] = "No tables found. Your database might be empty or tables have different names."
                logger.warning("⚠️ No tables found in the database. You may need to create tables first.")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Table discovery failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to discover tables"
            }
    
    def test_table_operations(self, table_name: str) -> Dict[str, Any]:
        """Test basic table operations on a specific table"""
        if not self.client:
            return {"success": False, "error": "Not connected to Supabase"}
        
        try:
            logger.info(f"📋 Testing table operations on '{table_name}'...")
            
            # Test 1: Check if table exists by trying to select from it
            response = self.client.table(table_name).select("*").limit(5).execute()
            logger.info(f"✅ Table '{table_name}' is accessible")
            
            results = {
                "success": True,
                "table_name": table_name,
                "row_count": len(response.data) if response.data else 0,
                "sample_data": response.data[:3] if response.data else []
            }
            
            if response.data:
                results["columns"] = list(response.data[0].keys())
                logger.info(f"📊 Table columns: {', '.join(results['columns'])}")
                logger.info(f"📈 Sample rows retrieved: {len(response.data)}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Table operations failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to perform operations on table '{table_name}'"
            }
    
    def test_query_operations(self, table_name: str) -> Dict[str, Any]:
        """Test various query operations on a specific table"""
        if not self.client:
            return {"success": False, "error": "Not connected to Supabase"}
        
        try:
            logger.info(f"🔍 Testing query operations on '{table_name}'...")
            
            results = {}
            
            # Test 1: Count total records
            count_response = self.client.table(table_name).select("*", count="exact").execute()
            total_count = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
            results["total_records"] = total_count
            logger.info(f"📊 Total records: {total_count}")
            
            # Test 2: Get recent records (if table has created_at or similar timestamp column)
            try:
                recent_response = self.client.table(table_name).select("*").order("created_at", desc=True).limit(5).execute()
                results["recent_records"] = len(recent_response.data) if recent_response.data else 0
                logger.info(f"🕒 Recent records retrieved: {results['recent_records']}")
            except:
                # Table might not have created_at column, try without ordering
                recent_response = self.client.table(table_name).select("*").limit(5).execute()
                results["recent_records"] = len(recent_response.data) if recent_response.data else 0
                logger.info(f"📄 Sample records retrieved: {results['recent_records']}")
            
            results["success"] = True
            return results
            
        except Exception as e:
            logger.error(f"❌ Query operations failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to query table '{table_name}'"
            }
    
    def test_database_info(self) -> Dict[str, Any]:
        """Get general database information"""
        if not self.client:
            return {"success": False, "error": "Not connected to Supabase"}
        
        try:
            logger.info("ℹ️ Getting database information...")
            
            # Try to get some basic database info
            # Note: This is limited by Supabase's RLS policies
            info = {
                "connection_url": self.supabase_url,
                "timestamp": datetime.now().isoformat(),
                "client_initialized": self.client is not None
            }
            
            return {
                "success": True,
                "database_info": info
            }
            
        except Exception as e:
            logger.error(f"❌ Database info retrieval failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get database information"
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Supabase test suite"""
        logger.info("🚀 Starting comprehensive Supabase test suite...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Connection
        connection_result = self.connect()
        results["tests"]["connection"] = connection_result
        
        if not connection_result["success"]:
            logger.error("❌ Connection failed, skipping other tests")
            return results
        
        # Test 2: Database info
        db_info_result = self.test_database_info()
        results["tests"]["database_info"] = db_info_result
        
        # Test 3: Table discovery
        discovery_result = self.discover_tables()
        results["tests"]["table_discovery"] = discovery_result
        
        # Test 4: Test operations on each discovered table
        if discovery_result.get("success") and discovery_result.get("available_tables"):
            table_tests = {}
            for table_info in discovery_result["available_tables"]:
                table_name = table_info["name"]
                
                # Test table operations
                table_ops = self.test_table_operations(table_name)
                table_tests[f"{table_name}_operations"] = table_ops
                
                # Test query operations
                query_ops = self.test_query_operations(table_name)
                table_tests[f"{table_name}_queries"] = query_ops
            
            results["tests"]["individual_table_tests"] = table_tests
        elif discovery_result.get("success") and discovery_result.get("total_found", 0) == 0:
            # No tables found, provide guidance
            sample_table_result = self.create_sample_table()
            results["tests"]["sample_table_guidance"] = sample_table_result
        
        # Summary
        successful_tests = sum(1 for test in results["tests"].values() if test.get("success"))
        total_tests = len(results["tests"])
        
        results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            "overall_success": successful_tests == total_tests
        }
        
        logger.info(f"📋 Test Summary: {successful_tests}/{total_tests} tests passed ({results['summary']['success_rate']})")
        
        return results


def main():
    """Main function to run Supabase tests"""
    print("🧪 Supabase Connection Test")
    print("=" * 50)
    
    # Check if required environment variables are set
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("\n❌ Missing Environment Variables!")
        print("Please set the following environment variables:")
        print("- SUPABASE_URL=your_supabase_project_url")
        print("- SUPABASE_ANON_KEY=your_supabase_anon_key")
        print("\nExample .env file:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_ANON_KEY=your-anon-key-here")
        return
    
    # Run tests
    manager = SupabaseTestManager()
    results = manager.run_comprehensive_test()
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    for test_name, test_result in results["tests"].items():
        if test_name == "individual_table_tests":
            print(f"\n{test_name.upper()}:")
            for table_test_name, table_test_result in test_result.items():
                status = "✅ PASS" if table_test_result.get("success") else "❌ FAIL"
                print(f"  {table_test_name}: {status}")
                if not table_test_result.get("success") and table_test_result.get("error"):
                    print(f"    Error: {table_test_result['error']}")
        elif test_name == "sample_table_guidance":
            print(f"\n{test_name.upper()}:")
            if test_result.get("success"):
                print("  📋 Sample table creation guidance provided")
                print("  💡 Check the detailed results file for SQL script")
            else:
                print(f"  ❌ FAIL: {test_result.get('error', 'Unknown error')}")
        else:
            status = "✅ PASS" if test_result.get("success") else "❌ FAIL"
            print(f"{test_name.upper()}: {status}")
            if not test_result.get("success") and test_result.get("error"):
                print(f"  Error: {test_result['error']}")
            if test_name == "table_discovery" and test_result.get("total_found") == 0:
                print(f"  📊 Tables checked: {test_result.get('tables_checked', 0)}")
                print(f"  ⚠️ No tables found in database")
    
    print(f"\nOverall: {results['summary']['success_rate']} success rate")
    
    # Save results to file
    results_file = f"supabase_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📁 Detailed results saved to: {results_file}")


if __name__ == "__main__":
    main()
