# ADR-001: Initial Architecture for E-commerce Platform

**Status:** Proposed

**Context:**
We need to build a new e-commerce platform quickly. The initial team is small, and we need to prioritize development speed and simplicity. The expected initial load is low, around 1,000 users per day.

**Decision:**
We will build the application as a single monolithic service.

**Architecture Details:**
- **Web Frontend & Backend:** A single Node.js application using the Express framework. It will handle both rendering the user interface (server-side rendering) and serving the REST API for client-side interactions.
- **Deployment:** The Node.js application will be deployed to a single AWS EC2 instance (t3.medium).
- **Database:** A single PostgreSQL database will be installed and run directly on the same EC2 instance as the application.
- **Authentication:** User session management will be handled by storing user IDs in a cookie. There is no password encryption planned for the first version.
- **Caching:** No caching layer will be implemented initially to maintain simplicity.

**Consequences:**
- **Positive:**
  - Extremely fast to develop and deploy.
  - Simple to understand for new developers.
  - Low initial infrastructure cost.
- **Negative:**
  - The entire system is a single point of failure.
  - Scaling requires scaling the entire monolith, which is inefficient.
  - The database and application on the same machine creates resource contention.
  - The security model for authentication is critically weak.