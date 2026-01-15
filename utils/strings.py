import unicodedata
import re

def to_snake_case(text):
    normalized = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
    snake = ''.join(
        c if c.isalnum() or c == '_' else '_'
        for c in normalized.lower().replace(' ', '_').replace('-', '_')
    )
    snake = re.sub(r'_+', '_', snake)
    return snake.strip('_')