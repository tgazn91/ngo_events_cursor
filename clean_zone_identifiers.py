#!/usr/bin/env python3
import os
import argparse
import sys

def delete_zone_files(root_dir):
    deleted_count = 0
    error_count = 0
    found_count = 0  # New counter for found files
    
    print(f"\nStarting scan in: {os.path.abspath(root_dir)}")  # Show absolute path
    
    for root, dirs, files in os.walk(root_dir):
        if not files:  # Skip directories with no files
            continue
            
        print(f"\nScanning: {root} ({len(files)} files)")
        for file in files:
            # Case-insensitive check and exact match
            if "zone.identifier" in file.lower():
                found_count += 1
                file_path = os.path.join(root, file)
                print(f"Found match: {file_path}")  # Show found files before deletion
                
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                    deleted_count += 1
                except OSError as e:
                    print(f"Error deleting {file_path}: {e}", file=sys.stderr)
                    error_count += 1

    print(f"\nScan complete. Found {found_count} Zone.Identifier files.")
    print(f"Deleted {deleted_count} files.")
    if error_count > 0:
        print(f"Encountered {error_count} errors", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Remove Zone.Identifier files')
    parser.add_argument('directory', nargs='?', default=os.getcwd(),
                      help='Directory to clean (default: current directory)')
    args = parser.parse_args()

    print(f"Scanning directory: {args.directory}")
    delete_zone_files(args.directory)
