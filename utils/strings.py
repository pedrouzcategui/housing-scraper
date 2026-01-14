import unicodedata

def to_snake_case(text):
    normalized = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
    return ''.join(c if c.isalnum() or c == '_' else '_' for c in normalized.lower().replace(' ', '_').replace('-', '_'))