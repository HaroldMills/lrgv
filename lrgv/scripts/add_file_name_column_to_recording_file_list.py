"""
Script that inserts a file name column into a recording file list that
already includes a file path column. I wrote the script using GitHub
Copilot.
"""


import csv
from pathlib import Path, PureWindowsPath
import sys

def process_csv(input_file_path, output_file_path):
    """
    Process CSV file to add a "File Name" column after the first column.
    Handles Windows file paths while running on macOS.
    
    Args:
        input_file_path (str): Path to input CSV file
        output_file_path (str): Path to output CSV file
    """
    input_path = Path(input_file_path)
    output_path = Path(output_file_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file '{input_path}' does not exist")
    
    with open(input_path, 'r', newline='', encoding='utf-8') as infile, \
         open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # Process header row
        header = next(reader)
        new_header = [header[0], "File Name"] + header[1:]
        writer.writerow(new_header)
        
        # Process data rows
        for row in reader:
            if len(row) >= 5:  # Ensure row has at least 5 columns
                windows_file_path = row[0]
                # Use PureWindowsPath to correctly parse Windows paths on macOS
                file_name = PureWindowsPath(windows_file_path).name
                # Create new row with file name inserted after first column
                new_row = [row[0], file_name] + row[1:]
                writer.writerow(new_row)
            else:
                # Handle rows with fewer columns (write as-is)
                writer.writerow(row)

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_csv> <output_csv>")
        print("Example: python script.py 'Recording Files.csv' 'Recording Files Modified.csv'")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        process_csv(input_file, output_file)
        print(f"Successfully processed '{input_file}' -> '{output_file}'")
        
        # Show a preview of the results
        print("\nPreview of output file (first 3 rows):")
        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i < 3:
                    print(f"Row {i+1}: {row[:3]}...")  # Show first 3 columns
                else:
                    break
                    
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    