from datetime import datetime
import os
import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from decimal import Decimal

from anthropic import Anthropic
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from jinja2 import Environment, FileSystemLoader

# Load environment variables
load_dotenv()

class CompanyInfo(BaseModel):
    """Company information model"""
    name: str
    address: str
    url: str
    business_description: str

class ProductInfo(BaseModel):
    """Product information model"""
    name: str
    value_proposition: str
    url: str
    company_address: str

class PricingTier(BaseModel):
    """Pricing tier model"""
    contacts: int
    price: Decimal
    price_per_contact: Decimal

class ProposalBrief(BaseModel):
    """Complete proposal brief model"""
    customer: CompanyInfo
    product: ProductInfo
    setup_fee: Decimal
    setup_items: List[str]
    pricing_tiers: List[PricingTier]
    payment_terms: List[str]

class ValuePropositionSection(BaseModel):
    """Value proposition section in the response"""
    title: str
    points: List[str]

class ValuePropositionResponse(BaseModel):
    """Structured value proposition response"""
    introduction: str
    sections: List[ValuePropositionSection]
    conclusion: str

class ContractSection(BaseModel):
    """Contract section in the response"""
    title: str
    content: str
    subsections: Optional[List[Dict[str, Any]]] = None

class ContractResponse(BaseModel):
    """Structured contract response"""
    sections: List[ContractSection]

def load_brief(file_path: str) -> ProposalBrief:
    """Load and parse the proposal brief from file"""
    try:
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        logger.debug(f"Read {len(lines)} lines from brief file")
        
        # Parse the brief file
        sections = {
            'customer': {},
            'product': {},
            'setup': {'items': []},
            'pricing': {'tiers': []},
            'payment': {'terms': []}
        }
        
        current_section = None
        
        for i, line in enumerate(lines):
            logger.debug(f"Processing line {i+1}: {line}")
            if line.startswith('Customer:'):
                current_section = 'customer'
                sections['customer']['name'] = line.split(':', 1)[1].strip()
                logger.debug(f"Found customer name: {sections['customer']['name']}")
            elif line.startswith('ADDRESS:'):
                if current_section == 'customer':
                    sections['customer']['address'] = line.split(':', 1)[1].strip()
                    logger.debug(f"Found customer address: {sections['customer']['address']}")
                elif current_section == 'product':
                    sections['product']['company_address'] = line.split(':', 1)[1].strip()
                    logger.debug(f"Found company address: {sections['product']['company_address']}")
            elif line.startswith('URL:'):
                if current_section == 'customer':
                    sections['customer']['url'] = line.split(':', 1)[1].strip()
                    logger.debug(f"Found customer URL: {sections['customer']['url']}")
                elif current_section == 'product':
                    sections['product']['url'] = line.split(':', 1)[1].strip()
                    logger.debug(f"Found product URL: {sections['product']['url']}")
            elif line.startswith('BUSINESS OF CUSTOMER:'):
                sections['customer']['business_description'] = line.split(':', 1)[1].strip()
                logger.debug(f"Found business description: {sections['customer']['business_description']}")
            elif line.startswith('PRODUCT BEING SOLD:'):
                current_section = 'product'
                sections['product']['name'] = line.split(':', 1)[1].strip()
                logger.debug(f"Found product name: {sections['product']['name']}")
            elif line.startswith('VALUE PROPOSITION:'):
                sections['product']['value_proposition'] = line.split(':', 1)[1].strip()
                logger.debug(f"Found value proposition: {sections['product']['value_proposition']}")
            elif line.startswith('SETUP FEE:'):
                current_section = 'setup'
                fee_str = line.split(':', 1)[1].strip()
                sections['setup']['fee'] = Decimal(''.join(filter(str.isdigit, fee_str)))
                logger.debug(f"Found setup fee: {sections['setup']['fee']}")
            elif line.startswith('- '):
                if current_section == 'setup':
                    sections['setup']['items'].append(line[2:].strip())
                    logger.debug(f"Found setup item: {line[2:].strip()}")
                elif current_section == 'payment':
                    sections['payment']['terms'].append(line[2:].strip())
                    logger.debug(f"Found payment term: {line[2:].strip()}")
                elif current_section == 'pricing':
                    # Parse pricing tier
                    if 'FOR UP TO' in line:
                        parts = line[2:].split(':')
                        contacts = int(''.join(filter(str.isdigit, parts[0])))
                        price_parts = parts[1].strip().split('(')
                        price = Decimal(''.join(filter(str.isdigit, price_parts[0])))
                        price_per_contact = Decimal(''.join(filter(lambda x: x.isdigit() or x == '.', price_parts[1].split()[0])))
                        tier = {
                            'contacts': contacts,
                            'price': price,
                            'price_per_contact': price_per_contact
                        }
                        sections['pricing']['tiers'].append(tier)
                        logger.debug(f"Found pricing tier: {tier}")
            elif line.startswith('USAGE FEE FOR A CAMPAIGN'):
                current_section = 'pricing'
                logger.debug("Switched to pricing section")
            elif line.startswith('PAYMENT TERMS:'):
                current_section = 'payment'
                logger.debug("Switched to payment terms section")

        logger.debug("Parsed sections:")
        logger.debug(f"Customer: {sections['customer']}")
        logger.debug(f"Product: {sections['product']}")
        logger.debug(f"Setup: {sections['setup']}")
        logger.debug(f"Pricing: {sections['pricing']}")
        logger.debug(f"Payment: {sections['payment']}")

        # Create the ProposalBrief object
        brief = ProposalBrief(
            customer=CompanyInfo(
                name=sections['customer']['name'],
                address=sections['customer']['address'],
                url=sections['customer']['url'],
                business_description=sections['customer']['business_description']
            ),
            product=ProductInfo(
                name=sections['product']['name'],
                value_proposition=sections['product']['value_proposition'],
                url=sections['product']['url'],
                company_address=sections['product']['company_address']
            ),
            setup_fee=sections['setup']['fee'],
            setup_items=sections['setup']['items'],
            pricing_tiers=[PricingTier(**tier) for tier in sections['pricing']['tiers']],
            payment_terms=sections['payment']['terms']
        )
        
        logger.info(f"Loaded brief for customer: {brief.customer.name}")
        return brief
    except Exception as e:
        logger.error(f"Error loading brief: {str(e)}")
        raise

class ProposalGenerator:
    """Handles the generation of personalized project proposals"""

    def __init__(self, api_key: Optional[str] = None, company_logo_path: Optional[str] = None):
        """Initialize the proposal generator with API key and company logo"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        self.logo_path = company_logo_path
        if self.logo_path and not os.path.exists(self.logo_path):
            logger.warning(f"Logo file not found at {self.logo_path}")
            self.logo_path = None

        self.anthropic = Anthropic(api_key=self.api_key)
        self.styles = getSampleStyleSheet()
        self.custom_styles = {
            'Heading1': ParagraphStyle(
                'Heading1',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#1a73e8')
            ),
            'Heading2': ParagraphStyle(
                'Heading2',
                parent=self.styles['Heading2'],
                fontSize=18,
                spaceAfter=20,
                textColor=colors.HexColor('#333333')
            ),
            'Normal': ParagraphStyle(
                'Normal',
                parent=self.styles['Normal'],
                fontSize=12,
                spaceAfter=12,
                textColor=colors.HexColor('#333333')
            ),
            'Quote': ParagraphStyle(
                'Quote',
                parent=self.styles['Normal'],
                fontSize=12,
                leftIndent=30,
                rightIndent=30,
                spaceAfter=20,
                textColor=colors.HexColor('#666666'),
                fontStyle='italic'
            ),
            'List': ParagraphStyle(
                'List',
                parent=self.styles['Normal'],
                fontSize=12,
                leftIndent=30,
                spaceAfter=10,
                bulletIndent=20,
                textColor=colors.HexColor('#333333')
            )
        }
        logger.info("ProposalGenerator initialized successfully")

    def generate_value_proposition(self, brief: ProposalBrief) -> ValuePropositionResponse:
        """Generate a personalized value proposition using Claude"""
        try:
            logger.info(f"Generating value proposition for {brief.customer.name}")
            prompt = f"""Create a compelling value proposition for the following client and product:

Customer Information:
{json.dumps(brief.customer.model_dump(), indent=2)}

Product Information:
{json.dumps(brief.product.model_dump(), indent=2)}

Format your response as a JSON object with the following structure:
{{
    "introduction": "A compelling introduction paragraph",
    "sections": [
        {{
            "title": "Section Title",
            "points": [
                "Benefit point 1 with metrics",
                "Benefit point 2 with metrics"
            ]
        }}
    ],
    "conclusion": "A strong concluding paragraph"
}}

Focus on specific, measurable benefits and ROI. Use concrete numbers and metrics where possible."""
            
            message = self.anthropic.beta.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system="You are an expert business proposal writer. Create compelling value propositions that focus on measurable benefits and ROI. Return ONLY valid JSON that matches the specified structure.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse the response as JSON and validate against our model
            response_json = json.loads(str(message.content))
            return ValuePropositionResponse(**response_json)
            
        except Exception as e:
            logger.error(f"Error generating value proposition: {str(e)}")
            raise

    def generate_contract_terms(self, brief: ProposalBrief) -> ContractResponse:
        """Generate contract terms using Claude"""
        try:
            logger.info("Generating contract terms")
            prompt = f"""Create a professional contract for the following proposal:

Proposal Details:
{json.dumps(brief.model_dump(), indent=2)}

Format your response as a JSON object with the following structure:
{{
    "sections": [
        {{
            "title": "Section Title",
            "content": "Main section content",
            "subsections": [
                {{
                    "title": "Subsection Title",
                    "content": "Subsection content"
                }}
            ]
        }}
    ]
}}

Include the following sections:
1. Scope of Services
2. Pricing and Payment Terms
3. Service Level Agreement
4. Term and Termination
5. Confidentiality
6. Intellectual Property
7. Limitation of Liability
8. General Terms and Conditions"""
            
            message = self.anthropic.beta.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8096,
                system="You are an expert contract writer. Create professional, comprehensive contracts that protect both parties' interests. Return ONLY valid JSON that matches the specified structure.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse the response as JSON and validate against our model
            response_json = json.loads(str(message.content))
            return ContractResponse(**response_json)
            
        except Exception as e:
            logger.error(f"Error generating contract terms: {str(e)}")
            raise

    def create_pdf_proposal(
        self, 
        brief: ProposalBrief,
        value_proposition: ValuePropositionResponse, 
        contract_terms: ContractResponse
    ) -> None:
        """Create a professionally formatted PDF proposal using reportlab"""
        try:
            logger.info(f"Creating PDF proposal for {brief.customer.name}")
            
            # Set up the document
            output_path = Path("proposals") / f"{brief.customer.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            output_path.parent.mkdir(exist_ok=True)
            
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build the document content
            story = []
            
            # Cover Page
            if self.logo_path:
                img = Image.open(self.logo_path)
                aspect = img.height / img.width
                img_width = 2 * inch
                img_height = img_width * aspect
                story.append(Spacer(1, 2*inch))
            
            story.append(Paragraph("Project Proposal", self.custom_styles['Heading1']))
            story.append(Spacer(1, inch))
            story.append(Paragraph(f"Prepared for:", self.custom_styles['Normal']))
            story.append(Paragraph(brief.customer.name, self.custom_styles['Heading2']))
            story.append(Paragraph(brief.customer.address, self.custom_styles['Normal']))
            story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", self.custom_styles['Normal']))
            story.append(PageBreak())
            
            # Table of Contents
            story.append(Paragraph("Table of Contents", self.custom_styles['Heading1']))
            sections = ['Executive Summary', 'Value Proposition', 'Scope of Work', 'Pricing', 'Terms and Conditions']
            for i, section in enumerate(sections, 1):
                story.append(Paragraph(f"{i}. {section}", self.custom_styles['Normal']))
            story.append(PageBreak())
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", self.custom_styles['Heading1']))
            story.append(Paragraph(brief.product.value_proposition, self.custom_styles['Normal']))
            story.append(PageBreak())
            
            # Value Proposition
            story.append(Paragraph("Value Proposition", self.custom_styles['Heading1']))
            story.append(Paragraph(value_proposition.introduction, self.custom_styles['Normal']))
            
            for section in value_proposition.sections:
                story.append(Paragraph(section.title, self.custom_styles['Heading2']))
                for point in section.points:
                    story.append(Paragraph(f"• {point}", self.custom_styles['List']))
            
            story.append(Paragraph(value_proposition.conclusion, self.custom_styles['Quote']))
            story.append(PageBreak())
            
            # Scope of Work and Pricing
            story.append(Paragraph("Scope of Work & Pricing", self.custom_styles['Heading1']))
            
            # Setup Fee Section
            story.append(Paragraph("Setup Fee", self.custom_styles['Heading2']))
            story.append(Paragraph(f"${brief.setup_fee:,.2f} USD", self.custom_styles['Normal']))
            
            for item in brief.setup_items:
                story.append(Paragraph(f"• {item}", self.custom_styles['List']))
            
            # Pricing Table
            story.append(Paragraph("Usage Fees (Per Language)", self.custom_styles['Heading2']))
            
            table_data = [['Contacts', 'Price (USD)', 'Per Contact']]
            for tier in brief.pricing_tiers:
                table_data.append([
                    f"{tier.contacts:,}",
                    f"${tier.price:,.2f}",
                    f"${tier.price_per_contact:.2f}"
                ])
            
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER')
            ])
            
            table = Table(table_data)
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Payment Terms
            story.append(Paragraph("Payment Terms", self.custom_styles['Heading2']))
            for term in brief.payment_terms:
                story.append(Paragraph(f"• {term}", self.custom_styles['List']))
            
            story.append(PageBreak())
            
            # Terms and Conditions
            story.append(Paragraph("Terms and Conditions", self.custom_styles['Heading1']))
            
            for section in contract_terms.sections:
                story.append(Paragraph(section.title, self.custom_styles['Heading2']))
                story.append(Paragraph(section.content, self.custom_styles['Normal']))
                
                if section.subsections:
                    for subsection in section.subsections:
                        story.append(Paragraph(subsection['title'], self.custom_styles['Heading2']))
                        story.append(Paragraph(subsection['content'], self.custom_styles['Normal']))
            
            # Build the PDF
            doc.build(story)
            logger.info(f"Proposal generated successfully: {output_path}")
            
        except Exception as e:
            logger.error(f"Error creating PDF proposal: {str(e)}")
            raise

def main():
    try:
        # Load the brief
        brief = load_brief('input/brief-1.txt')
        
        # Initialize generator
        generator = ProposalGenerator(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            company_logo_path='ReachGenie.png'
        )

        # Generate proposal components
        value_prop = generator.generate_value_proposition(brief)
        contract = generator.generate_contract_terms(brief)

        # Create PDF proposal
        generator.create_pdf_proposal(brief, value_prop, contract)

    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()