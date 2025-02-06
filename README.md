# Smart Proposals Generator

A professional proposal generation system that creates beautifully formatted PDF proposals using AI-powered content generation and ReportLab for PDF creation.

## Features

- 🤖 AI-powered value proposition and contract terms generation using Claude
- 📄 Professional PDF generation with ReportLab
- 🎨 Custom styling and formatting
- 📊 Dynamic pricing tables and content sections
- 🔄 Flexible template system
- 📱 Responsive layout design
- 🔒 Secure environment variable handling

## Project Structure

```
SmartProposals/
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── input/              # Input brief files
│   └── brief-1.txt     # Sample brief
├── templates/          # HTML/CSS templates
├── proposals/          # Generated PDF outputs
└── docs/              # Documentation
```

## Prerequisites

- Python 3.8+
- Anthropic API key for Claude
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/alinaqi/SmartProposals.git
cd SmartProposals
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your Anthropic API key:
     ```
     ANTHROPIC_API_KEY=your_api_key_here
     ```

## Usage

1. Prepare your proposal brief:
   - Create a text file in the `input/` directory
   - Follow the format in `input/brief-1.txt`

2. Run the generator:
```bash
python main.py
```

3. Find your generated proposal in the `proposals/` directory

## Brief Format

The input brief should include:
- Customer information (name, address, business description)
- Product details
- Setup fees and items
- Pricing tiers
- Payment terms

Example:
```
Customer: COMPANY_NAME
ADDRESS: Company Address
URL: https://company.com
BUSINESS OF CUSTOMER: Description

PRODUCT BEING SOLD: Product Name
VALUE PROPOSITION: Product value proposition
...
```

## Generated Proposal Structure

The generated PDF includes:
1. Professional cover page with logo
2. Table of contents
3. Executive summary
4. Value proposition
5. Scope of work and pricing
6. Terms and conditions

## Customization

- Modify styles in the `custom_styles` dictionary in `main.py`
- Adjust page layouts and content structure in the PDF generation code
- Customize prompts for AI-generated content

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Anthropic Claude](https://www.anthropic.com/claude) for AI-powered content generation
- [ReportLab](https://www.reportlab.com/) for PDF generation
- [Python-dotenv](https://github.com/theskumar/python-dotenv) for environment management 