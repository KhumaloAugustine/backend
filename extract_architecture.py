from docx import Document

doc = Document('PAMHoYA - Architecture Design Document.docx')
for p in doc.paragraphs:
    if p.text.strip():
        print(p.text)
