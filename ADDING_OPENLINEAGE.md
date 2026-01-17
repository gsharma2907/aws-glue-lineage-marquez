# Adding OpenLineage to Your Glue Jobs

This guide shows how to add OpenLineage lineage tracking to any AWS Glue job.

## Quick Start

Add this code to your existing Glue job to emit lineage events to Marquez.

### 1. Import Required Libraries

```python
import json
import urllib.request
import urllib.error
from datetime import datetime
import uuid
```

### 2. Add Configuration

```python
from awsglue.utils import getResolvedOptions

# Add MARQUEZ_URL to your job arguments
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'MARQUEZ_URL'])

MARQUEZ_URL = args['MARQUEZ_URL']
NAMESPACE = "your-namespace"  # e.g., "glue-lineage", "data-warehouse"
JOB_NAME = args['JOB_NAME']
RUN_ID = str(uuid.uuid4())
```

### 3. Add Helper Functions

```python
def send_lineage_event(event_type, event_data):
    """Send OpenLineage event to Marquez"""
    try:
        url = f"{MARQUEZ_URL}/api/v1/lineage"
        data = json.dumps(event_data).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"✅ {event_type} event sent: {response.status}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"⚠️  Failed to send {event_type} event: HTTP {e.code}")
        print(f"    Error details: {error_body}")
    except Exception as e:
        print(f"⚠️  Failed to send {event_type} event: {str(e)}")

def create_lineage_event(event_type, inputs=None, outputs=None):
    """Create OpenLineage event structure"""
    event = {
        "eventType": event_type,
        "eventTime": datetime.utcnow().isoformat() + "Z",
        "producer": "https://github.com/aws/aws-glue",
        "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json#/$defs/RunEvent",
        "run": {
            "runId": RUN_ID
        },
        "job": {
            "namespace": NAMESPACE,
            "name": JOB_NAME
        },
        "inputs": inputs or [],
        "outputs": outputs or []
    }
    return event
```

### 4. Define Your Datasets

```python
# Input dataset
input_dataset = {
    "namespace": NAMESPACE,
    "name": "your_input_table",  # e.g., "s3://bucket/path" or "database.table"
    "facets": {
        "schema": {
            "_producer": "https://github.com/OpenLineage/OpenLineage/tree/0.0.1/client/python",
            "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
            "fields": [
                {"name": "column1", "type": "STRING"},
                {"name": "column2", "type": "INTEGER"},
                {"name": "column3", "type": "DOUBLE"}
            ]
        }
    }
}

# Output dataset
output_dataset = {
    "namespace": NAMESPACE,
    "name": "your_output_table",
    "facets": {
        "schema": {
            "_producer": "https://github.com/OpenLineage/OpenLineage/tree/0.0.1/client/python",
            "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
            "fields": [
                {"name": "result_col1", "type": "STRING"},
                {"name": "result_col2", "type": "DOUBLE"}
            ]
        }
    }
}
```

### 5. Emit Events in Your Job

```python
# At the start of your job
print(f"🚀 Starting job: {JOB_NAME}")
print(f"📍 Run ID: {RUN_ID}")

start_event = create_lineage_event("START")
send_lineage_event("START", start_event)

try:
    # YOUR EXISTING GLUE JOB CODE HERE
    # Read data, transform, write, etc.
    
    # At the end of successful execution
    complete_event = create_lineage_event(
        "COMPLETE",
        inputs=[input_dataset],
        outputs=[output_dataset]
    )
    send_lineage_event("COMPLETE", complete_event)
    
    print("✅ Job completed successfully")
    
except Exception as e:
    print(f"❌ Job failed: {str(e)}")
    
    # On failure
    fail_event = create_lineage_event("FAIL")
    send_lineage_event("FAIL", fail_event)
    raise
```

## Complete Example

Here's a complete Glue job with OpenLineage:

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import json
import urllib.request
import urllib.error
from datetime import datetime
import uuid

# Initialize Glue
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'MARQUEZ_URL'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# OpenLineage configuration
MARQUEZ_URL = args['MARQUEZ_URL']
NAMESPACE = "my-data-pipeline"
JOB_NAME = args['JOB_NAME']
RUN_ID = str(uuid.uuid4())

def send_lineage_event(event_type, event_data):
    """Send OpenLineage event to Marquez"""
    try:
        url = f"{MARQUEZ_URL}/api/v1/lineage"
        data = json.dumps(event_data).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"✅ {event_type} event sent: {response.status}")
    except Exception as e:
        print(f"⚠️  Failed to send {event_type} event: {str(e)}")

def create_lineage_event(event_type, inputs=None, outputs=None):
    """Create OpenLineage event structure"""
    return {
        "eventType": event_type,
        "eventTime": datetime.utcnow().isoformat() + "Z",
        "producer": "https://github.com/aws/aws-glue",
        "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json#/$defs/RunEvent",
        "run": {"runId": RUN_ID},
        "job": {"namespace": NAMESPACE, "name": JOB_NAME},
        "inputs": inputs or [],
        "outputs": outputs or []
    }

# Define datasets
input_dataset = {
    "namespace": NAMESPACE,
    "name": "s3://my-bucket/input/data.parquet",
    "facets": {
        "schema": {
            "_producer": "https://github.com/OpenLineage/OpenLineage",
            "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
            "fields": [
                {"name": "id", "type": "INTEGER"},
                {"name": "name", "type": "STRING"},
                {"name": "value", "type": "DOUBLE"}
            ]
        }
    }
}

output_dataset = {
    "namespace": NAMESPACE,
    "name": "s3://my-bucket/output/processed.parquet",
    "facets": {
        "schema": {
            "_producer": "https://github.com/OpenLineage/OpenLineage",
            "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
            "fields": [
                {"name": "id", "type": "INTEGER"},
                {"name": "processed_value", "type": "DOUBLE"}
            ]
        }
    }
}

# Send START event
start_event = create_lineage_event("START")
send_lineage_event("START", start_event)

try:
    # YOUR ETL LOGIC HERE
    # Example:
    df = spark.read.parquet("s3://my-bucket/input/data.parquet")
    df_processed = df.select("id", (df["value"] * 2).alias("processed_value"))
    df_processed.write.parquet("s3://my-bucket/output/processed.parquet")
    
    # Send COMPLETE event
    complete_event = create_lineage_event(
        "COMPLETE",
        inputs=[input_dataset],
        outputs=[output_dataset]
    )
    send_lineage_event("COMPLETE", complete_event)
    
except Exception as e:
    # Send FAIL event
    fail_event = create_lineage_event("FAIL")
    send_lineage_event("FAIL", fail_event)
    raise

job.commit()
```

## Running Your Job

When running the job, pass the Marquez URL as an argument:

```bash
aws glue start-job-run \
  --job-name your-job-name \
  --arguments '{"--MARQUEZ_URL":"http://YOUR_MARQUEZ_IP:5000"}' \
  --region us-east-1
```

## Dataset Naming Conventions

Use descriptive, unique names for datasets:

### S3 Datasets
```python
"name": "s3://bucket-name/path/to/data"
```

### Database Tables
```python
"name": "database_name.table_name"
```

### Glue Catalog Tables
```python
"name": "glue://database/table"
```

## Schema Definition

Define schemas to track data structure:

```python
"schema": {
    "_producer": "https://github.com/OpenLineage/OpenLineage",
    "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
    "fields": [
        {"name": "column_name", "type": "DATA_TYPE"},
        {"name": "user_id", "type": "INTEGER"},
        {"name": "email", "type": "STRING"},
        {"name": "created_at", "type": "TIMESTAMP"}
    ]
}
```

### Supported Data Types
- STRING
- INTEGER / LONG
- DOUBLE / FLOAT
- BOOLEAN
- TIMESTAMP / DATE
- ARRAY
- STRUCT
- MAP

## Multiple Inputs/Outputs

For jobs with multiple sources or destinations:

```python
inputs = [
    {
        "namespace": NAMESPACE,
        "name": "s3://bucket/input1.parquet",
        "facets": {"schema": {...}}
    },
    {
        "namespace": NAMESPACE,
        "name": "s3://bucket/input2.parquet",
        "facets": {"schema": {...}}
    }
]

outputs = [
    {
        "namespace": NAMESPACE,
        "name": "s3://bucket/output1.parquet",
        "facets": {"schema": {...}}
    },
    {
        "namespace": NAMESPACE,
        "name": "s3://bucket/output2.parquet",
        "facets": {"schema": {...}}
    }
]

complete_event = create_lineage_event("COMPLETE", inputs=inputs, outputs=outputs)
```

## Best Practices

### 1. Use Consistent Namespaces
Group related jobs in the same namespace:
```python
NAMESPACE = "data-warehouse"  # All warehouse jobs
NAMESPACE = "ml-pipeline"     # All ML jobs
NAMESPACE = "analytics"       # All analytics jobs
```

### 2. Handle Failures Gracefully
Always send FAIL events on errors:
```python
try:
    # Your job logic
    send_lineage_event("COMPLETE", complete_event)
except Exception as e:
    send_lineage_event("FAIL", fail_event)
    raise  # Re-raise to fail the job
```

### 3. Don't Block on Lineage Failures
Lineage tracking should not break your job:
```python
def send_lineage_event(event_type, event_data):
    try:
        # Send event
        pass
    except Exception as e:
        # Log but don't raise
        print(f"⚠️  Lineage tracking failed: {e}")
```

### 4. Use Descriptive Dataset Names
```python
# Good
"name": "s3://data-lake/sales/transactions/2024/01/data.parquet"

# Bad
"name": "output_data"
```

### 5. Keep Schemas Updated
Update schema definitions when columns change:
```python
# Version 1
"fields": [{"name": "user_id", "type": "INTEGER"}]

# Version 2 (added column)
"fields": [
    {"name": "user_id", "type": "INTEGER"},
    {"name": "email", "type": "STRING"}
]
```

## Troubleshooting

### Events Not Appearing in Marquez

1. **Check Marquez URL**
   ```python
   print(f"Marquez URL: {MARQUEZ_URL}")
   ```

2. **Verify Network Connectivity**
   - Ensure Glue can reach Marquez endpoint
   - Check security groups and network ACLs

3. **Check CloudWatch Logs**
   - Look for "event sent" or "Failed to send" messages
   - Review error details

### Validation Errors (HTTP 422)

Common causes:
- Missing `producer` field
- Invalid `eventTime` format
- Missing required fields in datasets

### Connection Timeout

- Increase timeout in `urllib.request.urlopen(req, timeout=10)`
- Check if Marquez is running: `curl http://MARQUEZ_IP:5000/api/v1/health`

## Advanced: Dynamic Schema Detection

Automatically detect schema from DataFrame:

```python
def get_schema_from_dataframe(df):
    """Extract schema from Spark DataFrame"""
    fields = []
    for field in df.schema.fields:
        fields.append({
            "name": field.name,
            "type": str(field.dataType).upper()
        })
    return fields

# Use in dataset definition
output_dataset = {
    "namespace": NAMESPACE,
    "name": "s3://bucket/output.parquet",
    "facets": {
        "schema": {
            "_producer": "https://github.com/OpenLineage/OpenLineage",
            "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
            "fields": get_schema_from_dataframe(df_output)
        }
    }
}
```

## Summary

To add OpenLineage to any Glue job:

1. ✅ Add imports and configuration
2. ✅ Copy helper functions
3. ✅ Define input/output datasets
4. ✅ Send START event at beginning
5. ✅ Send COMPLETE event on success
6. ✅ Send FAIL event on error
7. ✅ Pass MARQUEZ_URL when running job

That's it! Your job will now track lineage in Marquez.
