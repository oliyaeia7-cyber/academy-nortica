from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import base64

from database import Base, engine
import models  # noqa: F401  -> ثبت مدل‌ها روی Base
from assets import LOGO_DATA_URI

import users_router
import plans_router
import chat_planner_router
import study_router
import exams_router
import leaderboard_router
import support_router
import subscription_router

import pages

Base.metadata.create_all(bind=engine)

app = FastAPI(title="نورتیکا | Noortika")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router.router)
app.include_router(plans_router.router)
app.include_router(chat_planner_router.router)
app.include_router(study_router.router)
app.include_router(exams_router.router)
app.include_router(leaderboard_router.router)
app.include_router(support_router.router)
app.include_router(subscription_router.router)

_LOGO_BYTES = base64.b64decode(LOGO_DATA_URI.split(",", 1)[1])


@app.get("/logo.jpg")
def serve_logo():
    return Response(
        content=_LOGO_BYTES,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=604800"},
    )


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    site = pages.SITE_URL or ""
    return (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {site}/sitemap.xml\n"
    )


@app.get("/sitemap.xml")
def sitemap_xml():
    site = pages.SITE_URL or ""
    paths = ["/", "/plan", "/exam", "/leaderboard", "/pricing", "/support", "/blog"]
    paths += [f"/blog/{slug}" for slug in pages.BLOG_POSTS.keys()]
    urls = "\n".join(
        f"  <url><loc>{site}{p}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>"
        for p in paths
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>"
    )
    return Response(content=xml, media_type="application/xml")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home():
    return pages.index_page()


@app.get("/plan", response_class=HTMLResponse)
def plan_page():
    return pages.plan_page()


@app.get("/exam", response_class=HTMLResponse)
def exam_page():
    return pages.exam_page()


@app.get("/leaderboard", response_class=HTMLResponse)
def leaderboard_page():
    return pages.leaderboard_page()


@app.get("/pricing", response_class=HTMLResponse)
def pricing_page():
    return pages.pricing_page()


@app.get("/support", response_class=HTMLResponse)
def support_page():
    return pages.support_page()


@app.get("/blog", response_class=HTMLResponse)
def blog_index():
    return pages.blog_index_page()


@app.get("/blog/{slug}", response_class=HTMLResponse)
def blog_post(slug: str):
    html = pages.blog_post_page(slug)
    if html is None:
        return HTMLResponse(
            content="<h1 style='font-family:sans-serif;text-align:center;margin-top:80px;'>مقاله مورد نظر پیدا نشد.</h1>"
                    "<p style='text-align:center;'><a href='/blog'>بازگشت به وبلاگ</a></p>",
            status_code=404,
        )
    return HTMLResponse(content=html)
