import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ai.model_api_client import ModelAPIClient, ModelAPIError


class ModelAPIClientTests(unittest.TestCase):
    def test_analyze_profile_calls_openai_compatible_chat_api(self) -> None:
        requests = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(
                    {
                        "id": "chatcmpl-fixture",
                        "choices": [
                            {
                                "message": {
                                    "content": json.dumps(
                                        {
                                            "company_name": "Acme Pool Heating",
                                            "profile_summary": "这是一家泳池热泵经销商。",
                                            "business_type": "经销商",
                                            "market_role": "渠道销售",
                                            "product_fit": "高度匹配泳池热泵",
                                            "customer_priority": "A",
                                            "score_total": 88,
                                            "score_breakdown": {
                                                "product_relevance": 30,
                                                "customer_type_fit": 18,
                                                "distribution_potential": 14,
                                                "market_country_fit": 9,
                                                "contactability": 9,
                                                "evidence_quality": 8,
                                                "risk_penalty": 0,
                                            },
                                            "contact_analysis": {
                                                "contact_quality": "high",
                                                "available_channels": ["email", "phone"],
                                                "preferred_channel": "email",
                                                "recommended_contacts": [
                                                    {
                                                        "type": "email",
                                                        "value": "sales@pool.example",
                                                        "label": "销售邮箱",
                                                        "reason": "适合发送渠道合作资料",
                                                    }
                                                ],
                                                "outreach_strategy": "先邮件发送产品目录，再电话跟进。",
                                            },
                                            "evidence": ["页面明确销售泳池热泵"],
                                            "risk_flags": [],
                                            "recommended_action": "优先联系采购负责人。",
                                        },
                                        ensure_ascii=False,
                                    )
                                }
                            }
                        ],
                    },
                    ensure_ascii=False,
                ).encode("utf-8")

        def fake_urlopen(request, timeout):
            requests.append((request, timeout))
            return FakeResponse()

        client = ModelAPIClient(
            api_key="sk-test",
            base_url="https://api.deepseek.com",
            temperature=0.2,
            timeout_seconds=33,
            urlopen=fake_urlopen,
        )

        result = client.analyze_profile(
            {
                "company": {"domain": "pool.example"},
                "contacts": {
                    "normalized_records": [
                        {"kind": "email", "value": "sales@pool.example", "label": "销售邮箱"}
                    ]
                },
            }
        )

        self.assertEqual(result.content["profile_summary"], "这是一家泳池热泵经销商。")
        request, timeout = requests[0]
        self.assertEqual(timeout, 33)
        self.assertEqual(request.full_url, "https://api.deepseek.com/chat/completions")
        self.assertEqual(request.headers["Authorization"], "Bearer sk-test")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "deepseek-v4-pro")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertIn("所有自然语言内容必须使用中文", payload["messages"][0]["content"])
        self.assertIn("禁止编造", payload["messages"][0]["content"])
        user_content = json.loads(payload["messages"][1]["content"])
        self.assertEqual(user_content["profile_package"]["company"]["domain"], "pool.example")
        self.assertEqual(
            user_content["profile_package"]["contacts"]["normalized_records"][0]["value"],
            "sales@pool.example",
        )
        self.assertIn("contact_analysis", user_content["schema"]["required"])
        self.assertEqual(result.content["contact_analysis"]["preferred_channel"], "email")

    def test_api_key_is_required(self) -> None:
        with self.assertRaisesRegex(ValueError, "api_key is required"):
            ModelAPIClient(api_key="", base_url="https://api.deepseek.com", model="deepseek-chat")

    def test_invalid_response_raises_model_api_error(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": "not-json"}}]}).encode("utf-8")

        client = ModelAPIClient(
            api_key="sk-test",
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            urlopen=lambda request, timeout: FakeResponse(),
        )

        with self.assertRaises(ModelAPIError):
            client.analyze_profile({"company": {"domain": "bad.example"}})


if __name__ == "__main__":
    unittest.main()
