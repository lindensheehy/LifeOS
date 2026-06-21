import csv

def parse(filepath):
    """
    Parses a Wealthsimple CSV file and returns standardized transaction data.
    Utilizes DictReader to safely handle a large number of potentially sparse columns.
    """
    transactions = []
    
    # utf-8-sig handles potential Byte Order Marks (BOM) common in generated CSVs
    with open(filepath, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Safely get the value, defaulting to '' if it is missing or None
            raw_cash = str(row.get('net_cash_amount') or '').strip()
            
            # If it's still empty after stripping, skip it (no cash moved)
            if not raw_cash:
                continue 
                
            amount = float(raw_cash)
            formatted_date = str(row.get('transaction_date') or '').strip()
            
            # Apply safe-getter to all description components
            desc_parts = [
                str(row.get('activity_type') or '').strip(),
                str(row.get('activity_sub_type') or '').strip(),
                str(row.get('symbol') or '').strip(),
                str(row.get('name') or '').strip()
            ]
            
            clean_desc = " - ".join([part for part in desc_parts if part])
            
            transaction = {
                "bank_company": "Wealthsimple",
                "account_type": str(row.get('account_type') or 'Unknown').strip(),
                "amount": amount,
                "date": formatted_date,
                "description": clean_desc,
                
                # Retain Wealthsimple-specific metadata
                "ws_activity_type": str(row.get('activity_type') or '').strip(),
                "ws_symbol": str(row.get('symbol') or '').strip(),
                "ws_quantity": str(row.get('quantity') or '').strip()
            }
            
            transactions.append(transaction)
            
    # Return the standardized payload
    return {
        "category": "transactions",
        "data": transactions
    }
