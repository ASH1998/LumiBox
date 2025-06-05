#!/usr/bin/env python3
"""
Test script to validate the setup and configuration.
This script checks if all dependencies are installed and configuration is valid.
"""

import os
import sys
import yaml
from dotenv import load_dotenv


def test_dependencies():
    """Test if all required dependencies are available."""
    print("Testing dependencies...")
    
    try:
        import psycopg2
        print("✓ psycopg2 is available")
    except ImportError:
        print("✗ psycopg2 is not installed")
        return False
    
    try:
        import yaml
        print("✓ PyYAML is available")
    except ImportError:
        print("✗ PyYAML is not installed")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv is available")
    except ImportError:
        print("✗ python-dotenv is not installed")
        return False
    
    try:
        import email
        print("✓ email module is available")
    except ImportError:
        print("✗ email module is not available")
        return False
    
    try:
        import mailbox
        print("✓ mailbox module is available")
    except ImportError:
        print("✗ mailbox module is not available")
        return False
    
    return True


def test_configuration():
    """Test if configuration files are present and valid."""
    print("\nTesting configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("✗ .env file not found")
        print("  Please copy .env.example to .env and configure your database credentials")
        return False
    else:
        print("✓ .env file found")
    
    # Load and validate environment variables
    load_dotenv()
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✓ {var} is set")
    
    if missing_vars:
        print(f"✗ Missing required environment variables: {missing_vars}")
        return False
    
    # Check YAML configuration
    config_path = 'config/database.yaml'
    if not os.path.exists(config_path):
        print(f"✗ Configuration file not found: {config_path}")
        return False
    else:
        print(f"✓ Configuration file found: {config_path}")
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        print("✓ YAML configuration is valid")
        
        # Check required configuration sections
        required_sections = ['database', 'processing', 'logging']
        for section in required_sections:
            if section in config:
                print(f"✓ Configuration section '{section}' found")
            else:
                print(f"✗ Configuration section '{section}' missing")
                return False
                
    except yaml.YAMLError as e:
        print(f"✗ YAML configuration error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading configuration: {e}")
        return False
    
    return True


def test_database_connection():
    """Test database connection."""
    print("\nTesting database connection...")
    
    try:
        import psycopg2
        
        # Load environment variables
        load_dotenv()
        
        db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        # Test connection
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f"✓ Database connection successful")
        print(f"  PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        print("  Please check your database credentials and ensure PostgreSQL is running")
        return False
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return False


def test_mbox_processor():
    """Test if MboxProcessor can be imported and initialized."""
    print("\nTesting MboxProcessor...")
    
    try:
        from src.mbox_processor import MboxProcessor
        print("✓ MboxProcessor can be imported")
        
        # Try to initialize (this will test configuration loading)
        processor = MboxProcessor()
        print("✓ MboxProcessor can be initialized")
        
        # Close the processor
        processor.close()
        print("✓ MboxProcessor can be closed properly")
        
        return True
        
    except Exception as e:
        print(f"✗ MboxProcessor test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("GMAIL MBOX PROCESSOR SETUP TEST")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("MboxProcessor", test_mbox_processor)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready to use.")
        print("\nNext steps:")
        print("1. Get your Gmail .mbox files from Google Takeout")
        print("2. Run: python example_usage.py /path/to/mbox/files")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
