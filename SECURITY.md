# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Agent Foundry seriously. If you discover a security vulnerability, please follow these steps:

### Do NOT

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed

### Do

1. **Report privately**: Send an email to the maintainers with details about the vulnerability
2. **Include details**: Provide as much information as possible:
   - Type of vulnerability
   - Full paths of affected source files
   - Location of affected code (tag/branch/commit or direct URL)
   - Step-by-step instructions to reproduce
   - Proof-of-concept or exploit code (if possible)
   - Impact of the vulnerability

### What to expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Assessment**: We will assess the vulnerability and determine its severity
- **Updates**: We will keep you informed about our progress
- **Resolution**: We aim to resolve critical vulnerabilities within 7 days
- **Credit**: We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices

When using Agent Foundry, follow these security best practices:

### API Keys and Secrets

- Never commit API keys or secrets to the repository
- Use environment variables for sensitive configuration
- Store secrets in a secure secrets manager
- Rotate API keys regularly

### Environment Configuration

```bash
# Use .env files (never commit these)
cp backend/.env.example backend/.env

# Set secure permissions
chmod 600 backend/.env
```

### Docker Security

- Always use non-root users in production containers
- Keep base images updated
- Scan images for vulnerabilities regularly
- Use multi-stage builds to minimize attack surface

### Network Security

- Use HTTPS in production
- Configure CORS appropriately for your deployment
- Implement rate limiting for API endpoints
- Use a Web Application Firewall (WAF) when possible

## Security Features

Agent Foundry includes several security features:

- **Multi-tenant authentication** via Frontegg integration
- **Role-based access control** for agent operations
- **Sandboxed code execution** for generated code
- **Input validation** on all API endpoints
- **SQL injection prevention** via parameterized queries

## Automated Security Scanning

This repository uses:

- **Dependabot**: Automated dependency vulnerability alerts and updates
- **CodeQL**: Automated code scanning for security vulnerabilities
- **Secret scanning**: Detection of accidentally committed secrets

## Contact

For security-related inquiries, please contact the maintainers through GitHub's private vulnerability reporting feature.
