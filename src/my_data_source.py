import os
from dataclasses import dataclass
import fitz  # PyMuPDF for PDF text extraction
import pdfplumber  # For extracting tables
from src.git_utils import setup_repository, read_file_from_repo  # Import from git_utils.py
from teams.ai.tokenizers import Tokenizer
from teams.ai.data_sources import DataSource
from teams.state.state import TurnContext
from teams.state.memory import Memory

@dataclass
class Result:
    output: str
    length: int
    too_long: bool

class MyDataSource(DataSource):
    """
    A data source that searches through files in a Git repository for a given query.
    Supports ingestion of PDF files, including extracting tables.
    """

    def __init__(self, name):
        """
        Initializes the data source by ensuring the Git repository is up to date.
        """
        self.name = name
        self._data = []

        # Set up and pull the latest from the repository
        setup_repository()

        # Load files from the repository
        self._load_files()

    def _load_files(self):
        """
        Loads text and PDF files from the repository.
        """
        repo_path = os.path.join(os.path.dirname(__file__), "data_repo")
        files = os.listdir(repo_path)
        for file in files:
            file_path = os.path.join(repo_path, file)
            if file.endswith('.pdf'):
                self._data.append(self._extract_pdf_data(file_path))
            else:
                file_content = read_file_from_repo(file)  # Use read_file_from_repo to read non-PDF files
                if file_content:
                    self._data.append(file_content)

    def name(self):
        return self.name

    async def render_data(self, context: TurnContext, memory: Memory, tokenizer: Tokenizer, maxTokens: int):
        """
        Renders the data source as a string of text, searching for a query in text or PDF data.
        """
        query = memory.get('temp.input')
        if not query:
            return Result('', 0, False)
        
        result = ''
        # Search through the loaded data for matches
        for data in self._data:
            if query in data:
                result += data

        # Keyword-based search in case of no exact match
        if not result:
            if 'history' in query.lower() or 'company' in query.lower():
                result += self._data[0] if len(self._data) > 0 else ""
            if 'perksplus' in query.lower() or 'program' in query.lower():
                result += self._data[1] if len(self._data) > 1 else ""
            if 'northwind' in query.lower() or 'health' in query.lower():
                result += self._data[2] if len(self._data) > 2 else ""
        
        return Result(self.formatDocument(result), len(result), False) if result else Result('', 0, False)

    def formatDocument(self, result):
        """
        Formats the result string.
        """
        return f"<context>{result}</context>"

    def _extract_pdf_data(self, file_path):
        """
        Extracts text and tables from a PDF file.
        """
        extracted_text = ""
        
        # Extract text using PyMuPDF
        with fitz.open(file_path) as pdf:
            for page in pdf:
                extracted_text += page.get_text("text")

        # Extract tables using pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    # Convert table to a readable format
                    table_text = self._format_table(table)
                    extracted_text += "\n" + table_text

        return extracted_text

    def _format_table(self, table):
        """
        Formats a table (list of lists) into a string for easy reading.
        """
        formatted_table = "\n".join(["\t".join(map(str, row)) for row in table])
        return f"<table>\n{formatted_table}\n</table>"
