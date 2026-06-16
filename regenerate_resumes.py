"""
Regenerate all 7 personalized resumes with the improved professional formatting.
Runs standalone — no Claude API call needed (summaries are pre-written).
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from linkedin_agent import create_personalized_resume, RESUME_DIR

JOBS = [
    {
        "company": "TCS Fuel / Apex Capital",
        "title": "Senior Software Engineer",
        "filename": "TCS-Fuel-Apex-Capital-Senior-Software-Engineer-2026-06-15.docx",
        "description": "Java Spring Boot microservices AWS Lambda SNS SQS DynamoDB reactive Spring WebFlux",
        "summary": (
            "Senior Software Engineer with 18+ years of experience building high-performance Java/Spring Boot "
            "microservices and event-driven architectures for financial and enterprise clients. Specialized in "
            "Spring WebFlux, Project Reactor, and AWS (Lambda, SNS/SQS, DynamoDB, S3) with a proven record "
            "of delivering cloud-native solutions at scale. Led the architecture of distributed financial "
            "platforms processing millions of transactions, integrating voice-biometric authentication "
            "and CQRS-based document management systems. Containerized with Docker/Kubernetes, CI/CD via Jenkins."
        ),
    },
    {
        "company": "Fidelity Investments",
        "title": "Principal Software Engineer Java Spring Boot REST",
        "filename": "Fidelity-Investments-Principal-Software-Engineer-Ja-2026-06-15.docx",
        "description": "Java Spring Boot REST microservices AWS financial services PostgreSQL DynamoDB",
        "summary": (
            "Principal-level Java Software Engineer with 18+ years delivering mission-critical financial "
            "backend systems using Java 17/21, Spring Boot, Spring WebFlux, and REST APIs. Expert in "
            "cloud-native microservices on AWS (Lambda, API Gateway, RDS/PostgreSQL, DynamoDB, Cognito) "
            "with deep knowledge of reactive programming via Project Reactor. Architected identity-validation "
            "and compliance platforms for banking clients, enforcing OAuth 2.0/JWT security and SLA-driven "
            "performance. Strong culture of quality: JUnit 5, Mockito, SonarQube, Docker/Kubernetes, Jenkins CI/CD."
        ),
    },
    {
        "company": "Worldpay",
        "title": "Software Engineer Java Spring Boot Microservices",
        "filename": "Worldpay-Software-Engineer-Java-Spring--2026-06-15.docx",
        "description": "Java Spring Boot microservices payments AWS Docker Kubernetes REST APIs PostgreSQL Redis",
        "summary": (
            "Software Engineer with 18+ years of expertise in Java (8-21), Spring Boot, and payment-processing "
            "microservices. Built distributed, event-driven transaction systems using AWS SNS/SQS, Redis for "
            "caching, PostgreSQL/MySQL for persistence, and Docker/Kubernetes for orchestration. Designed "
            "AES/RSA-secured API layers and CQRS-based complaint/document platforms for global financial clients. "
            "Proven at Worldpay-scale throughput: reactive Spring WebFlux pipelines with zero-downtime deployment "
            "via Jenkins CI/CD and SonarQube quality gates."
        ),
    },
    {
        "company": "PlanOmatic",
        "title": "Senior Software Engineer Back-End Java Spring Boot",
        "filename": "PlanOmatic-Senior-Software-Engineer-Back--2026-06-15.docx",
        "description": "Java Spring Boot backend REST APIs AWS S3 PostgreSQL microservices Docker",
        "summary": (
            "Senior Back-End Engineer with 18+ years specializing in Java/Spring Boot REST microservices, "
            "AWS cloud infrastructure, and scalable data pipelines. Delivered production-grade services for "
            "financial and real-estate-tech clients: S3-backed document storage, SNS/SQS event-driven pipelines, "
            "PostgreSQL/DynamoDB persistence layers, and Spring Security/OAuth 2.0 authentication. "
            "Clean Architecture advocate with rigorous TDD (JUnit 5/Mockito), Docker containerization, "
            "and Jenkins CI/CD. Thrives in remote-first Agile/SCRUM teams."
        ),
    },
    {
        "company": "Value Technology Inc",
        "title": "Java Full Stack Developer with React",
        "filename": "Value-Technology-Inc-Java-Full-Stack-Developer-with-2026-06-15.docx",
        "description": "Java Spring Boot React TypeScript fullstack developer REST APIs AWS PostgreSQL",
        "summary": (
            "Full-Stack Java Engineer with 18+ years building end-to-end web applications using ReactJS/Next.js "
            "frontends and Spring Boot/Java backends. Led full-stack architecture for a digital savings platform "
            "(Next.js + TypeScript + Spring WebFlux + AWS RDS), and card-management systems with React and PHP. "
            "Strong AWS expertise (Lambda, S3, API Gateway, Cognito) and solid DevOps practices (Docker, "
            "Kubernetes, Jenkins). Fluent in TypeScript, Node.js 22, REST APIs, and Agile workflows."
        ),
    },
    {
        "company": "PNC Financial Services",
        "title": "Technology Engineer Sr Java Full Stack",
        "filename": "PNC-Financial-Services-Technology-Engineer-Sr-Java-Fu-2026-06-15.docx",
        "description": "Java Spring Boot fullstack React AWS financial services DynamoDB PostgreSQL microservices",
        "summary": (
            "Senior Java Full-Stack Technology Engineer with 18+ years in financial services software, "
            "combining deep Java/Spring Boot backend expertise with ReactJS/Next.js frontend capabilities. "
            "Architected cloud-native financial platforms on AWS (Lambda, DynamoDB, RDS, Cognito, SNS/SQS) "
            "with reactive Spring WebFlux services. Built identity-validation, voice-biometric, and compliance "
            "microservices for banking clients. Security-focused: OAuth 2.0, JWT, AES/RSA, Spring Security. "
            "Strong financial domain knowledge, Docker/Kubernetes, Jenkins CI/CD, SOLID principles."
        ),
    },
    {
        "company": "Keeper Security, Inc.",
        "title": "Software Engineer Backend Java KeeperApp",
        "filename": "KeeperSecurity-Software-Engineer-Backend-Java-2026-06-15.docx",
        "description": "Java Spring Boot AWS Lambda DynamoDB S3 backend security microservices Docker Kubernetes",
        "summary": (
            "Backend Java Engineer with 18+ years building secure, high-availability cloud services using "
            "Java 17/21, Spring Boot, and AWS (Lambda, DynamoDB, S3, SNS/SQS, Cognito, CloudWatch). "
            "Specialized in security-first architectures: OAuth 2.0, JWT, AES/RSA encryption, Spring Security, "
            "and identity/authentication platforms -- directly relevant to Keeper's cybersecurity mission. "
            "Designed distributed microservices with CQRS, event-driven messaging, and reactive Spring WebFlux "
            "pipelines. Docker/Kubernetes deployments, Jenkins CI/CD, and JUnit 5/Mockito TDD. "
            "Trusted with sensitive banking and biometric data at enterprise scale."
        ),
    },
]


if __name__ == "__main__":
    print(f"\nRegenerating {len(JOBS)} resumes with professional formatting...\n")
    for job in JOBS:
        # Override the generated filename with the existing one so we keep the same name
        path = create_personalized_resume(
            job_title=job["title"],
            company=job["company"],
            job_description=job["description"],
            priority_label="Priority 1 - Backend Java (Spring Boot / Reactive)",
            tailored_summary=job["summary"],
        )
        # Rename to exact expected filename if different
        expected = RESUME_DIR / job["filename"]
        if path != expected and path.exists():
            path.rename(expected)
            print(f"    -> saved as {job['filename']}")

    print("\nAll resumes regenerated successfully!")
    print(f"Location: {RESUME_DIR}")
