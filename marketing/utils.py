from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

# Instantiate a signer (you can also configure a secret salt here if needed)
signer = TimestampSigner()


def generate_admission_token(prospect_id):
    """
    Generate a token for a prospect that includes the prospect_id and a timestamp.
    The token can be used in a URL.
    """
    return signer.sign(str(prospect_id))


def verify_admission_token(token, max_age=86400):
    """
    Verify the given token. If it is older than max_age (in seconds),
    or is invalid, return None; otherwise, return the prospect_id.
    """
    try:
        prospect_id = signer.unsign(token, max_age=max_age)
        return prospect_id
    except (SignatureExpired, BadSignature):
        return None


def get_progress_for_status(status):
    """
    Map the admission status to a progress percentage.
    Adjust the mapping as needed.
    """
    mapping = {
        'pending': 20,
        'documents_under_review': 40,
        'documents_review_cleared': 60,
        'cleared_by_admissions': 80,
        'awaiting_financial_clearance': 90,
        'student_cleared_financially': 100,
        'admission_completed': 100,
        'rejected': 0,
    }
    return mapping.get(status, 0)











