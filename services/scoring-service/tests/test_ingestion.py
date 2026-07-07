import pytest

from app.ingestion.synthetic_source import SyntheticFileIngestionSource


def test_loads_customer_bundle(synthetic_data_dir):
    source = SyntheticFileIngestionSource(synthetic_data_dir)
    bundle = source.load("demo-001")

    assert bundle.customer.external_ref == "demo-001"
    assert bundle.customer.employment_type == "salaried"
    assert len(bundle.accounts) == 1
    assert bundle.accounts[0].source == "upload"
    assert len(bundle.statements) == 1
    assert len(bundle.statements[0].transactions) == 7
    assert len(bundle.application_events) == 1


def test_missing_customer_raises_file_not_found(synthetic_data_dir):
    source = SyntheticFileIngestionSource(synthetic_data_dir)
    with pytest.raises(FileNotFoundError):
        source.load("does-not-exist")
