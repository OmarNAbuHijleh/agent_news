"""Cloud-backed alternative to the local SQLite QueryCache (see query_cache.py), targeting AWS
DynamoDB per the README's original cost-saving architecture (DynamoDB/ElastiCache).

NOT WIRED UP ANYWHERE YET - this is dead code. CachedResearchService still constructs the local
SQLite-backed QueryCache. To activate this backend once there's an actual deployment to share
the cache across:
    1. Create a DynamoDB table with a String partition key named `normalized_query`, and enable
       TTL on the `ttl` attribute (DynamoDB Console/Terraform: Time to Live attribute = "ttl").
    2. `pip install .[cloud]` (or add boto3 to the base dependency set).
    3. In CachedResearchService.__init__, replace `QueryCache()` with
       `DynamoDBQueryCache(config.CACHE_DYNAMODB_TABLE_NAME, region_name=config.CACHE_AWS_REGION)`.
Both classes satisfy the same QueryCacheBackend protocol (get/set/close), so no other code needs
to change.
"""
import time
import boto3
from config import CACHE_TTL_SECONDS


class DynamoDBQueryCache:
    """Same interface as QueryCache, backed by a DynamoDB table instead of a local SQLite file.

    Expected table schema:
        - Partition key: normalized_query (String)
        - Attributes written per item: result (String), created_at (Number, unix seconds),
          ttl (Number, unix seconds - configure this as the table's TTL attribute so DynamoDB
          reclaims expired items automatically. DynamoDB's TTL deletion isn't immediate, so
          created_at is still checked manually in get() for correctness in the meantime).
    """

    def __init__(self, table_name: str, ttl_seconds: int = CACHE_TTL_SECONDS, region_name: str | None = None):
        self._ttl_seconds = ttl_seconds
        self._table = boto3.resource("dynamodb", region_name=region_name).Table(table_name)

    def get(self, normalized_query: str) -> str | None:
        response = self._table.get_item(Key={"normalized_query": normalized_query})
        item = response.get("Item")
        if item is None:
            return None
        if time.time() - float(item["created_at"]) > self._ttl_seconds:
            return None
        return item["result"]

    def set(self, normalized_query: str, result: str) -> None:
        now = time.time()
        self._table.put_item(Item={
            "normalized_query": normalized_query,
            "result": result,
            "created_at": int(now),
            "ttl": int(now + self._ttl_seconds),
        })

    def close(self) -> None:
        # boto3 Table/resource connections are managed by botocore's own connection pool -
        # nothing to explicitly close. Kept only for interface parity with QueryCache.
        pass
