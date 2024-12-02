from typing import Dict, Any, Union
from azure.ai.documentintelligence.models import AnalyzeResult, DocumentPage, DocumentSpan, DocumentTable
from typing import List
from dataclasses import dataclass

from ..core.interfaces.text_preprocessor import TextPreprocessor
from ..core.exceptions import PreprocessingError
from ..core import TABLE_START_TOKEN, TABLE_END_TOKEN, PAGE_TOKEN

@dataclass
class DocumentElement:
    type: str
    content: any
    page_num: int
    vertical_position: float  # Y-coordinate to determine position on page

class BasicPreprocessorV2(TextPreprocessor):
    """Enhanced implementation of the TextPreprocessor interface with improved layout handling."""
    
    def __init__(self, table_format: str = "markdown"):
        """Initialize the preprocessor.
        
        Args:
            table_format: Format to use for table markup ("markdown" or "csv")
        """
        self.table_format = table_format

    def process(self, content: Union[str, AnalyzeResult]) -> str:
        """Process and format the extracted text."""
        try:
            if isinstance(content, str):
                return self._process_text(content)
            elif isinstance(content, AnalyzeResult):
                return self._process_analyze_result(content)
            elif hasattr(content, 'raw_response') and isinstance(content.raw_response, AnalyzeResult):
                return self._process_analyze_result(content.raw_response)
            else:
                raise PreprocessingError(f"Unsupported content type: {type(content)}")
        except Exception as e:
            raise PreprocessingError(f"Preprocessing failed: {str(e)}")

    def _process_text(self, text: str) -> str:
        """Process plain text input."""
        # Basic text cleaning
        cleaned = text.strip()
        cleaned = self._normalize_whitespace(cleaned)

    def _process_analyze_result(self, result: AnalyzeResult) -> str:
        """Process Azure Document Intelligence result."""
        elements = self._collect_document_elements(result)
        elements.sort(key=lambda x: (x.page_num, x.vertical_position))
        return self._format_document(elements)

    def _collect_document_elements(self, result: AnalyzeResult) -> list[DocumentElement]:
        """Collect all document elements with their positions."""
        elements = []
        
        # Iterate through pages and lines
        for page_num, page in enumerate(result.pages, 1):
            for line in page.lines:
                elements.append(DocumentElement(
                    content=line.content,
                    page_num=page_num,
                    type='line',
                    vertical_position=line.bounding_box[1] if hasattr(line, 'bounding_box') else 0
                ))
                
            # Handle tables if present
            if hasattr(result, 'tables'):
                for table in result.tables:
                    if table.bounding_regions[0].page_number == page_num:
                        elements.append(DocumentElement(
                            content=table,
                            page_num=page_num,
                            type='table',
                            vertical_position=table.bounding_regions[0].polygon[1]
                        ))
        
        return elements

    def _format_document(self, elements: List[DocumentElement]) -> str:
        """Format the document with elements in correct order."""
        formatted_text = []
        
        current_page = 0
        for element in elements:
            # Add page marker when page changes
            if element.page_num != current_page:
                current_page = element.page_num
                formatted_text.append(f"\n{PAGE_TOKEN}\n")
            
            # Format element based on its type
            if element.type == 'table':
                formatted_text.append(self._format_table(element.content))
            elif element.type == 'title':
                formatted_text.append(f"\n# {element.content}\n")
            elif element.type == 'sectionHeading':
                formatted_text.append(f"\n## {element.content}\n")
            else:
                formatted_text.append(element.content + "\n")
                
        return '\n'.join(formatted_text)

    def _format_table(self, table: DocumentTable) -> str:
        """Format table in a structured way with proper alignment and borders."""
        # Group cells by row index
        row_cells = {}
        for cell in table['cells']:
            row_index = cell['rowIndex']
            if row_index not in row_cells:
                row_cells[row_index] = []
            row_cells[row_index].append(cell)
        
        # Get max width for each column first
        column_widths = {}
        for row in row_cells.values():
            for cell in row:
                col_idx = cell['columnIndex']
                content_width = len(cell['content'])
                if col_idx not in column_widths or content_width > column_widths[col_idx]:
                    column_widths[col_idx] = content_width
        
        # Create horizontal separator function
        def make_separator(widths):
            return "+".join("-" * (w + 2) for w in widths.values())
        
        # Now we can safely create the separator
        separator = make_separator(column_widths)
        
        # Format the table
        formatted_rows = []
        formatted_rows.append(TABLE_START_TOKEN)
        formatted_rows.append(separator)
        
        # Format rows with borders
        for row_idx in sorted(row_cells.keys()):
            row = sorted(row_cells[row_idx], key=lambda x: x['columnIndex'])
            formatted_cells = []
            
            for cell in row:
                content = cell['content']
                col_idx = cell['columnIndex']
                # Handle column spans
                if 'columnSpan' in cell and cell['columnSpan'] > 1:
                    # Calculate total width for spanned columns
                    total_width = sum(column_widths.get(i, 0) for i in range(col_idx, col_idx + cell['columnSpan']))
                    formatted_cells.append(content.ljust(total_width))
                else:
                    # Normal cell padding
                    formatted_cells.append(content.ljust(column_widths[col_idx]))
            
            formatted_rows.append("| " + " | ".join(formatted_cells) + " |")
            formatted_rows.append(separator)
        
        formatted_rows.append(TABLE_END_TOKEN)
        return "\n".join(formatted_rows)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        import re
        return re.sub(r'\s+', ' ', text)

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'BasicPreprocessorV2':
        """Create a preprocessor instance from configuration."""
        return cls(
            table_format=config.get('preprocessors', {}).get('basic', {}).get('table_format', 'markdown')
        )

    @property
    def supported_formats(self) -> list[str]:
        """Return list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return ['pdf', 'jpeg', 'jpg', 'png', 'tiff', 'tif', 'bmp']