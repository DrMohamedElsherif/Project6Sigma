import pandas as pd
from typing import Optional, Callable, List

class ExcelPipeline:
    def __init__(self, file_path: str):
        """Initialize the pipeline with an Excel file path."""
        self.file_path = file_path
        self.data = None

    def load_sheet(self, sheet_name: str) -> 'ExcelPipeline':
        """Load a specific sheet by name from the Excel file."""
        try:
            self.data = pd.read_excel(self.file_path, sheet_name=sheet_name)
            return self
        except Exception as e:
            print(f"✗ Error loading sheet: {e}")
            raise
    
    def export(self, file_path: str, format: str = 'csv') -> 'ExcelPipeline':
        """Export the processed data to a file. ONLY USE FOR DEBUGGING
        
        Args:
            file_path: Path where to save the file
            format: Export format ('csv', 'json', 'txt', 'xlsx')
        """
        if self.data is None:
            raise ValueError("No data to export. Load and process data first.")
        
        try:
            if format == 'csv':
                self.data.to_csv(file_path, index=False)
            
            print(f"✓ Exported data to '{file_path}' ({format})")
            return self
        except Exception as e:
            print(f"✗ Error exporting data: {e}")
            raise
        
    def get_data(self):
        """Return the sheet data as a clean CSV string."""
        if self.data is None:
            raise ValueError("No data loaded. Call load_sheet() first.")
        
        # Drop rows that are completely empty
        df = self.data.dropna(how='all')
        # Drop columns that are completely empty
        df = df.dropna(axis=1, how='all')
        
        # Convert to CSV (this will be much cleaner than the repr)
        csv_string = df.to_csv(index=False)
        
        return csv_string