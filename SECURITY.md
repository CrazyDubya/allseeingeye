# Security Policy

## Supported Versions

We currently provide security updates for the following versions of AllSeeingEye:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

We take the security of AllSeeingEye seriously. If you believe you've found a security vulnerability, please follow these steps:

1. **Do not disclose the vulnerability publicly**
2. **Email us** at security@example.com with details about the vulnerability
3. Include the following information:
   - Type of vulnerability
   - Full path to the affected file(s)
   - Step-by-step instructions to reproduce the issue
   - Potential impact
   - Any possible mitigations you've identified

## What to Expect

- We will acknowledge receipt of your vulnerability report within 3 business days
- We will provide an initial assessment of the report within 7 business days
- We aim to release a fix for verified vulnerabilities within 30 days, depending on complexity
- We will keep you informed of our progress throughout the process

## Security Considerations

AllSeeingEye processes arbitrary files from the file system. As such, we have implemented several security measures:

- Path validation to prevent directory traversal
- Content sanitization to handle potentially malicious files
- Emoji sanitization to prevent hidden data in Unicode emoji sequences
- Homoglyph detection and replacement to prevent lookalike character attacks
- Control character stripping to prevent parser manipulation
- Resource limits to prevent denial-of-service attacks
- Secure file handling practices
- Obfuscation detection to identify potentially hidden malicious code

However, users should be aware of the following security considerations:

- AllSeeingEye should not be run with elevated privileges
- The tool should not be exposed to untrusted input or over the network
- When using LLM features, be aware of potential data exposure to external services

## Security Improvements

We are continuously improving the security of AllSeeingEye. Recent security enhancements include:

- Enhanced path validation
- Improved error handling
- Content sanitization
- Resource limiting
- Secure dependency management

If you have suggestions for additional security improvements, please open an issue or contact us at security@example.com.
