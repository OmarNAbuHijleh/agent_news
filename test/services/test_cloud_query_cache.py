from unittest.mock import MagicMock
import src.services.cloud_query_cache as cloud_cache_module
from src.services.cloud_query_cache import DynamoDBQueryCache


def make_cache(monkeypatch, ttl_seconds: int = 3600):
    fake_table = MagicMock()
    fake_resource = MagicMock()
    fake_resource.Table.return_value = fake_table
    monkeypatch.setattr(cloud_cache_module.boto3, "resource", MagicMock(return_value=fake_resource))

    cache = DynamoDBQueryCache("test-table", ttl_seconds=ttl_seconds)
    return cache, fake_table


def test_init_creates_table_resource_for_the_given_table_name(monkeypatch):
    fake_table = MagicMock()
    fake_resource = MagicMock()
    fake_resource.Table.return_value = fake_table
    fake_boto3_resource = MagicMock(return_value=fake_resource)
    monkeypatch.setattr(cloud_cache_module.boto3, "resource", fake_boto3_resource)

    DynamoDBQueryCache("test-table", region_name="us-east-1")

    fake_boto3_resource.assert_called_once_with("dynamodb", region_name="us-east-1")
    fake_resource.Table.assert_called_once_with("test-table")


def test_get_returns_none_when_item_missing(monkeypatch):
    cache, fake_table = make_cache(monkeypatch)
    fake_table.get_item.return_value = {}

    assert cache.get("nvidia stock price") is None
    fake_table.get_item.assert_called_once_with(Key={"normalized_query": "nvidia stock price"})


def test_get_returns_result_for_a_fresh_item(monkeypatch):
    cache, fake_table = make_cache(monkeypatch, ttl_seconds=3600)
    monkeypatch.setattr(cloud_cache_module.time, "time", lambda: 1000.0)
    fake_table.get_item.return_value = {
        "Item": {"normalized_query": "nvidia stock price", "result": "cached text", "created_at": 999, "ttl": 4599}
    }

    assert cache.get("nvidia stock price") == "cached text"


def test_get_returns_none_for_an_expired_item(monkeypatch):
    cache, fake_table = make_cache(monkeypatch, ttl_seconds=60)
    monkeypatch.setattr(cloud_cache_module.time, "time", lambda: 2000.0)
    fake_table.get_item.return_value = {
        "Item": {"normalized_query": "nvidia stock price", "result": "cached text", "created_at": 1000, "ttl": 1060}
    }

    assert cache.get("nvidia stock price") is None


def test_set_writes_result_created_at_and_ttl(monkeypatch):
    cache, fake_table = make_cache(monkeypatch, ttl_seconds=3600)
    monkeypatch.setattr(cloud_cache_module.time, "time", lambda: 1000.0)

    cache.set("nvidia stock price", "cached text")

    fake_table.put_item.assert_called_once_with(Item={
        "normalized_query": "nvidia stock price",
        "result": "cached text",
        "created_at": 1000,
        "ttl": 4600,
    })


def test_close_does_not_raise():
    cache = DynamoDBQueryCache.__new__(DynamoDBQueryCache)  # skip __init__, no table needed
    cache.close()
