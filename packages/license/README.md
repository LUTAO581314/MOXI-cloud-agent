# License Package

This package will implement license generation, signing, parsing, and validation
helpers used by the platform and Hermes deployment flow.

License payload should include:

- license id;
- organization id;
- plan;
- features;
- limits;
- issue time;
- expiry time;
- deployment mode;
- signature.

License payload must not include secrets, API keys, connector tokens, or customer
business data.
