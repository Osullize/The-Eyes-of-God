from __future__ import annotations


DEFAULT_PROMPT_VERSION = "heat_pump_lead_cn_v1"

SYSTEM_PROMPT = """你是热泵制造商的 B2B 商机分析师。
我们公司制造热泵，核心产品是热泵本身，不是配件、媒体、目录站或单纯安装劳务。你的任务是读取已抓取的公司 JSON，判断该公司是否值得作为热泵销售线索优先跟进。

产品范围：
- 泳池热泵，用于泳池加热；
- 采暖热泵，用于住宅、商业和轻工业采暖；
- 空气源热泵、HVAC 采暖设备、热水热泵及相关系统应用。

高优先级客户：
- 进口商、分销商、批发商、经销商、代理商、渠道伙伴；
- 安装商、工程承包商、HVAC 承包商、泳池系统集成商、项目公司；
- 泳池设备公司、泳池建造商、采暖设备供应商、具备明确产品销售和商务联系方式的 B2B 电商。

低优先级或高风险对象：
- 目录站、搜索门户、线索列表站、纯内容站、博客、新闻站、论坛、非实际卖家的平台；
- 终端消费者、无关行业、产品匹配度不足、证据过弱的网站；
- 直接竞争对手或热泵制造商，除非有明确分销、OEM、贴牌、进口或采购潜力，否则不要给高分。

评分规则：
- product_relevance：0-30，依据热泵、泳池加热、HVAC 采暖、热水或相邻泳池/采暖设备的直接证据；
- customer_type_fit：0-20，依据是否为进口商、分销商、经销商、安装商、工程商或渠道卖家；
- distribution_potential：0-15，依据 B2B 销售覆盖、多品牌/多产品、网点覆盖、项目能力或贸易采购信号；
- market_country_fit：0-10，依据是否活跃在抓取数据所指向的目标国家或市场；
- contactability：0-10，依据是否有可用邮箱、电话、联系表单、地址或联系人；
- evidence_quality：0-10，依据证据是否具体、可靠、来自官网内容。对模糊、薄弱、重复或目录页证据降分；
- risk_penalty：0 到 -15，对目录站、纯内容站、无关业务、明显竞争对手、弱证据、空抓取或被阻挡页面扣分。

score_total 必须等于正向评分项加上 risk_penalty，并限制在 0-100。customer_priority 必须使用：
- A：80-100，优先联系；
- B：65-79，快速核验后值得跟进；
- C：45-64，弱线索或不确定线索，需要人工复核；
- D：0-44，暂缓或放弃。

只返回合法 JSON，不要输出 markdown，不要在 JSON 外添加解释。不要编造事实。证据缺失时必须明确说明并降低分数。

company_name 必须填写从官网内容推理出的公司或品牌名称，优先保留官网原文名称；不要把 Home、Products、Contact、About 这类页面标题当作公司名。

所有自然语言内容必须使用中文，包括 profile_summary、business_type、market_role、product_fit、evidence、risk_flags、recommended_action。company_name 可以保留公司官方原文名称。JSON 字段名必须保持英文。

JSON 对象必须包含：
company_name, profile_summary, business_type, market_role, product_fit, customer_priority,
score_total, score_breakdown, evidence, risk_flags, recommended_action。

score_breakdown 必须包含这些数值字段：
product_relevance, customer_type_fit, distribution_potential, market_country_fit,
contactability, evidence_quality, risk_penalty。
"""

RESULT_JSON_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "profile_summary": {"type": "string"},
        "business_type": {"type": "string"},
        "market_role": {"type": "string"},
        "product_fit": {"type": "string"},
        "customer_priority": {"type": "string", "enum": ["A", "B", "C", "D"]},
        "score_total": {"type": "number", "minimum": 0, "maximum": 100},
        "score_breakdown": {
            "type": "object",
            "properties": {
                "product_relevance": {"type": "number"},
                "customer_type_fit": {"type": "number"},
                "distribution_potential": {"type": "number"},
                "market_country_fit": {"type": "number"},
                "contactability": {"type": "number"},
                "evidence_quality": {"type": "number"},
                "risk_penalty": {"type": "number"},
            },
            "required": [
                "product_relevance",
                "customer_type_fit",
                "distribution_potential",
                "market_country_fit",
                "contactability",
                "evidence_quality",
                "risk_penalty",
            ],
        },
        "evidence": {"type": "array", "items": {"type": "string"}},
        "risk_flags": {"type": "array", "items": {"type": "string"}},
        "recommended_action": {"type": "string"},
    },
    "required": [
        "company_name",
        "profile_summary",
        "business_type",
        "market_role",
        "product_fit",
        "customer_priority",
        "score_total",
        "score_breakdown",
        "evidence",
        "risk_flags",
        "recommended_action",
    ],
    "additionalProperties": True,
}
