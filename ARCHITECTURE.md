# Architecture Overview

## System Components

### 1. Marquez Platform (EC2)

**Components**:
- PostgreSQL 12 (Docker container)
- Marquez API (Docker container, port 5000)
- Marquez Web UI (Docker container, port 3000)

**Purpose**:
- Store lineage metadata
- Provide REST API for lineage events
- Visualize data lineage graphs

### 2. AWS Glue Jobs

**Jobs**:
- Transformation Job: ETL transformations
- Aggregation Job: Data aggregation

**Purpose**:
- Process data
- Emit OpenLineage events
- Track data transformations

### 3. S3 Bucket

**Purpose**:
- Store Glue job scripts
- Store job artifacts
- Version control for scripts

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                            │
│  (S3, RDS, Redshift, DynamoDB, etc.)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    AWS Glue Job                             │
│  1. Read data from source                                   │
│  2. Transform data                                          │
│  3. Write data to destination                               │
│  4. Emit OpenLineage events                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP POST
                         │ /api/v1/lineage
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Marquez API (EC2:5000)                         │
│  - Validate OpenLineage events                              │
│  - Store in PostgreSQL                                      │
│  - Provide REST API                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                            │
│  - Namespaces                                               │
│  - Jobs                                                     │
│  - Datasets                                                 │
│  - Runs                                                     │
│  - Lineage relationships                                    │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Marquez Web UI (EC2:3000)                      │
│  - Interactive lineage graph                                │
│  - Dataset explorer                                         │
│  - Job run history                                          │
│  - Search and filter                                        │
└─────────────────────────────────────────────────────────────┘
```

## OpenLineage Event Flow

### 1. Job Start
```json
{
  "eventType": "START",
  "eventTime": "2026-01-16T10:00:00Z",
  "producer": "https://github.com/aws/aws-glue",
  "run": {"runId": "uuid"},
  "job": {
    "namespace": "glue-lineage",
    "name": "transformation-job"
  }
}
```

### 2. Job Complete
```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-01-16T10:05:00Z",
  "producer": "https://github.com/aws/aws-glue",
  "run": {"runId": "uuid"},
  "job": {
    "namespace": "glue-lineage",
    "name": "transformation-job"
  },
  "inputs": [
    {
      "namespace": "glue-lineage",
      "name": "input_dataset",
      "facets": {
        "schema": {
          "fields": [...]
        }
      }
    }
  ],
  "outputs": [
    {
      "namespace": "glue-lineage",
      "name": "output_dataset",
      "facets": {
        "schema": {
          "fields": [...]
        }
      }
    }
  ]
}
```

## Network Architecture

```
Internet
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    VPC                                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Public Subnet                              │  │
│  │                                                      │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  EC2 Instance (Marquez)                        │ │  │
│  │  │  - Public IP                                   │ │  │
│  │  │  - Security Group:                             │ │  │
│  │  │    * Port 3000 (Web UI)                        │ │  │
│  │  │    * Port 5000 (API)                           │ │  │
│  │  │    * Port 22 (SSH)                             │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           AWS Glue (Managed Service)                 │  │
│  │  - Runs in AWS-managed VPC                          │  │
│  │  - Can access public endpoints                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Security Considerations

### Current (POC)
- Public EC2 instance
- Open security groups (0.0.0.0/0)
- No authentication on Marquez
- Embedded PostgreSQL in Docker

### Production Recommendations
- Private subnets for compute
- Application Load Balancer in public subnet
- VPC endpoints for AWS services
- Authentication (Cognito/OAuth)
- Encryption at rest and in transit
- RDS Aurora instead of Docker PostgreSQL
- WAF for API protection

## Scalability

### Current Limits
- Single EC2 instance
- Single PostgreSQL container
- No auto-scaling
- ~1000 jobs/day capacity

### Production Scaling
- ECS Fargate with auto-scaling
- RDS Aurora with read replicas
- ElastiCache for API caching
- CloudFront for static assets
- ~100,000+ jobs/day capacity

## Monitoring

### Metrics to Track
- Glue job success/failure rate
- Lineage event delivery rate
- Marquez API response time
- PostgreSQL connection count
- Storage utilization

### Logging
- Glue job logs → CloudWatch
- Marquez API logs → Docker logs
- PostgreSQL logs → Docker logs
- Access logs → ALB (production)

## Cost Breakdown

### Development/POC
| Component | Cost/Month |
|-----------|------------|
| EC2 t3.medium | $30 |
| EBS 20GB | $2 |
| S3 storage | $1 |
| Glue job runs | $1/run |
| **Total** | **~$35** |

### Production
| Component | Cost/Month |
|-----------|------------|
| ECS Fargate | $150 |
| RDS Aurora | $200 |
| ALB | $20 |
| ElastiCache | $100 |
| CloudWatch | $50 |
| **Total** | **~$520** |

With Reserved Instances: **~$350/month**

## Disaster Recovery

### Backup Strategy
- PostgreSQL: Daily snapshots
- S3: Versioning enabled
- CloudFormation: Infrastructure as Code

### Recovery Procedures
1. Restore PostgreSQL from snapshot
2. Redeploy EC2 from CloudFormation
3. Restore Glue jobs from S3
4. Verify lineage data integrity

### RTO/RPO
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 24 hours

## Future Enhancements

1. **Multi-Region Deployment**
   - Cross-region replication
   - Global lineage view
   - Disaster recovery

2. **Advanced Features**
   - Data quality metrics
   - Column-level lineage
   - Impact analysis automation
   - Lineage-based access control

3. **Integration**
   - Apache Airflow integration
   - dbt integration
   - Spark integration
   - Kafka integration

4. **Analytics**
   - Lineage analytics dashboard
   - Usage patterns
   - Performance optimization
   - Cost attribution
