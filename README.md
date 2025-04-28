# Verborum

A sophisticated translation portal that uses a multi-provider API chain (DeepL → Gemini Flash 1.5 → OpenAI GPT-4) with secure local key storage.

## Features

- Multi-provider translation chain with automatic fallback
- Secure local storage of API keys
- Grammar checking and analysis tools (coming soon)
- Interactive language practice exercises (coming soon)
- Conversation practice with AI (coming soon)

## Setup

1. Clone the repository

```bash
git clone https://github.com/DynaTools/verborum.git
cd verborum
```

2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. API Keys

You'll need API keys for the translation services:
- [DeepL API](https://www.deepl.com/pro-api) (Pro account required)
- [Google AI Studio](https://makersuite.google.com/app/apikey) for Gemini API
- [OpenAI Platform](https://platform.openai.com/api-keys) for GPT-4

The application will prompt for these keys on first run and store them securely in your browser's local storage.

4. Run the application

```bash
streamlit run Home.py
```

## Using Verborum

1. **Enter text** in the left panel (up to 5,000 characters)
2. Select **source language** (or use auto-detect)
3. Choose **target language** in the right panel
4. Set the desired **tone** (formal, informal, or default)
5. Click **Translate** to process the text
6. View the translated text in the output panel

### Advanced Features

- **Translation cache**: Frequently used translations are cached to reduce API calls
- **Automatic fallback**: If one translation provider fails, the system tries the next one
- **Retry mechanism**: Each provider is tried multiple times before falling back

## Development

The application uses:

- Streamlit 1.33.0 for the web interface
- Python-dotenv 1.0.0 for environment management
- Streamlit-browser-state 0.1.0 for client-side storage
- Pytest 7.4.0 for testing

### Testing

Run the tests with:

```bash
python -m pytest
```

### Project Structure

```
verborum-portal/
├── .github/           # GitHub Actions workflows
├── .streamlit/        # Streamlit configuration
├── services/          # API service implementations
├── utils/             # Utility functions
├── tests/             # Test suite
├── Home.py            # Main translator page
└── pages/             # Additional app pages
```

## Contributing

See CONTRIBUTING.md for development guidelines.

## License

MIT License
