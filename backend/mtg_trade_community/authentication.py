from rest_framework_simplejwt.authentication import JWTAuthentication


class OptionalJWTAuthentication(JWTAuthentication):
    """
    JWT auth that never raises on invalid/expired tokens.
    Invalid tokens are treated as anonymous (returns None).
    This allows AllowAny endpoints to work even when the client
    sends a stale token.
    """
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except Exception:
            return None
