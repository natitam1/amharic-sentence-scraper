# Security Policy

Report vulnerabilities privately through the repository owner's GitHub contact rather than a public issue when they could expose credentials, private datasets, local files, or third-party services. Include affected versions, reproduction steps, impact, and suggested mitigation.

Run the scraper without privileged filesystem access. Do not store secrets in `config.yaml`. Review dependency changes before installation. Keep `robots.fail_closed: true` unless a documented and legally reviewed deployment requires otherwise.
