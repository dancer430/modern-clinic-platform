from __future__ import annotations

from django.http import HttpResponse
from django.views.decorators.http import require_GET

from content.models import Department, DoctorProfile


def _iso(dt) -> str:
    return dt.strftime("%Y-%m-%d") if dt else ""


@require_GET
def sitemap(request) -> HttpResponse:
    base = f"{request.scheme}://{request.get_host()}"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    static_paths = [
        ("/portal/departments", ""),
        ("/portal/doctors", ""),
    ]
    for path, lastmod in static_paths:
        lines.append(f"<url><loc>{base}{path}</loc>")
        if lastmod:
            lines.append(f"<lastmod>{lastmod}</lastmod>")
        lines.append("</url>")
    for d in Department.objects.filter(is_published=True):
        lines.append(
            f"<url><loc>{base}/portal/departments/{d.slug}</loc>"
            f"<lastmod>{_iso(d.updated_at)}</lastmod></url>"
        )
    for p in DoctorProfile.objects.filter(is_published=True).select_related("user"):
        lines.append(
            f"<url><loc>{base}/portal/doctors/{p.user_id}</loc>"
            f"<lastmod>{_iso(p.updated_at)}</lastmod></url>"
        )
    lines.append("</urlset>")
    return HttpResponse("\n".join(lines), content_type="application/xml")
