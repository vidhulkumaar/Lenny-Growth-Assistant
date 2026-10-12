from reportlab.pdfgen import canvas

def create_pdf():
    c = canvas.Canvas("test_data.pdf")
    
    # Page 1
    c.drawString(100, 800, "Lenny Growth Assistant Architecture Document")
    c.drawString(100, 780, "This is the first page of the test document.")
    c.drawString(100, 760, "Key Fact: The database used is PostgreSQL with pgvector.")
    c.showPage()
    
    # Page 2
    c.drawString(100, 800, "Testing Document Upload")
    c.drawString(100, 780, "This is the second page.")
    c.drawString(100, 760, "Key Fact: The embedding model used is all-MiniLM-L6-v2.")
    c.drawString(100, 740, "Secret Fact: The mascot for this project is a blue penguin.")
    c.showPage()
    
    c.save()

if __name__ == "__main__":
    create_pdf()
