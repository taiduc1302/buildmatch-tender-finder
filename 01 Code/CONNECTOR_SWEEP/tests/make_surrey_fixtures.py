"""Build representative synthetic Surrey in-process PDFs to exercise the parser.
We deliberately produce TWO layouts that mirror the two failure modes seen live:
  1) a flowing-text layout with NO ruling lines (extract_tables() -> [])
  2) a ruled-table layout
Both contain the exact id formats the brief requires.
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
import os

OUT = "tests/fixtures"
os.makedirs(OUT, exist_ok=True)

# ---- PDF 1: flowing text, no table lines (the hard case) -------------------
def make_textflow_pdf(path):
    c = canvas.Canvas(path, pagesize=letter)
    w, h = letter
    y = h - 60
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "City of Surrey - Rezoning Applications In Process")
    y -= 22
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "Application No    Address                         Applicant/Owner            Proposal/Stage")
    y -= 18
    c.setFont("Helvetica", 9)
    rows = [
        ("25-0366", "13458 78 Ave, Surrey BC", "Beedie Living Inc",
         "Rezoning for 6-storey mixed-use residential with site servicing - In Process"),
        ("25-0268", "7685 152 St, Surrey BC", "Polygon Homes Ltd",
         "Rezoning 42-unit townhouse development, civil site servicing - Public Notification"),
        ("26-0004", "10212 King George Blvd, Surrey BC", "Anthem Properties",
         "Rezoning + subdivision for industrial warehouse - First Reading"),
        ("7926-0157-00", "5402 184 St, Surrey BC", "Qualico Developments",
         "Subdivision and road works, multi-family - In Process"),
        ("7925-0256-00", "2899 156 St, Surrey BC", "Wesbild Holdings Ltd",
         "Development permit, storm sewer and drainage servicing - In Process"),
    ]
    for app_no, addr, applicant, scope in rows:
        line = f"{app_no}    {addr}    {applicant}    {scope}"
        c.drawString(50, y, line[:120])
        y -= 16
        if len(line) > 120:
            c.drawString(120, y, line[120:240])
            y -= 16
    c.showPage()
    c.save()

# ---- PDF 2: ruled table (the normal case) ----------------------------------
def make_ruled_pdf(path):
    doc = SimpleDocTemplate(path, pagesize=letter)
    styles = getSampleStyleSheet()
    elems = [Paragraph("City of Surrey - Development Permit Applications In Process", styles["Title"]),
             Spacer(1, 12)]
    data = [["Application No", "Address", "Applicant/Owner", "Proposal/Stage"]]
    rows = [
        ["24-0345", "16088 Fraser Hwy, Surrey BC", "Onni Group", "Development permit, commercial mixed-use site servicing"],
        ["25-0411", "13300 104 Ave, Surrey BC", "Concord Pacific", "DP institutional, utilities and grading"],
        ["7926-0312-00", "6677 King George Blvd, Surrey BC", "Ledingham McAllister", "Subdivision, multi-family, road works"],
    ]
    data.extend(rows)
    t = Table(data, colWidths=[80, 150, 110, 160])
    t.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    elems.append(t)
    doc.build(elems)

make_textflow_pdf(os.path.join(OUT, "surrey_rezoning_inprocess_sample.pdf"))
make_ruled_pdf(os.path.join(OUT, "surrey_dp_inprocess_sample.pdf"))
print("wrote synthetic Surrey PDFs to", OUT)
