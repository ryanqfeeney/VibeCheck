from datetime import datetime
from typing import Optional
import mimetypes
from config.security_config import SecurityConfig

def validate_file(file) -> Optional[str]:
    if file.size > SecurityConfig.MAX_FILE_SIZE:
        return "File too large"
    
    # Get file type from extension
    file_type, _ = mimetypes.guess_type(file.name)
    if not file_type or file_type not in SecurityConfig.ALLOWED_MIME_TYPES:
        return "Invalid file type"
    
    return None

def sanitize_text(text: str) -> str:
    if len(text) > SecurityConfig.MAX_TEXT_LENGTH:
        raise ValueError(f"Text exceeds maximum length of {SecurityConfig.MAX_TEXT_LENGTH}")
    return text.strip()