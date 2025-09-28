# AWS Infrastructure with Official AWS Icons

```mermaid
flowchart TD
    subgraph dns["DNS & Domain"]
        R53@{ icon: "logos:aws-route53", form: "rect", label: "Route 53" }
        ACM@{ icon: "logos:aws-certificate-manager", form: "rect", label: "Certificate Manager" }
    end

    subgraph api["API Gateway"]
        DOMAIN[Custom Domain<br/>pass.lemaire.tel]
        APIGW@{ icon: "logos:aws-api-gateway", form: "rect", label: "API Gateway" }
    end

    subgraph compute["Compute"]
        L1@{ icon: "logos:aws-lambda", form: "rect", label: "Pass Redirect" }
        L2@{ icon: "logos:aws-lambda", form: "rect", label: "PassKit Registration" }
        L3@{ icon: "logos:aws-lambda", form: "rect", label: "PassKit Unregistration" }
        L4@{ icon: "logos:aws-lambda", form: "rect", label: "Log Errors" }
        L5@{ icon: "logos:aws-lambda", form: "rect", label: "Get Updatable" }
        L6@{ icon: "logos:aws-lambda", form: "rect", label: "S3 Pass Update" }
        LAYER[Lambda Layer<br/>Python Libraries]
    end

    subgraph storage["Storage"]
        S3@{ icon: "logos:aws-s3", form: "rect", label: "S3 Bucket" }
        DDB@{ icon: "logos:aws-dynamodb", form: "rect", label: "DynamoDB" }
    end

    subgraph security["Security"]
        SEC@{ icon: "logos:aws-secrets-manager", form: "rect", label: "Secrets Manager" }
        IAM@{ icon: "logos:aws-iam", form: "rect", label: "IAM" }
    end

    subgraph monitoring["Monitoring"]
        CW@{ icon: "logos:aws-cloudwatch", form: "rect", label: "CloudWatch" }
    end

    %% Connections
    R53 --> DOMAIN
    ACM --> DOMAIN
    DOMAIN --> APIGW

    %% API Gateway to Lambda
    APIGW --> L1
    APIGW --> L2
    APIGW --> L3
    APIGW --> L4
    APIGW --> L5

    %% Lambda to Storage
    L1 --> S3
    L2 --> DDB
    L3 --> DDB
    L5 --> DDB
    L6 --> DDB
    L6 --> SEC

    %% S3 Event
    S3 -.->|Event| L6
    LAYER --> L6

    %% IAM
    IAM -.-> L1
    IAM -.-> L2
    IAM -.-> L3
    IAM -.-> L4
    IAM -.-> L5
    IAM -.-> L6

    %% Logging
    APIGW --> CW
    L1 --> CW
    L2 --> CW
    L3 --> CW
    L4 --> CW
    L5 --> CW
    L6 --> CW

    %% Node styling
    classDef default fill:#f8f9fa,stroke:#dee2e6,stroke-width:2px,color:#495057

    %% Subgraph styling
    style dns fill:#f8f9fa,stroke:#dee2e6,stroke-width:2px
    style api fill:#f8f9fa,stroke:#dee2e6,stroke-width:2px
    style compute fill:#f8f9fa,stroke:#dee2e6,stroke-width:2px
    style storage fill:#f8f9fa,stroke:#dee2e6,stroke-width:2px
    style security fill:#f8f9fa,stroke:#dee2e6,stroke-width:2px
    style monitoring fill:#f8f9fa,stroke:#dee2e6,stroke-width:2px
```

## AWS Services with Official Icons

This diagram uses official AWS service icons from the Iconify logos collection:

### Network & DNS
- **logos:aws-route53** - DNS hosting and domain management
- **logos:aws-certificate-manager** - SSL/TLS certificates
- **logos:aws-api-gateway** - HTTP API endpoint management

### Compute
- **logos:aws-lambda** - Serverless compute functions (6 functions)

### Storage & Database
- **logos:aws-s3** - Object storage for pass files
- **logos:aws-dynamodb** - NoSQL database for device registrations

### Security
- **logos:aws-iam** - Identity and access management
- **logos:aws-secrets-manager** - Credential storage

### Monitoring
- **logos:aws-cloudwatch** - Logging and monitoring

### Architecture Benefits
- **Professional Look**: Official AWS service icons
- **Clear Service Identification**: Each icon represents the exact AWS service
- **Proper AWS Colors**: Official AWS color scheme
- **Clean Layout**: Logical grouping by service category