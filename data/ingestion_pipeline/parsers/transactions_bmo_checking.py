import csv

def parse(filepath):
    """
    Parses a BMO Checking CSV file and returns standardized transaction data.
    """
    transactions = []
    
    with open(filepath, mode='r', encoding='utf-8') as file:
        # Using an iterator instead of readlines() handles the file lazily,
        # which is safer and faster regardless of file size.
        iterator = iter(file)
        
        # Advance the iterator until we hit the row before the data
        for line in iterator:
            if line.startswith("First Bank Card"):
                break
                
        # Skip the actual column headers line
        try:
            next(iterator)
        except StopIteration:
            pass # File ended unexpectedly
            
        # Pass the remaining iterator directly to the CSV reader
        reader = csv.reader(iterator)
        
        for row in reader:
            if not row or len(row) < 5:
                continue 
                
            raw_date = row[2].strip()
            raw_amount = row[3].strip()
            raw_desc = row[4].strip()
            
            # Format YYYYMMDD to YYYY-MM-DD safely
            if len(raw_date) == 8:
                formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            else:
                formatted_date = raw_date
                
            clean_desc = " ".join(raw_desc.split())
            
            transaction = {
                "bank_company": "BMO",
                "account_type": "Checking",
                "amount": float(raw_amount),
                "date": formatted_date,
                "description": clean_desc
            }
            
            transactions.append(transaction)
            
    # Return the standardized payload for master.py to route
    return {
        "category": "transactions",
        "data": transactions
    }
