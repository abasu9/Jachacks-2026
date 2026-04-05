#!/usr/bin/env python3
"""
Employee Ranking Script

Reads employee data from CSV, computes deterministic ranking scores,
and outputs ranked results.

Usage:
    python3 employee_ranker.py input.csv output.csv
"""

import argparse
import csv
import logging
import math
import os
import sys


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def validate_employee_data(ap, pip_count, row_num):
    """
    Validate AP and pip_count values.
    
    Args:
        ap: Annual Performance score (should be float 0-2)
        pip_count: Number of PIPs (should be int >= 0)
        row_num: Row number for error reporting
    
    Returns:
        tuple: (is_valid, ap_float, pip_count_int, error_message)
    """
    try:
        ap_float = float(ap)
    except (ValueError, TypeError):
        return False, None, None, f"Row {row_num}: Invalid AP value '{ap}' (not numeric)"
    
    if ap_float < 0 or ap_float > 2:
        return False, None, None, f"Row {row_num}: AP value {ap_float} out of range [0, 2]"
    
    try:
        pip_count_int = int(pip_count)
    except (ValueError, TypeError):
        return False, None, None, f"Row {row_num}: Invalid pip_count '{pip_count}' (not numeric)"
    
    if pip_count_int < 0:
        return False, None, None, f"Row {row_num}: pip_count {pip_count_int} cannot be negative"
    
    return True, ap_float, pip_count_int, None


def calculate_ranking_score(ap, pip_count):
    """
    Calculate deterministic ranking score for an employee.
    
    Formula:
        ap_norm = AP / 2
        pip_penalty = 0.2 * log1p(pip_count)
        score = 0.85 * ap_norm - pip_penalty + 0.15
        score = clamp(score, 0, 1) and round to 2 decimals
    
    Args:
        ap: Annual Performance score (float, 0-2)
        pip_count: Number of PIPs (int, >= 0)
    
    Returns:
        tuple: (ap_normalized, pip_penalty, ranking_score)
    """
    # Normalize AP to [0, 1]
    ap_norm = ap / 2.0
    
    # Compute PIP penalty using diminishing returns
    pip_penalty = 0.2 * math.log1p(pip_count)
    
    # Calculate final score
    score = 0.85 * ap_norm - pip_penalty + 0.15
    
    # Clamp to [0, 1] and round to 2 decimal places
    score = round(max(0.0, min(1.0, score)), 2)
    
    # Round intermediate values for output
    ap_norm = round(ap_norm, 2)
    pip_penalty = round(pip_penalty, 2)
    
    return ap_norm, pip_penalty, score


def read_employee_csv(input_path):
    """
    Read employee data from CSV file.
    
    Args:
        input_path: Path to input CSV file
    
    Returns:
        tuple: (valid_rows, invalid_count)
            valid_rows: list of dicts with employee data
            invalid_count: number of skipped rows
    """
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    valid_rows = []
    invalid_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        if not headers:
            logger.error("CSV file is empty or has no headers")
            sys.exit(1)
        
        # Validate required columns
        required = {'employee_id', 'employee_name', 'AP', 'pip_count'}
        if not required.issubset(set(headers)):
            logger.error(f"Missing required columns. Need: {required}, Found: {set(headers)}")
            sys.exit(1)
        
        for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            ap = row.get('AP', '').strip()
            pip_count = row.get('pip_count', '').strip()
            
            # Skip empty rows
            if not ap and not pip_count:
                continue
            
            is_valid, ap_float, pip_int, error_msg = validate_employee_data(
                ap, pip_count, row_num
            )
            
            if not is_valid:
                logger.warning(error_msg)
                invalid_count += 1
                continue
            
            # Calculate scores
            ap_norm, pip_penalty, score = calculate_ranking_score(ap_float, pip_int)
            
            # Store required data plus computed values
            row_data = {
                'employee_id': row['employee_id'],
                'employee_name': row['employee_name'],
                'AP': row['AP'],
                'pip_count': row['pip_count'],
                'ap_normalized': ap_norm,
                'pip_penalty': pip_penalty,
                'ranking_score': score
            }
            
            valid_rows.append(row_data)
    
    return valid_rows, invalid_count


def write_output_csv(output_path, rows):
    """
    Write ranked employee data to CSV file.
    
    Args:
        output_path: Path to output CSV file
        rows: List of employee data dicts (already sorted and ranked)
    """
    output_headers = ['employee_id', 'employee_name', 'AP', 'pip_count', 
                      'ap_normalized', 'pip_penalty', 'ranking_score', 'rank']
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_headers)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Output written to: {output_path}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Calculate deterministic employee ranking scores from CSV data'
    )
    parser.add_argument('input_csv', help='Path to input CSV file')
    parser.add_argument('output_csv', help='Path to output CSV file')
    
    args = parser.parse_args()
    
    logger.info(f"Reading input file: {args.input_csv}")
    
    # Read and validate data
    valid_rows, invalid_count = read_employee_csv(args.input_csv)
    
    total_rows = len(valid_rows) + invalid_count
    
    if not valid_rows:
        logger.error("No valid rows to process")
        sys.exit(1)
    
    # Sort by ranking_score descending (highest score first)
    valid_rows.sort(key=lambda x: x['ranking_score'], reverse=True)
    
    # Assign ranks
    for rank, row in enumerate(valid_rows, start=1):
        row['rank'] = rank
    
    # Write output
    write_output_csv(args.output_csv, valid_rows)
    
    # Print summary
    print("\n" + "="*50)
    print("EXECUTION SUMMARY")
    print("="*50)
    print(f"Total rows read:        {total_rows}")
    print(f"Valid rows processed:   {len(valid_rows)}")
    print(f"Invalid rows skipped:   {invalid_count}")
    print(f"Output file:            {args.output_csv}")
    print("="*50 + "\n")


if __name__ == '__main__':
    main()
