import os
import fitz  # PyMuPDF
import openai
import plotly.graph_objects as go
import plotly.io as pio  # Add this import
from flask import Flask, request, render_template, Response
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)
UPLOAD_FOLDER = '/Users/sanketdhameliya/Documents'  # Ensure this is a valid path
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set your OpenAI API key here
openai.api_key = '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'

class InsurancePolicyInfo:
    def __init__(self):
        self.total_coverage_amount = 0.0
        self.insurance_type = ""
        self.categories = []
        self.covered_items = []
        self.not_covered_items = []
        self.covered_events = []
        self.annual_premium = 0.0
        self.insurer = ""
        self.insured = ""
        self.issue_date = ""
        self.renewal_date = ""
        self.policy_number = ""
        self.additional_info = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        text = extract_text_from_pdf(filepath)  # Define 'text' by extracting text from the PDF
        policy_info = query_openai_and_parse(text)
        chart_html = generate_sunburst_chart(policy_info)
        return render_template('screen2.html', chart_html=chart_html)
    else:
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
        return ""

def query_openai_and_parse(text):
    prompt = (
    "Please extract the following details from the insurance policy document:\n"
    "- Total coverage amount\n"
    "- Type of insurance\n"
    "- Categories of insurance covered\n"
    "- Details of what is covered under each category\n"
    "- Details of what is not covered under each category\n"
    "- Covered events\n"
    "- Annual premium\n"
    "- Name of the insurer\n"
    "- Name of the insured\n"
    "- Issue date\n"
    "- Renewal date\n"
    "- Policy number\n"
    "Document Text:\n"
    "<insert_document_text_here>"
)
    max_length = 4097 - len(prompt)
    truncated_text = text[:max_length]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts information from insurance policies."},
            {"role": "user", "content": prompt + truncated_text}
        ]
    )

    print("OpenAI Response:", response)  # Log the full response
    extracted_text = response.choices[0].message["content"]
    print("Extracted Text:", extracted_text)  # Log the extracted text
    return parse_openai_response(extracted_text)

def parse_openai_response(response_text):
    policy_info = InsurancePolicyInfo()
    # Parse total coverage amount
    coverage_amount_match = re.search(r'Total coverage amount: \$([\d,.]+)', response_text)
    if coverage_amount_match:
        policy_info.total_coverage_amount = float(coverage_amount_match.group(1).replace(',', ''))

    # Parse type of insurance (handles spaces and quotation marks)
    insurance_type_match = re.search(r'Type of insurance: (.+?)(?=\n|$)', response_text, re.DOTALL)
    if insurance_type_match:
        policy_info.insurance_type = insurance_type_match.group(1).strip()

    # Parse categories of insurance covered (handles spaces and quotation marks)
    categories_match = re.search(r'Categories of insurance covered: (.+?)(?=\n-|\n$)', response_text, re.DOTALL)
    if categories_match:
        policy_info.categories = [category.strip() for category in categories_match.group(1).split(',')]

    # Parse details of what is covered under each category
    covered_items_match = re.search(r'Details of what is covered under each category:(.+?)Details of what is not covered', response_text, re.DOTALL)
    if covered_items_match:
        covered_items_text = covered_items_match.group(1)
        covered_items = {}
        for line in covered_items_text.split('\n'):
            parts = line.strip().split(':')
            if len(parts) == 2:
                category = parts[0].strip()
                items = [item.strip() for item in parts[1].split(',')]
                covered_items[category] = items
        policy_info.covered_items = covered_items

    # Parse annual premium
    annual_premium_match = re.search(r'Annual premium: \$([\d,.]+)', response_text)
    if annual_premium_match:
        policy_info.annual_premium = float(annual_premium_match.group(1).replace(',', ''))

    # Parse name of the insurer (handles quotation marks)
    insurer_match = re.search(r'Name of the insurer: (.+?)(?=\n|$)', response_text, re.DOTALL)
    if insurer_match:
        policy_info.insurer = insurer_match.group(1).strip()

    # Parse name of the insured (handles quotation marks)
    insured_match = re.search(r'Name of the insured: (.+?)(?=\n|$)', response_text, re.DOTALL)
    if insured_match:
        policy_info.insured = insured_match.group(1).strip()

    # Parse issue date (handles quotation marks)
    issue_date_match = re.search(r'Issue date: (.+?)(?=\n|$)', response_text, re.DOTALL)
    if issue_date_match:
        policy_info.issue_date = issue_date_match.group(1).strip()

    # Parse renewal date (handles quotation marks)
    renewal_date_match = re.search(r'Renewal date: (.+?)(?=\n|$)', response_text, re.DOTALL)
    if renewal_date_match:
        policy_info.renewal_date = renewal_date_match.group(1).strip()

    # Parse policy number (handles quotation marks)
    policy_number_match = re.search(r'Policy number:(.+?)(?=\n-|\n$)', response_text, re.DOTALL)
    if policy_number_match:
        policy_numbers_text = policy_number_match.group(1)
        policy_numbers = {}
        for line in policy_numbers_text.split('\n'):
            parts = line.strip().split(':')
            if len(parts) == 2:
                category = parts[0].strip()
                number = parts[1].strip()
                policy_numbers[category] = number
        policy_info.policy_number = policy_numbers

    return policy_info


def generate_sunburst_chart(policy_info):
    if policy_info is None:
        return None

    # Extract relevant data from policy_info
    total_coverage_amount = policy_info.total_coverage_amount
    insurance_type = policy_info.insurance_type
    categories = policy_info.categories
    covered_items = policy_info.covered_items
    not_covered_items = policy_info.not_covered_items

    # Create the Sunburst chart using the extracted data
    fig = go.Figure()

    # Center of the Circle: Total coverage and total annual premiums
    fig.add_trace(go.Sunburst(
        labels=["Total Coverage Amount", "Insurance Type"],
        parents=["", ""],
        values=[total_coverage_amount, insurance_type],
        branchvalues="total",
    ))

    # Categories Ring: Represents categories within each insurance type
    categories_ring = go.Sunburst(
        labels=[insurance_type] + categories,  # Add insurance_type as the parent
        parents=[""] + [insurance_type] * len(categories),  # Add insurance_type as the parent
        values=[1] * (len(categories) + 1),  # Include insurance_type
        marker=dict(colors=["#FFA500", "#008000", "#0000FF", "#FF0000"] * (len(categories) + 1)),  # Example colors
    )
    fig.add_trace(categories_ring)

    # Covered Benefits Ring: Specific to each person’s policy, showing benefits covered
    covered_benefits = sum(covered_items.values(), []) if isinstance(covered_items, dict) else []  # Flatten the covered items
    covered_benefits_ring = go.Sunburst(
        labels=[category + ": " + ", ".join(covered_items[category]) for category in covered_items],
        parents=[category for category in covered_items],
        values=[1] * len(covered_benefits),
        marker=dict(colors=["#00FF00"] * len(covered_benefits)),  # Example color for covered benefits
    )
    fig.add_trace(covered_benefits_ring)

    # Not Covered Benefits Ring: Indicates benefits not covered by the policy
    not_covered_benefits = sum(not_covered_items.values(), []) if isinstance(not_covered_items, dict) else []  # Flatten the not covered items
    not_covered_benefits_ring = go.Sunburst(
        labels=[category + ": " + ", ".join(not_covered_items[category]) for category in not_covered_items],
        parents=[category for category in not_covered_items],
        values=[1] * len(not_covered_benefits),
        marker=dict(colors=["#FF0000"] * len(not_covered_benefits)),  # Example color for not covered benefits
    )
    fig.add_trace(not_covered_benefits_ring)

    # Update the layout of the chart
    fig.update_layout(
        margin=dict(t=0, l=0, r=0, b=0),
        sunburstcolorway=["#FFA500", "#008000", "#0000FF", "#FF0000"],  # Example colors
    )

    # Convert the chart to HTML
    chart_html = fig.to_html(full_html=False)

    return chart_html



if __name__ == '__main__':
    app.run(debug=True, port=8000)

