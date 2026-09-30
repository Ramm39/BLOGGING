ARTICLES = [
    {
        'slug': 'api-rate-limiting',
        'title': 'API Rate Limiting with Token Buckets and Redis: What Actually Works',
        'description': 'How I ship token-bucket rate limits with Redis, pick keys and limits, and avoid the mistakes that take APIs down under burst traffic.',
        'category': 'Backend',
        'date': '2026-08-02',
        'updated': '2026-09-29',
        'read_min': 8,
        'keywords': 'API rate limiting, token bucket, Redis rate limit, Express middleware, sliding window, 429 Too Many Requests',
        'excerpt': 'Rate limiting is not a nice-to-have once bots or a buggy client find your public endpoints. Here is the token-bucket design I use with Redis, including the failure modes I hit in production.',
        'sections': [
            {
                'h2': 'Why I finally stopped shipping APIs without limits',
                'paragraphs': [
                    'The first paid API I put on the public internet had auth, validation, and careful indexes. It did not have rate limits. A partner script with a retry loop stuck on a 500 burned through our MongoDB connection pool in under four minutes. CPU looked fine. Latency exploded. Customers saw timeouts.',
                    'That incident taught me a blunt rule: every externally reachable endpoint needs a budget. Not just auth. Auth tells you who is calling. Rate limits tell you how hard they can hit you. Without both, one bad client or leaked key can flatten everyone else.',
                    'I now treat rate limiting as part of the default middleware stack, same as CORS and request logging. The algorithm matters less than having something consistent, observable, and hard to bypass by opening a second process.',
                    "If you run multi-tenant SaaS, rate limits are part of fairness between tenants. Without them, one noisy customer becomes everyone else's latency problem—and your status page.",
                ],
            },
            {
                'h2': 'Token bucket vs fixed window vs sliding window',
                'paragraphs': [
                    'Fixed windows are simple: allow N requests per minute, reset on the clock. They fail at the boundary. A client can send N requests at 00:59 and N more at 01:00 and get 2N in two seconds. I have watched scrapers do exactly that against marketing APIs.',
                    'Sliding windows fix the burst at the cost of more bookkeeping. Token buckets sit in a sweet spot for APIs: you refill tokens at a steady rate, and you can allow short bursts up to a capacity. That matches how real UIs behave—idle, then a flurry of clicks.',
                    'I default to token bucket for product APIs. I use a strict fixed or sliding window only when a contract literally says “100 requests per calendar minute” and auditors care about the wall clock.',
                ],
                'bullets': [
                    'Fixed window: easy, cheap, bursty at boundaries',
                    'Sliding window: smoother, more Redis ops or memory',
                    'Token bucket: burst-friendly, good for interactive clients',
                ],
            },
            {
                'h2': 'Redis-backed token bucket in Node',
                'paragraphs': [
                    'In-memory maps work on a single Node process and fall apart behind a load balancer. Redis is the shared counter I trust. The pattern below uses a small Lua script so refill and consume are atomic. Without atomicity you under-count under concurrency and clients sneak past the limit. The script also reads the clock with Redis TIME instead of each app server\'s Date.now(), so clock skew between instances cannot over- or under-refill a bucket.',
                    'I key by authenticated user id when present, otherwise by IP plus route group. Never key only by IP for logged-in APIs—NAT and mobile carriers share addresses and you will punish the wrong people.',
                ],
                'code': "const REDIS_SCRIPT = `\nlocal key = KEYS[1]\nlocal capacity = tonumber(ARGV[1])\nlocal refill_per_ms = tonumber(ARGV[2])\nlocal cost = tonumber(ARGV[3])\n\n-- Use the Redis server clock so every app instance shares one time source\nlocal t = redis.call('TIME')\nlocal now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)\n\nlocal data = redis.call('HMGET', key, 'tokens', 'ts')\nlocal tokens = tonumber(data[1])\nlocal ts = tonumber(data[2])\n\nif tokens == nil then\n  tokens = capacity\n  ts = now\nend\n\nlocal elapsed = math.max(0, now - ts)\ntokens = math.min(capacity, tokens + elapsed * refill_per_ms)\n\nif tokens < cost then\n  redis.call('HSET', key, 'tokens', tokens, 'ts', now)\n  redis.call('PEXPIRE', key, math.ceil(capacity / refill_per_ms))\n  return {0, tokens}\nend\n\ntokens = tokens - cost\nredis.call('HSET', key, 'tokens', tokens, 'ts', now)\nredis.call('PEXPIRE', key, math.ceil(capacity / refill_per_ms))\nreturn {1, tokens}\n`;\n\nasync function takeToken(redis, key, { capacity, refillPerSec, cost = 1 }) {\n  const refillPerMs = refillPerSec / 1000;\n  const [allowed, remaining] = await redis.eval(\n    REDIS_SCRIPT, 1, key, capacity, refillPerMs, cost\n  );\n  return { allowed: allowed === 1, remaining: Number(remaining) };\n}",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Wiring it as Express middleware',
                'paragraphs': [
                    'I keep limits per route class, not one global number. Auth login stays tight. Read-heavy list endpoints get more headroom. Expensive report generation costs multiple tokens so one call counts like five cheap GETs.',
                    'Always return 429 with Retry-After when you can estimate it. Clients that respect the header stop hammering. Also emit RateLimit-Remaining style headers so partner integrations can back off before they fail.',
                    'I unit-test middleware with a fake Redis that records eval calls. That catches key shape bugs before load tests.',
                    "req.ip is only the client address if Express knows about the proxies in front of it. Behind a load balancer or CDN, set app.set('trust proxy', n) to the number of proxy hops (or the proxies' addresses); without it, req.ip is the proxy and every anonymous client shares one bucket. Avoid 'trust proxy' true unless the last proxy overwrites X-Forwarded-For, or clients can choose their own key.",
                ],
                'code': "function rateLimit({ name, capacity, refillPerSec, cost = 1 }) {\n  return async (req, res, next) => {\n    const subject = req.user?.id || req.ip;\n    const key = `rl:${name}:${subject}`;\n    try {\n      const result = await takeToken(redis, key, { capacity, refillPerSec, cost });\n      res.setHeader('X-RateLimit-Limit', String(capacity));\n      res.setHeader('X-RateLimit-Remaining', String(Math.floor(result.remaining)));\n      if (!result.allowed) {\n        // Seconds until enough tokens have refilled to cover this request's cost\n        const retryAfter = Math.max(1, Math.ceil((cost - result.remaining) / refillPerSec));\n        res.setHeader('Retry-After', String(retryAfter));\n        return res.status(429).json({ error: 'rate_limit_exceeded' });\n      }\n      return next();\n    } catch (err) {\n      // Fail open or closed? See next section.\n      console.error('rate limit redis error', err);\n      return next();\n    }\n  };\n}\n\n// Behind a load balancer/CDN: trust exactly the proxy hops in front of the app,\n// otherwise req.ip is the proxy's address and all anonymous clients share one bucket.\napp.set('trust proxy', 1);\n\napp.post('/auth/login', rateLimit({ name: 'login', capacity: 10, refillPerSec: 0.2 }), loginHandler);\napp.get('/api/items', rateLimit({ name: 'items', capacity: 120, refillPerSec: 2 }), listItems);",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Fail open, fail closed, and the Redis outage',
                'paragraphs': [
                    'When Redis blips, you choose: fail open (serve traffic, lose protection) or fail closed (reject everyone). Early on I failed open and a Redis restart coincided with a crawler spike. We stayed up for healthy users but the crawler enjoyed unrestricted access for three minutes.',
                    'For login, password reset, and anything billing-related I now fail closed with a clear 503. For low-risk public GETs I fail open and page ops. Document the choice. Do not leave it as an accidental catch that always calls next().',
                    'Also put a local circuit breaker around Redis so a dead cluster does not add 200ms of timeout latency to every request while Node waits on the client.',
                ],
            },
            {
                'h2': 'Testing and the mistakes I still see',
                'paragraphs': [
                    'Unit-test the Lua script with concurrent callers. I use a small Node script that fires 200 parallel requests against a local Redis and asserts the total allowed count stays within capacity plus a tiny float tolerance.',
                    'Load-test with realistic keys. A limit of 100/min “works” in staging when everyone shares one test user and fails in production when each user has their own bucket and aggregate load is higher.',
                ],
                'bullets': [
                    'Do not rate-limit health checks on the same key as user traffic',
                    'Separate anonymous and authenticated buckets',
                    'Log 429s with route and subject hash, not raw tokens',
                    'Watch p95 Redis latency—slow rate limits become your new bottleneck',
                    'Document partner-facing limits in the API docs before they guess',
                ],
            },
            {
                'h2': 'What I ship by default now',
                'paragraphs': [
                    'Token bucket in Redis, atomic Lua, per-route profiles, Retry-After on 429, and an explicit fail-open/fail-closed policy. That stack has survived partner bursts, leaked keys, and one very enthusiastic QA script.',
                    'Start stricter than you think, then raise limits with data. Raising a limit is a config change. Cleaning up after an unbounded endpoint is an incident.',
                ],
            },
            {
                'h2': 'Choosing numbers that survive contact with users',
                'paragraphs': [
                    'Limits look scientific in a design doc and arbitrary in production. I start from a capacity estimate: peak legitimate RPS for a single user or API key, times a safety factor of three, then round to something explainable in docs. Login might be 5 attempts per minute. A mobile app sync endpoint might be 60 per minute with a burst of 20.',
                    'I also cost expensive routes higher. A PDF export that hits the database and an object store might cost 10 tokens while a health-style metadata GET costs 1. That keeps the same bucket model without inventing a second limiter.',
                    'Document the limits publicly for partner APIs. Undocumented limits look like random outages. When we raised a partner from 60 to 300 after reviewing their traffic shape, the change was a config deploy—not an emergency rewrite.',
                ],
                'bullets': [
                    'Derive limits from observed p95 client behavior plus headroom',
                    'Charge multi-token costs for expensive handlers',
                    'Publish partner limits and changelog them',
                    'Alert on 429 rate, not only on 5xx',
                ],
            },
            {
                'h2': 'Edge rate limits vs application rate limits',
                'paragraphs': [
                    'CDN or API-gateway limits catch volumetric abuse early and protect origin CPU. Application limits enforce product rules per user and per route. I run both when traffic warrants it. Edge alone cannot express “this authenticated tenant gets 10 report jobs per hour.”',
                    'If you only put limits in Nginx and forget the app, a second ingress path—internal service mesh, forgotten port, new cloud load balancer—bypasses them. Defense in depth means the app still knows how to say no.',
                ],
            },
        ],
        'takeaways': [
            'Put rate limits on every public endpoint before launch, not after an incident.',
            'Prefer Redis-backed token buckets for multi-instance APIs; keep consume/refill atomic.',
            'Key by user id when authenticated; use IP only as a fallback for anonymous traffic.',
            'Return 429 with Retry-After and remaining-limit headers clients can honor.',
            'Decide fail-open vs fail-closed per route class when Redis is unavailable.',
            'Load-test with many subjects—shared staging keys hide real aggregate load.',
        ],
    },
    {
        'slug': 'nodejs-env-vars-security',
        'title': 'Environment Variables Security for Node Apps: Lessons from Leaked Secrets',
        'description': 'Practical rules for storing, loading, and rotating secrets in Node.js without leaking them through logs, git, or Docker images.',
        'category': 'Backend',
        'date': '2026-08-05',
        'updated': '2026-09-29',
        'read_min': 8,
        'keywords': 'Node.js environment variables, dotenv security, secrets management, process.env, .env.example, credential rotation, Kubernetes Secrets',
        'excerpt': 'Most Node secret leaks I investigate are not exotic exploits. They are .env files in git, DEBUG logs printing process.env, and Docker layers that baked credentials into the image.',
        'sections': [
            {
                'h2': 'The leak that made me paranoid about process.env',
                'paragraphs': [
                    'A junior engineer added console.log({ env: process.env }) while debugging a Stripe webhook. The log shipped to our hosted aggregator. Within an hour the dashboard showed API keys, database URLs, and a JWT secret sitting in plaintext search results. We rotated everything. It cost a Saturday.',
                    'Environment variables are convenient, not safe by default. They are readable by the process, often inherited by child processes, and easy to dump accidentally. Treat them as a delivery mechanism for secrets, then minimize how long and how widely those values exist in memory and logs.',
                    'Secret scanners in CI are cheap insurance. They will not catch everything, but they stop the classic accidental commit.',
                ],
            },
            {
                'h2': 'What belongs in env vars—and what does not',
                'paragraphs': [
                    'I put deployment-specific config and short-lived credentials in the environment: database URLs, API keys, feature flags that differ per env. I do not put large JSON blobs, private keys longer than necessary, or anything that should be different per request.',
                    'Public config can live in committed files. Secrets must not. The failure mode is mixing them: one “config” object that includes both NODE_ENV and STRIPE_SECRET_KEY, then logging the whole object.',
                ],
                'bullets': [
                    'OK in env: DB_URL, REDIS_URL, API keys, signing secrets',
                    'Commit freely: port defaults, feature names, non-secret timeouts',
                    'Never commit: .env with real values, service account JSON, PEM files',
                    'Prefer a secret manager for production; env injection at deploy time',
                ],
            },
            {
                'h2': 'Local dotenv without polluting git',
                'paragraphs': [
                    'I still use dotenv locally. Production never depends on a .env file on disk. The app reads process.env that the platform injects. That split keeps “works on my laptop” from becoming “we SCP a secrets file onto the box.”',
                    'Commit .env.example with placeholder values and comments. Add .env and .env.*.local to .gitignore before the first commit. I also add a pre-commit secret scan on the team repo after watching someone force-add a .env “just this once.”',
                ],
                'code': '# .env.example — safe to commit\nNODE_ENV=development\nPORT=3000\nDATABASE_URL=postgres://user:pass@localhost:5432/app\nJWT_SECRET=replace-me-with-long-random\nSTRIPE_SECRET_KEY=sk_test_replace_me\n\n# .gitignore\n.env\n.env.*\n!.env.example',
                'code_lang': 'bash',
            },
            {
                'h2': 'Load once, validate early, never print',
                'paragraphs': [
                    'I centralize env loading in one module. It fails fast if required keys are missing. Spreading process.env.FOO across fifty files makes it impossible to know what is required for boot.',
                    'Validation with zod or joi catches empty strings and wrong types before the server accepts traffic. That is better than a cryptic failure deep in a Stripe call at 2 a.m.',
                ],
                'code': "import { z } from 'zod';\n\nconst EnvSchema = z.object({\n  NODE_ENV: z.enum(['development', 'test', 'production']),\n  PORT: z.coerce.number().int().positive().default(3000),\n  DATABASE_URL: z.string().url(),\n  JWT_SECRET: z.string().min(32),\n  STRIPE_SECRET_KEY: z.string().startsWith('sk_'),\n});\n\nexport const env = EnvSchema.parse(process.env);\n\n// Never do this:\n// logger.info('boot', { env });\n\nexport function redactedEnvSummary() {\n  return {\n    NODE_ENV: env.NODE_ENV,\n    PORT: env.PORT,\n    DATABASE_URL: env.DATABASE_URL.replace(/:\\/\\/.*@/, '://***@'),\n    JWT_SECRET: '[redacted]',\n    STRIPE_SECRET_KEY: '[redacted]',\n  };\n}",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Docker and CI traps',
                'paragraphs': [
                    'ENV lines in Dockerfiles with real secrets bake values into image layers forever. Use runtime -e flags, orchestration secrets, or build args only for non-secrets. I have pulled “old” images from a registry and found keys from a previous customer still in the history.',
                    'In CI, map secrets from the vault or GitHub Actions secrets into env for the job. Do not echo them in scripts. Mask them in the CI UI. Be careful with set -x in bash—it prints expanded variables.',
                    'Child processes inherit the full environment. If you spawn a CLI tool you do not trust, scrub the env you pass it.',
                    'Build args in Docker are visible in image history. Never pass secrets as build-arg “just for compile time”: a build arg used in the final stage of a multi-stage build still lands in that image’s history. For secrets a build step really needs (a private registry token for npm ci, say), use a BuildKit secret mount (RUN --mount=type=secret), which exposes the value to that one RUN step without writing it to a layer. For everything the app needs at run time, prefer runtime injection.',
                ],
                'code': "// Bad: secret baked into image\n// ENV STRIPE_SECRET_KEY=sk_live_...\n\n// Better: inject at runtime\n// docker run -e STRIPE_SECRET_KEY --env-file /run/secrets/app.env myapp\n\n// Build-time secret without baking it into a layer (BuildKit):\n// Dockerfile:  RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci\n// Build:       docker build --secret id=npmrc,src=$HOME/.npmrc .\n\n// In Node when spawning untrusted tools:\nimport { spawn } from 'node:child_process';\nspawn('some-tool', [], {\n  env: { PATH: process.env.PATH, HOME: process.env.HOME },\n});",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Kubernetes Secrets for Node apps',
                'paragraphs': [
                    'A Kubernetes Secret is not encrypted just because it is a Secret. The base64 in its YAML is an encoding for the API, and base64 -d reverses it. By default the API server stores Secret data in etcd unencrypted, so anyone who can read the Secret object, or etcd and its backups, can read the credential. A Secret manifest committed to git is a plaintext secret in git.',
                    'How the pod consumes a Secret decides what happens on rotation. Environment variables set from a Secret (env with secretKeyRef, or envFrom) are fixed when the container starts and never change in a running container, so a new value needs a pod restart, for example kubectl rollout restart deployment/api. Files from a Secret volume are updated by the kubelet after the Secret changes, eventually rather than instantly, but a Secret mounted with subPath never receives updates. A Node app that reads the file once at boot still needs a restart or a re-read to pick up a rotated value.',
                    'Protect the object itself. Enable encryption at rest with the kube-apiserver flag --encryption-provider-config pointing at an EncryptionConfiguration, preferably with a KMS provider; managed platforms expose their own setting for this, so check it rather than assume. Restrict get, list and watch on secrets with RBAC to the workloads and people that need them: list and watch return Secret contents too, and anyone who can create a pod in a namespace can mount that namespace’s Secrets.',
                    'For production, keep the source of truth in an external manager such as Vault, AWS Secrets Manager, GCP Secret Manager or Azure Key Vault, and bring values into the cluster with the External Secrets Operator or the Secrets Store CSI Driver. Rotation and audit then happen in one place, and git only holds references to secret names, never values.',
                ],
                'code': "import { readFileSync } from 'node:fs';\n\n// Secret volume mounted at /var/run/secrets/db (no subPath, so updates arrive)\nconst PASSWORD_FILE = process.env.DB_PASSWORD_FILE ?? '/var/run/secrets/db/password';\n\n// Read at connect time, not once at boot, so a rotated password is picked up\nexport function dbPassword() {\n  return readFileSync(PASSWORD_FILE, 'utf8').trim();\n}",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Rotation and least privilege',
                'paragraphs': [
                    'Assume every secret will eventually leak. Design for rotation: short TTLs where the provider allows it, dual-key windows for JWT signing, and runbooks that do not require a full outage.',
                    'Give each service its own credentials. A marketing site should not share the production database user that can DROP TABLE. When the marketing deploy pipeline leaked, isolation saved the core API.',
                ],
            },
            {
                'h2': 'Checklist I run before every Node release',
                'paragraphs': [
                    'I keep this boring and repeatable. Boring is the point.',
                ],
                'bullets': [
                    'No .env with real secrets in the repo or Docker image',
                    'Required env validated at boot with clear errors',
                    'Log redaction helpers used; no raw process.env dumps',
                    'CI secrets masked; no set -x around secret expansion',
                    'Production secrets from a manager or platform injection',
                    'Rotation steps documented for DB, JWT, and payment keys',
                ],
            },
            {
                'h2': 'Twelve-factor habits that still apply',
                'paragraphs': [
                    'Config via environment remains right for 12-factor style apps. The update for 2026 is that production secrets increasingly come from a manager injected as env at process start, not from a long-lived file on disk. The process still sees process.env; the operators stop copying .env around Slack.',
                    'I keep a written inventory of every secret the app needs, who owns rotation, and the blast radius if it leaks. When the Stripe key leaked in logs, that inventory cut our response time: we knew exactly which services to restart and which dashboards to watch for fraud.',
                    'For monorepos, each package gets its own required env schema. Sharing one giant env object across web, worker, and CLI guarantees the CLI inherits production database credentials it never needed.',
                ],
            },
            {
                'h2': 'Runtime hardening around secrets in memory',
                'paragraphs': [
                    'You cannot fully erase secrets from a Node process, but you can reduce exposure. Avoid putting secrets on the prototype of widely logged objects. Prefer short-lived clients that close. Do not attach API keys to global.graphqlContext dumps used in error pages.',
                    'In workers, clear job payloads that included credentials after use when you control the queue schema. Bull and similar systems persist job data—never store raw secrets inside job JSON.',
                    'If a secret might have leaked, rotate first and investigate second. Argument about “maybe the log filter caught it” wastes the window attackers need.',
                ],
                'bullets': [
                    'Inventory secrets with owners and rotation owners',
                    'Per-package env schemas in monorepos',
                    'No secrets in job payloads or error page dumps',
                    'Rotate on suspicion, then do forensics',
                ],
            },
            {
                'h2': 'Example: stripping secrets from error reports',
                'paragraphs': [
                    'Error trackers love to serialize the world. I keep a denylist of env key substrings—SECRET, TOKEN, PASSWORD, KEY, PRIVATE—and scrub matching values before events leave the process. Framework defaults are not enough; custom context objects still leak.',
                    'The scrubber below matches key names, so KEY also catches SIGNING_KEY and accessKeyId. It does not inspect free-text values: a token pasted into an error message or log line needs a separate value check, such as a regex for your providers’ known key prefixes.',
                    'I also scrub Authorization headers and cookie values in HTTP error breadcrumbs. A single 500 on /checkout should not upload a session token to a SaaS you forgot was enabled in staging.',
                ],
                'code': "const SECRETISH = /(secret|token|password|passwd|key|private|authorization|cookie)/i;\n\nfunction scrub(value) {\n  if (value == null) return value;\n  if (Array.isArray(value)) return value.map(scrub);\n  if (typeof value === 'object') {\n    const out = {};\n    for (const [k, v] of Object.entries(value)) {\n      out[k] = SECRETISH.test(k) ? '[redacted]' : scrub(v);\n    }\n    return out;\n  }\n  return value;\n}\n\n// Sentry-style beforeSend\nfunction beforeSend(event) {\n  event.extra = scrub(event.extra);\n  event.contexts = scrub(event.contexts);\n  event.request = scrub(event.request); // headers: Authorization, Cookie\n  event.breadcrumbs = scrub(event.breadcrumbs);\n  return event;\n}",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Team process that keeps secrets boring',
                'paragraphs': [
                    'Onboarding docs should show how to get local secrets from 1Password or the company vault—not from a zip file in Drive. Shared .env files in chat are a process failure.',
                    'When someone leaves the team, rotate shared secrets they could access. Individual cloud IAM keys are easier to revoke than a single DATABASE_URL everyone copied.',
                    'I schedule a quarterly secret review: list env keys in production, confirm each is still needed, confirm rotation dates. Unused keys get deleted. Unused credentials still unlock systems.',
                ],
            },
        ],
        'takeaways': [
            'Env vars deliver secrets; they do not protect them from logs, children, or images.',
            'Commit .env.example only; keep real .env files out of git and Docker layers.',
            'Validate required env at boot in one module and fail fast on missing keys.',
            'Never log process.env; log a redacted summary of non-secret config.',
            'Inject secrets at runtime in production—prefer a secret manager over files on disk.',
            'Isolate credentials per service and practice rotation before you need it.',
        ],
    },
    {
        'slug': 'mongodb-aggregation-pipeline',
        'title': 'MongoDB Aggregation Pipelines I Actually Use in Production',
        'description': 'A practical walkthrough of MongoDB aggregation stages, indexing, and the patterns that replaced slow application-side joins in my Node services.',
        'category': 'Databases',
        'date': '2026-08-08',
        'updated': '2026-09-29',
        'read_min': 9,
        'keywords': 'MongoDB aggregation pipeline, $match $group $lookup, aggregation indexes, MongoDB performance, Node.js MongoDB',
        'excerpt': 'Aggregation pipelines stopped being “advanced Mongo” for me once report endpoints started timing out. This is the shape I use for filters, joins, and rollups without pulling half the collection into Node.',
        'sections': [
            {
                'h2': 'When find() is not enough',
                'paragraphs': [
                    'Early in a project I fetched all orders for a merchant, then reduced totals in JavaScript. It worked until the merchant hit 80k orders. Memory spiked, the event loop stalled, and the API returned 504s.',
                    'Aggregation moves that work next to the data. You filter early, project only needed fields, and let MongoDB stream results. The mental model is a Unix pipe: each stage transforms the stream for the next.',
                    'Aggregation is also how I implement rollups for invoices and tax reports where floating point in JS would scare accountants. Keep money in integer cents through the pipeline.',
                ],
            },
            {
                'h2': 'Pipeline shape that stays fast',
                'paragraphs': [
                    'My default order is: $match as early as possible, then $project or $addFields, then $group / $sort / $lookup, then final shaping. Putting $match first lets the planner use indexes. Putting $lookup last when possible avoids joining documents you will throw away.',
                    'I avoid $lookup inside hot request paths when a denormalized field would do. Lookups are powerful and expensive. For dashboards that run every minute, I often maintain a summary collection updated by the write path instead.',
                ],
                'bullets': [
                    '$match early — use indexed fields',
                    '$project for final output — the optimizer already drops fields later stages do not use',
                    '$sort after reducing cardinality when you can',
                    '$lookup only for fields you cannot afford to denormalize',
                    'Prefer $facet for multi-metric dashboards in one round trip',
                ],
            },
            {
                'h2': 'Example: merchant revenue by day',
                'paragraphs': [
                    'This is the report that replaced my Node reduce. Status and merchantId are indexed. I match first, then group by day in UTC, then sort.',
                ],
                'code': "const revenueByDay = await db.collection('orders').aggregate([\n  {\n    $match: {\n      merchantId: new ObjectId(merchantId),\n      status: { $in: ['paid', 'refunded'] },\n      createdAt: { $gte: start, $lt: end },\n    },\n  },\n  {\n    $project: {\n      day: {\n        $dateToString: { format: '%Y-%m-%d', date: '$createdAt', timezone: 'UTC' },\n      },\n      netCents: {\n        $cond: [\n          { $eq: ['$status', 'refunded'] },\n          { $multiply: ['$totalCents', -1] },\n          '$totalCents',\n        ],\n      },\n    },\n  },\n  {\n    $group: {\n      _id: '$day',\n      revenueCents: { $sum: '$netCents' },\n      orderCount: { $sum: 1 },\n    },\n  },\n  { $sort: { _id: 1 } },\n]).toArray();",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Joining with $lookup without melting the cluster',
                'paragraphs': [
                    'I use $lookup for admin views where freshness matters more than micro-latency. Always constrain the local side first. A $lookup after an unbounded collection scan is how you discover your working set size the hard way.',
                    'Prefer the pipeline form of $lookup when you need to filter the foreign collection. The simple localField/foreignField form is fine for one-to-one id joins.',
                ],
                'code': "const withCustomers = await db.collection('orders').aggregate([\n  { $match: { merchantId: oid, createdAt: { $gte: start } } },\n  { $limit: 100 },\n  {\n    $lookup: {\n      from: 'customers',\n      let: { cid: '$customerId' },\n      pipeline: [\n        { $match: { $expr: { $eq: ['$_id', '$$cid'] } } },\n        { $project: { name: 1, email: 1 } },\n      ],\n      as: 'customer',\n    },\n  },\n  { $unwind: { path: '$customer', preserveNullAndEmptyArrays: true } },\n]).toArray();",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Indexes and explain()',
                'paragraphs': [
                    "If the first $match cannot use an index, nothing downstream saves you. I run explain('executionStats') on new pipelines in staging with production-like data volume. Look for COLLSCAN on large collections and high nReturned versus totalDocsExamined ratios that look wrong.",
                    'Compound indexes should mirror the equality fields in $match, then range fields. For the revenue query above I use { merchantId: 1, status: 1, createdAt: 1 }.',
                    "Partial indexes that match the $match filter of a hot pipeline can shrink index size. Worth it when the collection is large and the query always includes status: 'paid'.",
                ],
            },
            {
                'h2': 'Mistakes that burned me',
                'paragraphs': [
                    'Allowing clients to pass arbitrary field names into $project or $match is an injection footgun. Build stages in code from allowlists. Never concatenate user strings into aggregation JSON.',
                    'Unbounded $group on high-cardinality keys blew memory on a shared Atlas tier. I now cap date ranges in the API and reject ranges larger than 90 days for heavy reports.',
                    'Forgetting allowDiskUse on rare huge sorts caused failures after we upgraded Mongo versions and defaults shifted. I set it explicitly on batch jobs, never on interactive requests if I can avoid spill.',
                ],
            },
            {
                'h2': 'Debugging and observability',
                'paragraphs': [
                    'I log pipeline name, merchant id, duration, and docs examined when available. Slow aggregation logs have caught missing indexes faster than any dashboard.',
                    'Keep pipelines in named functions, not inline in route handlers. That makes them testable with a fixture database and easier to review in PRs.',
                ],
            },
            {
                'h2': 'Facets for dashboard endpoints',
                'paragraphs': [
                    'Dashboards often need counts, totals, and a small recent list. Three round trips mean three chances to disagree under concurrent writes. $facet runs several independent sub-pipelines over the same filtered input within a single stage. The branches cannot use indexes themselves, and their combined output is one document, so it must stay under the 16MB BSON limit.',
                    'I still $match before $facet so each branch does not rescan the collection. Inside each branch I keep stages minimal. Facets that each $lookup the world will time out together and take the request with them.',
                ],
                'code': "const dashboard = await db.collection('orders').aggregate([\n  { $match: { merchantId: oid, createdAt: { $gte: start } } },\n  {\n    $facet: {\n      totals: [\n        { $group: { _id: null, revenue: { $sum: '$totalCents' }, n: { $sum: 1 } } },\n      ],\n      byStatus: [\n        { $group: { _id: '$status', n: { $sum: 1 } } },\n      ],\n      recent: [\n        { $sort: { createdAt: -1 } },\n        { $limit: 10 },\n        { $project: { totalCents: 1, status: 1, createdAt: 1 } },\n      ],\n    },\n  },\n]).next();",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Change streams are not aggregations—and that is fine',
                'paragraphs': [
                    'When people ask for “real-time aggregations,” they sometimes mean change streams updating a summary document. That is a different tool. I use aggregations for request/response reports and scheduled jobs. I use change streams or write-time increments when the UI needs live counters.',
                    'Mixing them poorly—running a full aggregation on every change—will melt Atlas. Update a summary collection incrementally on write, and use aggregation for historical ranges and audits.',
                ],
            },
            {
                'h2': 'Cursor batches and Node memory',
                'paragraphs': [
                    'toArray() on a huge aggregation result recreates the original problem—Node holds everything. For exports I stream the cursor and write CSV chunks. Set batchSize thoughtfully; default batches can still be large. Since MongoDB 6.0 the server allows disk use by default (allowDiskUseByDefault is true), so the explicit allowDiskUse: true below documents intent and overrides a cluster that turned the default off. Atlas Free and Flex clusters ignore allowDiskUse and never spill to disk.',
                    'For HTTP APIs I paginate with $skip/$limit only on small offsets, or better, range on _id or createdAt. Deep $skip on millions of documents is a known performance trap.',
                ],
                'code': "const cursor = db.collection('orders').aggregate(pipeline, { allowDiskUse: true, batchSize: 500 });\nfor await (const doc of cursor) {\n  await writeCsvRow(doc);\n}",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Testing aggregations without flaky clocks',
                'paragraphs': [
                    'I seed a fixture database with known ObjectIds and fixed createdAt values. Tests assert exact group keys and sums. Avoid Date.now() in fixtures unless you control the clock.',
                    'Snapshot-testing the pipeline array itself helps review in PRs: when someone reorders stages, the diff is obvious. Pair that with an integration test that runs against Mongo Memory Server or a disposable container.',
                    'Production incident tip: keep the last slow pipeline in logs as JSON. Being able to paste it into Compass or mongosh cuts mean time to understanding dramatically.',
                ],
                'bullets': [
                    'Stream cursors for large exports; avoid toArray()',
                    'Prefer range pagination over deep $skip',
                    'Fixture dates should be fixed and explicit',
                    'Log slow pipeline JSON for later replay',
                ],
            },
            {
                'h2': 'Putting it into the service layer',
                'paragraphs': [
                    'I wrap pipelines in repository functions with typed inputs: merchantId, start, end—not free-form stage arrays from the controller. Controllers should not invent aggregation stages from query strings.',
                    'Timeouts matter. Set maxTimeMS on heavy reports so a bad plan cannot hold a mongod thread forever. Return a clear 503 or 400 to the client when the range is too wide instead of letting the driver hang until the load balancer cuts the connection.',
                    'Finally, revisit denormalization quarterly. If you $lookup the same customer fields on every list view, copying a display name onto the order at write time may be cheaper. Aggregation is powerful; it is not an excuse to skip modeling.',
                    'That mix—indexed $match first, careful $group, rare $lookup, faceted dashboards, streamed exports—is the practical aggregation toolkit I actually keep reaching for.',
                ],
            },
        ],
        'takeaways': [
            'Use aggregation when you would otherwise pull large result sets into Node to reduce.',
            'Put selective $match first so indexes can cut the working set early.',
            'Use $project to shape final output; the optimizer already trims unused fields before $group.',
            'Verify new pipelines with explain() on realistic data volumes.',
            'Build stages from allowlists—never interpolate raw user input into pipelines.',
            'Cap date ranges and cardinality for interactive reports; use batch jobs for huge scans.',
        ],
    },
    {
        'slug': 'accessibility-wcag-checklist',
        'title': 'A WCAG Checklist Developers Can Finish Before Standup',
        'description': 'A practical WCAG-oriented checklist for frontend developers: keyboard, contrast, forms, names, and focus—without turning a11y into a separate project.',
        'category': 'Frontend',
        'date': '2026-08-12',
        'read_min': 8,
        'keywords': 'WCAG checklist, web accessibility, keyboard navigation, aria labels, color contrast, accessible forms',
        'excerpt': 'Accessibility work stuck on our backlog until I turned WCAG into a short, shippable checklist for every PR. Here is what I actually verify before calling a UI done.',
        'sections': [
            {
                'h2': 'Stop treating a11y as a phase',
                'paragraphs': [
                    'We once scheduled a two-week “accessibility sprint” after launch. Half the issues were buttons that were divs, forms without labels, and focus traps in modals. Fixing them late meant redesigning components customers already learned.',
                    'WCAG 2.2 AA is the bar most clients ask for. You do not need to memorize every success criterion. You need a repeatable check that catches the failures users hit every day: cannot tab, cannot read, cannot submit, cannot dismiss.',
                    'Legal risk is real in some markets, but I pitch a11y as product quality: more users can complete checkout. That framing gets budget.',
                ],
            },
            {
                'h2': 'Keyboard: if you cannot tab it, it is broken',
                'paragraphs': [
                    'I unplug the mouse and walk the happy path. Tab order should follow visual order. Interactive elements need a visible focus ring—do not remove outline without a replacement.',
                    'Custom controls must be reachable and operable with Enter/Space. Escape should close dialogs. Focus must move into a modal on open and return to the trigger on close. I have shipped a date picker that trapped focus forever; support tickets wrote themselves.',
                ],
                'bullets': [
                    'All actions reachable via keyboard',
                    'Visible :focus-visible styles on controls',
                    'Modals: focus trap, Escape, restore focus',
                    'No keyboard traps in carousels or menus',
                    'Skip link to main content on content-heavy pages',
                ],
            },
            {
                'h2': 'Names, roles, and the accessibility tree',
                'paragraphs': [
                    'Screen readers announce accessible names. An icon-only button with no aria-label is silence. Prefer visible text. When the design is icon-only, add aria-label that describes the action, not the icon shape.',
                    'Use native elements first: button, a, input, select. Role soup on divs is harder to get right. If you must build a custom widget, match the ARIA authoring practices for that pattern and test with VoiceOver or NVDA.',
                ],
                'code': '<!-- Bad -->\n<div class="icon-btn" onclick="deleteItem()">🗑</div>\n\n<!-- Better -->\n<button type="button" class="icon-btn" aria-label="Delete item" onclick="deleteItem()">\n  <span aria-hidden="true">🗑</span>\n</button>\n\n<!-- Links go places; buttons do things -->\n<a href="/settings">Settings</a>\n<button type="button" onclick="save()">Save</button>',
                'code_lang': 'html',
            },
            {
                'h2': 'Forms that fail for the right reasons',
                'paragraphs': [
                    'Every input needs a label associated with for/id or wrapping label. Placeholder is not a label. Error text must be tied to the field with aria-describedby and announced when validation runs.',
                    'Required fields need both visual indication and aria-required or the required attribute. Do not rely on color alone for errors.',
                    'Autocomplete attributes on auth and checkout fields help password managers and reduce errors. They are part of usable accessibility.',
                ],
                'code': '<label for="email">Email</label>\n<input\n  id="email"\n  name="email"\n  type="email"\n  autocomplete="email"\n  aria-invalid="true"\n  aria-describedby="email-error"\n  required\n/>\n<p id="email-error" class="error" role="alert">Enter a valid email address.</p>',
                'code_lang': 'html',
            },
            {
                'h2': 'Color, contrast, and motion',
                'paragraphs': [
                    'Body text should meet contrast ratios against its background. I use the browser DevTools contrast checker on real components, not just the design file, because CSS overlays change effective contrast.',
                    'Never convey state with color alone—add text or icons. Respect prefers-reduced-motion: disable non-essential animation when the user asks for it. Autoplaying video with sound is an automatic fail in my review.',
                ],
                'bullets': [
                    'Text contrast roughly 4.5:1 for normal text (AA)',
                    'UI component contrast for icons and borders where required',
                    'Status not by color alone',
                    'prefers-reduced-motion media query honored',
                    'Images have meaningful alt; decorative images alt=""',
                ],
            },
            {
                'h2': 'Images, media, and page structure',
                'paragraphs': [
                    'Alt text describes purpose. Decorative images get empty alt so readers skip them. Charts need a text summary or data table nearby—alt alone rarely carries a complex chart.',
                    'One h1 per page, heading levels in order. Landmarks (header, nav, main, footer) help skip navigation. I catch heading skips in PR review more often than exotic ARIA bugs.',
                ],
            },
            {
                'h2': 'My PR checklist (copy this)',
                'paragraphs': [
                    'I paste a short version into the PR template. If any box fails, the UI is not done.',
                ],
                'bullets': [
                    'Keyboard-only pass of the changed flow',
                    'Focus visible; modals manage focus',
                    'Buttons/links have accessible names',
                    'Form labels and error announcements present',
                    'Contrast checked on new text and controls',
                    'Automated axe or eslint-plugin-jsx-a11y clean on touched files',
                ],
            },
            {
                'h2': 'Automated tools and their blind spots',
                'paragraphs': [
                    'axe-core, Lighthouse, and eslint-plugin-jsx-a11y catch missing alt, contrast failures, and duplicate labels. They do not catch “the checkout flow makes no sense when tabbing” or “the toast disappears before a screen reader finishes.” Automation is a gate, not a certificate.',
                    'I run axe in CI on storybook or critical routes. Failures block merge. I still manually keyboard-test flows that change focus management. That split keeps noise low and coverage real.',
                    'When design hands over a component, I ask for focus states and error text in the spec. Retrofitting focus rings after visual QA freezes the design is how a11y work gets cut.',
                ],
            },
            {
                'h2': 'Dynamic content and live regions',
                'paragraphs': [
                    'SPAs update the page without full reloads. Screen reader users need announcements for important changes. aria-live regions for form success, cart updates, and filter result counts prevent silent UI changes.',
                    'Do not mark the entire page as live. That creates announcement storms. Prefer polite live regions for status and assertive only for critical errors. Clear the message node carefully so repeated identical messages still fire when needed.',
                ],
                'code': '<div aria-live="polite" aria-atomic="true" class="sr-only" id="status"></div>\n<script>\nfunction announce(msg) {\n  const el = document.getElementById(\'status\');\n  el.textContent = \'\';\n  requestAnimationFrame(() => { el.textContent = msg; });\n}\nannounce(\'3 products matched your filters\');\n</script>',
                'code_lang': 'html',
            },
            {
                'h2': 'Mobile touch targets and zoom',
                'paragraphs': [
                    'WCAG 2.2 pays more attention to target size. Tiny icon hit areas frustrate motor impairments and everyone on a bumpy train. I aim for about 24×24 CSS pixels minimum, larger when the UI allows.',
                    'Do not disable pinch zoom with maximum-scale=1. Users with low vision rely on zoom. If your layout breaks when zoomed, fix the layout.',
                    'Touch and keyboard both matter on hybrid devices. A control that works with a mouse hover menu but not with tap or keyboard is incomplete.',
                ],
            },
            {
                'h2': 'Content language and readable text',
                'paragraphs': [
                    'Set lang on the html element. Mark language changes inline when quoting another language so screen readers switch voices correctly.',
                    'Line length and spacing affect cognitive load. Extremely long lines of body text are harder for many readers. I keep article measure around 60–75 characters where the design allows.',
                    'Avoid justified text with awkward gaps on the web. Left-aligned body text remains the safest default for mixed languages and zoom levels.',
                ],
            },
            {
                'h2': 'Shipping culture beats heroics',
                'paragraphs': [
                    'The checklist only works if someone owns it. On my teams that is every frontend engineer for their PR, plus a periodic audit of top funnels with a screen reader.',
                    'Designers and engineers should share the same definition of done: keyboard works, name is announced, errors are clear, contrast passes. When that definition is in the ticket template, debates shrink.',
                    'You will not hit perfection on day one. You will stop shipping the same five bugs repeatedly. That is the win. Start with the checklist above on the next UI PR and expand coverage as the component library matures.',
                    'Accessibility is quality engineering with a human face. Treat it like performance budgets: measurable, enforceable, and part of normal delivery—not a special occasion.',
                ],
            },
        ],
        'takeaways': [
            'Bake keyboard, names, forms, and contrast into every UI PR—not a late sprint.',
            'Prefer native HTML controls; add ARIA only when you must extend behavior.',
            'Icon-only controls need aria-label; placeholders are not labels.',
            'Tie error messages to inputs with aria-describedby and announce them.',
            'Check contrast in the rendered page and honor prefers-reduced-motion.',
            'Use a short PR checklist plus an automated scanner for regressions.',
        ],
    },
    {
        'slug': 'debug-nodejs-memory-leaks',
        'title': 'Debugging Node.js Memory Leaks with Heap Snapshots',
        'description': 'How I confirm a Node memory leak, take heap snapshots, compare retainers, and fix the usual suspects: caches, listeners, and closed-over requests.',
        'category': 'Backend',
        'date': '2026-08-16',
        'updated': '2026-09-29',
        'read_min': 9,
        'keywords': 'Node.js memory leak, heap snapshot, Chrome DevTools, process.memoryUsage, EventEmitter leak, clinic heapprofiler',
        'excerpt': 'When a Node service climbs from 200MB to 2GB over a day, guessing wastes time. Here is the heap-snapshot workflow I use to find what is retaining memory.',
        'sections': [
            {
                'h2': 'Symptoms that are not always leaks',
                'paragraphs': [
                    'RSS climbing under load can be V8 holding onto heap after a burst, buffers in the kernel, or a real leak. I do not declare a leak until memory keeps rising across idle periods or after forced GC, and request rates are steady.',
                    'First metrics: process.memoryUsage(), container memory limit events, and GC pause time if you expose it. If heapUsed sawtooths but returns to a baseline after idle, you may just need a larger heap or better caching policy—not a hunt for retainers.',
                ],
                'code': 'setInterval(() => {\n  const m = process.memoryUsage();\n  console.log(JSON.stringify({\n    ts: new Date().toISOString(),\n    rss: m.rss,\n    heapTotal: m.heapTotal,\n    heapUsed: m.heapUsed,\n    external: m.external,\n  }));\n}, 30000);',
                'code_lang': 'javascript',
            },
            {
                'h2': 'Reproduce before you snapshot',
                'paragraphs': [
                    'I build a script that hits the suspected route in a loop with realistic payloads. Without a repro, snapshots show noise. With a repro, the retained size delta between snapshot A and B screams.',
                    'Run against a staging instance with production-like data volume. Tiny fixtures hide leaks in caches keyed by customer id.',
                    'Keep the repro script in the repo under scripts/leak-repro.js so the next engineer does not reinvent load generation.',
                ],
            },
            {
                'h2': 'Taking heap snapshots',
                'paragraphs': [
                    'For local debugging I start Node with --inspect and use Chrome DevTools Memory tab. Take a snapshot at idle baseline, run the load script, force a minor wait, take another snapshot, then compare.',
                    'In production-like containers I use Node’s built-in v8.writeHeapSnapshot() (available since Node 11.13; the old heapdump npm module is unmaintained) or the inspector protocol behind an authenticated admin endpoint that only ops can hit. Never expose unauthenticated snapshot endpoints. Without any endpoint, start Node with --heapsnapshot-signal=SIGUSR2 and send that signal to write a snapshot, or use --heapsnapshot-near-heap-limit=1 to capture one automatically as the heap approaches its limit.',
                ],
                'code': "# Local\nnode --inspect=0.0.0.0:9229 server.js\n\n# Or write a snapshot on demand (protect this route)\nimport v8 from 'node:v8';\nimport fs from 'node:fs';\n\napp.post('/admin/heapdump', requireAdmin, (req, res) => {\n  const file = `/tmp/heap-${Date.now()}.heapsnapshot`;\n  const snapshotStream = v8.writeHeapSnapshot(file);\n  res.json({ file: snapshotStream });\n});",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Reading the comparison',
                'paragraphs': [
                    'In DevTools, compare snapshots and sort by retained size delta. Look for arrays, maps, and detached DOM-like structures—though on the server it is usually Maps, arrays of request context, or sockets.',
                    'Click through retainer chains. Ask: who still points at this object? Common answers: a module-level Map, an EventEmitter listener list, a global cache without TTL, or a closure holding the entire Express req.',
                ],
            },
            {
                'h2': 'Leaks I keep finding',
                'paragraphs': [
                    'Unbounded caches: const cache = new Map() keyed by userId with no eviction. Fix with LRU and a max size, or Redis with TTL.',
                    'EventEmitter listener leaks: subscribe per request to a shared bus and forget to unsubscribe. MaxListeners warnings are a gift—do not raise the limit to silence them without fixing the cause.',
                    'Timers and intervals created per connection that never clear. WebSocket servers are frequent offenders.',
                    'Third-party SDKs sometimes register global handlers. If retained size points into node_modules, upgrade or isolate the SDK in a worker process.',
                ],
                'code': "// Leaky pattern\nconst sessions = new Map();\napp.post('/login', (req, res) => {\n  sessions.set(req.body.userId, { req, huge: req.body }); // retains request forever\n});\n\n// Better: store ids and minimal state, bound the map\nimport { LRUCache } from 'lru-cache';\nconst sessions = new LRUCache({ max: 5000, ttl: 1000 * 60 * 30 });\napp.post('/login', (req, res) => {\n  sessions.set(req.body.userId, { userId: req.body.userId, role: 'user' });\n});",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Native memory and external buffers',
                'paragraphs': [
                    'Sometimes heapUsed looks stable while RSS climbs. That can be Buffer allocations, native addons, or compression libraries. Check process.memoryUsage().external and tool-specific metrics.',
                    'Streaming large uploads into memory is a classic. Prefer streaming to disk or object storage. I once “temporarily” collected upload chunks in an array for “just image uploads” and then a client sent 400MB videos.',
                ],
            },
            {
                'h2': 'Fix, verify, prevent',
                'paragraphs': [
                    'After a fix, re-run the same load script and confirm the second snapshot no longer grows the hot objects. Add a memory ceiling alert in staging that fails the deploy if heapUsed trends up across a soak test.',
                    'Code review flags: module-level collections, addListener without removeListener, setInterval without clear, and caching user content without bounds.',
                ],
            },
            {
                'h2': 'Clinic, 0x, and when DevTools is enough',
                'paragraphs': [
                    'Chrome DevTools snapshots handle most app-level leaks. For CPU paired with memory weirdness I reach for clinic heapprofiler or doctor. They add overhead—use them in staging soak tests, not on every production pod.',
                    'If the leak only appears after hours, schedule snapshot capture at +10m, +60m, +180m under synthetic load. Comparing three points shows growth rate and whether a particular constructor keeps climbing.',
                    'Document the finding in the ticket with before/after retained sizes. Future you will thank present you when the same Map pattern returns in another service.',
                ],
            },
            {
                'h2': 'Promises, closures, and the quiet retainers',
                'paragraphs': [
                    'Long-lived promises that close over request-scoped objects keep those objects alive until the promise settles. A dangling retry loop holding the original req body is a leak shaped like “we are being careful about retries.”',
                    'Async queues that buffer failed jobs in memory without a max length will grow forever during a downstream outage. Bound the queue. Shed load. Prefer durable queues for work that must survive process restart anyway.',
                ],
                'bullets': [
                    'Bound in-memory retry buffers',
                    'Avoid closing over full req/res in timers',
                    'Snapshot on a schedule during soak tests',
                    'Record retained-size deltas in the fix PR',
                ],
            },
            {
                'h2': 'A walkthrough of one real leak',
                'paragraphs': [
                    'We had a notification service whose heap grew ~15MB per hour under steady load. Snapshots showed thousands of Discord webhook payload strings retained by an array on a module-level Metrics object that pushed every outbound body “for debugging.”',
                    'The fix was three lines: stop retaining bodies, keep only counters, and sample errors to the logger. Heap stabilized within minutes of deploy. The expensive part was not the fix—it was proving the retainer with two snapshots so nobody argued about “maybe Redis.”',
                    'Takeaway I repeat in postmortems: if you add a debug collector, give it a max length on day one. Debug code becomes production code the moment it ships.',
                ],
            },
            {
                'h2': 'Production safety while debugging',
                'paragraphs': [
                    'Heap snapshots are large and CPU-heavy. Taking them on every pod during peak traffic can cause the outage you are investigating. Prefer a single canary instance, off-peak windows, or staging soak with production traffic replay.',
                    'Strip secrets from snapshots before sharing with vendors or pasting into tickets. Snapshots can contain strings from requests, including tokens.',
                    'After remediation, leave the metrics and alerts in place. Leaks return in new features that copy old patterns.',
                ],
                'bullets': [
                    'Snapshot canaries, not the whole fleet at once',
                    'Treat heapsnapshot files as sensitive',
                    'Keep memory trend alerts after the fix',
                    'Cap every new in-process collector',
                ],
            },
            {
                'h2': 'Habits that prevent the next leak',
                'paragraphs': [
                    'Code review questions I ask: Does this Map or array live at module scope? What is its maximum size? Who clears this interval? Does this listener die with the socket?',
                    'Load tests should include a memory assertion: after N minutes of steady traffic and a short idle, heapUsed must not exceed baseline by more than a set percentage. CI will not catch every leak, but it catches the loud ones before customers do.',
                    'When you vendor a new SDK, read its README for global state and debugging flags. Many “enable verbose logging” options retain payloads. Keep them off in production.',
                    'Heap snapshots look intimidating once. After two investigations they become a normal tool—like reading a stack trace. Invest in that skill; it pays back the first time RSS graphs only go up and to the right.',
                ],
            },
        ],
        'takeaways': [
            'Confirm a leak with steady load plus rising heap across idle/GC—not a single RSS spike.',
            'Reproduce with a script before taking snapshots so comparisons are meaningful.',
            'Compare two heap snapshots and follow retainer chains to the owning cache or listener.',
            'Bound in-process caches; prefer TTL/LRU over unbounded Maps.',
            'Unsubscribe listeners and clear timers per connection lifecycle.',
            'Guard heapdump endpoints and add soak-test memory alerts to catch regressions.',
        ],
    },
    {
        'slug': 'vite-vs-webpack',
        'title': 'Vite vs Webpack in 2026: When I Pick Which',
        'description': 'A practitioner comparison of Vite and Webpack for real apps—dev server speed, legacy constraints, microfrontends, and migration costs.',
        'category': 'Developer Tools',
        'date': '2026-08-19',
        'updated': '2026-09-29',
        'read_min': 8,
        'keywords': 'Vite vs Webpack, Vite 2026, Webpack 5, frontend bundler, Vite 8 Rolldown, Oxc, module federation',
        'excerpt': 'I still maintain Webpack apps and start most greenfield UI in Vite. Here is how I choose in 2026 without rewriting working build pipelines for sport.',
        'sections': [
            {
                'h2': 'The question is not which is “better”',
                'paragraphs': [
                    'Webpack shaped a decade of frontend tooling. Vite changed the default expectation for cold start and HMR. In 2026 both ship production apps successfully. The decision is about constraints: team knowledge, plugin ecosystem needs, and how painful a migration would be.',
                    'I measure three things: time to first meaningful edit on a laptop, production bundle correctness for our targets, and the cost of the weird requirement—legacy browsers, Module Federation, or a custom loader nobody else has.',
                    'I also ask: will juniors on the team debug this build file? Opaque config is an operational liability.',
                ],
            },
            {
                'h2': 'Where Vite wins for me',
                'paragraphs': [
                    'Greenfield React, Vue, and Svelte apps start in Vite unless a hard requirement says otherwise. Native ESM in dev plus fast Oxc transforms (esbuild before Vite 8) make cold starts feel instant compared to older Webpack setups we still have.',
                    'Config stays smaller for common cases. Official templates are good. SSR and library modes are first-class enough for most product work I do.',
                    'Since Vite 8 (March 2026), production builds and dependency pre-bundling use Rolldown, a Rust bundler with a Rollup-compatible plugin API, instead of Rollup and esbuild. Tree-shaking is strong. For typical SPAs targeting modern browsers, I have not missed Webpack.',
                ],
                'bullets': [
                    'New SPAs and component libraries',
                    'Teams that value fast HMR over custom loader archaeology',
                    'Modern browser baselines (no IE, limited legacy)',
                    'Simple multi-page setups Vite supports cleanly',
                ],
            },
            {
                'h2': 'Where Webpack still earns its keep',
                'paragraphs': [
                    'Module Federation at scale is still a Webpack stronghold in several enterprises I work with. If your org standardized on Federation for microfrontends and the graph is already wired, ripping it out for Vite’s federation options is a program, not a weekend.',
                    'Exotic loaders, decades-old CSS pipelines, and “this one plugin only exists for Webpack” situations are real. I have seen migrations stall for months because of a single internal loader that rewrote i18n catalogs.',
                    'Some large codebases already invested in Webpack persistent caching and carefully tuned splitChunks. The build is slow but known. Vite may be faster—and still lose on total cost of change.',
                ],
            },
            {
                'h2': 'Dev experience numbers from one migration',
                'paragraphs': [
                    'On a mid-size React app (~1.2k modules), Webpack 5 cold start averaged about 28 seconds on my M-series laptop. Vite cold start was under 2 seconds. HMR for a leaf component went from ~3–5 seconds of “wait, did it refresh?” to near-immediate.',
                    'Production build times were closer: Vite/Rollup around 40 seconds, Webpack with filesystem cache warm around 35–50 depending on cache hits. The daily win was developer loop, not CI by itself.',
                    'CI caching for Vite is straightforward with dependency hashes. Webpack filesystem cache also works—measure both before declaring a winner for pipelines.',
                ],
            },
            {
                'h2': 'Migration path that did not blow up',
                'paragraphs': [
                    'I do not big-bang rewrite webpack.config.js on Friday. I move one package in a monorepo first—usually the design system or a leaf app—and keep Webpack for the host until federation or shared deps are sorted.',
                    'Watch for differences in env handling (import.meta.env vs DefinePlugin), asset URL behavior, and how CSS modules hash class names. Visual diffs caught a missing global stylesheet import we had accidentally relied on Webpack’s context for.',
                ],
                'code': "// vite.config.js — typical SPA\nimport { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\n\nexport default defineConfig({\n  plugins: [react()],\n  server: { port: 5173, proxy: { '/api': 'http://localhost:3000' } },\n  build: {\n    sourcemap: true,\n    // Vite 8: rollupOptions is now rolldownOptions, and the object form of\n    // manualChunks is gone; use Rolldown's codeSplitting groups instead.\n    rolldownOptions: {\n      output: {\n        codeSplitting: {\n          groups: [\n            { name: 'vendor', test: /node_modules[\\\\/]react(-dom)?[\\\\/]/ },\n          ],\n        },\n      },\n    },\n  },\n});",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Decision heuristic I use in 2026',
                'paragraphs': [
                    'New app, modern browsers, no Federation mandate: Vite. Existing Webpack app with no pain: leave it, maybe upgrade Webpack and cache settings. Painful Webpack only in local dev: evaluate Vite for that package. Hard Federation or unique loaders: stay on Webpack until there is a funded migration.',
                    'Also check your framework’s recommendation. Next.js ships its own bundler (Turbopack) and Nuxt builds on Vite by default; forcing a different bundler underneath the framework is usually the wrong fight.',
                ],
                'bullets': [
                    'Optimize for daily edit-refresh loop first',
                    'Treat production parity and plugin gaps as blockers',
                    'Migrate leaf packages before hosts',
                    'Budget time for env and asset path differences',
                    'Do not migrate solely because of blog hype',
                ],
            },
            {
                'h2': 'Plugin ecosystems and the long tail',
                'paragraphs': [
                    'Vite’s plugin API is Rollup-compatible (Rolldown keeps that API since Vite 8) and has a separate story for dev middleware. Most popular tools have Vite plugins in 2026. The long tail still bites: an internal Markdown transform written against Webpack’s loader API may need a rewrite.',
                    'Estimate that rewrite in hours before promising “we’ll just switch.” I once quoted two days and spent two weeks on a SVG pipeline that depended on Webpack’s resourceQuery quirks.',
                    'Conversely, staying on Webpack forever because of one obscure plugin can cost more in engineer frustration than rewriting the plugin. Put a calendar reminder on “revisit migration” every two quarters if DX pain is high.',
                ],
            },
            {
                'h2': 'TypeScript, CSS, and monorepos',
                'paragraphs': [
                    'Both tools handle TypeScript. Vite leans on Oxc (esbuild before Vite 8) for transpile speed and leaves typechecking to vue-tsc/tsc in CI—which is the right split. Do not expect the bundler to be your typechecker.',
                    'In monorepos, Vite’s dependency prebundling needs careful optimizeDeps includes for linked workspace packages. Webpack’s module resolution pain is older and better documented in tribal knowledge—neither is free.',
                    'Pick one story for CSS: CSS modules, vanilla-extract, Tailwind. Fighting the bundler and the CSS approach at the same time makes migrations unreadable in review.',
                ],
            },
            {
                'h2': 'Library mode and publishing packages',
                'paragraphs': [
                    'When I publish a UI kit, Vite library mode with multiple formats (ES and CJS when required) is usually enough. Preserve modules when consumers need treeshaking across deep imports.',
                    'Webpack is still used in some design-system pipelines that emit many asset flavors. If your package build is already green and automated, migration is optional.',
                    'Externalize peer dependencies—react, react-dom—so you do not bundle a second copy into every consumer. Both tools support externals; forgetting them causes “Invalid hook call” tickets.',
                ],
                'code': "export default defineConfig({\n  build: {\n    lib: {\n      entry: 'src/index.ts',\n      name: 'UiKit',\n      formats: ['es'],\n      fileName: 'ui-kit',\n    },\n    rolldownOptions: {\n      external: ['react', 'react-dom'],\n    },\n  },\n});",
                'code_lang': 'javascript',
            },
            {
                'h2': 'What I tell stakeholders',
                'paragraphs': [
                    'Leadership hears “Webpack is old” and “Vite is fast.” I translate to risk language: estimated eng-days, regression risk on checkout, and expected weekly hours saved in local builds. Without those numbers the loudest blog post wins.',
                    'If the team is drowning in 40-second HMR, Vite (or a framework upgrade that includes a faster bundler) is an easy yes. If production builds are fine and Federation is critical, keep Webpack and invest in cache and developer machines instead.',
                ],
            },
            {
                'h2': 'My default recommendation this year',
                'paragraphs': [
                    'Start new product UIs on Vite or on a framework that already chose a fast bundler for you. Keep healthy Webpack apps healthy. Migrate when local DX pain is measurable and Federation or custom loaders are not blockers.',
                    'Re-evaluate yearly. The gap between tools narrows and widens as releases ship. The constant is your constraints: team skill, plugin needs, and customer-facing risk.',
                    'Ignore internet arguments that declare one tool dead. Ship software. Measure cold start. Measure production. Choose the boring option that makes Monday morning editing pleasant.',
                ],
            },
        ],
        'takeaways': [
            'Choose Vite for most new modern SPAs; keep Webpack when Federation or unique loaders dominate.',
            'Judge tools by cold start, HMR, production correctness, and migration cost—not brand.',
            'Expect larger wins in local DX than in already-cached CI production builds.',
            'Migrate incrementally: leaf apps first, host bundles later.',
            'Watch import.meta.env, CSS, and asset URL differences during cutover.',
            'Follow your meta-framework’s default bundler unless you have a strong reason not to.',
        ],
    },
    {
        'slug': 'kubernetes-secrets-management',
        'title': 'Kubernetes Secrets Management Basics Without Shooting Yourself in the Foot',
        'description': 'How to handle Kubernetes Secrets safely: encoding myths, RBAC, external secret stores, rotation, and the mounting patterns I use in real clusters.',
        'category': 'DevOps',
        'date': '2026-08-23',
        'read_min': 8,
        'keywords': 'Kubernetes Secrets, Sealed Secrets, External Secrets Operator, RBAC secrets, kubectl create secret, secret rotation',
        'excerpt': 'Kubernetes Secrets are base64, not encryption. Here is how I store, mount, and rotate credentials in clusters without leaving plaintext in git or world-readable env dumps.',
        'sections': [
            {
                'h2': 'Secret is a type, not a guarantee',
                'paragraphs': [
                    'The first time someone told me “it’s fine, it’s in a Secret,” I decoded the base64 in etcd-backed storage and read the database password in cleartext. Base64 is encoding. Anyone with permission to read the Secret object can read the value.',
                    'Default cluster encryption of Secret data at rest is not always on. Verify encryptionConfiguration on the API server. Until then, treat etcd access and API read access as equivalent to holding the credential.',
                    'Compliance questionnaires often ask how secrets are stored at rest. “We use Kubernetes Secrets” is an incomplete answer without encryption and access control details.',
                ],
            },
            {
                'h2': 'Never commit raw Secret manifests',
                'paragraphs': [
                    'I do not put plaintext Secret YAML in git. Not even in private repos. Git history keeps them forever. Use a sealed mechanism or generate Secrets in the cluster from an external store at sync time.',
                    'For demos, kubectl create secret generic is fine. For GitOps, I use Sealed Secrets or External Secrets Operator pulling from AWS Secrets Manager, GCP Secret Manager, or Vault.',
                ],
                'code': '# Create from literals (interactive / CI), not from committed YAML values\nkubectl -n payments create secret generic db-credentials \\\n  --from-literal=username=app \\\n  --from-literal=password="$(openssl rand -base64 24)" \\\n  --dry-run=client -o yaml | kubectl apply -f -\n\n# Prefer files mounted as volumes over env for less accidental leakage\nkubectl -n payments create secret generic db-credentials \\\n  --from-file=username=./username.txt \\\n  --from-file=password=./password.txt',
                'code_lang': 'bash',
            },
            {
                'h2': 'RBAC: who can get secrets',
                'paragraphs': [
                    'Limit get/list/watch on secrets to the controllers and humans who need them. Developers who only need to restart pods do not need secret read. I have audited clusters where every engineer in a group could kubectl get secret -o yaml across namespaces.',
                    'Service accounts should mount only the secrets their workload needs. Do not share one mega-secret across twelve deployments “for convenience.”',
                ],
                'bullets': [
                    'Separate namespaces for trust boundaries when possible',
                    'Avoid cluster-admin for day-to-day humans',
                    'Prefer Role over ClusterRole for secret access',
                    'Audit kubectl auth can-i get secrets -n … for each team role',
                ],
            },
            {
                'h2': 'Mounting: files vs environment variables',
                'paragraphs': [
                    'Env vars are easy to dump and inherit. I prefer volume mounts at /var/run/secrets/app/… and have the app read files. Many frameworks support both.',
                    'If you must use env, inject specific keys, not every key in a blob. Restart pods on rotation—Kubernetes will not always hot-reload env from an updated Secret depending on how you consume it. File mounts from Secret volumes update asynchronously; apps may need to watch or restart.',
                ],
                'code': 'apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api\nspec:\n  template:\n    spec:\n      containers:\n        - name: api\n          image: ghcr.io/example/api:1.4.2\n          volumeMounts:\n            - name: db\n              mountPath: /var/run/secrets/db\n              readOnly: true\n          env:\n            - name: DB_PASSWORD_FILE\n              value: /var/run/secrets/db/password\n      volumes:\n        - name: db\n          secret:\n            secretName: db-credentials\n            items:\n              - key: password\n                path: password',
                'code_lang': 'yaml',
            },
            {
                'h2': 'External stores and rotation',
                'paragraphs': [
                    'External Secrets Operator keeps the cluster Secret in sync with a cloud manager. Rotation happens in one place. I set refresh intervals consciously—too aggressive thrashes; too slow leaves revoked credentials active.',
                    'Application support for dual credentials matters. Database users that allow two passwords during rotation avoid downtime. JWT signing with kid headers lets you roll keys without killing sessions instantly.',
                    'Annotate Secrets with owning team and rotation date. Stale credentials with no owner are incident fuel.',
                ],
            },
            {
                'h2': 'Common failure modes',
                'paragraphs': [
                    'Logging the environment at boot. Debug containers with mounted secrets left running. CI jobs that print helm template output including secret values. Backups of etcd without encryption resting in object storage.',
                    'Also: copying prod secrets into the dev cluster “to reproduce a bug.” Use scrubbed fixtures. Prod credentials in shared dev clusters are how leaks widen.',
                ],
            },
            {
                'h2': 'Minimum bar I accept for a cluster',
                'paragraphs': [
                    'Encryption at rest enabled for Secrets, tight RBAC, no plaintext Secrets in git, mounts scoped per workload, and a documented rotation path. That bar is boring and it prevents most of the incidents I get called into.',
                ],
            },
            {
                'h2': 'Sealed Secrets vs External Secrets vs CSI drivers',
                'paragraphs': [
                    'Sealed Secrets encrypt for a specific cluster controller key so ciphertext can live in git. Simple and good for small teams. Key backup and disaster recovery matter—lose the sealing key and you cannot decrypt.',
                    'External Secrets Operator syncs from a cloud manager. Better when security already standardized on Vault or AWS Secrets Manager. CSI secret store drivers mount secrets without always creating a Kubernetes Secret object—useful for stronger isolation, with its own operational learning curve.',
                    'I pick Sealed Secrets for small clusters without a central vault. I pick External Secrets when the company already has a secret manager and rotation policies. I avoid inventing a fourth custom operator.',
                ],
                'bullets': [
                    'Sealed Secrets: git-friendly ciphertext, cluster-bound keys',
                    'External Secrets: central source of truth and rotation',
                    'CSI drivers: mount without durable Secret objects when required',
                    'Standardize on one pattern per environment tier',
                ],
            },
            {
                'h2': 'Incident response when a Secret escapes',
                'paragraphs': [
                    'Assume the value is compromised once it appears in a ticket, screenshot, or CI log. Rotate in the upstream system, update the Kubernetes Secret or external store, roll pods, then invalidate old credentials on the provider side.',
                    'Search cluster events, git history, and log systems for the secret prefix patterns. Add detection rules for high-entropy strings in application logs if you do not already have them.',
                    'Afterward, fix the path that leaked—boot logging, overly broad RBAC, or a debug container. Rotation without fixing the path is a countdown to the next page.',
                ],
            },
            {
                'h2': 'GitOps workflow that stays honest',
                'paragraphs': [
                    'Desired state in git should reference secret names and external secret mappings, not values. Pull request reviewers should never need to see live credentials to approve a deploy.',
                    'Policy-as-code can deny Kubernetes Secret manifests that contain data: keys in application repos. That guardrail stops the “quick fix” PR that pastes a password into YAML.',
                    'Break-glass procedures matter. When the secret manager is down, how do you ship a hotfix? Document a manual path that still audits who accessed what—and retire temporary credentials afterward.',
                ],
            },
            {
                'h2': 'Namespaces, multi-tenancy, and soft walls',
                'paragraphs': [
                    'Namespaces are not strong security boundaries by themselves, but they help organize RBAC. Tenant A’s secrets should not be readable by tenant B’s deploy role.',
                    'On multi-tenant clusters, prefer separate namespaces per team or environment and NetworkPolicies that match. Secrets sitting in default are a smell.',
                    'Controllers that sync secrets cluster-wide need careful review. A misconfigured ExternalSecret with the wrong namespace selector is a cross-tenant leak waiting to happen.',
                ],
                'bullets': [
                    'Reference secret names in git, not values',
                    'Policy-deny plaintext Secret data in app repos',
                    'Document break-glass and audit it',
                    'Review cluster-wide secret sync carefully',
                ],
            },
            {
                'h2': 'A short implementation order',
                'paragraphs': [
                    'If your cluster is early: enable encryption at rest, lock down RBAC for secrets, stop committing plaintext, mount files for the first apps, and pick Sealed Secrets or External Secrets before the third service copies a password into YAML.',
                    'If your cluster is mature but messy: inventory who can get secrets, rotate anything that ever lived in git, and migrate the highest-risk credentials to an external manager first—databases, identity providers, payment keys.',
                    'Teach the team the base64 myth once. It sticks better than any policy PDF. Then enforce the policy with admission controls so the myth does not have to be relearned in an incident channel.',
                ],
            },
        ],
        'takeaways': [
            'Kubernetes Secrets are base64-encoded objects—protect them with RBAC and etcd encryption at rest.',
            'Never commit plaintext Secret manifests; use sealing or an external secret store with GitOps.',
            'Grant secret read access narrowly to humans and service accounts.',
            'Prefer file mounts over environment variables when practical.',
            'Plan credential rotation with dual-key or dual-password windows.',
            'Keep prod secrets out of shared dev clusters and CI logs.',
        ],
    },
    {
        'slug': 'deploy-static-site-guide',
        'title': 'Deploy a Static Site: Netlify, GitHub Pages, and Nginx Step by Step',
        'description': 'A practical guide to shipping a static HTML/CSS/JS site to Netlify, GitHub Pages, and a VPS with Nginx—including caching, HTTPS, and the mistakes that break deploys.',
        'category': 'DevOps',
        'date': '2026-08-27',
        'updated': '2026-09-29',
        'read_min': 8,
        'keywords': "deploy static site, Netlify deploy, GitHub Pages, Nginx static files, HTTPS Let's Encrypt, cache-control headers",
        'excerpt': 'BudhiWorks itself is a static site. Here is how I deploy the same kind of project to Netlify, GitHub Pages, or a plain Nginx box—without mystery 404s and stale caches.',
        'sections': [
            {
                'h2': 'What “static” buys you',
                'paragraphs': [
                    'A static site is HTML, CSS, JS, and assets on a CDN or web server. No app server process to babysit. Deploys are file syncs. That simplicity is why blogs, docs, and marketing sites should stay static until they truly need a backend.',
                    'Your job is correct URLs, HTTPS, cache headers, and a pipeline that publishes only the intended directory. Most outages I see are wrong publish directories, missing redirects for SPA routes, or CDN caches that never expire after a bad release.',
                    'Static does not mean “no pipeline.” Even hand-written HTML benefits from link checkers and HTML validators in CI before publish.',
                ],
            },
            {
                'h2': 'Option A: Netlify',
                'paragraphs': [
                    'Connect the Git repo, set the publish directory (for this project that might be the repo root or a dist/ folder), and leave the build command empty if there is no build step. For a generator, set build and publish accordingly.',
                    'Add a netlify.toml so settings live in git. Force HTTPS. Use _redirects or the toml redirects table for clean URLs. Preview deploys on pull requests catch broken links before production.',
                ],
                'code': '# netlify.toml\n[build]\n  publish = "."\n  # command = "npm run build"  # if you have a build\n\n[[headers]]\n  for = "/*"\n  [headers.values]\n    X-Frame-Options = "DENY"\n    X-Content-Type-Options = "nosniff"\n\n[[headers]]\n  for = "/assets/*"\n  [headers.values]\n    # Only safe if files under /assets have content-hashed names\n    Cache-Control = "public, max-age=31536000, immutable"\n\n[[headers]]\n  for = "/*.html"\n  [headers.values]\n    Cache-Control = "public, max-age=0, must-revalidate"',
                'code_lang': 'toml',
            },
            {
                'h2': 'Option B: GitHub Pages',
                'paragraphs': [
                    'Pages can publish from a branch (often gh-pages) or from GitHub Actions. I prefer Actions: build on main, upload artifacts, deploy with the official Pages action. That keeps source and published artifacts separate.',
                    'Project sites live at username.github.io/repo/. Asset paths must respect that base. Absolute paths starting at / break on project pages. Relative paths or a configured base URL fix it.',
                ],
                'code': '# .github/workflows/pages.yml\nname: Deploy Pages\non:\n  push:\n    branches: [main]\npermissions:\n  contents: read\n  pages: write\n  id-token: write\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n    environment:\n      name: github-pages\n      url: ${{ steps.deployment.outputs.page_url }}\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/configure-pages@v4\n      - uses: actions/upload-pages-artifact@v3\n        with:\n          path: .\n      - id: deployment\n        uses: actions/deploy-pages@v4',
                'code_lang': 'yaml',
            },
            {
                'h2': 'Option C: Nginx on a VPS',
                'paragraphs': [
                    'For full control I rsync the site to /var/www/site and point Nginx at it. Certbot handles Let’s Encrypt certificates. This path costs more ops time and gives you exact cache and header behavior.',
                    'rsync with --delete prevents old articles from lingering after renames. I learned that when a deleted draft kept ranking in search because the file never left the server.',
                    'The deploy itself runs from your machine or CI, not from the Nginx config: rsync -avz --delete ./site/ user@server:/var/www/site/',
                ],
                'code': '# Redirect all HTTP to HTTPS (certbot --nginx can add this for you)\nserver {\n  listen 80;\n  server_name example.com www.example.com;\n  return 301 https://$host$request_uri;\n}\n\nserver {\n  listen 443 ssl;\n  http2 on;  # nginx 1.25.1+; replaces the deprecated "listen ... http2"\n  server_name example.com www.example.com;\n\n  ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;\n  ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;\n\n  root /var/www/site;\n  index index.html;\n\n  location / {\n    try_files $uri $uri/ =404;\n  }\n\n  # Fingerprinted files (e.g. app.3f9a1c2b.css) never change: cache for a year\n  # Regexes containing { } must be quoted in nginx config\n  location ~* "\\.[0-9a-f]{8,}\\.(css|js|jpg|jpeg|png|gif|ico|svg|webp|woff2)$" {\n    add_header Cache-Control "public, max-age=31536000, immutable";\n  }\n\n  # Un-hashed assets and HTML: revalidate on each use (cheap 304s via ETag)\n  location ~* \\.(css|js|jpg|jpeg|png|gif|ico|svg|webp|woff2|html)$ {\n    add_header Cache-Control "no-cache";\n  }\n}',
                'code_lang': 'nginx',
            },
            {
                'h2': 'Automating the VPS deploy with GitHub Actions',
                'paragraphs': [
                    'Once a site has a build step, a workflow on main can build and rsync it so nobody deploys from a laptop. The example below checks out the repo, installs a current Node LTS with actions/setup-node (Node 20 reached end of life in April 2026, so use 22 or 24), runs npm ci against the committed lockfile, builds, and syncs dist/ to the Nginx root with --delete. Adjust dist/ to your publish directory, or drop the Node steps if the site has no build.',
                    'The SSH step needs a known_hosts entry as well as the key; without one, rsync stops with “Host key verification failed”. Generate the entry once from a machine you trust (ssh-keyscan -t ed25519 your.server), compare its fingerprint with ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub on the server, and store it as the DEPLOY_KNOWN_HOSTS secret. Turning off StrictHostKeyChecking instead removes the protection against a spoofed host. Keep the three secrets in a GitHub environment named production so deploys can require a reviewer.',
                    'The concurrency block allows one deploy at a time. By default a newer run waits and replaces any older pending run, so an older commit cannot deploy after a newer one. cancel-in-progress: true would also cancel a deploy that is already running, which can stop rsync halfway through. For GitHub Pages, use the Option B workflow instead; this one is for servers you control.',
                ],
                'code': '# .github/workflows/deploy.yml\nname: Build and deploy\non:\n  push:\n    branches: [main]\n\npermissions:\n  contents: read\n\n# One deploy at a time; a newer run replaces any older *pending* run\nconcurrency:\n  group: deploy-production\n  cancel-in-progress: false\n\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n    environment: production\n    steps:\n      - uses: actions/checkout@v7\n      - uses: actions/setup-node@v7\n        with:\n          node-version: 24\n          cache: npm\n      - run: npm ci\n      - run: npm run build\n      - name: Configure SSH\n        env:\n          SSH_KEY: ${{ secrets.DEPLOY_SSH_KEY }}\n          KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}\n        run: |\n          install -d -m 700 ~/.ssh\n          install -m 600 /dev/null ~/.ssh/id_ed25519\n          printf \'%s\\n\' "$SSH_KEY" > ~/.ssh/id_ed25519\n          printf \'%s\\n\' "$KNOWN_HOSTS" > ~/.ssh/known_hosts\n      - name: Rsync to server\n        env:\n          HOST: ${{ secrets.DEPLOY_HOST }}\n        run: rsync -az --delete dist/ "deploy@$HOST:/var/www/site/"',
                'code_lang': 'yaml',
            },
            {
                'h2': 'Caching and cache-busting',
                'paragraphs': [
                    'Hash filenames for CSS/JS when you have a build step, then cache them forever. HTML should revalidate so users pick up new asset references. Without that split, you either break users with stale HTML pointing at missing hashed files, or you never cache and waste bandwidth.',
                    'After a bad deploy on a CDN, purge intentionally. Hoping “it will expire” during an incident is how you spend an hour explaining why half the audience sees the old homepage.',
                    'Version the deploy. A simple GENERATED_AT or git SHA in a meta tag makes “what’s live?” answerable without SSH.',
                ],
            },
            {
                'h2': 'Checks before you call it live',
                'paragraphs': [
                    'Hit the homepage, an article URL, and a known 404. Confirm HTTPS redirects. View source on CSS/JS URLs. Run a quick Lighthouse pass for broken a11y and huge images. Submit the sitemap if it is a content site.',
                ],
                'bullets': [
                    'Publish directory is correct (no accidental parent folder)',
                    'HTTPS works and HTTP redirects',
                    'Article deep links return 200',
                    'CSS/JS load (watch base path on GitHub project pages)',
                    'HTML short cache; hashed assets long cache',
                    'robots.txt and sitemap.xml reachable',
                ],
            },
            {
                'h2': 'Which host I choose',
                'paragraphs': [
                    'Netlify or similar PaaS for speed and preview deploys. GitHub Pages for simple docs when the repo already lives on GitHub and the base path is acceptable. Nginx when I need custom headers, multiple sites on one box, or data residency constraints.',
                    'Start on a PaaS. Move to a VPS when you have a concrete reason. Premature Nginx is unpaid sysadmin work.',
                ],
            },
            {
                'h2': 'Custom domains and DNS gotchas',
                'paragraphs': [
                    'Point the apex and www with the records your host documents. Apex often needs ALIAS/ANAME or A records; CNAME-only setups fail on bare domains. Wait for DNS TTL before declaring failure.',
                    'Set canonical host redirects early—www to apex or the reverse—so analytics and sitemaps do not split. Mixed content warnings usually mean an asset still referenced via http://; fix the HTML, not only the certificate.',
                    'For BudhiWorks-style article sites, keep canonical link tags aligned with the final domain. Publishing under a netlify.app URL and later moving to a custom domain without updating canonicals confuses search engines.',
                ],
            },
            {
                'h2': 'SPAs versus multi-page static sites',
                'paragraphs': [
                    'Multi-page static HTML (like this blogging repo) needs try_files that serve real files and a clean 404. SPA mode that rewrites everything to index.html will hide missing articles as the homepage shell—bad for content sites.',
                    'If you do ship an SPA admin elsewhere, use a separate location block or host. Do not reuse the blog’s Nginx try_files for an app that needs history API fallbacks.',
                    'Precompress assets with gzip or brotli at the CDN. On Nginx, gzip_static on serves precompressed .gz files (the module ships in most distro and nginx.org packages); serving .br files needs the separate ngx_brotli module and its brotli_static directive. It is free performance for text-heavy blogs.',
                ],
                'bullets': [
                    'Content sites: real paths and real 404 pages',
                    'SPA fallbacks only where the app needs them',
                    'Align canonical URLs with the custom domain',
                    'Enable HTTPS redirects and HSTS once stable',
                ],
            },
            {
                'h2': 'Headers worth setting on day one',
                'paragraphs': [
                    'Besides cache policy, I set X-Content-Type-Options nosniff, a conservative Referrer-Policy, and a Content-Security-Policy that fits the site. Static blogs can use strict CSPs more easily than complex SPAs.',
                    "The CSP has to allow everything the page really loads, and ads load a lot. AdSense code pulls further scripts and iframes from several Google domains that change over time, so an allowlist such as script-src 'self' https://pagead2.googlesyndication.com under default-src 'self' blocks the ads. Google supports only a nonce-based strict CSP for AdSense, shown below. The nonce must be random on every response, so a purely static host has to inject it at the edge or in the web server; where that is not possible, leave script-src out rather than ship a policy that breaks ads. Test any policy with Content-Security-Policy-Report-Only first.",
                    'HSTS comes after you are sure HTTPS works on all subdomains you cover. Premature HSTS with includeSubDomains has locked teams out of internal HTTP tools on sibling hosts.',
                    'Security headers do not replace careful script hygiene. They reduce blast radius when a mistake happens.',
                ],
                'code': "# Strict CSP in the form Google supports for AdSense. {random} must be a fresh,\n# unguessable value per response; put the same value in nonce=\"...\" on the\n# adsbygoogle.js script tag and on the inline (adsbygoogle = ...).push() script.\nContent-Security-Policy: object-src 'none'; \\\n  script-src 'nonce-{random}' 'unsafe-inline' 'unsafe-eval' 'strict-dynamic' https: http:; \\\n  base-uri 'none'; frame-ancestors 'none'\nReferrer-Policy: strict-origin-when-cross-origin\nX-Content-Type-Options: nosniff",
                'code_lang': 'text',
            },
            {
                'h2': 'Rollback in under a minute',
                'paragraphs': [
                    'Netlify and similar hosts keep deploy history—rollback is a click. On GitHub Pages, redeploy the previous commit SHA. On Nginx, keep the last rsync tree under /var/www/site-prev and symlink swap atomically.',
                    'Practice rollback once before you need it. The first bad CSS deploy at peak reading time is a poor moment to learn your host’s UI.',
                    'For content sites, prefer fixing forward when the error is a typo. Prefer rollback when the error is “deleted the stylesheet” or “wrong publish folder emptied the site.”',
                ],
            },
            {
                'h2': 'Ship checklist I reuse',
                'paragraphs': [
                    'Before DNS cutover: dry-run deploy on a preview URL, click three article links, validate CSS loads, confirm sitemap and robots, confirm 404 page exists.',
                    'At cutover: lower TTL ahead of time if you control DNS, flip records, watch HTTPS cert issuance, purge CDN if needed, verify canonical host redirect.',
                    'After cutover: spot-check Search Console or analytics for spike in 404s, keep the previous deploy ready for rollback for 24 hours, then delete stale hosts so you do not accidentally edit the wrong place next week.',
                    'Static sites are simple until they are not. The steps above keep Netlify, GitHub Pages, and Nginx deploys predictable enough that content work stays the hard part—which is where you want the effort.',
                ],
                'bullets': [
                    'Preview before production DNS',
                    'Verify deep links and assets on the real host',
                    'Keep a one-step rollback ready for a day',
                    'Monitor 404s after cutover',
                ],
            },
        ],
        'takeaways': [
            'Static hosting is a publish-directory problem plus HTTPS and cache policy.',
            'Netlify.toml (or equivalent) keeps headers and publish settings in git.',
            'GitHub Pages project URLs need correct base paths for assets.',
            'On a VPS, rsync --delete and Certbot plus clear Nginx cache rules.',
            'Cache hashed assets forever; revalidate HTML so references stay fresh.',
            'Verify deep links, HTTPS, and asset URLs after every first deploy to a new host.',
        ],
    },
]
