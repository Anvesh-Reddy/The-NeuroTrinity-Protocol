# The NeuroTrinity Protocol

A multi-agent AI system that combines specialized agents (Architect, Alchemist, Trainer) with internet search and RAG capabilities to provide comprehensive health and wellness recommendations.

## Features

- **Multi-Agent Architecture**: Three specialist agents analyze requests from different perspectives
- **Internet Search Integration**: Real-time web data retrieval using DuckDuckGo
- **RAG (Retrieval-Augmented Generation)**: Load and embed user documents for personalized recommendations
- **Conversation Memory**: Maintains chat history for context-aware responses
- **Structured Output**: JSON-based responses with prioritized actions

## Project Structure

```
The-NeuroTrinity-Protocol/
├── main.py                 # Main application with chat interface
├── data_models.py          # Pydantic models for structured outputs
├── agent_prompts.py        # System prompts for each specialist agent
├── keys.env               # Environment variables (create this file)
└── README.md              # This file
```

## Installation

### Prerequisites
- Python 3.8+
- Google Gemini API key

### Setup Steps

1. **Clone/Navigate to project directory**
   ```bash
   cd The-NeuroTrinity-Protocol
   ```

2. **Create virtual environment**
   ```bash
   python -m venv neuroenv
   source neuroenv/bin/activate  # On Windows: neuroenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install google-genai python-dotenv duckduckgo-search numpy chardet
   ```

4. **Set up environment variables**
   Create a `keys.env` file in the project root:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

### Running the Application

```bash
python main.py
```

### Interactive Commands

Once the app is running, you can use these commands:

- **Normal Query**: Type your health/wellness question
  ```
  You: I woke up groggy, what should I do?
  Health Data: Blood pressure 145/95 mmHg
  ```

- **Load Documents**: Load user documents for RAG
  ```
  You: load path/to/your/documents.txt
  ```

- **View History**: See previous conversations
  ```
  You: history
  ```

- **Exit**: Quit the application
  ```
  You: quit
  ```

## How It Works

### Protocol Flow

1. **User Input**: Accepts health/wellness query and optional health data
2. **Internet Search**: Retrieves relevant web data for the query
3. **RAG Retrieval**: Fetches relevant user documents from embedded database
4. **Specialist Analysis**: 
   - **Architect**: Strategic planning and structure
   - **Alchemist**: Transformation and optimization
   - **Trainer**: Implementation and execution
5. **Concierge Synthesis**: Combines all recommendations into prioritized action plan
6. **Memory Update**: Stores conversation for future context

### Agent Roles

- **The Architect**: Designs comprehensive strategies and frameworks
- **The Alchemist**: Transforms insights into practical solutions
- **The Trainer**: Creates actionable implementation plans
- **Prime Concierge**: Synthesizes all recommendations into cohesive plan

## RAG Database

### Loading Documents

Documents should be in plain text format, separated by double newlines:

```
Document 1 content here

Document 2 content here

Document 3 content here
```

Supported encodings: UTF-8, Latin-1, CP1252, ISO-8859-1 (auto-detected)

### How RAG Works

1. Documents are embedded using Gemini's embedding model
2. Query is embedded and compared using cosine similarity
3. Top-3 relevant documents are retrieved
4. Retrieved documents are passed to all specialist agents

## API Requirements

- **Gemini API**: For LLM calls and embeddings
- **DuckDuckGo API**: For internet search (free, no key required)

## Output Format

Each response includes:

```
Executive Summary: [High-level overview]

1. [PRIORITY_LEVEL] [Action]
   Agent: [Agent Name] | Domain: [Category]
   Rationale: [Explanation]
```

Priority levels: HIGH, MEDIUM, LOW

## Troubleshooting

### Encoding Error
If you get encoding errors when loading documents, ensure the file is in a supported format (UTF-8, Latin-1, etc.)

### API Key Error
Verify `GEMINI_API_KEY` is set in `keys.env`

### Search Unavailable
DuckDuckGo search requires internet connection. The app will continue without search if unavailable.

### No Documents in RAG
Load documents using `load <file_path>` command before querying

## Performance Notes

- First query may take longer due to embedding generation
- Subsequent queries use cached embeddings
- Internet search adds 2-3 seconds per query
- RAG retrieval is fast after initial embedding

## Future Enhancements

- Persistent vector database (Pinecone, Weaviate)
- Multi-language support
- Custom embedding models
- Document summarization
- Real-time health data integration
