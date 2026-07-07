from app.ingestion.base import IngestionSource
from app.models.domain import CustomerBundle


class PdfUploadIngestionSource(IngestionSource):
    """Stub for parsing an uploaded PDF bank statement (pdfplumber/camelot
    against reportlab-rendered synthetic PDFs, then AWS Textract in
    production). Deferred to the Phase 8 stretch goal — the MVP proves the
    scoring pipeline against structured synthetic statements first.
    """

    def load(self, external_ref: str) -> CustomerBundle:
        raise NotImplementedError("PDF ingestion is a Phase 8 stretch goal")
