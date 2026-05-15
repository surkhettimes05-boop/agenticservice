from custom_agents.agentic_it_firm.agents.leads import PublicLeadSourceClient


def test_public_lead_source_client_normalizes_results():
    client = PublicLeadSourceClient(search_client=lambda query: [
        {"title": "Acme Health", "url": "https://acme.example", "snippet": "Healthcare automation company hiring developers"}
    ])

    leads = client.search("healthcare automation")

    assert leads[0]["company_name"] == "Acme Health"
    assert leads[0]["source"] == "public_web_search"
    assert "hiring developers" in leads[0]["signals"][0]
