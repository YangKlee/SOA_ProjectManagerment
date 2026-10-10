# Log service

## Shared internal credential

INTERNAL_SERVICE_TOKEN is the common environment setting across trusted services.
This service currently has no token-authenticated internal contract; the setting
does not introduce endpoints or change public authorization. User JWTs and Consul
ACL credentials remain separate. Never commit a real token or send it to the
frontend. See the root README for coordinated provisioning and rotation.

Supply the setting through process environment; .env.example documents the name, but no dotenv loader/dependency is added.
