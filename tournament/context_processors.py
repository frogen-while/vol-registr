from .constants import REGISTRATION_CLOSED


def registration_status(request):
    return {"registration_closed": REGISTRATION_CLOSED}
