import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import re
import tempfile
from pylatex import Document, Command, Package
from pylatex.utils import NoEscape
import base64
from pathlib import Path
import shutil
import subprocess
import sys
import platform

# Load environment variables from .env file
load_dotenv()

st.set_page_config(
    page_title="Student Worksheet Creator",
    page_icon="📝",
    layout="wide",
)

# Get API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Sidebar for info
with st.sidebar:
    st.header("About")
    st.markdown(
        "This app uses OpenAI to generate customized student worksheets. "
        "Fill in the form and click 'Generate Worksheet' to create your educational content."
    )
    st.markdown("---")
    if not api_key:
        st.warning("⚠️ No API key found in .env file. Please create a .env file with your OPENAI_API_KEY.")
    else:
        st.success("✅ API key loaded from .env file")

# Main form
st.subheader("Worksheet Details")

with st.form("worksheet_form"):
    # Input fields for worksheet variables
    subject = st.text_input(
        "Subject/Topic",
        help="A brief description of the primary subject or topic of the worksheet",
        placeholder="e.g., Photosynthesis, Fractions, World War II, Creative Writing"
    )
    
    grade_level = st.text_input(
        "Target Audience (Grade/Age Level)",
        help="The grade range, age group, or skill level of the students",
        placeholder="e.g., 5th Grade, Ages 10-12, High School, Beginner"
    )
    
    learning_objectives = st.text_area(
        "Learning Objectives",
        help="Key learning goals or competencies students should achieve",
        placeholder="e.g., Understand the process of photosynthesis, Identify key parts of a plant, Explain how plants convert light energy to chemical energy"
    )
    
    optional_details = st.text_area(
        "Optional Details",
        help="Any specific themes, difficulty levels, time constraints, or style guidelines",
        placeholder="e.g., Include diagrams, Make it suitable for a 30-minute activity, Focus on hands-on experiments"
    )
    
    # Form submission button
    submit_button = st.form_submit_button("Generate Worksheet")

# Helper function to prepare LaTeX for rendering
def prepare_latex_for_rendering(latex_content):
    """
    Prepare LaTeX content for rendering with st.latex
    - Removes document class and begin/end document tags if present
    - Ensures content is not too large
    - Handles common LaTeX errors
    """
    # Remove document class and begin/end document tags if present
    latex_content = re.sub(r'\\documentclass.*?\{.*?\}', '', latex_content)
    latex_content = re.sub(r'\\begin\{document\}', '', latex_content)
    latex_content = re.sub(r'\\end\{document\}', '', latex_content)
    
    # Remove any usepackage commands
    latex_content = re.sub(r'\\usepackage.*?\{.*?\}', '', latex_content)
    
    # Limit size if too large (st.latex has rendering limits)
    if len(latex_content) > 10000:
        sections = latex_content.split('\\section')
        if len(sections) > 1:
            # Return just the first section if content is too large
            return sections[0] + "\\section" + sections[1]
        else:
            # Or just the first part of the content
            return latex_content[:10000] + "\n\\ldots \\text{(content truncated for rendering)}"
    
    return latex_content.strip()

# Function to convert LaTeX to PDF using PyLaTeX and return the PDF bytes
def convert_latex_to_pdf(latex_content):
    """
    Convert LaTeX content to PDF using PyLaTeX.
    
    Args:
        latex_content (str): The LaTeX content to convert.
        
    Returns:
        bytes: The PDF file content as bytes.
    """
    # Create a temporary directory to work in
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Two approaches: direct PyLaTeX or subprocess with pdflatex
        # Try PyLaTeX first, fall back to subprocess if needed
        
        try:
            # Approach 1: Use PyLaTeX to create a document
            # This is the preferred method for Streamlit Cloud
            
            # Extract document class if present, or use default
            doc_class_match = re.search(r'\\documentclass(\[.*?\])?\{(.*?)\}', latex_content)
            if doc_class_match:
                doc_class = doc_class_match.group(2)
                # Remove the document class from content as we'll add it via PyLaTeX
                latex_content = re.sub(r'\\documentclass(\[.*?\])?\{.*?\}', '', latex_content)
            else:
                doc_class = 'article'
            
            # Remove begin/end document tags if present
            latex_content = re.sub(r'\\begin\{document\}', '', latex_content)
            latex_content = re.sub(r'\\end\{document\}', '', latex_content)
            
            # Create PyLaTeX document
            doc = Document(documentclass=doc_class)
            
            # Add common packages that might be needed
            doc.packages.append(Package('amsmath'))
            doc.packages.append(Package('amssymb'))
            doc.packages.append(Package('graphicx'))
            doc.packages.append(Package('geometry', options=['margin=1in']))
            
            # Extract and add any usepackage commands
            package_matches = re.finditer(r'\\usepackage(\[.*?\])?\{(.*?)\}', latex_content)
            for match in package_matches:
                options_str = match.group(1)
                package_name = match.group(2)
                
                # Process options if present
                options = []
                if options_str:
                    # Remove brackets and split by comma
                    options_str = options_str[1:-1]  # Remove [ and ]
                    options = [opt.strip() for opt in options_str.split(',')]
                
                # Add package to document
                doc.packages.append(Package(package_name, options=options))
            
            # Remove usepackage commands from content as we've added them via PyLaTeX
            latex_content = re.sub(r'\\usepackage(\[.*?\])?\{.*?\}', '', latex_content)
            
            # Add the remaining content as NoEscape to prevent escaping of LaTeX commands
            doc.append(NoEscape(latex_content))
            
            # Generate PDF
            output_filename = temp_dir_path / "worksheet"
            doc.generate_pdf(output_filename, clean_tex=False)
            
            # Read the generated PDF
            pdf_path = output_filename.with_suffix('.pdf')
            if pdf_path.exists():
                with open(pdf_path, "rb") as pdf_file:
                    return pdf_file.read()
            else:
                # If PyLaTeX approach failed, try the subprocess approach
                raise FileNotFoundError("PDF not generated by PyLaTeX")
                
        except Exception as pylatex_error:
            st.warning(f"PyLaTeX approach failed: {str(pylatex_error)}. Trying alternative approach...")
            
            try:
                # Approach 2: Use subprocess to call pdflatex directly
                # This is a fallback for environments where pdflatex is available
                
                # Path for the temporary tex file
                tex_file_path = temp_dir_path / "worksheet.tex"
                
                # Write the LaTeX content to the tex file
                with open(tex_file_path, "w", encoding="utf-8") as tex_file:
                    # Make sure the LaTeX content has proper document structure
                    if "\\documentclass" not in latex_content:
                        # Add document class if missing
                        latex_content = "\\documentclass{article}\n\\usepackage{amsmath,amssymb,graphicx}\n\\begin{document}\n" + latex_content
                    
                    if "\\end{document}" not in latex_content:
                        # Add end document if missing
                        latex_content = latex_content + "\n\\end{document}"
                        
                    tex_file.write(latex_content)
                
                # Check if pdflatex is available
                try:
                    # Different command check based on OS
                    if platform.system() == "Windows":
                        check_cmd = ["where", "pdflatex"]
                    else:
                        check_cmd = ["which", "pdflatex"]
                    
                    subprocess.run(check_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    pdflatex_available = True
                except subprocess.CalledProcessError:
                    pdflatex_available = False
                
                if not pdflatex_available:
                    raise Exception("pdflatex is not available in the system path")
                
                # Run pdflatex twice to resolve references
                for _ in range(2):
                    subprocess.run(
                        ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(temp_dir_path), str(tex_file_path)],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                
                # Read the generated PDF
                pdf_path = temp_dir_path / "worksheet.pdf"
                if pdf_path.exists():
                    with open(pdf_path, "rb") as pdf_file:
                        return pdf_file.read()
                else:
                    raise Exception("PDF was not generated successfully")
                    
            except subprocess.CalledProcessError as e:
                raise Exception(f"PDF generation failed: {e.stderr.decode('utf-8') if e.stderr else 'Unknown error'}")
            except Exception as e:
                raise Exception(f"Error during PDF conversion: {str(e)}")

# Handle form submission
if submit_button:
    if not api_key:
        st.error("OpenAI API key not found. Please add your OPENAI_API_KEY to the .env file.")
    elif not subject or not grade_level or not learning_objectives:
        st.error("Please fill in all required fields (Subject, Grade Level, and Learning Objectives)")
    else:
        try:
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
            
            # Status container for progress updates
            status_container = st.empty()
            
            # First API call - Generate worksheet content
            with st.spinner("Step 1/2: Generating worksheet content using OpenAI..."):
                status_container.info("Creating educational worksheet based on your inputs. This may take a moment...")
                
                # Construct the prompt
                prompt = f"""
                You are an advanced educational content generator tasked with creating high-quality worksheets.

                ### Input Variables

                1. **Subject/Topic:** {subject}
                   - A brief description of the primary subject or topic of the worksheets.

                2. **Target Audience (Grade/Age Level):** {grade_level}
                   - The grade range, age group, or skill level of the students.

                3. **Learning Objectives:** {learning_objectives}
                   - A list or description of the key learning goals or competencies students should achieve.

                4. **Required Sections:**  
                   - **Instructions** (clear, concise, and engaging)  
                   - **Examples** (illustrative and aligned with the topic)  
                   - **Practice Exercises** (varied question types, skill-based, and scaffolded)  
                   - **Real-Life Applications** (contextual, practical exercises linking to everyday scenarios)

                5. **Optional Details:** {optional_details}
                   - Any specific themes, difficulty levels, time constraints, or style guidelines.

                ### Task (In Detail)

                1. **Generate Worksheets:**  
                   - Create a set of worksheets tailored to the subject for students at the specified grade level. Incorporate the specified learning objectives.  

                2. **Structure and Flow:**  
                   - The worksheets **must** include the four core sections (Instructions, Examples, Practice Exercises, Real-Life Applications).  
                   - Clearly label each section and provide smooth transitions so students can follow along effortlessly.

                3. **Activity Design:**  
                   - Craft engaging activities that encourage critical thinking, problem-solving, and hands-on practice.  
                   - Vary question formats (e.g., multiple choice, fill-in-the-blank, matching, short answer, and open-ended).  

                4. **Customization and Style:**  
                   - Integrate any extra guidelines or stylistic preferences provided in optional details.  
                   - Ensure the final output is well-formatted with clear headings and consistent spacing.

                ### Return Format

                - **Title** and/or **Topic Heading**  
                - **Brief Introduction** or overview of what the worksheets will cover  
                - **Instructions** (a short paragraph explaining how to use the worksheet)  
                - **Examples** (one or more detailed examples illustrating key points)  
                - **Practice Exercises** (clearly numbered or labeled questions with sufficient space or lines for answers)  
                - **Real-Life Applications** (at least one scenario-based question or activity linking to everyday experiences)  
                - **Answer Key** (optional, but recommended if appropriate)  

                ### Warnings, Precautions, and Guidelines

                1. **Age/Grade Appropriateness:**  
                   - The content must be aligned with the grade level and free of inappropriate material.

                2. **Clarity and Accessibility:**  
                   - Instructions and questions should be easy to understand for non-native speakers and diverse learners.

                3. **Accuracy and Relevance:**  
                   - Ensure all factual details are correct and directly related to the subject and learning objectives.  

                4. **Bias and Inclusion:**  
                   - Avoid cultural, racial, or gender biases. Use inclusive language and examples whenever possible.

                5. **Copyright and Plagiarism:**  
                   - Only use material you have permission to use. Avoid directly copying large segments from external sources.

                6. **Formatting:**  
                   - The final layout must accommodate clear headings and consistent spacing for easy reading and printing.
                """
                
                # Make the API call
                response = client.chat.completions.create(
                    model="o3-mini-2025-01-31",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    response_format={"type": "text"},
                    reasoning_effort="high"
                )
                
                # Extract the response
                if response and response.choices:
                    worksheet_content = response.choices[0].message.content
                    status_container.success("✅ Worksheet content generated successfully!")
                else:
                    st.error("Failed to generate worksheet. Please try again.")
                    st.stop()
            
            # Second API call - Convert to LaTeX
            with st.spinner("Step 2/2: Converting worksheet to LaTeX format..."):
                status_container.info("Converting the worksheet to LaTeX format. This may take a moment...")
                
                latex_response = client.chat.completions.create(
                    model="o3-mini-2025-01-31",
                    messages=[
                        {
                            "role": "system",
                            "content": "Return Content as Latex. Return Latex Only."
                        },
                        {
                            "role": "user",
                            "content": worksheet_content
                        }
                    ],
                    response_format={"type": "text"},
                    reasoning_effort="high"
                )
                
                # Extract the LaTeX content
                if latex_response and latex_response.choices:
                    latex_content = latex_response.choices[0].message.content
                    status_container.success("✅ Worksheet generated and converted to LaTeX successfully!")
                else:
                    latex_content = "Failed to convert to LaTeX"
                    status_container.warning("⚠️ Worksheet generated but LaTeX conversion failed.")
            
            # Clear the status container
            status_container.empty()
            
            # Create tabs for different formats
            tab1, tab2, tab3 = st.tabs(["Markdown", "LaTeX", "PDF"])
            
            with tab1:
                st.subheader("Markdown Format")
                st.code(worksheet_content, language="markdown")
                st.download_button(
                    label="Download Markdown",
                    data=worksheet_content,
                    file_name=f"{subject.replace(' ', '_')}_worksheet.md",
                    mime="text/markdown",
                )
            
            with tab2:
                st.subheader("LaTeX Format")
                
                # Display LaTeX code
                with st.expander("View LaTeX Code", expanded=False):
                    st.code(latex_content, language="latex")
                
                # Render LaTeX
                st.subheader("Rendered LaTeX Preview")
                try:
                    # Prepare LaTeX content for rendering
                    prepared_latex = prepare_latex_for_rendering(latex_content)
                    
                    # Render in smaller chunks if needed
                    if len(prepared_latex) > 5000:
                        st.warning("The LaTeX content is large and has been split into sections for rendering.")
                        sections = prepared_latex.split('\\section')
                        
                        if len(sections) > 1:
                            for i, section in enumerate(sections[:3]):  # Limit to first 3 sections
                                if i > 0:
                                    section_content = "\\section" + section
                                else:
                                    section_content = section
                                    
                                if section_content.strip():
                                    st.subheader(f"Section {i+1}")
                                    st.latex(section_content)
                            
                            if len(sections) > 3:
                                st.info(f"{len(sections)-3} more sections not shown. Download the full LaTeX file to view all content.")
                        else:
                            # Split by paragraphs if no sections
                            paragraphs = prepared_latex.split('\n\n')
                            for i, para in enumerate(paragraphs[:5]):  # Limit to first 5 paragraphs
                                if para.strip():
                                    st.latex(para)
                            
                            if len(paragraphs) > 5:
                                st.info(f"{len(paragraphs)-5} more paragraphs not shown. Download the full LaTeX file to view all content.")
                    else:
                        # Render the entire content if it's not too large
                        st.latex(prepared_latex)
                        
                except Exception as latex_error:
                    st.error(f"Could not render LaTeX: {str(latex_error)}")
                    st.info("The LaTeX code may contain syntax errors or be too complex for direct rendering. You can still download the file and use a LaTeX editor.")
                
                # Download button
                st.download_button(
                    label="Download LaTeX",
                    data=latex_content,
                    file_name=f"{subject.replace(' ', '_')}_worksheet.tex",
                    mime="text/plain",
                )
                
            with tab3:
                st.subheader("PDF Format")
                
                try:
                    # Show status while generating PDF
                    with st.spinner("Generating PDF..."):
                        pdf_bytes = convert_latex_to_pdf(latex_content)
                    
                    # Create a download button for the PDF
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"{subject.replace(' ', '_')}_worksheet.pdf",
                        mime="application/pdf",
                    )
                    
                    # Display PDF directly in Streamlit
                    # Encode PDF to base64 for displaying in an iframe
                    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                    
                except Exception as pdf_error:
                    st.error(f"Could not generate PDF: {str(pdf_error)}")
                    st.info("PDF generation requires LaTeX to be installed. For Streamlit Cloud deployment, you may need to add LaTeX to the packages.txt file.")
                    
                    # Provide a link to download just the LaTeX file as a fallback
                    st.markdown("### Fallback Option")
                    st.markdown("If PDF generation is not working, you can download the LaTeX file and compile it locally:")
                    st.download_button(
                        label="Download LaTeX File",
                        data=latex_content,
                        file_name=f"{subject.replace(' ', '_')}_worksheet.tex",
                        mime="text/plain",
                    )
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}") 