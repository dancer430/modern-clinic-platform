from rest_framework.throttling import AnonRateThrottle


class PortalAnonThrottle(AnonRateThrottle):
    scope = "portal_anon"
