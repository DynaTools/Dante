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

3. Run the application

```bash
streamlit run Home.py
```

## Development

The application uses:

- Streamlit 1.33.0 for the web interface
- Python-dotenv 1.0.0 for environment management
- Streamlit-browser-state 0.1.0 for client-side storage
- Pytest 7.4.0 for testing

## Contributing

See CONTRIBUTING.md for development guidelines.

## License

MIT License
