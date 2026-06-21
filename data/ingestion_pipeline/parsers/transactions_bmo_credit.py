import csv

def parse(filepath):
    """
    Parses a BMO Credit CSV file and returns standardized transaction data.
    """
    transactions = []
    
    with open(filepath, mode='r', encoding='utf-8') as file:
        iterator = iter(file)
        
        # Advance the iterator until we hit the header row
        for line in iterator:
            if line.startswith("Item #"):
                # We found the header row and consumed it.
                # The next iteration will be the first row of actual data.
                break
                
        # Pass the remaining iterator directly to the CSV reader
        reader = csv.reader(iterator)
        
        for row in reader:
            if not row or len(row) < 6:
                continue 
                
            # Index 2: Transaction Date, Index 4: Amount, Index 5: Description
            raw_date = row[2].strip()
            raw_amount = row[4].strip()
            raw_desc = row[5].strip()
            
            # Reformat YYYYMMDD to ISO YYYY-MM-DD
            if len(raw_date) == 8:
                formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            else:
                formatted_date = raw_date
                
            # Invert the sign: BMO purchases are positive, payments are negative.
            # We multiply by -1 so purchases become negative (money out).
            amount = float(raw_amount) * -1
            
            # Clean up whitespace gaps
            clean_desc = " ".join(raw_desc.split())
            
            transaction = {
                "bank_company": "BMO",
                "account_type": "Credit",
                "amount": amount,
                "date": formatted_date,
                "description": clean_desc
            }
            
            transactions.append(transaction)
            
    # Return the standardized payload
    return {
        "category": "transactions",
        "data": transactions
    }
