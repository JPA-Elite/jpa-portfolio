import os
import unittest

from flask import Flask

from app.seo import (
    NOINDEX_ROBOTS,
    PROFESSIONAL,
    PROFESSIONAL_EXCLUDED_PAGES,
    SOCIAL,
    inject_page_seo,
    page_key_for_endpoint,
    page_seo_context,
    resolve_page_seo,
    site_variant,
)

TEMPLATE_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "templates"
)


def _make_app():
    app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
    app.config["LANDING_DOMAIN"] = "jpastack.com"
    app.config["PROFESSIONAL_DOMAIN"] = "professional.jpastack.com"
    app.config["SOCIAL_DOMAIN"] = "social.jpastack.com"
    app.config["ADMIN_DOMAIN"] = "config.jpastack.com"
    app.config["DOMAIN_ROUTING_ENABLED"] = True
    return app


class SeoResolutionTests(unittest.TestCase):
    def test_site_variant_maps_professional_and_everything_else_to_social(self):
        self.assertEqual(site_variant(PROFESSIONAL), PROFESSIONAL)
        self.assertEqual(site_variant("social"), SOCIAL)
        self.assertEqual(site_variant("unknown"), SOCIAL)
        self.assertEqual(site_variant(None), SOCIAL)

    def test_page_key_for_known_and_unknown_endpoints(self):
        self.assertEqual(page_key_for_endpoint("pages.portfolio"), "portfolio")
        self.assertEqual(page_key_for_endpoint("pages.gallery"), "gallery")
        self.assertEqual(page_key_for_endpoint("pages.built_app_details"), "app_details")
        self.assertEqual(page_key_for_endpoint("pages.unknown"), "")

    def test_professional_and_social_titles_differ_for_same_page(self):
        professional = resolve_page_seo("pages.portfolio", PROFESSIONAL)
        social = resolve_page_seo("pages.portfolio", SOCIAL)
        self.assertNotEqual(professional["title"], social["title"])
        self.assertNotEqual(professional["description"], social["description"])
        self.assertEqual(professional["site"], PROFESSIONAL)
        self.assertEqual(social["site"], SOCIAL)

    def test_each_public_page_has_unique_metadata_per_site(self):
        endpoints = [
            "pages.portfolio",
            "pages.gallery",
            "pages.vlog",
            "pages.music",
            "pages.concern",
            "pages.donation",
            "pages.booking",
        ]
        for site in (PROFESSIONAL, SOCIAL):
            titles = [resolve_page_seo(endpoint, site)["title"] for endpoint in endpoints]
            descriptions = [resolve_page_seo(endpoint, site)["description"] for endpoint in endpoints]
            self.assertEqual(len(titles), len(set(titles)), f"duplicate titles for {site}")
            self.assertEqual(
                len(descriptions), len(set(descriptions)), f"duplicate descriptions for {site}"
            )

    def test_unknown_endpoint_falls_back_to_site_defaults(self):
        meta = resolve_page_seo("pages.unknown", SOCIAL)
        self.assertTrue(meta["title"])
        self.assertTrue(meta["description"])
        self.assertEqual(meta["robots"], "index,follow")

    def test_overrides_apply(self):
        meta = resolve_page_seo(
            "pages.portfolio",
            PROFESSIONAL,
            {"title": "Custom", "robots": NOINDEX_ROBOTS},
        )
        self.assertEqual(meta["title"], "Custom")
        self.assertEqual(meta["robots"], NOINDEX_ROBOTS)

    def test_add_portfolio_form_is_noindex(self):
        meta = resolve_page_seo("pages.add_portfolio_form", SOCIAL)
        self.assertEqual(meta["robots"], NOINDEX_ROBOTS)

    def test_professional_personal_pages_are_noindex_and_uncanonical(self):
        endpoint_by_page = {
            "vlog": "pages.vlog",
            "music": "pages.music",
            "concern": "pages.concern",
            "donation": "pages.donation",
            "visitors": "pages.visitors",
        }
        self.assertEqual(set(endpoint_by_page), set(PROFESSIONAL_EXCLUDED_PAGES))
        for page_key, endpoint in endpoint_by_page.items():
            with self.subTest(page=page_key):
                professional = resolve_page_seo(endpoint, PROFESSIONAL)
                self.assertEqual(professional["robots"], NOINDEX_ROBOTS)
                self.assertEqual(professional["canonical"], "")
                social = resolve_page_seo(endpoint, SOCIAL)
                if page_key != "visitors":
                    self.assertEqual(social["robots"], "index,follow")


class SeoContextTests(unittest.TestCase):
    def test_canonical_uses_site_domain_and_request_path(self):
        app = _make_app()
        with app.test_request_context(
            "/gallery", headers={"Host": "professional.jpastack.com"}
        ):
            meta = page_seo_context()
        self.assertEqual(meta["canonical"], "https://professional.jpastack.com/gallery")
        self.assertEqual(meta["site"], PROFESSIONAL)
        self.assertIn("/static/images/", meta["image"])

    def test_social_canonical_prefers_landing_domain(self):
        app = _make_app()
        with app.test_request_context("/vlog", headers={"Host": "social.jpastack.com"}):
            meta = page_seo_context()
        self.assertEqual(meta["canonical"], "https://jpastack.com/vlog")
        self.assertEqual(meta["site"], SOCIAL)

    def test_context_processor_injects_page_seo(self):
        app = _make_app()
        app.context_processor(inject_page_seo)

        @app.route("/music", endpoint="pages.music")
        def music():
            from flask import render_template_string

            return render_template_string("{{ page_seo.title }}|{{ page_seo.page }}")

        client = app.test_client()
        response = client.get("/music", headers={"Host": "jpastack.com"})
        self.assertEqual(
            response.get_data(as_text=True),
            "My Favorite Music Playlist | Joshua Algadipe|music",
        )

    def test_seo_component_renders_core_tags_once(self):
        app = _make_app()
        app.context_processor(inject_page_seo)

        @app.route("/gallery", endpoint="pages.gallery")
        def gallery():
            from flask import render_template

            return render_template("components/seo_meta.html")

        response = app.test_client().get(
            "/gallery", headers={"Host": "professional.jpastack.com"}
        )
        html = response.get_data(as_text=True)
        self.assertEqual(html.count("<title>"), 1)
        self.assertEqual(html.count('name="description"'), 1)
        self.assertIn('name="robots" content="index,follow"', html)
        self.assertIn('rel="canonical" href="https://professional.jpastack.com/gallery"', html)
        self.assertIn('property="og:title"', html)
        self.assertIn('name="twitter:card" content="summary_large_image"', html)

    def test_component_omits_canonical_for_professional_excluded_page(self):
        app = _make_app()
        app.context_processor(inject_page_seo)

        @app.route("/music", endpoint="pages.music")
        def music_page():
            from flask import render_template

            return render_template("components/seo_meta.html")

        response = app.test_client().get(
            "/music", headers={"Host": "professional.jpastack.com"}
        )
        html = response.get_data(as_text=True)
        self.assertIn('name="robots" content="noindex,nofollow"', html)
        self.assertNotIn('rel="canonical"', html)


class SitemapTests(unittest.TestCase):
    def test_professional_sitemap_omits_personal_pages(self):
        from app.sitemap import generate_sitemap

        app = _make_app()
        with app.test_request_context("/sitemap.xml", headers={"Host": "jpastack.com"}):
            xml = generate_sitemap().get_data(as_text=True)
        self.assertIn("jpastack.com/vlog", xml)
        self.assertIn("jpastack.com/music", xml)
        self.assertIn("professional.jpastack.com/gallery", xml)
        self.assertIn("professional.jpastack.com/build", xml)
        self.assertNotIn("professional.jpastack.com/vlog", xml)
        self.assertNotIn("professional.jpastack.com/music", xml)
        self.assertNotIn("professional.jpastack.com/concern", xml)
        self.assertNotIn("professional.jpastack.com/donation", xml)


if __name__ == "__main__":
    unittest.main()
