import csv
import os

def parse(filepath):
    """
    Parses a Simplii CSV file and returns standardized transaction data.
    Strictly requires 'checking', 'saving', or 'credit' to be present in the filename.
    """
    filename = os.path.basename(filepath).lower()
    
    # Strict validation: Fail loudly if the account type cannot be determined
    if 'saving' in filename:
        account_type = 'Saving'
    elif 'credit' in filename:
        account_type = 'Credit'
    elif 'checking' in filename:
        account_type = 'Checking'
    else:
        raise ValueError(
            f"Validation Failed: Simplii filename '{filename}' must contain "
            "'checking', 'saving', or 'credit' to determine account type."
        )
        
    transactions = []
    
    with open(filepath, mode='r', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        
        try:
            next(reader) 
        except StopIteration:
            pass
            
        for row in reader:
            if not row or len(row) < 4:
                continue 
                
            raw_date = row[0].strip()
            raw_desc = row[1].strip()
            funds_out = row[2].strip()
            funds_in = row[3].strip()
            
            try:
                month, day, year = raw_date.split('/')
                formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            except ValueError:
                continue
            
            clean_desc = " ".join(raw_desc.split())
            
            if funds_in:
                amount = float(funds_in.replace(',', ''))
            elif funds_out:
                amount = -float(funds_out.replace(',', ''))
            else:
                continue
            
            transaction = {
                "bank_company": "Simplii",
                "account_type": account_type,
                "amount": amount,
                "date": formatted_date,
                "description": clean_desc
            }
            
            transactions.append(transaction)

    return {
        "category": "transactions",
        "data": transactions
    }
