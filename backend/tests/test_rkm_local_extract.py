import asyncio

from app.ai.local_provider import LocalAIProvider


def test_local_extract_rkm_draft_has_required_sections():
    text = """
    # Sales intake
    - Customer name: SEGi
    - Request type: Proposal
    ## Requirement details
    Customer needs reliable campus WiFi coverage across hostel and south block.
    Firewall and 10Gbps uplinks are required. Assume existing server room remains.
    Risk: incomplete floor plans may delay AP placement.
    """
    result = asyncio.run(LocalAIProvider().extract_rkm_draft(text))
    assert result["business_objectives"]
    assert result["functional_requirements"]
    assert result["non_functional_requirements"]
    assert result["assumptions"]
    assert result["risks"]
    assert result["current_environment"]["items"]
    assert "reasoning_summary" in result
