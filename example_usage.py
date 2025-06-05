#!/usr/bin/env python3
"""
Example usage of the MboxProcessor class.
This script demonstrates how to use the MboxProcessor to process Gmail .mbox files.
"""

import os
import sys
from src.mbox_processor import MboxProcessor


def main():
    """Main function to demonstrate MboxProcessor usage."""
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("Error: .env file not found!")
        print("Please create a .env file based on .env.example with your database credentials.")
        print("Example:")
        print("  cp .env.example .env")
        print("  # Then edit .env with your actual database credentials")
        return 1
    
    # Get path from command line argument or prompt user
    if len(sys.argv) > 1:
        mbox_path = sys.argv[1]
    else:
        mbox_path = input("Enter path to .mbox file or directory containing .mbox files: ").strip()
    
    if not mbox_path:
        print("Error: No path provided!")
        return 1
    
    if not os.path.exists(mbox_path):
        print(f"Error: Path does not exist: {mbox_path}")
        return 1
    
    try:
        # Initialize the processor
        print("Initializing MboxProcessor...")
        processor = MboxProcessor()
        
        # Process the mbox file(s)
        if os.path.isfile(mbox_path) and mbox_path.endswith('.mbox'):
            print(f"Processing single mbox file: {mbox_path}")
            stats = processor.process_mbox_file(mbox_path)
            
            print("\n" + "="*50)
            print("PROCESSING RESULTS")
            print("="*50)
            print(f"Total emails found: {stats['total_emails']}")
            print(f"Successfully processed: {stats['processed_emails']}")
            print(f"Skipped emails: {stats['skipped_emails']}")
            print(f"Failed emails: {stats['failed_emails']}")
            
        elif os.path.isdir(mbox_path):
            print(f"Processing directory: {mbox_path}")
            stats = processor.process_mbox_directory(mbox_path)
            
            print("\n" + "="*50)
            print("PROCESSING RESULTS")
            print("="*50)
            print(f"Total .mbox files found: {stats['total_files']}")
            print(f"Successfully processed files: {stats['processed_files']}")
            print(f"Failed files: {stats['failed_files']}")
            print(f"Total emails found: {stats['total_emails']}")
            print(f"Successfully processed emails: {stats['processed_emails']}")
            print(f"Skipped emails: {stats['skipped_emails']}")
            print(f"Failed emails: {stats['failed_emails']}")
            
            if stats['results']:
                print("\nPer-file results:")
                for filename, file_stats in stats['results'].items():
                    if 'error' in file_stats:
                        print(f"  {filename}: ERROR - {file_stats['error']}")
                    else:
                        print(f"  {filename}: {file_stats['processed_emails']}/{file_stats['total_emails']} emails processed")
        
        else:
            print("Error: Path must be either a .mbox file or a directory containing .mbox files")
            return 1
        
        print("\nProcessing completed successfully!")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        return 1
    
    finally:
        # Always close the processor
        try:
            processor.close()
        except:
            pass
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
