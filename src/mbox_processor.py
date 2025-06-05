import os
import sys
import logging
import mailbox
import email
import json
import yaml
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from email.utils import parsedate_tz, mktime_tz
from email.header import decode_header
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv
import argparse


class MboxProcessor:
    """
    A class to process Gmail .mbox files and store emails in PostgreSQL database.
    """
    
    def __init__(self, config_path: str = "config/database.yaml", 
                 start_date: Optional[datetime] = None, 
                 end_date: Optional[datetime] = None,
                 show_sample: bool = False):
        """
        Initialize the MboxProcessor with configuration.
        
        Args:
            config_path (str): Path to the YAML configuration file
            start_date (Optional[datetime]): Start date for filtering emails
            end_date (Optional[datetime]): End date for filtering emails
            show_sample (bool): If True, only show sample emails without processing
        """        # Load environment variables
        load_dotenv()
        
        # Store filtering parameters
        self.start_date = start_date
        self.end_date = end_date
        self.show_sample = show_sample
        
        # Get database schema from environment
        self.db_schema = os.getenv('DB_SCHEMA', 'public')
        
        # Load configuration
        self.config = self._load_config(config_path)
          # Setup logging
        self._setup_logging()
        
        # Initialize database connection pool (skip if showing samples)
        self.connection_pool = None
        if not self.show_sample:
            self._init_database_pool()
            self._init_database_schema()
        
        self.logger.info(f"MboxProcessor initialized - Sample mode: {self.show_sample}, "
                        f"Date range: {start_date} to {end_date}, Schema: {self.db_schema}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_format = self.config['logging']['format']
        date_format = self.config['logging']['date_format']
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            datefmt=date_format
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _init_database_pool(self):
        """Initialize PostgreSQL connection pool."""
        try:
            db_config = {
                'host': os.getenv('DB_HOST'),
                'port': os.getenv('DB_PORT'),
                'database': os.getenv('DB_NAME'),
                'user': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD')            }
            
            # Validate required environment variables
            missing_vars = [key for key, value in db_config.items() if not value]
            if missing_vars:
                raise ValueError(f"Missing required environment variables: {missing_vars}")
            
            pool_config = self.config['database']['connection_pool']
            
            self.connection_pool = SimpleConnectionPool(
                minconn=pool_config['min_connections'],
                maxconn=pool_config['max_connections'],
                **db_config
            )
            
            self.logger.info("Database connection pool initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    def _init_database_schema(self):
        """Initialize database tables."""
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            # Create emails table
            emails_schema = self.config['database']['tables']['emails']['schema']
            emails_schema_formatted = emails_schema.format(schema=self.db_schema)
            cursor.execute(emails_schema_formatted)
            
            # Create attachments table
            attachments_schema = self.config['database']['tables']['attachments']['schema']
            attachments_schema_formatted = attachments_schema.format(schema=self.db_schema)
            cursor.execute(attachments_schema_formatted)
            
            conn.commit()
            self.logger.info(f"Database schema initialized in schema: {self.db_schema}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database schema: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.connection_pool.putconn(conn)
    
    def _decode_header_value(self, header_value: str) -> str:
        """Decode email header value."""
        if not header_value:
            return ""
        
        decoded_parts = decode_header(header_value)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_string += part.decode(encoding)
                    except (UnicodeDecodeError, LookupError):
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += str(part)
        
        return decoded_string.strip()
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse email date string to datetime object."""
        if not date_string:
            return None
        
        try:
            parsed_date = parsedate_tz(date_string)
            if parsed_date:
                timestamp = mktime_tz(parsed_date)
                return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError, OverflowError):
            self.logger.warning(f"Failed to parse date: {date_string}")
        
        return None
    
    def _extract_email_metadata(self, message: email.message.Message) -> Dict[str, Any]:
        """Extract metadata from email message."""
        metadata = {
            'message_id': self._decode_header_value(message.get('Message-ID', '')),
            'subject': self._decode_header_value(message.get('Subject', '')),
            'sender': self._decode_header_value(message.get('From', '')),
            'recipient': self._decode_header_value(message.get('To', '')),
            'date_sent': self._parse_date(message.get('Date')),
            'thread_id': self._decode_header_value(message.get('X-GM-THRID', '')),
            'labels': [],
            'body_text': '',
            'body_html': '',
            'attachments_count': 0,
            'raw_headers': {}
        }
        
        # Extract Gmail labels if present
        labels_header = message.get('X-Gmail-Labels')
        if labels_header:
            metadata['labels'] = [label.strip() for label in labels_header.split(',')]
        
        # Extract raw headers
        for key, value in message.items():
            metadata['raw_headers'][key] = self._decode_header_value(value)
        
        # Extract body content
        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                if content_type == 'text/plain' and 'attachment' not in content_disposition:
                    try:
                        metadata['body_text'] = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
                elif content_type == 'text/html' and 'attachment' not in content_disposition:
                    try:
                        metadata['body_html'] = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
                elif 'attachment' in content_disposition:
                    metadata['attachments_count'] += 1
        else:
            content_type = message.get_content_type()
            if content_type == 'text/plain':
                try:
                    metadata['body_text'] = message.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
            elif content_type == 'text/html':
                try:
                    metadata['body_html'] = message.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
        
        return metadata
    
    def _is_email_in_date_range(self, email_date: Optional[datetime]) -> bool:
        """Check if email date falls within the specified date range."""
        if not email_date:
            return True  # Include emails without dates if no filter is set
        
        if self.start_date and email_date < self.start_date:
            return False
        
        if self.end_date and email_date > self.end_date:
            return False
        
        return True
    
    def _print_sample_email(self, email_data: Dict[str, Any], index: int):
        """Print a sample email for preview."""
        print(f"\n--- Email #{index} ---")
        print(f"Message ID: {email_data['message_id']}")
        print(f"Subject: {email_data['subject']}")
        print(f"From: {email_data['sender']}")
        print(f"To: {email_data['recipient']}")
        print(f"Date: {email_data['date_sent']}")
        print(f"Labels: {email_data['labels']}")
        print(f"Attachments: {email_data['attachments_count']}")
        print(f"Body (first 200 chars): {email_data['body_text'][:200]}...")
        print("-" * 50)
    
    def _save_email_to_db(self, email_data: Dict[str, Any]) -> Optional[int]:
        """Save email data to PostgreSQL database."""
        try:
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            insert_query = f"""
                INSERT INTO {self.db_schema}.emails (
                    message_id, subject, sender, recipient, date_sent, 
                    body_text, body_html, attachments_count, labels, 
                    thread_id, raw_headers, date_received
                ) VALUES (
                    %(message_id)s, %(subject)s, %(sender)s, %(recipient)s, %(date_sent)s,
                    %(body_text)s, %(body_html)s, %(attachments_count)s, %(labels)s,
                    %(thread_id)s, %(raw_headers)s, %(date_received)s
                ) ON CONFLICT (message_id) DO UPDATE SET
                    subject = EXCLUDED.subject,
                    sender = EXCLUDED.sender,
                    recipient = EXCLUDED.recipient,
                    date_sent = EXCLUDED.date_sent,
                    body_text = EXCLUDED.body_text,
                    body_html = EXCLUDED.body_html,
                    attachments_count = EXCLUDED.attachments_count,
                    labels = EXCLUDED.labels,
                    thread_id = EXCLUDED.thread_id,
                    raw_headers = EXCLUDED.raw_headers,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
            """
            
            email_data['date_received'] = datetime.now()
            email_data['raw_headers'] = json.dumps(email_data['raw_headers'])
            
            cursor.execute(insert_query, email_data)
            result = cursor.fetchone()
            email_id = result[0] if result else None
            
            conn.commit()
            return email_id
            
        except psycopg2.IntegrityError as e:
            self.logger.warning(f"Email already exists: {email_data.get('message_id')}")
            conn.rollback()
            return None
        except Exception as e:
            self.logger.error(f"Failed to save email to database: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.connection_pool.putconn(conn)
    
    def process_mbox_file(self, mbox_path: str) -> Dict[str, int]:
        """
        Process a single .mbox file and save emails to database or show samples.
        
        Args:
            mbox_path (str): Path to the .mbox file
            
        Returns:
            Dict[str, int]: Statistics about processed emails
        """
        if not os.path.exists(mbox_path):
            raise FileNotFoundError(f"Mbox file not found: {mbox_path}")
        
        stats = {
            'total_emails': 0,
            'processed_emails': 0,
            'skipped_emails': 0,
            'failed_emails': 0,
            'filtered_by_date': 0
        }
        
        self.logger.info(f"Processing mbox file: {mbox_path}")
        
        if self.show_sample:
            print(f"\n=== SAMPLE EMAILS FROM: {mbox_path} ===")
            if self.start_date or self.end_date:
                print(f"Date filter: {self.start_date} to {self.end_date}")
        
        try:
            mbox = mailbox.mbox(mbox_path)
            batch_size = self.config['processing']['batch_size']
            batch_count = 0
            sample_count = 0
            max_samples = 5  # Show maximum 5 sample emails
            
            for message in mbox:
                stats['total_emails'] += 1
                
                try:
                    # Extract email metadata
                    email_data = self._extract_email_metadata(message)
                    
                    # Skip emails without message ID
                    if not email_data['message_id']:
                        stats['skipped_emails'] += 1
                        continue
                    
                    # Check date range filter
                    if not self._is_email_in_date_range(email_data['date_sent']):
                        stats['filtered_by_date'] += 1
                        continue
                    
                    if self.show_sample:
                        # Show sample emails
                        if sample_count < max_samples:
                            self._print_sample_email(email_data, sample_count + 1)
                            sample_count += 1
                        stats['processed_emails'] += 1
                    else:
                        # Save to database
                        email_id = self._save_email_to_db(email_data)
                        
                        if email_id:
                            stats['processed_emails'] += 1
                        else:
                            stats['skipped_emails'] += 1
                    
                    batch_count += 1
                    
                    # Log progress (only when not showing samples)
                    if not self.show_sample and batch_count % batch_size == 0:
                        self.logger.info(f"Processed {batch_count} emails from {mbox_path}")
                
                except Exception as e:
                    self.logger.error(f"Failed to process email: {e}")
                    stats['failed_emails'] += 1
                    continue
            
            if self.show_sample:
                print(f"\n=== SAMPLE COMPLETE ===")
                print(f"Total emails in file: {stats['total_emails']}")
                print(f"Emails in date range: {stats['processed_emails']}")
                print(f"Filtered by date: {stats['filtered_by_date']}")
                print(f"Sample emails shown: {min(sample_count, max_samples)}")
            else:
                self.logger.info(f"Completed processing {mbox_path}: {stats}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to process mbox file {mbox_path}: {e}")
            raise
    
    def process_mbox_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Process all .mbox files in a directory.
        
        Args:
            directory_path (str): Path to directory containing .mbox files
            
        Returns:
            Dict[str, Any]: Overall statistics and per-file results
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not os.path.isdir(directory_path):
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        # Find all .mbox files
        mbox_files = [f for f in os.listdir(directory_path) if f.endswith('.mbox')]
        
        if not mbox_files:
            self.logger.warning(f"No .mbox files found in directory: {directory_path}")
            return {'total_files': 0, 'results': {}}
        
        self.logger.info(f"Found {len(mbox_files)} .mbox files in {directory_path}")
        
        overall_stats = {
            'total_files': len(mbox_files),
            'processed_files': 0,
            'failed_files': 0,
            'total_emails': 0,
            'processed_emails': 0,
            'skipped_emails': 0,
            'failed_emails': 0,
            'filtered_by_date': 0,
            'results': {}
        }
        
        for mbox_file in mbox_files:
            mbox_path = os.path.join(directory_path, mbox_file)
            
            try:
                file_stats = self.process_mbox_file(mbox_path)
                overall_stats['results'][mbox_file] = file_stats
                overall_stats['processed_files'] += 1
                
                # Aggregate stats
                for key in ['total_emails', 'processed_emails', 'skipped_emails', 'failed_emails', 'filtered_by_date']:
                    overall_stats[key] += file_stats[key]
                    
            except Exception as e:
                self.logger.error(f"Failed to process file {mbox_file}: {e}")
                overall_stats['failed_files'] += 1
                overall_stats['results'][mbox_file] = {'error': str(e)}
        
        self.logger.info(f"Directory processing completed: {overall_stats}")
        return overall_stats
    
    def close(self):
        """Close database connections."""
        if self.connection_pool:
            self.connection_pool.closeall()
            self.logger.info("Database connections closed")


def parse_date(date_string: str) -> datetime:
    """Parse date string in various formats."""
    formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date: {date_string}. Use format YYYY-MM-DD")


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description='Process Gmail .mbox files and store emails in PostgreSQL database.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all emails in a file
  python mbox_processor.py /path/to/emails.mbox

  # Process emails from a specific date range
  python mbox_processor.py /path/to/emails.mbox --start-date 2024-01-01 --end-date 2024-12-31

  # Show sample emails without saving to database
  python mbox_processor.py /path/to/emails.mbox --sample

  # Show samples with date filtering
  python mbox_processor.py /path/to/emails.mbox --sample --start-date 2024-06-01
        """
    )
    
    parser.add_argument('path', help='Path to .mbox file or directory containing .mbox files')
    parser.add_argument('--start-date', '-s', type=str, 
                       help='Start date for filtering emails (YYYY-MM-DD)')
    parser.add_argument('--end-date', '-e', type=str,
                       help='End date for filtering emails (YYYY-MM-DD)')
    parser.add_argument('--sample', action='store_true',
                       help='Show sample emails without processing/saving to database')
    parser.add_argument('--config', '-c', default='config/database.yaml',
                       help='Path to configuration file (default: config/database.yaml)')
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = None
    end_date = None
    
    if args.start_date:
        try:
            start_date = parse_date(args.start_date)
        except ValueError as e:
            print(f"Error parsing start date: {e}")
            sys.exit(1)
    
    if args.end_date:
        try:
            end_date = parse_date(args.end_date)
        except ValueError as e:
            print(f"Error parsing end date: {e}")
            sys.exit(1)
    
    # Validate date range
    if start_date and end_date and start_date > end_date:
        print("Error: Start date must be before end date")
        sys.exit(1)
    
    try:
        processor = MboxProcessor(
            config_path=args.config,
            start_date=start_date,
            end_date=end_date,
            show_sample=args.sample
        )
        
        if os.path.isfile(args.path) and args.path.endswith('.mbox'):
            # Process single file
            stats = processor.process_mbox_file(args.path)
            if not args.sample:
                print(f"Processing completed: {stats}")
        elif os.path.isdir(args.path):
            # Process directory
            stats = processor.process_mbox_directory(args.path)
            if not args.sample:
                print(f"Directory processing completed: {stats}")
        else:
            print("Error: Path must be either a .mbox file or a directory containing .mbox files")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'processor' in locals():
            processor.close()


if __name__ == "__main__":
    main()
