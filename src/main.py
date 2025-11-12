from agent import ArchitectureReviewerAgent

def main():
    print("=" * 60)
    print("Architecture Reviewer & Recommender Agent")
    print("=" * 60)
    
    agent = ArchitectureReviewerAgent()
    
    architecture = """
    We're building a microservices e-commerce platform:
    
    - Frontend: React SPA hosted on S3 + CloudFront
    - API Gateway: AWS API Gateway with Lambda authorizers
    - Services: 5 microservices running on ECS Fargate
    - Database: Single RDS PostgreSQL instance (db.t3.large)
    - Cache: No caching implemented yet
    - Authentication: JWT tokens stored in localStorage
    - Logging: CloudWatch logs
    - Monitoring: Basic CloudWatch metrics
    
    Expected load: 10,000 requests/minute peak
    Budget: $5000/month
    """
    
    print("\nArchitecture to review:")
    print(architecture)
    print("\n" + "=" * 60)
    print("Starting review...\n")
    
    result = agent.review(architecture)
    
    print("\n" + "=" * 60)
    print("FINAL REVIEW")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    main()