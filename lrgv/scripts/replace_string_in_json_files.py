import argparse
from pathlib import Path


def main():

    parser = create_argument_parser()
    args = parser.parse_args()

    path = Path(args.directory_path)
    json_files = list(path.glob('*.json'))

    for filepath in json_files:

        try:

            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()

            if args.search_string in content:

                new_content = content.replace(
                    args.search_string, args.replacement_string)
                
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)

        except Exception as e:
            print(f'Error processing file "{filepath.name}": {e}')


def create_argument_parser():

    parser = argparse.ArgumentParser(
        description=\
            'Replace a string in all JSON files in a specified directory.')
    
    parser.add_argument(
        'directory_path', type=str,
        help='Path to the directory containing JSON files.')
    
    parser.add_argument(
        'search_string', type=str,
        help='The string to search for in the JSON files.')
    
    parser.add_argument(
        'replacement_string', type=str,
        help='The string to replace the search string with.')
    
    return parser


if __name__ == '__main__':
    main()
