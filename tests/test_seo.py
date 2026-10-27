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

    def test_social_canonical_uses_social_domain(self):
        app = _make_app()
        with app.test_request_context("/vlog", headers={"Host": "social.jpastack.com"}):
            meta = page_seo_context()
        self.assertEqual(meta["canonical"], "https://social.jpastack.com/vlog")
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
    def test_professional_sitemap_lists_only_professional_pages(self):
        from app.sitemap import generate_sitemap

        app = _make_app()
        with app.test_request_context(
            "/sitemap.xml", base_url="https://professional.jpastack.com"
        ):
            xml = generate_sitemap().get_data(as_text=True)
        self.assertIn("<loc>https://professional.jpastack.com/portfolio</loc>", xml)
        self.assertIn("<loc>https://professional.jpastack.com/build</loc>", xml)
        self.assertNotIn("professional.jpastack.com/gallery", xml)
        self.assertNotIn("professional.jpastack.com/vlog", xml)
        self.assertNotIn("professional.jpastack.com/music", xml)
        self.assertNotIn("professional.jpastack.com/concern", xml)
        self.assertNotIn("professional.jpastack.com/donation", xml)
        self.assertNotIn("<loc>https://jpastack.com/", xml)

    def test_landing_sitemap_lists_professional_pages(self):
        from app.sitemap import generate_sitemap

        app = _make_app()
        with app.test_request_context(
            "/sitemap.xml", base_url="https://jpastack.com"
        ):
            xml = generate_sitemap().get_data(as_text=True)
        self.assertIn("<loc>https://professional.jpastack.com/portfolio</loc>", xml)
        self.assertIn("<loc>https://professional.jpastack.com/build</loc>", xml)
        self.assertNotIn("<loc>https://jpastack.com/", xml)
        self.assertNotIn("professional.jpastack.com/vlog", xml)

    def test_social_sitemap_lists_only_social_pages(self):
        from app.sitemap import generate_sitemap

        app = _make_app()
        with app.test_request_context(
            "/sitemap.xml", base_url="https://social.jpastack.com"
        ):
            xml = generate_sitemap().get_data(as_text=True)
        self.assertIn("<loc>https://social.jpastack.com/", xml)
        self.assertIn("<loc>https://social.jpastack.com/vlog</loc>", xml)
        self.assertIn("<loc>https://social.jpastack.com/music</loc>", xml)
        self.assertNotIn("professional.jpastack.com", xml)
        self.assertNotIn("https://jpastack.com", xml)

    def test_professional_and_social_sitemaps_list_active_built_apps(self):
        from unittest import mock

        from app.sitemap import generate_sitemap

        app = _make_app()
        with mock.patch(
            "app.sitemap._active_built_app_slugs", return_value=["stickman-run-app"]
        ):
            with app.test_request_context(
                "/sitemap.xml", base_url="https://professional.jpastack.com"
            ):
                professional_xml = generate_sitemap().get_data(as_text=True)
            with app.test_request_context(
                "/sitemap.xml", base_url="https://social.jpastack.com"
            ):
                social_xml = generate_sitemap().get_data(as_text=True)
            with app.test_request_context(
                "/sitemap.xml", base_url="https://jpastack.com"
            ):
                landing_xml = generate_sitemap().get_data(as_text=True)
        self.assertIn(
            "<loc>https://professional.jpastack.com/apps/stickman-run-app</loc>",
            professional_xml,
        )
        self.assertIn(
            "<loc>https://social.jpastack.com/apps/stickman-run-app</loc>",
            social_xml,
        )
        self.assertNotIn("/apps/stickman-run-app", landing_xml)

    def test_built_app_paths_encode_slugs_and_skip_empty_ones(self):
        from unittest import mock

        from app.sitemap import _built_app_paths

        with mock.patch(
            "app.sitemap._active_built_app_slugs",
            return_value=["stickman run", "", "ok-app"],
        ):
            self.assertEqual(
                _built_app_paths(), ["/apps/stickman%20run", "/apps/ok-app"]
            )

    def test_active_built_app_slugs_returns_empty_on_failure(self):
        from unittest import mock

        from app.sitemap import _active_built_app_slugs

        with mock.patch(
            "app.Repositories.BuiltAppRepository.BuiltAppRepository.__init__",
            return_value=None,
        ), mock.patch(
            "app.Services.BuiltAppService.BuiltAppService.get_active_built_apps",
            side_effect=RuntimeError("mongo unavailable"),
        ):
            self.assertEqual(_active_built_app_slugs(), [])


if __name__ == "__main__":
    unittest.main()
