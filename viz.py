import os
import fitz  # PyMuPDF
import openai
import plotly.graph_objects as go
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import re  # Added for regular expressions

app = Flask(__name__)
UPLOAD_FOLDER = '/Users/sanketdhameliya/Documents'  # Ensure this is a valid path
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

openai.api_key = os.getenv('OPENAI_API_KEY')

class InsurancePolicyInfo:
    def __init__(self, total_coverage_amount=0, insurance_type="", categories=None, covered_items=None, not_covered_items=None, covered_events=None, additional_info=None):
        self.total_coverage_amount = total_coverage_amount
        self.insurance_type = insurance_type
        self.categories = categories if categories else []
        self.covered_items = covered_items if covered_items else []
        self.not_covered_items = not_covered_items if not_covered_items else []
        self.covered_events = covered_events if covered_events else []
        self.additional_info = additional_info if additional_info else {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    print("Upload route hit")  # Debug print
    if 'file' not in request.files:
        print("No file part")  # Debug print
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        print("No selected file")  # Debug print
        return 'No selected file'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        text = extract_text_from_pdf(filepath)
        policy_info = query_openai_and_parse(text)

        chart_html = generate_sunburst_chart(policy_info)
        print("Chart HTML generated")  # Debug print

        return render_template('screen2.html', chart_html=chart_html)
    else:
        print("Invalid file type")  # Debug print
        return 'Invalid file type'

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return ""

def query_openai_and_parse(text):
    # Define the prompt first
    prompt = (
        "I need a structured summary of this insurance policy, focusing on specific details. "
        "Please list the following: total coverage amount, type of insurance, "
        "categories of insurance covered, what is covered under each category, "
        "what is not covered under each category, covered events, "
        "annual premium, name of the insurer, name of the insured, "
        "issue date , renewal date and policy number"
    )

    # Then calculate the maximum length for the text
    max_length = 4097 - len(prompt)

    # Truncate the text to fit within the model's maximum context length
    truncated_text = text[:max_length]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt + truncated_text}]
    )
    print("OpenAI Response:", response)  # Debug print

    # Extract information from OpenAI response
    extracted_text = response.choices[0].message['content']
    return parse_openai_response(extracted_text)

# Extract total coverage amount using regular expressions
def extract_total_coverage_amount(text):
    total_coverage_amount = None

    if isinstance(text, str):
        # Use regular expressions to find the total coverage amount in various formats
        match_million = re.search(r'BENEFIT_AMOUNT:\s*([\w\s$]+)', text)
        match_dollars = re.search(r'PREMIUM:\s*([\w\s$]+)', text)

        if match_million:
            total_coverage_amount = match_million.group(1).strip()
        elif match_dollars:
            total_coverage_amount = match_dollars.group(1).strip()

    return total_coverage_amount

def parse_openai_response(response_text):
    policy_info = InsurancePolicyInfo()

    # Split the response text into lines
    lines = response_text.split('\n')

    for line in lines:
        # Extract total coverage amount
        match_coverage_amount = re.search(r'Total Coverage Amount: (.*?)$', line)
        if match_coverage_amount:
            policy_info.total_coverage_amount = match_coverage_amount.group(1).strip()

        # Extract type of insurance
        match_insurance_type = re.search(r'Type of Insurance: (.*?)$', line)
        if match_insurance_type:
            policy_info.insurance_type = match_insurance_type.group(1).strip()

        # Extract categories of insurance covered
        if line.startswith(str(len(policy_info.categories) + 1) + '. '):
            categories_text = line.split(': ')[1].strip()
            policy_info.categories.append(categories_text)

        # Extract what is covered under each category
        if line.startswith(str(len(policy_info.covered_items) + 1) + '. '):
            covered_items_text = line.split(': ')[1].strip()
            policy_info.covered_items.append(covered_items_text)

        # Extract what is not covered under each category
        if line.startswith(str(len(policy_info.not_covered_items) + 1) + '. '):
            non_covered_items_text = line.split(': ')[1].strip()
            policy_info.not_covered_items.append(non_covered_items_text)

        # Extract covered events
        if line.startswith('- '):
            covered_events_text = line.strip('- ').strip()
            policy_info.covered_events.append(covered_events_text)

        # Extract additional information based on keywords and patterns
        match_additional_info = re.search(r'(Annual Premium|Insurer|Insured|Issue Date|Renewal Date|Policy Number): (.*?)$', line)
        if match_additional_info:
            info_type = match_additional_info.group(1)
            info_value = match_additional_info.group(2)
            policy_info.additional_info[info_type] = info_value.strip()

    return policy_info


def generate_sunburst_chart(policy_info):
    labels = ["Total Coverage"]
    parents = [""]
    values = [policy_info.total_coverage_amount if policy_info.total_coverage_amount else 0.0]
    hovertext = [f"Total Coverage: {policy_info.total_coverage_amount}" if policy_info.total_coverage_amount else "Total Coverage: None"]

    if policy_info.insurance_type:
        labels.append(policy_info.insurance_type)
        parents.append("Total Coverage")
        values.append(policy_info.total_coverage_amount / 2 if policy_info.total_coverage_amount else 0.0)
        hovertext.append(f"Insurance Type: {policy_info.insurance_type}")

    for category in policy_info.categories:
        labels.append(category)
        parents.append(policy_info.insurance_type if policy_info.insurance_type else "Total Coverage")
        values.append(1.0)
        hovertext.append(f"Category: {category}")

    for item in policy_info.covered_items:
        labels.append(item)
        parents.append(policy_info.categories[0] if policy_info.categories else (policy_info.insurance_type if policy_info.insurance_type else "Total Coverage"))
        values.append(1.0)
        hovertext.append(f"Covered Item: {item}")

    for item in policy_info.not_covered_items:
        labels.append(item)
        parents.append(policy_info.categories[0] if policy_info.categories else (policy_info.insurance_type if policy_info.insurance_type else "Total Coverage"))
        values.append(1.0)
        hovertext.append(f"Not Covered Item: {item}")

    for event in policy_info.covered_events:
        labels.append(event)
        parents.append(policy_info.categories[0] if policy_info.categories else (policy_info.insurance_type if policy_info.insurance_type else "Total Coverage"))
        values.append(1.0)
        hovertext.append(f"Covered Event: {event}")

    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        hovertext=hovertext,
        hoverinfo="text"
    ))

    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    chart_html = fig.to_html(full_html=False, include_plotlyjs=False, default_height=400, default_width=600)

    return chart_html

if __name__ == '__main__':
    app.run(debug=True, port=8080)
