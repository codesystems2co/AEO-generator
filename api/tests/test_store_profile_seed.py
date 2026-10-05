import unittest

from app.services.store_profile import organization_name_from_ld, seed_remediation_from_page


class SeedRemediationFromPageTest(unittest.TestCase):
    def test_ferrum_page_seeds_title_h1_meta_and_org(self):
        page = {
            "title": "Ferrum Aditiva | Impresión 3D en metal DMLS/SLM",
            "meta_description": "Fabricación aditiva en metal DMLS/SLM para piezas industriales.",
            "h1_list": ["Impresión 3D en metal DMLS/SLM"],
            "organization_name": "Ferrum Aditiva",
            "og_site_name": "Ferrum Aditiva",
        }
        seeded = seed_remediation_from_page(page)
        self.assertEqual(seeded["title"], page["title"])
        self.assertEqual(seeded["h1"], "Impresión 3D en metal DMLS/SLM")
        self.assertEqual(seeded["meta_description"], page["meta_description"])
        self.assertEqual(seeded["organization_name"], "Ferrum Aditiva")
        self.assertEqual(seeded["og_site_name"], "Ferrum Aditiva")
        self.assertEqual(seeded["backend"], "page")

    def test_empty_page_returns_empty_remediation(self):
        self.assertEqual(seed_remediation_from_page({}), {})
        self.assertEqual(seed_remediation_from_page(None), {})


class OrganizationJsonLdTest(unittest.TestCase):
    def test_organization_name_from_ld(self):
        block = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Ferrum Aditiva",
        }
        self.assertEqual(organization_name_from_ld(block), "Ferrum Aditiva")

    def test_organization_name_from_graph(self):
        block = {
            "@graph": [
                {"@type": "WebSite", "name": "Site"},
                {"@type": "Organization", "name": "Ferrum Aditiva"},
            ]
        }
        self.assertEqual(organization_name_from_ld(block), "Ferrum Aditiva")


if __name__ == "__main__":
    unittest.main()
