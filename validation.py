def validate_user_data(**fields):
    missing = [key for key, value in fields.items() if not value]
    return missing

