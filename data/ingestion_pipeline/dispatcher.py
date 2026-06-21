import os
import re
import shutil
import traceback
from datetime import datetime

# Import your parsers here
from parsers import transactions_bmo_checking
from parsers import transactions_bmo_credit
from parsers import transactions_simplii
from parsers import transactions_ws
from parsers import apple_health
from parsers import spotify
from parsers import discord
# from parsers import epic_games

# Preprocessed Discord channel files: "{ChannelID}_{SafeName}.json", where
# ChannelID is a 'c'-prefixed snowflake (e.g. c1298004514602745926_general.json).
# SafeName may itself contain dots (e.g. "..._Egg_Inc..json"), so the body is
# matched loosely up to the trailing .json extension.
_DISCORD_FILENAME_RE = re.compile(r'^c\d+_.*\.json$')

def _identify_file(filepath):
    """
    Peeks at the file to determine its type and returns a tuple:
    (file_type_string, parser_module)
    """
    filename = os.path.basename(filepath).lower()
    
    # 1. Filename-based routing (for strict cases like Simplii)
    if 'streaming_history' in filename:
        return 'spotify', spotify

    if 'simplii' in filename:
        return 'simplii', transactions_simplii

    # Discord preprocessed exports are identified purely by filename shape.
    if _DISCORD_FILENAME_RE.match(filename):
        return 'discord', discord

    # 2. Content-based routing (Peek at the first few lines safely)
    try:
        # utf-8-sig ensures we can read files with or without BOMs safely
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            # Safely read up to 10 lines without throwing exceptions on short files
            head = []
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                head.append(line)
                
        for line in head:
            # BMO Checking
            # We look for two key columns to guarantee it's not just a file 
            # that happens to contain the phrase "First Bank Card" in a note.
            if 'First Bank Card' in line and 'Transaction Type' in line:
                return 'bmo_checking', transactions_bmo_checking
            
            # BMO Credit
            if 'Item #' in line and 'Posting Date' in line and 'Transaction Amount' in line:
                return 'bmo_credit', transactions_bmo_credit
            
            # Wealthsimple
            # We check a few distinct columns from the WS schema
            if 'transaction_date' in line and 'net_cash_amount' in line and 'activity_type' in line:
                return 'wealthsimple', transactions_ws
            
            if '<!DOCTYPE HealthData' in line or '<HealthData' in line:
                return 'apple_health', apple_health
                
    except UnicodeDecodeError:
        pass # Likely a binary zip/db file, which we can route later based on extensions

    # Return None if we have no idea what this file is
    return None, None


def dispatch(filepath, processed_dir="processed", failed_dir="failed"):
    """
    The main entry point. Identifies the file, runs the parser, and moves the file.
    Returns the standardized data payload, or None if it fails.
    """
    # Ensure our target directories exist
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(failed_dir, exist_ok=True)
    
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1]
    now = datetime.now()
    timestamp = f"{now.strftime('%Y-%m-%d-%H%M%S')}-{now.strftime('%f')[:3]}"
    
    # 1. Identify the file
    file_type, parser_module = _identify_file(filepath)
    
    if not parser_module:
        print(f"Dispatcher: Could not identify '{filename}'. Moving to failed/.")
        failed_path = os.path.join(failed_dir, f"unidentified_{timestamp}_{filename}")
        shutil.move(filepath, failed_path)
        return None

    # 2. Execute the parser
    try:
        print(f"Dispatcher: Routing '{filename}' to {file_type} parser...")
        payload = parser_module.parse(filepath)
        
        # 3. Handle Success (Move to processed/)
        processed_path = os.path.join(processed_dir, f"{file_type}_{timestamp}{ext}")
        shutil.move(filepath, processed_path)
        print(f"Dispatcher: Success! Moved to {processed_path}")
        
        return payload
        
    except Exception as e:
        # 4. Handle Failure (Move to failed/ on crash or ValueError)
        print(f"Dispatcher: ERROR parsing '{filename}': {str(e)}")
        # traceback.print_exc() # Uncomment this if you need to debug a crashed parser
        
        failed_path = os.path.join(failed_dir, f"error_{file_type}_{timestamp}{ext}")
        shutil.move(filepath, failed_path)
        
        return None
