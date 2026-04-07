from odoo import http
from odoo.http import request
import base64
import logging
_logger = logging.getLogger(__name__)

class PrintInvoiceController(http.Controller):
    @http.route('/print/invoice/<int:invoice_id>', type='http', auth='user')
    def print_invoice(self, invoice_id):
        try:
            # Get the invoice record
            invoice = request.env['account.move'].sudo().browse(invoice_id)
            if not invoice.exists():
                return request.make_response("Invoice not found", headers=[('Content-Type', 'text/plain')])
            
            # Generate PDF content - handle the report generation differently
            report = request.env.ref('account.account_invoices').sudo()
            
            # Get the PDF content directly
            pdf_content = report._render_qweb_pdf(invoice.id)[0]  # Use index 0 to get content directly
            
            # Convert to base64
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Create HTML with embedded PDF and print script
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Invoice {invoice.name}</title>
                <script type="text/javascript">
                    window.onload = function() {{
                        var pdfData = '{pdf_base64}';
                        var byteCharacters = atob(pdfData);
                        var byteNumbers = new Array(byteCharacters.length);
                        for (var i = 0; i < byteCharacters.length; i++) {{
                            byteNumbers[i] = byteCharacters.charCodeAt(i);
                        }}
                        var byteArray = new Uint8Array(byteNumbers);
                        var blob = new Blob([byteArray], {{type: 'application/pdf'}});
                        var blobUrl = URL.createObjectURL(blob);
                        
                        document.getElementById('pdf-viewer').src = blobUrl;
                        
                        // Wait for PDF to load then print
                        document.getElementById('pdf-viewer').onload = function() {{
                            setTimeout(function() {{
                                window.print();
                            }}, 1000);
                        }};
                    }};
                </script>
                <style>
                    body, html {{
                        margin: 0;
                        padding: 0;
                        height: 100%;
                        overflow: hidden;
                    }}
                    iframe {{
                        width: 100%;
                        height: 100%;
                        border: none;
                    }}
                </style>
            </head>
            <body>
                <iframe id="pdf-viewer"></iframe>
            </body>
            </html>
            """
            
            # Return HTML response
            return request.make_response(html, headers=[
                ('Content-Type', 'text/html'),
                ('Cache-Control', 'no-cache')
            ])
            
        except Exception as e:
            _logger.error("Error printing invoice: %s", e)
            # Log more detailed information for debugging
            import traceback
            _logger.error(traceback.format_exc())
            
            error_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        text-align: center;
                    }}
                    .error-container {{
                        background-color: #f8d7da;
                        border: 1px solid #f5c6cb;
                        color: #721c24;
                        padding: 20px;
                        border-radius: 5px;
                        margin-top: 30px;
                    }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <h2>Error Processing Invoice</h2>
                    <p>There was an error processing your request. Please contact your system administrator.</p>
                    <p>Error details: {str(e)}</p>
                </div>
            </body>
            </html>
            """
            return request.make_response(error_message, headers=[('Content-Type', 'text/html')])