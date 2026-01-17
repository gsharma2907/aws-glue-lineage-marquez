# AWS Glue Data Lineage with Marquez

A complete solution for tracking data lineage in AWS Glue ETL pipelines using OpenLineage and Marquez.

## Overview

This project demonstrates how to implement end-to-end data lineage tracking for AWS Glue jobs using the OpenLineage standard and Marquez as the lineage visualization platform.

### Features

- ✅ OpenLineage-compliant Glue jobs
- ✅ Marquez deployment on AWS EC2
- ✅ Multi-stage ETL pipeline tracking
- ✅ Interactive lineage visualization
- ✅ Schema tracking and evolution
- ✅ Impact analysis and root cause tracing

## Architecture

```
AWS Glue Jobs
    ↓ (HTTP POST)
    ↓ OpenLineage Events
    ↓
Marquez API (EC2:5000)
    ↓
PostgreSQL (Docker)
    ↓
Marquez Web UI (EC2:3000)
    ↓
User Browser
```

## Quick Start

### Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Python 3.6+
- Basic knowledge of AWS Glue and CloudFormation

### 1. Deploy Infrastructure

```bash
# Deploy EC2 instance for Marquez
aws cloudformation deploy \
  --template-file cloudformation/ec2-marquez.yaml \
  --stack-name lineage-ec2 \
  --region us-east-1 \
  --parameter-overrides \
    VpcId=<YOUR_VPC_ID> \
    PublicSubnet=<YOUR_PUBLIC_SUBNET> \
  --capabilities CAPABILITY_IAM

# Deploy Glue job infrastructure
aws cloudformation deploy \
  --template-file cloudformation/glue-infrastructure.yaml \
  --stack-name lineage-glue \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM
```

### 2. Get Marquez URL

```bash
MARQUEZ_URL=$(aws cloudformation describe-stacks \
  --stack-name lineage-ec2 \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`MarquezApiUrl`].OutputValue' \
  --output text)

echo "Marquez API: $MARQUEZ_URL"
echo "Marquez Web: ${MARQUEZ_URL/5000/3000}"
```

### 3. Upload Glue Scripts

```bash
# Get S3 bucket name
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name lineage-glue \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`ArtifactsBucket`].OutputValue' \
  --output text)

# Upload scripts
aws s3 cp glue/glue_job_with_openlineage.py s3://$BUCKET/scripts/
aws s3 cp glue/glue_job_aggregation.py s3://$BUCKET/scripts/
```

### 4. Run Glue Jobs

```bash
# Run transformation job
aws glue start-job-run \
  --job-name lineage-transformation-job \
  --arguments "{\"--MARQUEZ_URL\":\"$MARQUEZ_URL\"}" \
  --region us-east-1

# Run aggregation job
aws glue start-job-run \
  --job-name lineage-aggregation-job \
  --arguments "{\"--MARQUEZ_URL\":\"$MARQUEZ_URL\"}" \
  --region us-east-1
```

### 5. View Lineage

Open the Marquez Web UI in your browser and navigate to the `glue-lineage` namespace to see your data lineage graph.

## Project Structure

```
.
├── cloudformation/
│   ├── ec2-marquez.yaml          # Marquez on EC2
│   └── glue-infrastructure.yaml  # Glue jobs and S3
├── glue/
│   ├── glue_job_with_openlineage.py  # ETL transformation job
│   └── glue_job_aggregation.py       # Aggregation job
├── docs/
│   └── ARCHITECTURE.md           # Detailed architecture
└── README.md
```

## Data Flow Example

The demo includes a two-stage pipeline:

1. **Transformation Job**
   - Input: `sample_input_data` (id, name, value)
   - Transformation: Uppercase names, square values
   - Output: `transformed_output_data` (id, name_upper, value_squared)

2. **Aggregation Job**
   - Input: `transformed_output_data`
   - Transformation: Count, average, sum
   - Output: `aggregated_statistics` (total_records, avg_value_squared, sum_value_squared)

## OpenLineage Integration

The Glue jobs emit OpenLineage events with:

- Job metadata (namespace, name, run ID)
- Dataset schemas (input and output)
- Transformation logic
- Run status (START, COMPLETE, FAIL)

Example event structure:

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-01-16T23:50:09Z",
  "producer": "https://github.com/aws/aws-glue",
  "schemaURL": "https://openlineage.io/spec/1-0-5/OpenLineage.json",
  "run": {
    "runId": "uuid-here"
  },
  "job": {
    "namespace": "glue-lineage",
    "name": "lineage-transformation-job"
  },
  "inputs": [...],
  "outputs": [...]
}
```

## Cost Estimate

### Development/POC
- EC2 t3.medium: ~$30/month
- S3 storage: ~$1/month
- Glue job runs: ~$1 per run
- **Total: ~$35/month**

## Configuration

### Environment Variables

The Glue jobs accept the following arguments:

- `--MARQUEZ_URL`: Marquez API endpoint (required)
- `--job-language`: python (default)

### Customization

To adapt for your use case:

1. Modify Glue scripts to read from your data sources (S3, RDS, etc.)
2. Update dataset names and schemas
3. Add custom transformations
4. Configure job parameters in CloudFormation

## Monitoring

### Check Marquez Health

```bash
curl http://<MARQUEZ_IP>:5000/api/v1/health
```

### View Lineage via API

```bash
# List namespaces
curl http://<MARQUEZ_IP>:5000/api/v1/namespaces

# List jobs
curl http://<MARQUEZ_IP>:5000/api/v1/namespaces/glue-lineage/jobs

# Get job details
curl http://<MARQUEZ_IP>:5000/api/v1/namespaces/glue-lineage/jobs/<JOB_NAME>
```

### CloudWatch Logs

Glue job logs are available in CloudWatch Logs under `/aws-glue/jobs/output`.

## Troubleshooting

### Marquez not accessible
- Check EC2 security group allows ports 3000 and 5000
- Verify Docker containers are running: `docker ps`
- Check logs: `docker logs marquez-api`

### Glue job fails to send lineage
- Verify MARQUEZ_URL is correct
- Check network connectivity from Glue to EC2
- Review CloudWatch logs for error details

### No lineage data in Marquez
- Confirm OpenLineage events have `producer` field
- Check Marquez API logs for validation errors
- Verify job completed successfully

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Resources

- [OpenLineage Specification](https://openlineage.io/)
- [Marquez Documentation](https://marquezproject.github.io/marquez/)
- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [AWS CloudFormation Documentation](https://docs.aws.amazon.com/cloudformation/)

## Acknowledgments

- OpenLineage community for the lineage standard
- Marquez project for the visualization platform
- AWS Glue team for the ETL service

## Support

For issues and questions:
- Open a GitHub issue
- Check existing issues and documentation
- Review CloudWatch logs for debugging

---

**Note**: This is a reference implementation. Adapt security, networking, and configuration for your specific requirements before production use.
