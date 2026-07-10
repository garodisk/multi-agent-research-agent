MOCK_RESEARCH: dict[str, dict] = {
    "apple": {
        "company": "Apple Inc.",
        "recent_news": "Launched Vision Pro headset; services revenue hit record $23B quarterly",
        "stock_info": "Trading at $195, up 45% YTD, market cap ~$3T",
        "key_developments": "Apple Intelligence AI integration across iOS 18 product line; India manufacturing expansion",
        "ceo": "Tim Cook",
        "founded": "1976",
    },
    "tesla": {
        "company": "Tesla",
        "recent_news": "Cybertruck deliveries ramping up; price cuts across Model 3 and Y",
        "stock_info": "Trading at $242, volatile quarter with 20% swing",
        "key_developments": "FSD v12 full end-to-end neural net rollout; energy storage segment growing 50% YoY",
        "ceo": "Elon Musk",
        "founded": "2003",
    },
}


def lookup_company(query: str) -> dict | None:
    query_lower = query.lower()
    for key, data in MOCK_RESEARCH.items():
        if key in query_lower or data["company"].lower() in query_lower:
            return data
    return None
