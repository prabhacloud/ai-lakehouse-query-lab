"""Read the same S3 Table with Spark and emit an article-safe result."""

from hashlib import sha256
import json

from pyspark.sql import SparkSession


spark = SparkSession.builder.appName("ai-lakehouse-query-lab").getOrCreate()

query = """
SELECT category, ROUND(SUM(amount), 2) AS total_amount
FROM s3tablesbucket.lab.events
WHERE event_date = DATE '2026-11-01'
GROUP BY category
ORDER BY category
"""

rows = [
    [row["category"], float(row["total_amount"])]
    for row in spark.sql(query).collect()
]
canonical = "\n".join(
    json.dumps(row, separators=(",", ":")) for row in rows
).encode("utf-8")

print(
    "AIQLAB_RESULT="
    + json.dumps(
        {
            "engine": "emr-serverless",
            "rows": rows,
            "row_count": len(rows),
            "result_hash": sha256(canonical).hexdigest(),
        },
        separators=(",", ":"),
    )
)

spark.stop()
