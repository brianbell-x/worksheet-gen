# Student Worksheet Creator

A Streamlit application that uses OpenAI to generate customized student worksheets in both Markdown and PDF formats.

## Features

- Generate educational worksheets based on subject, grade level, and learning objectives
- Customize with additional details and requirements
- Get worksheets in both Markdown and PDF formats
- Download worksheets for offline use or printing

## Setup

### Prerequisites

- Python 3.7 or higher
- LaTeX (for PDF generation)
- OpenAI API key

### Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd worksheet-creator
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root directory
   - Add your OpenAI API key to the `.env` file:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

### Running Locally

Run the Streamlit app:
```bash
streamlit run worksheet_creator.py
```

The app will be available at http://localhost:8501

### Deployment to Streamlit Cloud

1. Push the code to GitHub
2. Connect your GitHub repository to Streamlit Cloud
3. Set the `OPENAI_API_KEY` secret in the Streamlit Cloud dashboard
4. Deploy

## Requirements

See `requirements.txt` for Python package dependencies.

The `packages.txt` file includes system dependencies for LaTeX that are needed for PDF generation when deploying on Streamlit Cloud.

## Troubleshooting

If PDF generation doesn't work:
- Ensure LaTeX is properly installed
- For Streamlit Cloud deployment, check that the `packages.txt` file is present
- Try downloading the LaTeX file instead and compile it locally

## License

[MIT License](LICENSE) 