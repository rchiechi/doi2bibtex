import re
from .getdoilogger import return_logger

logger = return_logger(__name__)

def validate_and_fix_bibtex(bibtex: str) -> str:
    """
    Validate and fix common BibTeX syntax errors.
    
    Args:
        bibtex: Raw BibTeX string
        
    Returns:
        Fixed BibTeX string or empty string if unfixable
    """
    if not bibtex or not bibtex.strip():
        return ''
    
    bibtex = bibtex.strip()
    
    # Check if it starts with @ and has basic structure
    if not bibtex.startswith('@'):
        logger.error(f"Invalid BibTeX: doesn't start with @")
        return ''
    
    # Extract the entry type and key
    try:
        # Find the first { and extract everything before it
        first_brace = bibtex.find('{')
        if first_brace == -1:
            logger.error(f"Invalid BibTeX: no opening brace found")
            return ''
        
        entry_header = bibtex[:first_brace]
        
        # Find matching closing brace for the entry
        brace_count = 0
        last_brace = -1
        for i, char in enumerate(bibtex[first_brace:], first_brace):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    last_brace = i
                    break
        
        if last_brace == -1:
            logger.error(f"Invalid BibTeX: unmatched braces")
            return ''
        
        # Extract the content between braces
        content = bibtex[first_brace+1:last_brace]
        
        # Split content into key and fields
        first_comma = content.find(',')
        if first_comma == -1:
            # No fields, just a key
            return bibtex
        
        entry_key = content[:first_comma].strip()
        fields_str = content[first_comma+1:].strip()
        
        # Parse and fix fields
        fixed_fields = []
        
        # Simple regex to match field = value pairs
        import re
        # This pattern matches: fieldname = {value} or fieldname = "value" or fieldname = value
        field_pattern = r'(\w+)\s*=\s*({[^}]*}|"[^"]*"|\S+)'
        
        # First, let's fix common issues
        # Replace any field name followed by comma without = value
        fields_str = re.sub(r'(\w+)\s*,', r'\1 = {},', fields_str)
        
        # Find all valid fields
        matches = re.finditer(field_pattern, fields_str)
        
        for match in matches:
            field_name = match.group(1)
            field_value = match.group(2)
            
            # Ensure value is properly quoted
            if not (field_value.startswith('{') or field_value.startswith('"')):
                # If it's a number, leave it as is, otherwise wrap in braces
                if not field_value.isdigit():
                    field_value = '{' + field_value + '}'
            
            fixed_fields.append(f'{field_name} = {field_value}')
        
        if not fixed_fields:
            # Try to salvage by splitting on commas and fixing each part
            parts = fields_str.split(',')
            for part in parts:
                part = part.strip()
                if '=' in part:
                    key, value = part.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if value and not (value.startswith('{') or value.startswith('"')):
                        if not value.isdigit():
                            value = '{' + value + '}'
                    if key and value:
                        fixed_fields.append(f'{key} = {value}')
        
        # Reconstruct the BibTeX entry
        if fixed_fields:
            fixed_bibtex = f"{entry_header}{{{entry_key},\n  " + ",\n  ".join(fixed_fields) + "\n}"
        else:
            fixed_bibtex = f"{entry_header}{{{entry_key}}}"
        
        return fixed_bibtex
        
    except Exception as e:
        logger.error(f"Error parsing BibTeX: {e}")
        return ''