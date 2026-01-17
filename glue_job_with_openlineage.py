import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, upper
import json
import urllib.request
import urllib.error
from datetime import datetime
import uuid

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'MARQUEZ_URL'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

MARQUEZ_URL = args['MARQUEZ_URL']
NAMESPACE = "glue-lineage"
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

# START event
print(f"🚀 Starting job: {JOB_NAME}")
print(f"📍 Run ID: {RUN_ID}")
print(f"🔗 Marquez URL: {MARQUEZ_URL}")

start_event = create_lineage_event("START")
send_lineage_event("START", start_event)

try:
    # Define input dataset
    input_dataset = {
        "namespace": NAMESPACE,
        "name": "sample_input_data",
        "facets": {
            "schema": {
                "_producer": "https://github.com/OpenLineage/OpenLineage/tree/0.0.1/client/python",
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
                "fields": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name", "type": "STRING"},
                    {"name": "value", "type": "DOUBLE"}
                ]
            }
        }
    }
    
    # Create sample data
    sample_data = [
        (1, "Alice", 10.5),
        (2, "Bob", 20.3),
        (3, "Charlie", 15.7),
        (4, "Diana", 25.1),
        (5, "Eve", 30.9)
    ]
    
    from pyspark.sql.types import StructType, StructField, IntegerType, StringType, DoubleType
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("value", DoubleType(), True)
    ])
    
    df_input = spark.createDataFrame(sample_data, schema)
    print("📊 Input Data:")
    df_input.show()
    
    # Transform data
    df_output = df_input.select(
        col("id"),
        upper(col("name")).alias("name_upper"),
        (col("value") * col("value")).alias("value_squared")
    )
    
    print("📊 Output Data:")
    df_output.show()
    
    # Define output dataset
    output_dataset = {
        "namespace": NAMESPACE,
        "name": "transformed_output_data",
        "facets": {
            "schema": {
                "_producer": "https://github.com/OpenLineage/OpenLineage/tree/0.0.1/client/python",
                "_schemaURL": "https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json",
                "fields": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name_upper", "type": "STRING"},
                    {"name": "value_squared", "type": "DOUBLE"}
                ]
            }
        }
    }
    
    # COMPLETE event with lineage
    complete_event = create_lineage_event(
        "COMPLETE",
        inputs=[input_dataset],
        outputs=[output_dataset]
    )
    send_lineage_event("COMPLETE", complete_event)
    
    print("✅ Job completed successfully")
    
except Exception as e:
    print(f"❌ Job failed: {str(e)}")
    
    # FAIL event
    fail_event = create_lineage_event("FAIL")
    send_lineage_event("FAIL", fail_event)
    raise

job.commit()
