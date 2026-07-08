from app.integrations.core_banking.mock_client import MockCoreBankingClient


def test_kyc_profile_is_deterministic_per_external_ref():
    client = MockCoreBankingClient()
    first = client.get_kyc_profile("demo-001")
    second = client.get_kyc_profile("demo-001")
    assert first == second


def test_kyc_profile_varies_by_external_ref():
    client = MockCoreBankingClient()
    profile_a = client.get_kyc_profile("demo-001")
    profile_b = client.get_kyc_profile("demo-002")
    assert profile_a.full_name != profile_b.full_name or profile_a.pan_masked != profile_b.pan_masked


def test_kyc_profile_masks_pan_and_phone():
    client = MockCoreBankingClient()
    profile = client.get_kyc_profile("demo-001")
    assert profile.pan_masked.startswith("XXXXX")
    assert profile.phone_masked.startswith("XXXXXX")
    assert len(profile.full_name.split()) == 2
