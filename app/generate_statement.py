import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print 'Page X of Y'."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        # Top rule
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 36, letter[0] - 40, 36)
        
        # Footer text
        footer_left = "HDFC Bank Ltd. • Indiranagar Branch • Account No: 50100492815892 • Customer ID: 94819283"
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawString(40, 24, footer_left)
        self.drawRightString(letter[0] - 40, 24, page_str)
        self.restoreState()

def create_hdfc_statement(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0F172A")
    )
    header_right = ParagraphStyle(
        'HeaderRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        alignment=2,
        textColor=colors.HexColor("#334155")
    )
    section_title = ParagraphStyle(
        'SecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0F172A")
    )
    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F172A")
    )
    cell_normal = ParagraphStyle(
        'CellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1E293B")
    )
    cell_credit = ParagraphStyle(
        'CellCredit',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        alignment=2,
        textColor=colors.HexColor("#065F46")
    )
    cell_debit = ParagraphStyle(
        'CellDebit',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=2,
        textColor=colors.HexColor("#991B1B")
    )
    cell_num = ParagraphStyle(
        'CellNum',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=2,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    def make_header(page_title):
        header_table = Table(
            [
                [
                    Paragraph("<b>HDFC BANK</b><br/><font size=8 color='#475569'>We understand your world</font>", title_style),
                    Paragraph(
                        "<b>HDFC Bank Limited</b><br/>Branch: 100 Feet Road, Indiranagar, Bengaluru - 560038<br/>"
                        "IFSC: HDFC0000184 • MICR: 560240008<br/>GSTIN: 29AAACH2702H1ZQ",
                        header_right
                    )
                ]
            ],
            colWidths=[200, 332]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#0F172A")),
        ]))
        return header_table

    # ================= PAGE 1 =================
    story.append(make_header("Page 1"))
    story.append(Spacer(1, 10))

    # Account metadata box
    acc_info = [
        [
            Paragraph("<b>Account Holder:</b> Aarav Sharma<br/><b>Address:</b> 402, Sovereign Heights, 12th Main<br/>HAL 2nd Stage, Indiranagar, Bengaluru - 560008<br/><b>Mobile:</b> +91 98450 12849 • <b>Email:</b> aarav.s@outlook.com", cell_normal),
            Paragraph(
                "<b>Account Number:</b> 50100492815892 (Savings - Regular)<br/>"
                "<b>Customer ID:</b> 94819283<br/>"
                "<b>Statement Period:</b> 01 Oct 2024 to 31 Oct 2024<br/>"
                "<b>Currency:</b> INR (Indian Rupee)",
                cell_normal
            )
        ]
    ]
    t_acc = Table(acc_info, colWidths=[280, 252])
    t_acc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_acc)
    story.append(Spacer(1, 10))

    # Reconciliation Summary Banner
    summary_data = [
        [
            Paragraph("<b>Opening Balance</b>", cell_bold),
            Paragraph("<b>Total Credits (Paisa Aaya)</b>", cell_bold),
            Paragraph("<b>Total Debits (Paisa Gaya)</b>", cell_bold),
            Paragraph("<b>Net Month Savings</b>", cell_bold),
            Paragraph("<b>Closing Balance</b>", cell_bold)
        ],
        [
            Paragraph("₹ 45,500.00", cell_num),
            Paragraph("+ ₹ 82,000.00", cell_credit),
            Paragraph("- ₹ 54,300.00", cell_debit),
            Paragraph("+ ₹ 27,700.00", cell_credit),
            Paragraph("₹ 73,200.00", cell_bold)
        ]
    ]
    t_sum = Table(summary_data, colWidths=[106, 115, 110, 101, 100])
    t_sum.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#FFFFFF")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>ACCOUNT STATEMENT TRANSACTIONS — BATCH 1 (01 OCT – 06 OCT 2024)</b>", section_title))
    story.append(Spacer(1, 5))

    # Page 1 Table (includes Opening Balance + Salary ₹82,000 + Swiggy ₹420)
    tx_p1 = [
        [
            Paragraph("<b>Date</b>", cell_bold),
            Paragraph("<b>Transaction Narrative / Description</b>", cell_bold),
            Paragraph("<b>Chq/Ref No.</b>", cell_bold),
            Paragraph("<b>Debits (₹)</b>", cell_bold),
            Paragraph("<b>Credits (₹)</b>", cell_bold),
            Paragraph("<b>Balance (₹)</b>", cell_bold)
        ],
        [
            Paragraph("01/10/2024", cell_normal),
            Paragraph("OPENING BALANCE BROUGHT FORWARD", cell_normal),
            Paragraph("—", cell_normal),
            Paragraph("", cell_normal),
            Paragraph("", cell_normal),
            Paragraph("45,500.00", cell_num)
        ],
        [
            Paragraph("02/10/2024", cell_normal),
            Paragraph("ACH CR-INFOSYS LIMITED-SALARY-OCT2024-CMS293810293", cell_normal),
            Paragraph("CMS293810293", cell_normal),
            Paragraph("", cell_normal),
            Paragraph("82,000.00", cell_credit),
            Paragraph("1,27,500.00", cell_num)
        ],
        [
            Paragraph("04/10/2024", cell_normal),
            Paragraph("UPI-SWIGGY-BANGALORE-UPI/428192849102/PAY", cell_normal),
            Paragraph("UPI428192849", cell_normal),
            Paragraph("420.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,27,080.00", cell_num)
        ],
        [
            Paragraph("05/10/2024", cell_normal),
            Paragraph("UPI-ZOMATO LIMITED-DELIVERY-UPI/428201948291/ORDER", cell_normal),
            Paragraph("UPI428201948", cell_normal),
            Paragraph("780.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,26,300.00", cell_num)
        ],
        [
            Paragraph("06/10/2024", cell_normal),
            Paragraph("POS-NATURES BASKET-INDIRANAGAR-BANGALORE-CARD5892", cell_normal),
            Paragraph("POS84920194", cell_normal),
            Paragraph("3,500.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,22,800.00", cell_num)
        ]
    ]
    t_p1 = Table(tx_p1, colWidths=[60, 232, 75, 55, 55, 55])
    t_p1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    for i in range(len(tx_p1[0])):
        tx_p1[0][i].style.textColor = colors.white
    story.append(t_p1)

    # ================= PAGE 2 =================
    story.append(PageBreak())
    story.append(make_header("Page 2"))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>ACCOUNT STATEMENT TRANSACTIONS — BATCH 2 (07 OCT – 14 OCT 2024)</b>", section_title))
    story.append(Spacer(1, 5))

    tx_p2 = [
        [
            Paragraph("<b>Date</b>", cell_bold),
            Paragraph("<b>Transaction Narrative / Description</b>", cell_bold),
            Paragraph("<b>Chq/Ref No.</b>", cell_bold),
            Paragraph("<b>Debits (₹)</b>", cell_bold),
            Paragraph("<b>Credits (₹)</b>", cell_bold),
            Paragraph("<b>Balance (₹)</b>", cell_bold)
        ],
        [
            Paragraph("07/10/2024", cell_normal),
            Paragraph("BBPS-BESCOM ELECTRICITY-BANGALORE-BILLPAY-94819284", cell_normal),
            Paragraph("BBPS94819284", cell_normal),
            Paragraph("2,140.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,20,660.00", cell_num)
        ],
        [
            Paragraph("08/10/2024", cell_normal),
            Paragraph("POS-SHELL INDIRANAGAR-FUEL AND LUBE-BLR-CARD5892", cell_normal),
            Paragraph("POS10293841", cell_normal),
            Paragraph("2,200.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,18,460.00", cell_num)
        ],
        [
            Paragraph("10/10/2024", cell_normal),
            Paragraph("NET-AMAZON PAY INDIA-RETAIL SHOPPING-ORD-9281039", cell_normal),
            Paragraph("AMZN9281039", cell_normal),
            Paragraph("3,900.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,14,560.00", cell_num)
        ],
        [
            Paragraph("12/10/2024", cell_normal),
            Paragraph("UPI-CULT.FIT FITNESS PASS-BANGALORE-UPI/428591829102", cell_normal),
            Paragraph("UPI428591829", cell_normal),
            Paragraph("3,500.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,11,060.00", cell_num)
        ],
        [
            Paragraph("14/10/2024", cell_normal),
            Paragraph("UPI-UBER TRIPS INDIA-COMMUTE-UPI/428710293847/RIDES", cell_normal),
            Paragraph("UPI428710293", cell_normal),
            Paragraph("960.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,10,100.00", cell_num)
        ]
    ]
    t_p2 = Table(tx_p2, colWidths=[60, 232, 75, 55, 55, 55])
    t_p2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    for i in range(len(tx_p2[0])):
        tx_p2[0][i].style.textColor = colors.white
    story.append(t_p2)

    # ================= PAGE 3 =================
    story.append(PageBreak())
    story.append(make_header("Page 3"))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>ACCOUNT STATEMENT TRANSACTIONS — BATCH 3 (15 OCT – 23 OCT 2024)</b>", section_title))
    story.append(Spacer(1, 5))

    tx_p3 = [
        [
            Paragraph("<b>Date</b>", cell_bold),
            Paragraph("<b>Transaction Narrative / Description</b>", cell_bold),
            Paragraph("<b>Chq/Ref No.</b>", cell_bold),
            Paragraph("<b>Debits (₹)</b>", cell_bold),
            Paragraph("<b>Credits (₹)</b>", cell_bold),
            Paragraph("<b>Balance (₹)</b>", cell_bold)
        ],
        [
            Paragraph("16/10/2024", cell_normal),
            Paragraph("POS-MYNTRA DESIGNS-ONLINE RETAIL SHOPPING-BLR", cell_normal),
            Paragraph("MYN39201948", cell_normal),
            Paragraph("2,500.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,07,600.00", cell_num)
        ],
        [
            Paragraph("18/10/2024", cell_normal),
            Paragraph("UPI-FRESHTOHOME-GROCERIES-UPI/428901928374/FOOD", cell_normal),
            Paragraph("UPI428901928", cell_normal),
            Paragraph("1,500.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,06,100.00", cell_num)
        ],
        [
            Paragraph("20/10/2024", cell_normal),
            Paragraph("POS-APOLLO PHARMACY-HEALTH AND WELLNESS-BLR-CARD5892", cell_normal),
            Paragraph("POS49102938", cell_normal),
            Paragraph("1,500.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,04,600.00", cell_num)
        ],
        [
            Paragraph("21/10/2024", cell_normal),
            Paragraph("ACH DR-AIRTEL XSTREAM BROADBAND-FIBER INTERNET-BLR", cell_normal),
            Paragraph("ACH82910394", cell_normal),
            Paragraph("1,400.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,03,200.00", cell_num)
        ],
        [
            Paragraph("22/10/2024", cell_normal),
            Paragraph("UPI-UBER COMMUTE-BANGALORE-UPI/429102938475/CAB", cell_normal),
            Paragraph("UPI429102938", cell_normal),
            Paragraph("1,000.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,02,200.00", cell_num)
        ],
        [
            Paragraph("23/10/2024", cell_normal),
            Paragraph("POS-THE ROASTERY COFFEE CAFE-FOOD-INDIRANAGAR", cell_normal),
            Paragraph("POS59102948", cell_normal),
            Paragraph("2,000.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("1,00,200.00", cell_num)
        ]
    ]
    t_p3 = Table(tx_p3, colWidths=[60, 232, 75, 55, 55, 55])
    t_p3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    for i in range(len(tx_p3[0])):
        tx_p3[0][i].style.textColor = colors.white
    story.append(t_p3)

    # ================= PAGE 4 =================
    story.append(PageBreak())
    story.append(make_header("Page 4"))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>ACCOUNT STATEMENT TRANSACTIONS — BATCH 4 (24 OCT – 31 OCT 2024)</b>", section_title))
    story.append(Spacer(1, 5))

    # Page 4 contains Rent ₹18,000 and SBI Auto Loan ₹9,000 and closing summary
    tx_p4 = [
        [
            Paragraph("<b>Date</b>", cell_bold),
            Paragraph("<b>Transaction Narrative / Description</b>", cell_bold),
            Paragraph("<b>Chq/Ref No.</b>", cell_bold),
            Paragraph("<b>Debits (₹)</b>", cell_bold),
            Paragraph("<b>Credits (₹)</b>", cell_bold),
            Paragraph("<b>Balance (₹)</b>", cell_bold)
        ],
        [
            Paragraph("25/10/2024", cell_normal),
            Paragraph("ACH DR-STATE BANK OF INDIA-AUTO LOAN EMI-LN39281729", cell_normal),
            Paragraph("ACH74920194", cell_normal),
            Paragraph("9,000.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("91,200.00", cell_num)
        ],
        [
            Paragraph("28/10/2024", cell_normal),
            Paragraph("NEFT DR-HDFC0000041-HOUSE RENT OCT2024 TO LANDLORD RAJESH VERMA", cell_normal),
            Paragraph("N28102938102", cell_normal),
            Paragraph("18,000.00", cell_debit),
            Paragraph("", cell_normal),
            Paragraph("73,200.00", cell_num)
        ],
        [
            Paragraph("31/10/2024", cell_normal),
            Paragraph("CLOSING BALANCE CARRIED FORWARD", cell_bold),
            Paragraph("—", cell_normal),
            Paragraph("", cell_normal),
            Paragraph("", cell_normal),
            Paragraph("<b>73,200.00</b>", cell_bold)
        ]
    ]
    t_p4 = Table(tx_p4, colWidths=[60, 232, 75, 55, 55, 55])
    t_p4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    for i in range(len(tx_p4[0])):
        tx_p4[0][i].style.textColor = colors.white
    story.append(t_p4)
    story.append(Spacer(1, 15))

    # Audit & Statutory Verification Table on Page 4
    final_audit = [
        [
            Paragraph("<b>FINANCIAL AUDIT & STATEMENT RECONCILIATION CERTIFICATE</b>", cell_bold),
            Paragraph("<b>OFFICIAL SEAL</b>", cell_bold)
        ],
        [
            Paragraph(
                "• Opening Balance on 01-Oct-2024: <b>₹ 45,500.00</b><br/>"
                "• Total Inward Remittances / Credits (1 transaction): <b>+ ₹ 82,000.00</b><br/>"
                "• Total Outward Remittances / Debits (12 transactions): <b>- ₹ 54,300.00</b><br/>"
                "• Net Monthly Accumulation: <b>+ ₹ 27,700.00</b><br/>"
                "• Closing Reconciled Balance on 31-Oct-2024: <b>₹ 73,200.00</b><br/>"
                "<font color='#065F46'><b>STATUS: ZERO ARITHMETIC VARIANCE • RECONCILED</b></font><br/>"
                "Generated on: 31-Oct-2024 23:59:59 IST • System Generated E-Statement",
                cell_normal
            ),
            Paragraph(
                "<font size=7 color='#334155'>Digitally signed by:<br/>"
                "<b>HDFC BANK LTD CENTRAL SERVER</b><br/>"
                "Time: 2024.11.01 04:12:18 IST<br/>"
                "Location: Mumbai Data Center 02<br/>"
                "Signature Valid: SHA256-RSA<br/>"
                "RBI Regulation Act 1949 Section 35A</font>",
                cell_normal
            )
        ]
    ]
    t_audit = Table(final_audit, colWidths=[360, 172])
    t_audit.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#64748B")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_audit)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Statement generated successfully at: {output_path}")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "uploads")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "HDFC_Bank_Statement_Oct2024.pdf")
    create_hdfc_statement(out_file)
