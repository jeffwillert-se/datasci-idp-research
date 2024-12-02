from typing import Dict, Any, Union
from azure.ai.documentintelligence.models import AnalyzeResult
from shapely.geometry import Polygon

from ..core.interfaces.text_preprocessor import TextPreprocessor
from ..core.exceptions import PreprocessingError
from ..core import TABLE_START_TOKEN, TABLE_END_TOKEN, PAGE_TOKEN

class BasicPreprocessor(TextPreprocessor):
    """Basic implementation of the TextPreprocessor interface.
    
    This preprocessor handles common text formatting tasks:
    1. Table detection and formatting
    2. Page boundary marking
    3. Basic text cleaning and normalization
    """
    
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
        cleaned = self._normalize_line_endings(cleaned)
        
        return cleaned

    def _process_analyze_result(self, result: AnalyzeResult) -> str:
        """Process Azure Document Intelligence result."""
        processed_text = []
        
        for page_num, page in enumerate(result.pages, 1):
            # Get tables for this page from the root result
            tables = self._tables_by_page(page_num, result) if hasattr(result, 'tables') else []
            
            # Process text content
            lines = []
            for line in page.lines:
                # Create polygon from line's bounding box for intersection check
                if not self._is_in_tables_polygon(line, tables):
                    lines.append(line.content)
            
            # Combine page content
            page_text = "\n".join(lines)
            
            # Insert table markers at appropriate positions
            page_text = self._insert_tables(page_text, tables)
            
            # Add page marker
            processed_text.append(f"{PAGE_TOKEN}\n{page_text}")
        
        return "\n".join(processed_text)

    def _insert_tables(self, text: str, tables: list) -> str:
        """Insert formatted tables into text at appropriate positions."""
        if not tables:
            return text
        
        # Format tables with markers
        formatted_tables = self._extract_tables(tables)
        
        # Combine text and tables
        data_tables = [
            [
                table.bounding_regions[0].page_number,
                table.spans[0].offset,
                formatted['content']
            ]
            for table, formatted in zip(tables, formatted_tables)
        ]
        
        # Sort by position
        data_tables = sorted(data_tables, key=lambda x: x[1])
        
        # Insert tables into text
        result = text
        for table_data in data_tables:
            result += f"\n{table_data[2]}\n"
        
        return result

    def _tables_by_page(self, page_nr: int, result: AnalyzeResult) -> list:
        """Get tables for a specific page."""
        return [
            t for t in result.tables
            if t.bounding_regions[0].page_number == page_nr
        ]

    def _is_in_tables_polygon(self, line, tables) -> bool:
        """Check if a line is part of a table using polygon intersection."""
        if not hasattr(line, 'bounding_regions') or not tables:
            return False
        
        line_polygon = self._polygon_from_flat_list(line.bounding_regions[0].polygon)
        
        for table in tables:
            table_polygon = self._polygon_from_flat_list(
                table.bounding_regions[0].polygon
            )
            if line_polygon.centroid.within(table_polygon):
                return True
        return False

    def _polygon_from_flat_list(self, flat_list) -> Polygon:
        """Convert flat list of coordinates to a Polygon object."""
        points = list(zip(flat_list[::2], flat_list[1::2]))
        return Polygon(points)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace characters."""
        # Replace multiple spaces with single space
        return " ".join(text.split())

    def _normalize_line_endings(self, text: str) -> str:
        """Normalize line endings."""
        # Replace various line endings with \n
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _extract_tables(self, tables: list) -> list:
        """Extract and format tables."""
        formatted_tables = []
        for table in tables:
            if self.table_format == "markdown":
                formatted = self._format_table_markdown(table)
            else:
                formatted = self._format_table_csv(table)
            formatted_tables.append({
                'content': formatted,
                'bounds': table.bounding_regions[0].polygon if table.bounding_regions else None
            })
        return formatted_tables

    def _format_table_markdown(self, table) -> str:
        """Format table in markdown style."""
        result_str = []
        curr_row_idx = 0
        curr_row = []
        
        # Sort cells by row and column index
        cells = sorted(table.cells, key=lambda c: (c.row_index, c.column_index))
        
        for cell in cells:
            if cell.row_index > curr_row_idx:
                # Add the completed row
                result_str.append("| " + " | ".join(curr_row) + " |")
                curr_row = []
                curr_row_idx = cell.row_index
            
            curr_row.append(cell.content)
        
        # Add the last row
        if curr_row:
            result_str.append("| " + " | ".join(curr_row) + " |")
        
        if result_str:
            # Add header separator
            header_sep = "|" + "|".join(["---"] * len(result_str[0].split("|"))) + "|"
            result_str.insert(1, header_sep)
        
        return f"{TABLE_START_TOKEN}\n" + "\n".join(result_str) + f"\n{TABLE_END_TOKEN}"

    def _format_table_csv(self, table) -> str:
        """Format table in CSV style."""
        rows = []
        for row in table.cells:
            cols = [cell.content.replace(",", ";") for cell in row]  # Escape commas
            rows.append(",".join(cols))
        return f"{TABLE_START_TOKEN}\n" + "\n".join(rows) + f"\n{TABLE_END_TOKEN}"

    def _is_in_tables(self, line, tables) -> bool:
        """Check if a line is part of a table."""
        if not line.bounding_box or not tables:
            return False
            
        for table in tables:
            if table['bounds'] and self._is_within_bounds(line.bounding_box, table['bounds']):
                return True
        return False

    def _is_within_bounds(self, line_box, table_bounds) -> bool:
        """Check if a line is within table bounds."""
        # Simple bounding box intersection check
        return (line_box[0] >= table_bounds[0] and
                line_box[1] >= table_bounds[1] and
                line_box[2] <= table_bounds[2] and
                line_box[3] <= table_bounds[3])

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'BasicPreprocessor':
        """Create a preprocessor instance from configuration."""
        return cls(
            table_format=config.get('table_format', 'markdown')
        )

    @property
    def supported_formats(self) -> list[str]:
        """Return list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return ['pdf', 'jpeg', 'jpg', 'png', 'tiff', 'tif', 'bmp']
