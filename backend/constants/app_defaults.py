CLIENT_IP_HEADER = "X-Forwarded-For"
UNKNOWN_VALUE = "Unknown"
UNKNOWN_MODEL_VALUE = "Unknown Model"

IPINFO_URL_TEMPLATE = "https://ipinfo.io/{ip}/json"
PH_TIMEZONE = "Asia/Manila"

SITEMAP_BASE_URL = "https://jpa-portfolio.onrender.com"


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data: https:; script-src 'self' https://cdn.jsdelivr.net https://unpkg.com https://hcaptcha.com https://*.hcaptcha.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; font-src 'self' https://cdn.jsdelivr.net; connect-src 'self' https://hcaptcha.com https://*.hcaptcha.com https://ipinfo.io; frame-src https://hcaptcha.com https://*.hcaptcha.com;",
}
