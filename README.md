
# 📚 PDF Q&A Chatbot

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-green.svg)](https://openai.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<div align="center">
    <img src="https://raw.githubusercontent.com/yourusername/pdf-qa-chatbot/main/docs/demo.gif" alt="Demo" width="600"/>
</div>

## 🌟 Features

- 📝 **Smart PDF Processing**: Extract and understand text from PDF documents
- 🤖 **AI-Powered Answers**: Get accurate responses using OpenAI's GPT models
- 🎯 **Context-Aware**: Responses are based on the actual content of your documents
- 💫 **Modern UI/UX**: Clean, responsive design with dark mode support
- 📱 **Mobile-Friendly**: Works seamlessly on all devices
- 🚀 **Real-Time Updates**: Instant answers with loading indicators
- 📋 **Copy & Share**: Easy-to-use copy functionality for answers

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pdf-qa-chatbot.git
   cd pdf-qa-chatbot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## 🚀 Quick Start

1. **Run the application**
   ```bash
   streamlit run app.py
   ```

2. **Access the web interface**
   - Open your browser and go to `http://localhost:8501`
   - The app will be ready to use!

## 💡 Usage Guide

1. **Ask Questions**
   - Type your question in the input box
   - Press Enter or click "Ask" button
   - Wait for the AI to process and respond

2. **View Answers**
   - Answers appear in a clean, formatted style
   - Code snippets are properly formatted
   - Citations are included when relevant

3. **Manage History**
   - Clear conversation history using the sidebar
   - Copy any answer to clipboard
   - Review previous Q&A pairs

## 🔧 Technical Details

### Dependencies
- `streamlit`: Web application framework
- `openai`: AI model integration
- `faiss-cpu`: Vector similarity search
- `pdfminer.six`: PDF text extraction
- `python-dotenv`: Environment management
- Additional dependencies in `requirements.txt`

### Architecture
```
pdf-qa-chatbot/
├── app.py              # Main Streamlit application
├── utils/
│   └── utils.py       # Utility functions
├── requirements.txt    # Project dependencies
└── .env               # Environment variables
```

## 🌐 Deployment

This application is deployed on Streamlit Cloud. You can access it [here](your_deployment_url).

To deploy your own instance:

1. Fork this repository
2. Connect to [Streamlit Cloud](https://share.streamlit.io)
3. Deploy from your fork
4. Add your OpenAI API key in Streamlit secrets

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for their powerful GPT models
- Streamlit for the amazing web framework
- FAISS for efficient similarity search
- The open-source community for various tools and libraries

---

<div align="center">
    Made with ❤️ by Your Name
</div>