ALLOWED_EMAIL_DOMAINS = frozenset({"gmail.com", "company.com"})


def validate_allowed_email_domain(email: str) -> str:
    """Require emails ending with @gmail.com or @company.com."""
    normalized = email.strip().lower()
    if "@" not in normalized:
        raise ValueError("Email must end with @gmail.com or @company.com")

    _, domain = normalized.rsplit("@", 1)
    if domain not in ALLOWED_EMAIL_DOMAINS:
        raise ValueError("Email must end with @gmail.com or @company.com")
    return normalized
