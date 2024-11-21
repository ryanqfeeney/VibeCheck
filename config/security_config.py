class SecurityConfig:
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_TEXT_LENGTH = 5000
    ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png']
    RATE_LIMIT_PERIOD = 60  # seconds
    MAX_REQUESTS_PER_PERIOD = 4  # requests per minute
    MAX_DAILY_COST = 0.1  # $0.001 = 