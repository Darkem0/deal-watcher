# Source access policy

Deal Watcher is designed for public, permitted sources that accept normal automated HTTP access. Some price-comparison and commerce sites may return HTTP 403, CAPTCHA, or an anti-bot page to automated clients.

The project does not solve CAPTCHAs. CAPTCHA bypass, stealth browsers, proxy rotation, fingerprint spoofing, cookie theft, and access-control weakening are out of scope. If a source does not permit normal access, its adapter stays disabled or experimental.

Direct automated HTTP access to Akakçe returned HTTP 403 during controlled verification. Akakçe is therefore disabled in the production configuration. Offline parser fixtures may remain for research and regression testing. An operator may build a new integration when a documented API, feed, or explicit permission is available.

Respect terms of service, robots policies, rate limits, and applicable law. Use conservative polling, jitter, and backoff. Do not increase request frequency or weaken protections to force access.
