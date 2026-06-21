import xml.etree.ElementTree as ET

def parse(filepath):
    """
    Streams an Apple Health export.xml file to extract records without 
    blowing up system memory.
    """
    health_data = []
    
    # iterparse() streams the file, emitting an 'end' event when an element is fully read
    context = ET.iterparse(filepath, events=('end',))
    
    for event, elem in context:
        if elem.tag == 'Record':
            # Apple prepends 'HKQuantityTypeIdentifier' or 'HKCategoryTypeIdentifier'.
            raw_type = elem.get('type', '')
            clean_type = raw_type.replace('HKQuantityTypeIdentifier', '').replace('HKCategoryTypeIdentifier', '')
            
            raw_start_date = elem.get('startDate', '')
            
            # If there's no date, we can't route it, so skip it
            if not raw_start_date:
                elem.clear()
                continue
                
            # Extract just the YYYY-MM-DD for our master.py routing
            # Format is "2018-08-22 10:11:20 -0400"
            formatted_date = raw_start_date[:10]
            
            record = {
                "category": "AppleHealth", 
                "type": clean_type,
                "source": elem.get('sourceName', 'Unknown'),
                "value": elem.get('value', ''),
                "unit": elem.get('unit', ''),
                "start_time": raw_start_date,
                "end_time": elem.get('endDate', ''),
                "date": formatted_date
            }
            
            # Extract nested MetadataEntry tags
            metadata = {}
            for child in elem:
                if child.tag == 'MetadataEntry':
                    metadata[child.get('key')] = child.get('value')
            
            if metadata:
                record["metadata"] = metadata
                
            health_data.append(record)
            
            # --- CRITICAL MEMORY OPTIMIZATION ---
            # This deletes the element from memory once we've extracted its data.
            elem.clear() 

    return {
        "category": "apple_health", # Routes to apple_health.json
        "data": health_data
    }
