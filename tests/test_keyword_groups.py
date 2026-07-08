import tempfile
import textwrap
import unittest
from contextlib import contextmanager
from pathlib import Path

from database.keyword_groups import (
    create_keyword_group,
    delete_keyword_group,
    generate_keyword_specs,
    import_keyword_group_from_yaml,
    list_keyword_groups,
    update_keyword_group,
)
from database.models import KeywordGroup
from database.session import create_all, create_engine_from_url, create_session_factory


class KeywordGroupTests(unittest.TestCase):
    @contextmanager
    def make_session(self):
        engine = create_engine_from_url("sqlite:///:memory:")
        create_all(engine)
        Session = create_session_factory(engine)
        session = Session()
        try:
            yield session
        finally:
            session.close()
            engine.dispose()

    def test_create_list_update_and_delete_keyword_group(self) -> None:
        with self.make_session() as session:
            group = create_keyword_group(
                session,
                {
                    "name": "France Pool Heating",
                    "country": "France",
                    "country_terms": "France\nen France",
                    "keyword_terms": "pool heat pump\nPompes à chaleur pour piscines",
                    "product_terms": "pool heat pump",
                    "role_terms": "distributor",
                    "search_templates": "{product} {role} {country}",
                    "notes": "French pool heating campaign",
                    "is_active": True,
                },
            )
            session.commit()

            listed = list_keyword_groups(session)
            updated = update_keyword_group(session, group.id, {"notes": "Updated note", "is_active": False})
            session.commit()
            deleted = delete_keyword_group(session, group.id)
            session.commit()

            remaining = list_keyword_groups(session)

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["name"], "France Pool Heating")
        self.assertEqual(listed[0]["product_terms"], "pool heat pump")
        self.assertEqual(listed[0]["role_terms"], "distributor")
        self.assertEqual(listed[0]["search_templates"], "{product} {role} {country}")
        self.assertEqual(updated["notes"], "Updated note")
        self.assertFalse(updated["is_active"])
        self.assertTrue(deleted)
        self.assertEqual(remaining, [])

    def test_generate_keyword_specs_from_keyword_group(self) -> None:
        with self.make_session() as session:
            group = create_keyword_group(
                session,
                {
                    "name": "France Pool Heating",
                    "country": "France",
                    "country_terms": "France\nen France",
                    "keyword_terms": "pool heat pump\nPompes à chaleur pour piscines",
                    "notes": "",
                    "is_active": True,
                },
            )
            session.commit()

            specs = generate_keyword_specs(session, group.id)

        self.assertEqual(len(specs), 4)
        self.assertEqual(specs[0].keyword, "pool heat pump France")
        self.assertEqual(specs[0].country, "France")
        self.assertEqual(specs[0].industry, "France Pool Heating")
        self.assertEqual(specs[0].industry_term, "pool heat pump")
        self.assertIn("Pompes à chaleur pour piscines en France", {spec.keyword for spec in specs})

    def test_generate_keyword_specs_from_product_role_templates(self) -> None:
        with self.make_session() as session:
            group = create_keyword_group(
                session,
                {
                    "name": "Italy Pool Structured",
                    "country": "Italy",
                    "country_terms": "Italy\nItalia",
                    "keyword_terms": "",
                    "product_terms": "pool heat pump\npompa di calore piscina",
                    "role_terms": "distributor\ninstallatore",
                    "search_templates": "{product} {role} {country}\n{product} {role} in {country}",
                    "notes": "",
                    "is_active": True,
                },
            )
            session.commit()

            specs = generate_keyword_specs(session, group.id)
            listed = list_keyword_groups(session)

        keywords = {spec.keyword for spec in specs}
        self.assertEqual(len(specs), 16)
        self.assertEqual(listed[0]["keyword_count"], 16)
        self.assertIn("pool heat pump distributor Italy", keywords)
        self.assertIn("pool heat pump distributor in Italia", keywords)
        self.assertIn("pompa di calore piscina installatore Italy", keywords)
        self.assertEqual(specs[0].industry_term, "pool heat pump distributor")

    def test_generate_keyword_specs_dedupes_template_results(self) -> None:
        with self.make_session() as session:
            group = create_keyword_group(
                session,
                {
                    "name": "Italy Site Search",
                    "country": "Italy",
                    "country_terms": "Italy\nItalia",
                    "keyword_terms": "",
                    "product_terms": "pool heat pump",
                    "role_terms": "distributor",
                    "search_templates": "site:.it {product} {role}",
                    "notes": "",
                    "is_active": True,
                },
            )
            session.commit()

            specs = generate_keyword_specs(session, group.id)

        self.assertEqual([spec.keyword for spec in specs], ["site:.it pool heat pump distributor"])

    def test_import_keyword_group_from_yaml_upserts_by_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_path = Path(temp_dir) / "keywords_france.yaml"
            yaml_path.write_text(
                textwrap.dedent(
                    """
                    countries:
                      France:
                        terms:
                          - France
                          - en France
                    industries:
                      pool_heat_pump:
                        terms:
                          - pool heat pump
                        synonyms:
                          - pompe à chaleur piscine
                    """
                ).strip(),
                encoding="utf-8",
            )

            with self.make_session() as session:
                first = import_keyword_group_from_yaml(session, yaml_path)
                second = import_keyword_group_from_yaml(session, yaml_path)
                session.commit()

                groups = session.query(KeywordGroup).all()

        self.assertEqual(first.id, second.id)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].name, "keywords_france")
        self.assertEqual(groups[0].country, "France")
        self.assertEqual(groups[0].country_terms, "France\nen France")
        self.assertEqual(groups[0].keyword_terms, "pool heat pump\npompe à chaleur piscine")
        self.assertEqual(groups[0].product_terms, "")
        self.assertEqual(groups[0].role_terms, "")
        self.assertEqual(groups[0].search_templates, "")


if __name__ == "__main__":
    unittest.main()
