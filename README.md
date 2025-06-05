# LumiBox - Intelligent Gmail Backup & Search

<div align="center">
  <img src="assets/lumilogo.png" alt="LumiBox Logo" width="200"/>
</div>

A Python application that reads Gmail .mbox files (from Gmail backup/export) and stores email data with metadata in a PostgreSQL database. **LumiBox is evolving into an AI-powered email intelligence platform** with natural language search, conversation analysis, and privacy-first local processing.

## 🎯 Vision

Transform from a simple backup tool to a comprehensive email intelligence system:
- **Complete Gmail Backup**: Secure local storage with full fidelity
- **AI-Powered Search**: Natural language queries using local LLMs
- **Privacy-First**: All processing happens on your infrastructure
- **Actionable Insights**: Email analytics, summaries, and relationship mapping

## Features

### Current (v1.0)
- **Mbox File Processing**: Reads Gmail .mbox files and extracts email metadata
- **PostgreSQL Storage**: Stores emails with comprehensive metadata in PostgreSQL
- **Configuration Management**: Uses YAML configuration files and environment variables
- **Batch Processing**: Processes multiple .mbox files from a directory
- **Error Handling**: Robust error handling with detailed logging
- **Duplicate Prevention**: Prevents duplicate emails using message ID
- **Connection Pooling**: Efficient database connection management

### Coming Soon (AI-Powered Features)
- **🤖 Natural Language Search**: "Find emails about the contract negotiation with Acme Corp"
- **🧠 Intelligent Summaries**: AI-generated email thread summaries and insights
- **🔍 Semantic Search**: Find emails by meaning, not just keywords
- **📊 Email Analytics**: Communication patterns, relationship mapping, productivity insights
- **💬 Conversational Interface**: Chat with your email history using local LLMs
- **🔒 Privacy-First AI**: All AI processing happens locally on your machine

> See [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) for the complete feature development plan.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Git

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd LumiBox
   pip install -r requirements.txt
   ```

2. **Configure database**:
   ```bash
   # Create PostgreSQL database
   createdb gmail_mbox
   
   # Setup environment
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Process your Gmail backup**:
   ```bash
   python example_usage.py /path/to/your/mbox/files
   ```

### Next Steps
- 📖 Read the [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) to understand the AI features coming next
- 🚀 Follow the development progress for natural language email search
- 💡 Check the [Issues](https://github.com/yourusername/LumiBox/issues) to contribute or suggest features

---

## Detailed Documentation

## Project Structure

```
LumiBox/
├── src/
│   └── mbox_processor.py      # Main MboxProcessor class
├── config/
│   └── database.yaml          # Database and processing configuration
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── example_usage.py          # Example usage script
├── PROJECT_ROADMAP.md        # 🚀 Complete development roadmap and AI features plan
└── README.md                 # This file
```

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd LumiBox
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**:
   - Install PostgreSQL if not already installed
   - Create a database for storing emails:
     ```sql
     CREATE DATABASE gmail_mbox;
     ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file with your database credentials:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=gmail_mbox
   DB_USER=your_username
   DB_PASSWORD=your_password
   LOG_LEVEL=INFO
   ```

## Getting Your Gmail Data

To export .mbox files from Gmail:

1. Go to [Google Takeout](https://takeout.google.com/)
2. Select "Mail" 
3. Choose "Include all messages in Mail"
4. Select format as "mbox"
5. Download and extract the archive
6. Use the extracted .mbox files with LumiBox

## Technical Details

### Current Email Metadata Extraction

The processor extracts comprehensive metadata from each email:

- **Headers**: All email headers including custom Gmail headers
- **Content**: Both plain text and HTML versions
- **Attachments**: Count and metadata (content can be stored)
- **Gmail Labels**: Extracted from X-Gmail-Labels header
- **Thread Information**: Gmail thread IDs
- **Dates**: Both original send date and processing timestamp

### Future AI-Powered Features

#### 🧠 Intelligent Search Capabilities
- **Natural Language Queries**: "Show me emails about budget discussions from Q4"
- **Semantic Understanding**: Find emails by meaning, not just keywords
- **Context-Aware Results**: Understanding email threads and relationships
- **Multi-Modal Search**: Search by content, attachments, dates, and relationships

#### 🤖 AI Analysis & Insights
- **Thread Summarization**: AI-generated summaries of long email conversations
- **Action Item Extraction**: Automatically identify tasks and deadlines
- **Sentiment Analysis**: Understand the tone and urgency of communications
- **Relationship Mapping**: Visualize communication patterns and networks

#### 🔒 Privacy-First AI
- **Local Processing**: All AI operations happen on your machine
- **No Data Transmission**: Emails never leave your infrastructure
- **Offline Capable**: Works without internet connection
- **Open Source Models**: Use local LLMs like Llama, Mistral, etc.

### Database Schema

The application automatically creates the following tables:

### `emails` table
- `id`: Primary key (auto-increment)
- `message_id`: Unique email message ID
- `subject`: Email subject
- `sender`: Sender email address
- `recipient`: Recipient email addresses
- `date_sent`: Original send date
- `date_received`: Processing timestamp
- `body_text`: Plain text body
- `body_html`: HTML body
- `attachments_count`: Number of attachments
- `labels`: Gmail labels (array)
- `thread_id`: Gmail thread ID
- `raw_headers`: All email headers (JSON)
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

### `attachments` table
- `id`: Primary key (auto-increment)
- `email_id`: Foreign key to emails table
- `filename`: Attachment filename
- `content_type`: MIME type
- `size_bytes`: File size
- `content`: Binary content
- `created_at`: Record creation timestamp

## Current Usage (v1.0)

### Basic Usage

1. **Using the example script**:
   ```bash
   python example_usage.py /path/to/mbox/files
   ```

2. **Using the MboxProcessor class directly**:
   ```python
   from src.mbox_processor import MboxProcessor
   
   # Initialize processor
   processor = MboxProcessor()
   
   # Process a single .mbox file
   stats = processor.process_mbox_file('/path/to/file.mbox')
   print(f"Processed {stats['processed_emails']} emails")
   
   # Process all .mbox files in a directory
   stats = processor.process_mbox_directory('/path/to/mbox/directory')
   print(f"Processed {stats['processed_emails']} total emails")
   
   # Always close when done
   processor.close()
   ```

### Command Line Usage

```bash
# Process a single .mbox file
python src/mbox_processor.py /path/to/file.mbox

# Process all .mbox files in a directory
python src/mbox_processor.py /path/to/mbox/directory

# Using the example script (interactive)
python example_usage.py

# Using the example script with path argument
python example_usage.py /path/to/mbox/files
```

---

## Technical Details

## Configuration

### Environment Variables (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | localhost |
| `DB_PORT` | PostgreSQL port | 5432 |
| `DB_NAME` | Database name | gmail_mbox |
| `DB_USER` | Database username | - |
| `DB_PASSWORD` | Database password | - |
| `LOG_LEVEL` | Logging level | INFO |

### YAML Configuration (config/database.yaml)

The YAML configuration file contains:

- **Database connection pool settings**
- **Table schemas**
- **Processing batch size**
- **Retry configuration**
- **Logging format**

You can modify these settings as needed for your environment.

## Gmail Export Instructions

To get .mbox files from Gmail:

1. Go to [Google Takeout](https://takeout.google.com/)
2. Select "Mail" 
3. Choose "Include all messages in Mail"
4. Select format as "mbox"
5. Download and extract the archive
6. Use the extracted .mbox files with this application

## 🚀 What's Next: AI-Powered Email Intelligence

LumiBox is evolving beyond simple backup to become a comprehensive email intelligence platform:

### Phase 1: Smart Search (Next 2-4 weeks)
- Vector database integration for semantic search
- Natural language query processing
- Local LLM integration with Ollama

### Phase 2: Agentic RAG (Weeks 3-6)
- Context-aware email search
- Conversation thread analysis
- AI-powered email summaries

### Phase 3: Advanced Analytics (Weeks 7-10)
- Communication pattern analysis
- Relationship mapping
- Productivity insights

**Get Involved**: 
- 📋 Check [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) for detailed plans
- 🐛 Report issues or suggest features
- 💻 Contribute to the AI integration development

---

## Current Usage (v1.0)

### Email Metadata Extraction

The processor extracts comprehensive metadata from each email:

- **Headers**: All email headers including custom Gmail headers
- **Content**: Both plain text and HTML versions
- **Attachments**: Count and metadata (content can be stored)
- **Gmail Labels**: Extracted from X-Gmail-Labels header
- **Thread Information**: Gmail thread IDs
- **Dates**: Both original send date and processing timestamp

### Error Handling

- **Duplicate Prevention**: Uses message ID to prevent duplicates
- **Encoding Handling**: Properly decodes various character encodings
- **Malformed Emails**: Gracefully handles corrupted or malformed emails
- **Database Errors**: Comprehensive error handling with rollback
- **Logging**: Detailed logging for debugging and monitoring

### Performance Features

- **Connection Pooling**: Efficient database connection management
- **Batch Processing**: Configurable batch sizes for large datasets
- **Progress Tracking**: Regular progress updates during processing
- **Memory Efficient**: Processes emails one at a time to manage memory

## Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. **Permission Errors**:
   - Check file permissions on .mbox files
   - Ensure database user has necessary privileges

3. **Memory Issues with Large Files**:
   - Reduce batch size in `config/database.yaml`
   - Process files individually instead of entire directories

4. **Encoding Errors**:
   - The processor handles most encoding issues automatically
   - Check logs for specific encoding problems

### Logging

The application provides detailed logging. To increase verbosity:

```env
LOG_LEVEL=DEBUG
```

Logs include:
- Processing progress
- Error details
- Database operations
- Performance metrics

## Dependencies

- `psycopg2-binary`: PostgreSQL adapter
- `python-dotenv`: Environment variable management
- `PyYAML`: YAML configuration parsing
- `email-validator`: Email validation utilities

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🎯 Project Evolution

**From Simple Backup → Intelligent Email Platform**

LumiBox started as a Gmail backup tool but is evolving into something much more powerful:

- **Phase 1 (Current)**: Reliable Gmail backup and storage ✅
- **Phase 2 (Next)**: AI-powered search and natural language queries 🚀
- **Phase 3 (Future)**: Complete email intelligence platform with analytics 🔮

**Why This Matters:**
- **Privacy Control**: Your email data stays on your infrastructure
- **AI Without Compromise**: Get AI benefits while maintaining privacy
- **Future-Proof**: Own your data as AI capabilities continue to evolve
- **Open Source**: Transparent, auditable, and extensible

**Join the Journey**: Star ⭐ this repo and watch for updates as we build the future of private email intelligence!

---

*💡 Have ideas for AI features? Check out [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) and join the discussion!*

## Contributing & Development

### Current Focus
We're actively developing AI-powered features! Priority areas:

1. **Vector Search Implementation**: Help integrate ChromaDB or Qdrant
2. **LLM Integration**: Ollama setup and local model management
3. **RAG Pipeline**: Context-aware search and retrieval
4. **Web UI Development**: React-based search interface

### How to Contribute

1. Fork the repository
2. Create a feature branch
3. Check [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) for current priorities
4. Make your changes and add tests
5. Submit a pull request

### Development Setup

```bash
# Clone and setup development environment
git clone <your-fork-url>
cd LumiBox
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Coming soon

# Run tests
python -m pytest tests/  # Coming soon

# Start development server (future web UI)
npm run dev  # Coming soon
```

## Roadmap & Vision

🎯 **See [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md)** for:
- Detailed feature development timeline
- Technical architecture plans  
- AI integration roadmap
- Success metrics and milestones

## Support & Community

For questions, issues, or contributions:
- 📋 [GitHub Issues](https://github.com/yourusername/LumiBox/issues) - Bug reports and feature requests
- 💬 [Discussions](https://github.com/yourusername/LumiBox/discussions) - General questions and ideas
- 📧 Email: [your-email] - Direct contact for sensitive issues
- 📖 [Wiki](https://github.com/yourusername/LumiBox/wiki) - Extended documentation and guides
