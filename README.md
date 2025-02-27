# Student Worksheet Creator

A Streamlit application that uses OpenAI to generate customized student worksheets for various subjects and grade levels.

## Features

- Generate high-quality educational worksheets using OpenAI
- Customize worksheets by subject, grade level, and learning objectives
- Get worksheets in both Markdown and LaTeX formats
- Download worksheets in your preferred format
- Simple and intuitive user interface

## Requirements

- Python 3.7+
- OpenAI API key

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your OpenAI API key:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file and add your API key
# OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

1. Run the Streamlit app:

```bash
streamlit run worksheet_creator.py
```

2. Access the application in your web browser (typically at http://localhost:8501)
3. Fill in the worksheet details:
   - Subject/Topic
   - Target Audience (Grade/Age Level)
   - Learning Objectives
   - Optional Details (if needed)
4. Click "Generate Worksheet" to create your worksheet
5. View the generated worksheet in either Markdown or LaTeX format using the tabs
6. Download the worksheet in your preferred format

## Notes

- The application uses the OpenAI o3-mini-2025-01-31 model
- Your OpenAI API key is loaded from the `.env` file
- The LaTeX conversion is performed by a second API call to OpenAI
- You can use the LaTeX format for professional printing or academic publishing 