from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import anthropic
from datetime import datetime

class PDFGenerator:
    def __init__(self, anthropic_api_key):
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        
    def generate_invoice_content(self, invoice):
        items_list = []
        for item in invoice.items:
            items_list.append(f"{item.description}: {item.quantity} x {invoice.currency} {item.unit_price}")
        items_text = "; ".join(items_list)

        prompt = f"""Generate a professional invoice description for:
        Company: {invoice.client_name}
        Amount: {invoice.currency} {invoice.total}
        Items: {items_text}
        
        Format it as a formal business document."""

        try:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                system="You are a professional invoice writer. Generate formal, concise invoice descriptions.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            if hasattr(message, 'content'):
                if isinstance(message.content, list):
                    return message.content[0].text if message.content else "Invoice Description"
                return str(message.content)
            return "Invoice Description"

        except Exception as e:
            print(f"Error generating content: {str(e)}")
            return "Invoice Description"  # Fallback content

    def create_pdf(self, invoice, output_path):
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            styles = getSampleStyleSheet()
            elements = []
            
            header = Paragraph(f"INVOICE #{invoice.invoice_number}", styles['Heading1'])
            elements.append(header)
            elements.append(Spacer(1, 20))
            
            elements.append(Paragraph(f"To: {invoice.client_name}", styles['Normal']))
            elements.append(Paragraph(f"Email: {invoice.client_email}", styles['Normal']))
            elements.append(Paragraph(f"Address: {invoice.client_address}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            items_data = [['Description', 'Quantity', 'Unit Price', 'Amount']]
            for item in invoice.items:
                items_data.append([
                    str(item.description),
                    str(item.quantity),
                    f"{invoice.currency} {item.unit_price}",
                    f"{invoice.currency} {item.amount}"
                ])
            
            items_data.append(['', '', 'Subtotal:', f"{invoice.currency} {invoice.subtotal}"])
            items_data.append(['', '', 'Tax:', f"{invoice.currency} {invoice.tax_amount}"])
            items_data.append(['', '', 'Total:', f"{invoice.currency} {invoice.total}"])
            
            table = Table(items_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            doc.build(elements)
            return output_path
            
        except Exception as e:
            print(f"Error creating PDF: {str(e)}")
            raise e