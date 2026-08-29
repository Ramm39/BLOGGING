ARTICLES = [
    {
        'slug': 'how-to-fix-cors-errors',
        'title': 'How to Fix CORS Errors in Browser APIs (Preflight, Credentials, and Proxies)',
        'description': "A practitioner's playbook for diagnosing Access-Control-Allow-Origin failures, fixing OPTIONS preflight, cookie credentials, and Vite/Express proxy setups.",
        'category': 'Backend',
        'date': '2026-06-02',
        'read_min': 11,
        'keywords': 'CORS errors, Access-Control-Allow-Origin, preflight OPTIONS, credentials cookies, Express CORS, Vite proxy',
        'excerpt': 'I still see CORS turn a 20-minute feature into a two-hour rabbit hole. Here is the checklist I use when the browser blocks a fetch that works fine in curl.',
        'sections': [
            {
                'h2': 'What the browser actually blocked',
                'paragraphs': [
                    'Last quarter I burned an afternoon on a dashboard that worked in Postman and failed in Chrome with a blocked CORS policy on https://api.example.com/me from origin http://localhost:5173. Curl returned 200. The API was fine. The browser was enforcing the same-origin policy on a cross-origin fetch.',
                    'CORS is not authentication. It is a browser gate: the server must opt in to being readable by a specific origin. If you only test with curl, Insomnia, or server-to-server calls, you will never see the failure. I now reproduce every failing request in DevTools Network with Preserve log on before I touch middleware.',
                    'One more habit that saved me: click the failing request and read the Console message carefully. Chrome often says the response to the preflight request does not pass access control, which means you are debugging OPTIONS, not GET. I paste the exact Origin header into a note so I do not fix the wrong host after a port change from 5173 to 5174.',
                ],
            },
            {
                'h2': 'Simple requests vs preflight',
                'paragraphs': [
                    'A GET or POST with Content-Type application/x-www-form-urlencoded, multipart/form-data, or text/plain, and no custom headers, can be a simple request. Everything else triggers a preflight: an OPTIONS request before the real method.',
                    'In my apps, JSON APIs almost always preflight because we send Content-Type application/json and often Authorization. If OPTIONS is not handled, Chrome shows a CORS error even though the real route would have returned 200. I have fixed this three times by adding an OPTIONS handler or enabling CORS middleware that answers preflight.',
                    'Watch for frameworks that only register GET/POST and return 404 for OPTIONS. NestJS, Express routers with strict method lists, and API gateways that block unknown methods all produce the same symptom. In one staging env, our ALB returned 405 for OPTIONS while Node never saw the request — we enabled OPTIONS at the load balancer, not only in Express.',
                ],
                'code': "# Express: answer preflight explicitly if you are not using cors()\napp.options('/api/*', (req, res) => {\n  res.setHeader('Access-Control-Allow-Origin', 'http://localhost:5173');\n  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,PATCH,DELETE,OPTIONS');\n  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');\n  res.setHeader('Access-Control-Max-Age', '86400');\n  res.sendStatus(204);\n});",
                'code_lang': 'javascript',
            },
            {
                'h2': 'The credentials trap',
                'paragraphs': [
                    'When the frontend needs cookies with credentials include in fetch, or withCredentials true in Axios, the server cannot respond with Access-Control-Allow-Origin as a wildcard. It must echo a specific origin and set Access-Control-Allow-Credentials true.',
                    'I once shipped origin true in the cors package and forgot credentials true on the client. Cookies never arrived. Another time I set both sides correctly but left SameSite=Strict on a cross-site cookie — CORS looked fixed, session still empty. Check Set-Cookie attributes in the response headers, not only ACAO.',
                    'Numbers from a real incident: about 70 percent of login-then-logout reports on a SPA were cookie attribute mismatches, not bad JWT secrets. DevTools showed a SameSite warning. We switched to SameSite=None Secure for the cross-site API host and those tickets dropped overnight.',
                ],
                'code': "// Client\nfetch('https://api.example.com/me', {\n  method: 'GET',\n  credentials: 'include',\n  headers: { 'Content-Type': 'application/json' },\n});\n\n// Server (cors package)\nimport cors from 'cors';\napp.use(cors({\n  origin: ['http://localhost:5173', 'https://app.example.com'],\n  credentials: true,\n  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],\n  allowedHeaders: ['Content-Type', 'Authorization'],\n}));",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Local fix: Vite proxy instead of fighting CORS',
                'paragraphs': [
                    'For local development I prefer same-origin requests through a Vite or Next proxy. The browser talks to http://localhost:5173/api/... and Vite forwards to the real API. No CORS headers required locally because the page origin matches the request origin.',
                    'I use this pattern on every greenfield SPA now. Production still needs real CORS or a gateway on the same domain. The proxy is a developer ergonomics tool, not a production security model.',
                    'One footgun: if your API already prefixes routes with /api and Vite also mounts at /api, you may double-prefix after a rewrite. I log the proxied URL once at startup. Also set changeOrigin true when the upstream checks Host headers; without it some frameworks reject the request before CORS middleware runs.',
                ],
                'code': "// vite.config.ts\nimport { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\n\nexport default defineConfig({\n  plugins: [react()],\n  server: {\n    proxy: {\n      '/api': {\n        target: 'http://localhost:4000',\n        changeOrigin: true,\n      },\n    },\n  },\n});",
                'code_lang': 'typescript',
            },
            {
                'h2': 'Allowlists that do not bite you in staging',
                'paragraphs': [
                    'Hardcoding http://localhost:5173 works until someone uses 5174, a preview deploy URL, or 127.0.0.1 instead of localhost. Browsers treat those as different origins. I keep an env list and reject missing Origin rather than reflecting whatever the client sends.',
                    'Reflecting arbitrary Origin values with credentials enabled lets any website read authenticated responses. Our allowlist lives in CORS_ORIGINS and we fail closed in production. In development we allow a shortlist of localhost ports so preview branches still work.',
                ],
                'code': "function corsOrigin(req, callback) {\n  const allowed = (process.env.CORS_ORIGINS || '')\n    .split(',')\n    .map((s) => s.trim())\n    .filter(Boolean);\n  const origin = req.header('Origin');\n  if (!origin) return callback(null, false);\n  if (allowed.includes(origin)) return callback(null, true);\n  return callback(new Error(`Origin ${origin} not allowed`), false);\n}\n\napp.use(cors({ origin: corsOrigin, credentials: true }));",
                'code_lang': 'javascript',
            },
            {
                'h2': 'My 10-minute diagnosis checklist',
                'paragraphs': [
                    'Open the failed request in Network. If you see a red OPTIONS with 404 or 405, fix preflight first. If OPTIONS is 204 but the real request fails CORS, compare Origin with Access-Control-Allow-Origin character-for-character — trailing slashes and http versus https matter.',
                    'Confirm you did not set a wildcard with credentials. Confirm custom headers are listed in Access-Control-Allow-Headers. If you use a CDN or API gateway, check that it forwards OPTIONS and does not strip ACA headers. In one production incident Cloudflare cached a preflight without credentials for 24 hours and every cookie-auth user looked broken until we purged.',
                ],
                'bullets': [
                    'Reproduce in the browser Network tab, not only curl',
                    'Fix OPTIONS before debugging the real method',
                    'Never combine a wildcard ACAO with credentials',
                    'Prefer a local proxy for SPA plus separate API in development',
                    'Verify gateway or CDN does not strip or cache bad CORS responses',
                    'Diff Origin versus ACAO including scheme and port',
                ],
            },
            {
                'h2': 'Production pattern I settle on',
                'paragraphs': [
                    'Allowlist exact frontend origins from env. Reject unknown origins. Keep credentials only if you truly need cookie sessions; Bearer tokens in Authorization avoid cookie plus CORS complexity for many SPAs.',
                    'For mobile WebViews and multiple subdomains, I sometimes put API and app under a shared parent domain and terminate TLS at a reverse proxy so browsers see same-site requests. That removed an entire class of CORS tickets for one client — about 40 percent of their API-is-down Slack threads were actually CORS misconfig.',
                    'I also document the matrix in the README: which env, which origin, cookie or bearer, proxy or direct. The next person debugging at 11pm should not rediscover these rules from stack traces alone.',
                ],
            },
        ],
        'takeaways': [
            'CORS failures are browser-only; curl success proves nothing about the frontend.',
            'JSON plus custom headers means OPTIONS preflight must succeed first.',
            'Credentials require a concrete ACAO origin, never a wildcard.',
            'Use a Vite or Next proxy locally; configure real CORS for production.',
            'Gateways can strip or cache CORS headers — inspect the final response.',
            'Allowlist origins from env; never reflect arbitrary Origin with credentials.',
        ],
    },
    {
        'slug': 'core-web-vitals-guide',
        'title': 'Core Web Vitals Guide: Practical LCP, INP, and CLS Checklist',
        'description': 'Field-tested ways to improve Largest Contentful Paint, Interaction to Next Paint, and Cumulative Layout Shift with numbers from real production apps.',
        'category': 'Web Performance',
        'date': '2026-06-05',
        'read_min': 12,
        'keywords': 'Core Web Vitals, LCP, INP, CLS, web performance, fetchpriority, font-display',
        'excerpt': 'I treat Core Web Vitals as a release gate, not a blog buzzword. This is the checklist we run before shipping marketing pages and authenticated dashboards.',
        'sections': [
            {
                'h2': 'Targets I actually ship against',
                'paragraphs': [
                    "Google's good thresholds are LCP at or under 2.5s, INP at or under 200ms, and CLS at or under 0.1 at the 75th percentile of field data. Lab scores from Lighthouse on a cable connection can lie. I prioritize CrUX and Search Console field data, then RUM from our own web-vitals beacons.",
                    'On a client storefront, lab LCP was 1.8s and field p75 was 3.4s because real users were on mid-range Androids over 4G. We stopped celebrating Lighthouse greens and started optimizing the hero image and TTFB.',
                    'I also split dashboards from marketing in reporting. Authenticated apps often look poor on LCP because the largest paint waits on an API. Mixing those cohorts hid a 1.1s LCP regression on the homepage for two weeks before we noticed.',
                ],
            },
            {
                'h2': 'LCP: make the largest element arrive early',
                'paragraphs': [
                    'Find the LCP element in Performance or the Web Vitals overlay. For us it is usually a hero img, an H1 block with a web font, or a product card image. I set explicit width and height or aspect-ratio, compress to AVIF or WebP, and add fetchpriority high on the LCP image only — never on every image.',
                    'I also preload that image in head when it is not discoverable early. CSS background heroes are the worst offenders. Moving a CSS background hero to an img dropped LCP by about 900ms on one landing page.',
                    'Before and after on that page at field p75: LCP went from 3.6s to 2.4s after we cut hero weight from about 480KB JPEG to about 95KB AVIF, added preload, and stopped lazy-loading the LCP image. loading=lazy on the hero is a mistake I still catch in PRs.',
                ],
                'code': '<!-- In <head> for known LCP image -->\n<link rel="preload" as="image" href="/hero.avif" type="image/avif" fetchpriority="high" />\n\n<img\n  src="/hero.avif"\n  width="1280"\n  height="720"\n  alt="Product dashboard"\n  fetchpriority="high"\n  decoding="async"\n/>',
                'code_lang': 'html',
            },
            {
                'h2': 'INP: keep the main thread free after clicks',
                'paragraphs': [
                    'INP replaced FID. It measures how long the page stays unresponsive after a user interaction across the visit. Our worst INP came from a filters panel that re-rendered a 2,000-row table synchronously on every checkbox toggle.',
                    'Fixes that moved p75 INP from about 380ms to about 140ms: debounce expensive handlers at 150ms, virtualize long lists, break work with scheduler.postTask or requestIdleCallback for non-urgent updates, and avoid layout thrashing in event handlers. I profile with the Performance panel Interactions track, not guesses.',
                    'Another pattern that hurt us: opening a modal that synchronously parsed a large JSON blob and built a chart. Moving parse and chart construction behind startTransition in React kept the click responsive; the chart filled in a frame later. Users preferred a fast open over a frozen button.',
                ],
                'code': "// Bad: sync filter of huge list on every keystroke\ninput.addEventListener('input', (e) => {\n  renderRows(filterAll(rows, e.target.value)); // freezes UI\n});\n\n// Better: debounce + yield\nimport { debounce } from './debounce';\n\nconst onFilter = debounce((value) => {\n  const filtered = filterAll(rows, value);\n  requestAnimationFrame(() => renderRows(filtered));\n}, 150);\n\ninput.addEventListener('input', (e) => onFilter(e.target.value));",
                'code_lang': 'javascript',
            },
            {
                'h2': 'CLS: reserve space before paint',
                'paragraphs': [
                    'CLS spikes when ads, late fonts, or images without dimensions shove content. I set image dimensions, use font-display optional or swap with a close fallback metric, and reserve min-height for async embeds.',
                    'A cookie banner that injected above the fold without reserved space cost us 0.18 CLS on mobile. We fixed it by rendering a 72px placeholder in the initial HTML shell. CLS fell under 0.05 within a week of field data.',
                    'Web fonts were the other villain. Swap without matched metrics caused a visible jump of the H1. We switched to a fallback with similar x-height via size-adjust and the shift became hard to notice in field data.',
                ],
                'bullets': [
                    'Always set width/height or aspect-ratio on images and video',
                    'Avoid inserting DOM above existing content without a reserved slot',
                    'Prefer transform animations over top/left that trigger layout',
                    'Load webfonts with a fallback that has similar metrics',
                    'Test CLS with throttling and ad slots enabled — empty lab pages hide it',
                ],
            },
            {
                'h2': 'Wire RUM so arguments end',
                'paragraphs': [
                    'I ship the web-vitals library attribution build and POST LCP, INP, and CLS to our analytics endpoint with route name, connection type, and device class. Without attribution, LCP is bad is not actionable — you need the element and the phase such as TTFB versus resource load versus render delay.',
                    "Sample at 100 percent on low-traffic marketing sites; on high-traffic apps I sample 5 to 10 percent and still get stable p75 within a day. Alert when a route's p75 LCP rises more than 400ms week-over-week after a deploy.",
                ],
                'code': "import { onLCP, onINP, onCLS } from 'web-vitals/attribution';\n\nfunction send(metric) {\n  const body = JSON.stringify({\n    name: metric.name,\n    value: metric.value,\n    id: metric.id,\n    route: location.pathname,\n    navType: metric.navigationType,\n  });\n  navigator.sendBeacon('/rum', body);\n}\n\nonLCP(send);\nonINP(send);\nonCLS(send);",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Images beyond the hero',
                'paragraphs': [
                    'Below the fold I use responsive srcset with 1x and 2x and modern formats, and I lazy-load everything that is not the LCP candidate. A product grid that eagerly loaded twelve 200KB JPEGs pushed LCP out because bandwidth contested the hero. After lazy-loading grid images, field LCP improved another roughly 350ms on 4G profiles.',
                    'I also cap decoded size. Serving a 4000px-wide asset into a 400px slot wastes memory and decode time on mobile. Our image CDN enforces max width by breakpoint. When marketing insists on a video background, I treat the poster frame as the LCP image and defer video until after load or first interaction.',
                ],
            },
            {
                'h2': 'Server and cache levers that move field LCP',
                'paragraphs': [
                    'Half of our LCP regressions were TTFB. Edge caching HTML for anonymous marketing pages with 30 to 60s stale-while-revalidate and keeping API origin within the same region as users mattered more than shaving 4KB of JS.',
                    'I also audit third parties. One tag manager container added 280ms to LCP on mobile. We deferred non-essential tags until after requestIdleCallback or first interaction. Measure before and after with the same RUM dashboard — screenshots of Lighthouse alone do not convince stakeholders.',
                ],
            },
            {
                'h2': 'Release checklist we paste into PRs',
                'paragraphs': [
                    'Before merge on customer-facing routes: identify LCP element; confirm preload and fetchpriority; no layout shift from fonts or banners; interaction handlers under about 50ms of sync work on mid-tier CPU; bundle diff does not add a new blocking script in head.',
                    'We fail the PR if lab LCP on a throttled mobile profile jumps more than 300ms without a documented reason. That rule alone caught two accidental full-page client hydration of marketing content.',
                    'We keep a soft budget of about 170KB gzipped JS for marketing routes. Crossing the budget opens a required comment explaining the trade. That social pressure prevented two accidental charting libraries on the homepage. I paste lab LCP, INP, and CLS on Moto G throttling next to the diff so reviewers stop arguing about vibes.',
                ],
            },
        ],
        'takeaways': [
            'Trust field p75 from CrUX or RUM over a single Lighthouse run on desktop cable.',
            'LCP usually needs a discoverable, prioritized, correctly sized hero image.',
            'INP improves when you cut sync main-thread work after clicks and keypresses.',
            'CLS is mostly reserved space: dimensions, banners, and font fallbacks.',
            'TTFB and third-party tags often dominate real-user LCP more than micro-optimizations.',
            'Ship RUM with attribution so you know which element and phase regressed.',
        ],
    },
    {
        'slug': 'jwt-authentication-nodejs',
        'title': 'JWT Access and Refresh Tokens in Node/Express with httpOnly Cookies',
        'description': 'How I implement short-lived access JWTs and rotating refresh tokens in Express, stored in httpOnly cookies, with concrete rotation and revocation notes.',
        'category': 'Backend',
        'date': '2026-06-08',
        'read_min': 12,
        'keywords': 'JWT authentication, refresh token, httpOnly cookie, Node.js Express, access token, token rotation',
        'excerpt': 'I stopped putting JWTs in localStorage after one XSS demo emptied a staging account. Here is the access plus refresh cookie pattern we use in production Express apps.',
        'sections': [
            {
                'h2': 'Threat model in one paragraph',
                'paragraphs': [
                    "Access tokens in localStorage are trivial to steal if any XSS lands. Tokens in memory-only JS are safer but disappear on refresh. httpOnly cookies keep tokens off document.cookie, and Secure plus SameSite reduce drive-by sends. XSS can still trigger authenticated requests from the victim's browser — cookies are not magic — but they stop simple token exfiltration scripts.",
                    'I use a short-lived access JWT of 5 to 15 minutes and a longer refresh token of 7 to 30 days that we rotate and store hashed server-side. Stolen refresh tokens should not live forever.',
                    'Our pen-test writeup put it bluntly: with localStorage JWTs, a single reflected XSS stole sessions from three test accounts in under a minute. With httpOnly cookies, the same payload could still act as the user but could not exfiltrate a reusable bearer token to an attacker laptop. That trade is worth the CSRF work.',
                ],
            },
            {
                'h2': 'Issuing tokens',
                'paragraphs': [
                    'On login I verify password with bcrypt at cost 12, then mint an access JWT signed with HS256 or better RS256 or EdDSA in larger systems. Claims stay minimal: sub, role, iat, exp. No PII blobs. Refresh token is a random 32-plus byte string; we store sha256 of the token in Postgres with user_id, expires_at, replaced_by, and revoked_at.',
                    'Clock skew between API instances bit us once: tokens looked expired 30 seconds early. We allow a 30-second clockTolerance on verify, and we NTP-sync the fleet. Also rotate JWT_ACCESS_SECRET only with a dual-key verify window so deploys do not log everyone out at once.',
                ],
                'code': "import jwt from 'jsonwebtoken';\nimport crypto from 'crypto';\n\nconst ACCESS_TTL = '10m';\nconst REFRESH_DAYS = 14;\n\nexport function signAccessToken(user) {\n  return jwt.sign(\n    { sub: user.id, role: user.role },\n    process.env.JWT_ACCESS_SECRET,\n    { expiresIn: ACCESS_TTL }\n  );\n}\n\nexport function createRefreshToken() {\n  return crypto.randomBytes(48).toString('base64url');\n}\n\nexport function hashToken(token) {\n  return crypto.createHash('sha256').update(token).digest('hex');\n}\n\nexport function setAuthCookies(res, accessToken, refreshToken) {\n  const common = {\n    httpOnly: true,\n    secure: process.env.NODE_ENV === 'production',\n    sameSite: 'lax',\n    path: '/',\n  };\n  res.cookie('access_token', accessToken, { ...common, maxAge: 10 * 60 * 1000 });\n  res.cookie('refresh_token', refreshToken, {\n    ...common,\n    path: '/auth',\n    maxAge: REFRESH_DAYS * 24 * 60 * 60 * 1000,\n  });\n}",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Middleware that reads the cookie',
                'paragraphs': [
                    'I do not accept access tokens from query strings. Cookie or Authorization Bearer for API clients. Cookie path scoping for refresh under /auth limits accidental sends to every asset request — a mistake I made when both cookies shared path slash and every image request carried a refresh token.',
                    'Query-string tokens also end up in access logs, referrer headers, and browser history. We banned them in a security review after finding tokens in CDN logs.',
                ],
                'code': "import cookieParser from 'cookie-parser';\n\napp.use(cookieParser());\n\nexport function requireAuth(req, res, next) {\n  const header = req.headers.authorization;\n  const token =\n    (header && header.startsWith('Bearer ') && header.slice(7)) ||\n    req.cookies.access_token;\n\n  if (!token) return res.status(401).json({ error: 'unauthenticated' });\n\n  try {\n    req.user = jwt.verify(token, process.env.JWT_ACCESS_SECRET);\n    next();\n  } catch {\n    return res.status(401).json({ error: 'invalid_token' });\n  }\n}",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Refresh with rotation',
                'paragraphs': [
                    'POST /auth/refresh reads the refresh cookie, hashes it, looks up a non-revoked row, issues a new access plus refresh pair, marks the old refresh as replaced, and sets cookies again. If a previously replaced refresh is presented again, I revoke the whole family — classic reuse detection for token theft.',
                    'Without rotation, a leaked refresh token works until expiry. With rotation and reuse detection, we cut session abuse windows from days to minutes in one incident response drill.',
                    'Race condition note: two parallel tabs can refresh at the same millisecond. One wins; the other looks like reuse. We solve this with a short grace window of about 10 seconds where the previous refresh still works if replaced_by was set recently by the same family, or by serializing refresh with a per-user lock.',
                ],
                'code': "app.post('/auth/refresh', async (req, res) => {\n  const raw = req.cookies.refresh_token;\n  if (!raw) return res.status(401).json({ error: 'no_refresh' });\n\n  const row = await db.refreshTokens.findByHash(hashToken(raw));\n  if (!row || row.revoked_at || row.expires_at < new Date()) {\n    return res.status(401).json({ error: 'invalid_refresh' });\n  }\n  if (row.replaced_by) {\n    await db.refreshTokens.revokeFamily(row.family_id);\n    return res.status(401).json({ error: 'reuse_detected' });\n  }\n\n  const user = await db.users.findById(row.user_id);\n  const access = signAccessToken(user);\n  const nextRefresh = createRefreshToken();\n  await db.refreshTokens.rotate(row.id, hashToken(nextRefresh), REFRESH_DAYS);\n  setAuthCookies(res, access, nextRefresh);\n  res.json({ ok: true });\n});",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Silent refresh on the client',
                'paragraphs': [
                    'The SPA keeps a fetch interceptor: on 401, try /auth/refresh once, retry the original request, and if refresh fails redirect to login. Without a single-flight mutex, five parallel 401s spawn five refreshes and trigger reuse detection. I gate refresh behind a shared promise.',
                ],
                'code': "let refreshPromise = null;\n\nasync function refreshOnce() {\n  if (!refreshPromise) {\n    refreshPromise = fetch('/auth/refresh', {\n      method: 'POST',\n      credentials: 'include',\n    }).finally(() => {\n      refreshPromise = null;\n    });\n  }\n  return refreshPromise;\n}\n\nasync function apiFetch(input, init) {\n  const res = await fetch(input, { ...init, credentials: 'include' });\n  if (res.status !== 401) return res;\n  const refreshed = await refreshOnce();\n  if (!refreshed.ok) throw new Error('session_expired');\n  return fetch(input, { ...init, credentials: 'include' });\n}",
                'code_lang': 'javascript',
            },
            {
                'h2': 'CSRF when cookies are involved',
                'paragraphs': [
                    'Cookie auth reintroduces CSRF for state-changing requests. I use SameSite=Lax as a good default for most apps plus a double-submit CSRF token for mutating routes, or SameSite=Strict for sensitive admin tools that can tolerate harsher UX.',
                    'SPA on app.example.com and API on api.example.com needs careful cookie Domain and CORS credentials. Same-site under a parent domain is simpler when you can afford it.',
                ],
            },
            {
                'h2': 'Cookie attributes I verify in staging',
                'paragraphs': [
                    'Before calling a release done I open Application Cookies on staging and confirm: httpOnly checked, Secure on HTTPS, SameSite as designed, path scoped for refresh, and expiry matching TTL. I have shipped a missing Secure flag that worked on localhost HTTP and silently dropped cookies in production HTTPS redirects.',
                    'Cross-subdomain cookies need Domain=.example.com carefully. Too broad and every subdomain receives the session cookie. For native mobile clients we still issue Bearer access tokens in the JSON body and skip cookies. The same signing and refresh tables back both clients.',
                    'I log refresh outcomes as counters: success, expired, reuse_detected, missing. A spike in reuse_detected without a security incident usually means the client double-refresh race. Never log raw tokens — log a truncated hash prefix if you need correlation.',
                ],
            },
            {
                'h2': 'Mistakes I will not repeat',
                'paragraphs': [
                    'Storing refresh tokens plaintext in the DB. Using a 7-day access JWT to avoid refresh complexity. Putting secrets in the JWT payload and expecting them to stay secret. Forgetting to clear cookies on logout while only deleting the client store.',
                    'Logout must clear cookies with res.clearCookie and revoke the refresh row. For force-logout-all-devices, revoke all refresh families for that user_id. We expose that as a security settings action. Document the token TTLs in the security runbook so on-call can answer session questions without reading code at 2am.',
                ],
                'bullets': [
                    'Access JWT: minutes, not days',
                    'Refresh: random opaque token, hashed at rest, rotated',
                    'httpOnly plus Secure plus scoped path',
                    'Reuse detection on refresh',
                    'Logout revokes server-side state, not only cookies',
                    'Single-flight client refresh to avoid false reuse alarms',
                ],
            },
        ],
        'takeaways': [
            'Prefer httpOnly cookies over localStorage for browser session tokens.',
            'Keep access JWTs short-lived; persist opaque refresh tokens hashed in the DB.',
            'Rotate refresh tokens and revoke the family on reuse.',
            'Cookie auth needs a CSRF strategy with SameSite plus tokens for mutations.',
            'Logout and sign out everywhere must revoke server-side refresh rows.',
            'Serialize client silent-refresh so parallel 401s do not look like theft.',
        ],
    },
    {
        'slug': 'docker-compose-for-developers',
        'title': 'Docker Compose for Local Node, Postgres, and Redis',
        'description': 'A practical Compose file for day-to-day Node development with Postgres and Redis, including volumes, healthchecks, and the mistakes that ate my weekends.',
        'category': 'DevOps',
        'date': '2026-06-11',
        'read_min': 12,
        'keywords': 'Docker Compose, Node.js, Postgres, Redis, local development, healthcheck, volumes',
        'excerpt': 'I want one command that brings up API, Postgres, and Redis the same way on every laptop. This is the Compose setup we copy into new services.',
        'sections': [
            {
                'h2': 'Why Compose instead of five terminal tabs',
                'paragraphs': [
                    'Onboarding used to be install Postgres 16, Redis 7, create a role, remember the port conflicts with the other project. New hires lost a day. Compose gives us reproducible ports, versions, and seed scripts. I still run the Node process on the host with hot reload when I iterate fast, and only containerize Node when we need parity with production images.',
                    'Two modes: full stack in Compose for demos and CI, and docker compose up db redis while npm run dev hits localhost mapped ports. Both share the same compose.yaml.',
                    'Before Compose, we had a wiki page with 14 steps and three different Homebrew formulae depending on macOS version. After Compose, first successful up median time for new hires went from roughly a day to under 30 minutes, including cloning and copying .env.example.',
                ],
            },
            {
                'h2': 'A Compose file that survives Monday mornings',
                'paragraphs': [
                    'Pin image tags. postgres:latest bit us when a major jumped overnight. Named volumes keep data across restarts. Healthchecks stop the API from racing migrations before Postgres accepts connections — that race caused flaky CI for weeks.',
                    'I also set restart unless-stopped on db and redis for long-lived laptops, and I keep resource limits light so a runaway migration cannot freeze Docker Desktop. Memory 512M for Postgres is enough for local datasets under a few GB.',
                ],
                'code': 'services:\n  db:\n    image: postgres:16.3-alpine\n    environment:\n      POSTGRES_USER: app\n      POSTGRES_PASSWORD: app\n      POSTGRES_DB: app_dev\n    ports:\n      - "5432:5432"\n    volumes:\n      - pgdata:/var/lib/postgresql/data\n      - ./docker/db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro\n    healthcheck:\n      test: ["CMD-SHELL", "pg_isready -U app -d app_dev"]\n      interval: 5s\n      timeout: 5s\n      retries: 10\n\n  redis:\n    image: redis:7.2-alpine\n    ports:\n      - "6379:6379"\n    command: ["redis-server", "--save", "60", "1", "--loglevel", "warning"]\n    healthcheck:\n      test: ["CMD", "redis-cli", "ping"]\n      interval: 5s\n      timeout: 3s\n      retries: 10\n\n  api:\n    build:\n      context: .\n      dockerfile: Dockerfile.dev\n    env_file: .env.docker\n    environment:\n      DATABASE_URL: postgres://app:app@db:5432/app_dev\n      REDIS_URL: redis://redis:6379\n    ports:\n      - "4000:4000"\n    volumes:\n      - .:/app\n      - /app/node_modules\n    depends_on:\n      db:\n        condition: service_healthy\n      redis:\n        condition: service_healthy\n\nvolumes:\n  pgdata:',
                'code_lang': 'yaml',
            },
            {
                'h2': 'Networking and .env gotchas',
                'paragraphs': [
                    'Inside the Compose network, hostname is the service name db or redis, not localhost. I have pasted localhost into a containerized API more times than I will admit — connection refused, 30 minutes of blame on Postgres.',
                    'Host-run Node must use localhost:5432. Container-run Node must use db:5432. We keep two env files: .env for host and .env.docker for Compose, or we template DATABASE_URL in scripts. Document that in README in bold; it is the number one Slack question.',
                    'Port collisions are the other weekly pain. If another project already bound 5432, Compose fails in a cryptic way. I map host 5433 to container 5432 for secondary projects and put the host port in .env so people do not hardcode.',
                ],
            },
            {
                'h2': 'Anonymous volumes for node_modules',
                'paragraphs': [
                    'The trick of bind-mounting . to /app plus an anonymous volume at /app/node_modules prevents the host from overwriting Linux node_modules with macOS binaries or an empty folder. Without the anonymous volume, native modules like bcrypt crash with invalid ELF headers.',
                    'When dependencies change, I run docker compose run --rm api npm ci or rebuild. Cold npm ci in the image took about 90s on our M2; mounting source keeps edit-reload under a second with nodemon.',
                ],
                'code': '# Dockerfile.dev\nFROM node:22-alpine\nWORKDIR /app\nCOPY package.json package-lock.json ./\nRUN npm ci\nCOPY . .\nCMD ["npm", "run", "dev"]',
                'code_lang': 'dockerfile',
            },
            {
                'h2': 'Migrations that wait for healthy Postgres',
                'paragraphs': [
                    'Even with depends_on healthchecks, I wrap migration commands in a tiny retry script for CI. Postgres can accept connections and still reject the first migration if the role setup from init.sql is mid-flight on a slow disk.',
                    'We run migrations as a one-shot Compose service in CI, not as a side effect of API boot, so failed migrations fail the job clearly instead of leaving a half-booted API.',
                ],
                'code': '# scripts/wait-and-migrate.sh\nset -euo pipefail\nfor i in $(seq 1 30); do\n  if pg_isready -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE"; then\n    npx prisma migrate deploy\n    exit 0\n  fi\n  sleep 2\ndone\necho "Postgres never became ready" >&2\nexit 1',
                'code_lang': 'bash',
            },
            {
                'h2': 'Seeding data without fighting init.sql',
                'paragraphs': [
                    'init.sql runs only on first volume create. For day-to-day seed data I use a Make target that runs a Node script against localhost after Compose is healthy. That script is idempotent with upsert by natural key so re-running it does not duplicate rows.',
                    'When I need a clean slate I explicitly run docker compose down -v, bring db and redis back, then migrate and seed. Teaching that reset stopped people from editing init.sql and wondering why nothing changed. Large dumps belong outside git on object storage.',
                ],
            },
            {
                'h2': 'Resetting state without drama',
                'paragraphs': [
                    'docker compose down keeps volumes. docker compose down -v wipes Postgres data — useful for migration experiments, catastrophic if you thought it was a soft stop. I alias dc-reset only after confirming the project name.',
                    'For shared laptops, set COMPOSE_PROJECT_NAME so volume names do not collide with another repo also calling its service db.',
                ],
                'bullets': [
                    'Pin major.minor image tags',
                    'Healthcheck before depends_on',
                    'Use service DNS names inside the network',
                    'Anonymous volume for node_modules on bind mounts',
                    'Know the difference between down and down -v',
                    'Remap host ports when 5432 or 6379 are already taken',
                ],
            },
            {
                'h2': 'CI uses the same Compose file',
                'paragraphs': [
                    'In GitHub Actions we run docker compose up -d db redis, wait for health, then run tests on the runner with host networking to published ports. Sharing the Compose file means local and CI Postgres majors cannot drift.',
                    'We cache the Postgres image layers and avoid building the API image in unit-test jobs. Integration jobs that need the API container build with BuildKit cache mounts so npm ci is not a cold 90s every time. A fixed sleep was sometimes too short on busy runners; healthchecks fixed that class of flake permanently.',
                ],
            },
            {
                'h2': 'What I do not put in local Compose',
                'paragraphs': [
                    'I avoid shipping production secrets in compose. Local passwords are app/app and never reused. I do not emulate the full Kubernetes mesh locally unless we are debugging mesh-specific bugs — Compose is for data stores and optional API parity.',
                    'Redis persistence is optional locally; I enable light RDB saves so cache warmups survive a reboot during a long feature branch. Postgres init scripts run only on empty volumes — after the first boot, change schema with migrations, not by editing init.sql and expecting it to re-run.',
                    'In GitHub Actions we run the same Compose file for db and redis, wait for health, then run tests on published ports. Flakes dropped once healthchecks gated the test start instead of a fixed sleep 10. Publish a one-line happy path in the README: compose up db redis, copy env, npm i, npm run dev.',
                ],
            },
        ],
        'takeaways': [
            'Compose the databases; optionally run Node on the host for faster reload.',
            'Pin image versions and wait on healthchecks before starting the API.',
            'localhost versus service name depends on whether the process is in a container.',
            'Bind-mount source with an anonymous node_modules volume to avoid native binary clashes.',
            'Treat down -v as destructive; use a unique COMPOSE_PROJECT_NAME per repo.',
            'Run migrations as an explicit step with retries, not as a silent boot side effect.',
        ],
    },
    {
        'slug': 'react-useeffect-common-mistakes',
        'title': 'React useEffect Mistakes I Keep Reviewing in PRs',
        'description': 'Dependency arrays, cleanup, fetch races, and infinite loops — concrete useEffect anti-patterns from production React code reviews.',
        'category': 'Frontend',
        'date': '2026-06-14',
        'read_min': 12,
        'keywords': 'React useEffect, dependency array, cleanup function, infinite loop, Strict Mode, fetch race',
        'excerpt': 'Most useEffect bugs I review are not exotic. They are missing deps, missing cleanup, or effects that should have been event handlers.',
        'sections': [
            {
                'h2': 'Effect vs event: the question I ask first',
                'paragraphs': [
                    'If something happens because the user clicked, put it in the click handler. If something synchronizes React with an external system such as document title, WebSocket, or a non-React widget, use an effect. I still see useEffect that saves draft form on every keystroke and hammers the API — that belongs behind a debounce in an event or a dedicated autosave hook with clear intent.',
                    'React docs pushed this mental model hard, and our bug rate dropped once we enforced it in review by asking what external system this is syncing.',
                    'Concrete number: on one form, autosave-via-effect fired about 40 requests per minute of typing. Moving to a debounced blur or interval save cut that to about 4 and removed a rate-limit incident on the draft endpoint.',
                ],
            },
            {
                'h2': 'The infinite loop starter pack',
                'paragraphs': [
                    'Classic: effect sets state that is also in the dependency array, without a guard. Or depending on an object or array literal created each render. Or depending on a function prop that the parent recreates every render.',
                    'I ask authors to log render counts for a few minutes when they suspect a loop. Seeing 200-plus renders per second in Strict Mode is a strong signal before the tab locks up.',
                ],
                'code': '// Loop: new options object every render → effect → setState → render → ...\nfunction Chart({ data }) {\n  const [series, setSeries] = useState([]);\n  const options = { animate: true }; // new reference each time\n\n  useEffect(() => {\n    setSeries(transform(data, options));\n  }, [data, options]);\n\n  return <Canvas series={series} />;\n}\n\n// Fix: depend on primitives / stable values\nuseEffect(() => {\n  setSeries(transform(data, { animate: true }));\n}, [data]);',
                'code_lang': 'javascript',
            },
            {
                'h2': 'Fetch without cleanup equals race',
                'paragraphs': [
                    'User switches from product 1 to product 2 quickly. Request 1 finishes after request 2 and overwrites state. I have watched this show the wrong product name in QA. AbortController in cleanup is the default fix.',
                    'If you cannot abort, at least ignore stale responses with an incrementing request id or a cancelled flag. The wrong-name bug shipped once because QA clicked slowly.',
                ],
                'code': "useEffect(() => {\n  const controller = new AbortController();\n  let cancelled = false;\n\n  async function load() {\n    try {\n      const res = await fetch(`/api/products/${id}`, { signal: controller.signal });\n      const json = await res.json();\n      if (!cancelled) setProduct(json);\n    } catch (err) {\n      if (err.name !== 'AbortError') setError(err);\n    }\n  }\n\n  load();\n  return () => {\n    cancelled = true;\n    controller.abort();\n  };\n}, [id]);",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Strict Mode double mount is not your enemy',
                'paragraphs': [
                    'In React 18-plus development, effects mount, clean up, and mount again to surface missing cleanup. Developers fix this by removing Strict Mode. That hides bugs. If your effect opens a socket or increments an analytics counter twice in dev, add proper cleanup and idempotent setup.',
                    'We once double-charged a metering API in production after a remount path we never tested — Strict Mode would have caught the missing cleanup in dev.',
                ],
            },
            {
                'h2': 'Derived state that should not be state',
                'paragraphs': [
                    'If you can compute fullName from first and last during render, do not store it in state updated by an effect. Effects for pure derivation add an extra paint and drift bugs. Same for filtering a list: derive during render or memoize if the list is huge. We only memoized after 5k-plus rows.',
                    'Prop-to-state sync effects are another smell. Prefer fully controlled components or remount with key equals id when you truly need fresh local state per entity.',
                ],
                'bullets': [
                    'Empty deps means once per mount — confirm that is intentional',
                    'Omit deps only with a documented eslint-disable and a reason',
                    'Cleanup subscriptions, timers, and in-flight fetches',
                    'Do not put React Query or SWR fetch solely in raw useEffect if the library already owns cache',
                    'Prefer keying a child to reset state instead of syncing props to state in effects',
                ],
            },
            {
                'h2': 'Subscriptions done right',
                'paragraphs': [
                    'Window listeners, IntersectionObserver, and media queries need subscribe in the effect and unsubscribe in cleanup. I also keep the handler stable or read latest values via a ref when the listener must stay registered once.',
                    'Forums still recommend empty deps plus eslint-disable for listeners that close over state. Prefer a ref for latest state: register once, read ref.current inside the handler. That avoids resubscribing on every render without lying about dependencies.',
                ],
                'code': "useEffect(() => {\n  function onResize() {\n    setWidth(window.innerWidth);\n  }\n  window.addEventListener('resize', onResize);\n  onResize();\n  return () => window.removeEventListener('resize', onResize);\n}, []);",
                'code_lang': 'javascript',
            },
            {
                'h2': 'Timers and intervals I keep rejecting',
                'paragraphs': [
                    'Polling with setInterval inside an effect without clearing it on unmount or dependency change leaks timers. I have seen tabs with dozens of intervals after soft navigation in an SPA shell.',
                    'Prefer setTimeout chains when the interval should wait for the previous fetch to finish, or use a library that owns polling. Always return clearInterval or clearTimeout from the effect cleanup.',
                ],
                'code': 'useEffect(() => {\n  let timer = null;\n  let stopped = false;\n\n  async function tick() {\n    await refreshInbox();\n    if (!stopped) timer = setTimeout(tick, 15000);\n  }\n\n  tick();\n  return () => {\n    stopped = true;\n    if (timer) clearTimeout(timer);\n  };\n}, []);',
                'code_lang': 'javascript',
            },
            {
                'h2': 'Data libraries versus hand-rolled effects',
                'paragraphs': [
                    'If the team already uses React Query or SWR, I reject new useEffect fetch for server state unless there is a clear gap. Those libraries handle caching, dedupe, retries, and cancellation. Re-implementing them poorly is how we got three different loading-state conventions in one app.',
                    'Effects still make sense for wiring: syncing a query result into a non-React map SDK, or writing document.title. Keep the boundary clear — server state in the library, external sync in effects. When migrating, replace one screen at a time and delete the old effect rather than leaving both paths.',
                ],
            },
            {
                'h2': 'Measuring before micro-optimizing effects',
                'paragraphs': [
                    'Not every effect that runs twice in Strict Mode is a production bug. I care when it hits the network, writes to analytics, or mutates a third-party widget. Cosmetic double logs in development are noise.',
                    'For expensive sync work after render, I check the Profiler. One optimize PR wrapped derived data in an effect to keep render pure and made the UI worse by delaying paint. We reverted and computed during render instead. Profile first, then decide whether an effect earns its keep.',
                ],
            },
            {
                'h2': 'What I write in the review comment',
                'paragraphs': [
                    'Is this syncing an external system? If not, move to the event handler. Will this race when id changes? What cleans this up under Strict Mode double invoke? Those three questions catch most of our useEffect defects before merge.',
                    'If the author cannot answer in one sentence, I ask them to delete the effect and try again. Roughly half the time the better design appears within minutes. I keep a short internal doc with before and after snippets of these patterns; linking it from the PR template cut repeat review comments by roughly half.',
                ],
            },
        ],
        'takeaways': [
            'Use effects for external synchronization, not for ordinary user-event logic.',
            'Unstable object or function dependencies are a common infinite-loop source.',
            'Abort in-flight fetches on cleanup to prevent racey setState.',
            'Strict Mode double mounting highlights missing cleanup — fix cleanup, do not remove Strict Mode.',
            'Prefer derived values during render over prop-to-state mirroring effects.',
            'Always clear timers and intervals in effect cleanup.',
        ],
    },
    {
        'slug': 'nextjs-app-router-data-fetching',
        'title': 'Next.js App Router Data Fetching: fetch, Cache, and revalidate Patterns',
        'description': 'Practical App Router patterns for cached fetch, revalidate, no-store dynamic data, and when I reach for Server Actions — based on shipping Next.js 14/15 apps.',
        'category': 'Frontend',
        'date': '2026-06-18',
        'read_min': 12,
        'keywords': 'Next.js App Router, fetch cache, revalidate, no-store, Server Components, Server Actions',
        'excerpt': 'App Router caching surprised us in production: a live admin page served stale inventory for 60 seconds. Here is how I choose fetch options on purpose.',
        'sections': [
            {
                'h2': 'Default mental model',
                'paragraphs': [
                    'In the App Router, fetch in Server Components can be cached and deduplicated. That is great for marketing pages and terrible for per-user dashboards if you leave defaults wrong. I treat every fetch as needing an explicit caching policy in code review.',
                    'Rule of thumb I use: public, slow-changing content gets cache plus revalidate. User-specific or money-adjacent data gets cache no-store or export const dynamic equals force-dynamic. Mixed pages get segment config plus tagged revalidation.',
                    'Next version upgrades sometimes change default caching behavior. After one upgrade, a previously dynamic route started caching. We now assert cache headers in an integration test for account routes so upgrades cannot silently flip policy.',
                ],
            },
            {
                'h2': 'Static-ish content with time-based revalidation',
                'paragraphs': [
                    'Blog indexes and pricing pages tolerate slight staleness. revalidate 60 means ISR-style refresh at most once per minute per deployment semantics. We saw TTFB drop from about 400ms to about 80ms on a docs landing page after caching the CMS fetch.',
                    'Do not use a 60-second window for content that editors expect to appear instantly. Either shorten revalidate for that segment or use on-demand tags. Mixing feels-live marketing copy with a 5-minute revalidate creates trust issues with the content team.',
                ],
                'code': "// app/blog/page.tsx\nasync function getPosts() {\n  const res = await fetch('https://cms.example.com/posts', {\n    next: { revalidate: 60, tags: ['posts'] },\n  });\n  if (!res.ok) throw new Error('Failed to load posts');\n  return res.json();\n}\n\nexport default async function BlogIndex() {\n  const posts = await getPosts();\n  return (\n    <ul>\n      {posts.map((p) => (\n        <li key={p.slug}>{p.title}</li>\n      ))}\n    </ul>\n  );\n}",
                'code_lang': 'typescript',
            },
            {
                'h2': 'On-demand revalidation with tags',
                'paragraphs': [
                    'When editors publish, waiting 60s is awkward. We tag fetches and call revalidateTag posts from a webhook Server Action or route handler after CMS publish. That cut where-is-my-post support pings to near zero.',
                    'Protect the webhook with a shared secret and rate limiting. An open revalidate endpoint is a cheap DoS against your origin and cache.',
                ],
                'code': "// app/api/revalidate/route.ts\nimport { revalidateTag } from 'next/cache';\nimport { NextRequest, NextResponse } from 'next/server';\n\nexport async function POST(req: NextRequest) {\n  const secret = req.headers.get('x-revalidate-secret');\n  if (secret !== process.env.REVALIDATE_SECRET) {\n    return NextResponse.json({ ok: false }, { status: 401 });\n  }\n  revalidateTag('posts');\n  return NextResponse.json({ revalidated: true });\n}",
                'code_lang': 'typescript',
            },
            {
                'h2': 'Dynamic user data',
                'paragraphs': [
                    "Account pages that read session cookies must not serve another user's cache entry. I use cache no-store on those fetches and read auth in the server component. Alternatively set dynamic to force-dynamic at the route segment.",
                    "The inventory bug I mentioned: we had cached fetch to /api/stock without realizing the route was shared. Two users saw each other's warehouse counts briefly. Fix was no-store plus moving stock behind an authenticated route handler.",
                    'After the fix we added a regression test that fetches the same route as two sessions and asserts different bodies. Cache bugs are silent without tests like that.',
                ],
                'code': "async function getBalance(userId: string) {\n  const res = await fetch(`${process.env.API_URL}/balance/${userId}`, {\n    cache: 'no-store',\n    headers: { Authorization: `Bearer ${process.env.INTERNAL_TOKEN}` },\n  });\n  return res.json();\n}",
                'code_lang': 'typescript',
            },
            {
                'h2': 'Server Actions for mutations',
                'paragraphs': [
                    'I use Server Actions for form posts that do not need a separate REST surface: update profile, create comment, toggle flag. Keep them thin — validate with Zod, call a service function, revalidate tags, redirect.',
                    'Do not put complex business logic only inside the action file if other entry points such as API routes and jobs need the same rules. Extract a shared service so authorization checks stay consistent.',
                ],
                'code': "'use server';\n\nimport { z } from 'zod';\nimport { revalidatePath } from 'next/cache';\nimport { updateDisplayName } from '@/server/users';\n\nconst schema = z.object({\n  displayName: z.string().trim().min(2).max(80),\n});\n\nexport async function saveProfile(formData: FormData) {\n  const parsed = schema.safeParse({\n    displayName: formData.get('displayName'),\n  });\n  if (!parsed.success) return { error: 'invalid_name' };\n\n  await updateDisplayName(parsed.data.displayName);\n  revalidatePath('/settings/profile');\n  return { ok: true };\n}",
                'code_lang': 'typescript',
            },
            {
                'h2': 'Streaming and Suspense boundaries',
                'paragraphs': [
                    'For pages with a fast shell and a slow panel I wrap the slow Server Component in Suspense so the shell streams first. Users see navigation chrome and a skeleton while the slow fetch completes. That improved perceived performance even when total time-to-full-content stayed similar.',
                    'I avoid putting the entire page behind one slow await at the top of the tree. A single blocking await getEverything defeats streaming. Split fetches by section. Error boundaries around streamed sections stop one failing widget from blanking the whole route — we learned that when recommendations 500ed and took the product page down.',
                ],
            },
            {
                'h2': 'Auth cookies and the cache',
                'paragraphs': [
                    'Reading cookies in a layout opts routes into dynamic rendering. That is correct for dashboards and easy to forget on a shared root layout that also wraps marketing pages. We split layouts so public marketing stays statically cacheable while app routes stay dynamic.',
                    'If you must read cookies deep in a tree, be intentional about which segments inherit dynamic behavior. Accidental dynamic marketing pages raised origin load and erased the TTFB wins from ISR.',
                ],
                'code': '// app/(marketing)/layout.tsx — no cookies(), cache-friendly\nexport default function MarketingLayout({ children }) {\n  return <div className="marketing">{children}</div>;\n}\n\n// app/(app)/layout.tsx — auth-aware, dynamic\nimport { cookies } from \'next/headers\';\n\nexport default async function AppLayout({ children }) {\n  const session = cookies().get(\'access_token\');\n  return <AppShell signedIn={Boolean(session)}>{children}</AppShell>;\n}',
                'code_lang': 'typescript',
            },
            {
                'h2': 'Client fetch versus Server Components',
                'paragraphs': [
                    'I keep initial data on the server when SEO or first paint matters. Client components use SWR or React Query for interactive polling filters. Duplicating the same REST call on server and client without a shared contract caused drift — we now generate types from OpenAPI and share the path helpers.',
                    'Server Actions work well for mutations with progressive enhancement. I still validate on the server with Zod; never trust the action payload shape alone.',
                ],
                'bullets': [
                    'Be explicit: revalidate, no-store, or force-dynamic',
                    'Tag cached fetches for webhook-driven updates',
                    'Never cache personalized responses under a shared key',
                    'Prefer Server Components for first paint; client libraries for live interactivity',
                    'Protect revalidate endpoints with a secret',
                    'Regression-test personalized routes across two sessions',
                ],
            },
            {
                'h2': 'Debugging why is this stale',
                'paragraphs': [
                    'Check whether you are looking at the Full Route Cache, the Data Cache, or the browser cache. Next.js Dev overlay and logging fetch cache hits in development help. In one case the CDN in front of us cached HTML despite no-store on fetch — we had to set Cache-Control on the response headers from the route.',
                    'Document the caching choice in a one-line comment above non-obvious fetches. My incident checklist order: response headers from the browser, Next fetch cache tags, CDN purge, whether the deploy rolled out to all regions. Skipping the CDN step wasted an hour once. When in doubt I draw three boxes — Data Cache, Full Route Cache, CDN — and mark where the stale bytes live.',
                ],
            },
        ],
        'takeaways': [
            'Treat every App Router fetch as needing an explicit cache policy.',
            'Use time-based revalidate for public content; tags for editor-driven updates.',
            'Personalized and financial data should use no-store or force-dynamic.',
            'Server Components for initial HTML; client caches for interactive freshness.',
            'Stale bugs can live in Next caches, the browser, or your CDN — check all three.',
            'Validate Server Action input with Zod and share business logic with other entry points.',
        ],
    },
    {
        'slug': 'postgresql-indexes-explained',
        'title': 'PostgreSQL Indexes Explained: When B-tree Helps, When It Hurts',
        'description': 'How I decide to add B-tree indexes, read EXPLAIN ANALYZE, and avoid write-heavy indexes that slowed our API more than they helped.',
        'category': 'Databases',
        'date': '2026-06-21',
        'read_min': 12,
        'keywords': 'PostgreSQL indexes, B-tree, EXPLAIN ANALYZE, query performance, index selectivity, Postgres',
        'excerpt': 'I added five indexes in a panic once and made writes 3 times slower. Now I only ship indexes backed by EXPLAIN ANALYZE and a workload note.',
        'sections': [
            {
                'h2': 'What a B-tree index is paying for',
                'paragraphs': [
                    'A B-tree index is a sorted structure Postgres maintains beside the heap table. Point lookups and range scans on the indexed columns become logarithmic instead of sequential. The cost: every INSERT, UPDATE, and DELETE must update matching indexes. On a busy events table we saw insert latency climb from about 2ms to about 7ms p95 after blindly indexing six columns just in case.',
                    'Low-cardinality columns such as is_active boolean alone rarely deserve a standalone B-tree. Postgres may still seq-scan if half the rows match. Composite or partial indexes are usually smarter.',
                    'I keep a spreadsheet of candidate indexes with query from APM, current p95, estimated rows, proposed definition, and write-path impact. If we cannot fill those cells, we do not create the index yet.',
                ],
            },
            {
                'h2': 'EXPLAIN ANALYZE before and after',
                'paragraphs': [
                    'I never argue about indexes without plans. EXPLAIN ANALYZE BUFFERS on a production-sized copy or anonymized dump shows actual time and whether an Index Scan or Bitmap Index Scan appeared.',
                    'Watch for Seq Scan on multi-million-row tables with a selective WHERE, and for Index Scan that still filters most rows because the index does not match the predicate well. Also compare shared hit versus read buffers — an index that lives in RAM behaves differently under cold cache.',
                ],
                'code': "EXPLAIN (ANALYZE, BUFFERS)\nSELECT *\nFROM orders\nWHERE customer_id = 48291\n  AND created_at >= NOW() - INTERVAL '30 days'\nORDER BY created_at DESC\nLIMIT 50;",
                'code_lang': 'sql',
            },
            {
                'h2': 'Composite order matters',
                'paragraphs': [
                    'For the query above, customer_id then created_at DESC matches equality then sort or range. created_at then customer_id is weaker for that filter pattern. I think of leftmost prefix rules the same way I did with MySQL years ago — still valid for default B-tree.',
                    'After adding CREATE INDEX CONCURRENTLY on orders for customer_id and created_at DESC, that query dropped from 180ms to 4ms on a 12M-row table. CONCURRENTLY mattered because a blocking CREATE INDEX locked writes for minutes in staging.',
                    'INCLUDE columns helped another report query avoid heap fetches: we included status and total_cents so the index-only scan answered the list view. Measure heap fetches in EXPLAIN before celebrating.',
                ],
                'code': "-- Prefer concurrent builds in production\nCREATE INDEX CONCURRENTLY idx_orders_customer_created\n  ON orders (customer_id, created_at DESC);\n\n-- Partial index: only open tickets (smaller, faster)\nCREATE INDEX CONCURRENTLY idx_tickets_open_assignee\n  ON tickets (assignee_id)\n  WHERE status = 'open';",
                'code_lang': 'sql',
            },
            {
                'h2': 'When indexes hurt',
                'paragraphs': [
                    'Write-heavy tables with indexes unused by queries are pure overhead. Functions wrapping columns such as LOWER(email) cannot use a plain email index unless you create an expression index on LOWER(email). Leading wildcards in LIKE will not use a normal B-tree; consider pg_trgm when search needs it.',
                    'Too many overlapping indexes confuse the planner and waste cache. I audit with pg_stat_user_indexes for idx_scan equals zero after a meaningful period of weeks, not hours.',
                    'On the events table, dropping three unused indexes brought insert p95 from about 7ms back to about 3ms and freed roughly 18GB of disk. Writes improved more than any read path suffered.',
                ],
                'bullets': [
                    'Measure with EXPLAIN ANALYZE on realistic data volumes',
                    'Match composite column order to filter plus sort patterns',
                    'Prefer partial indexes for common status filters',
                    'Build CONCURRENTLY in prod to avoid long write locks',
                    'Drop unused indexes after watching idx_scan',
                ],
            },
            {
                'h2': 'Finding dead indexes in production',
                'paragraphs': [
                    'After two weeks of real traffic, I query pg_stat_user_indexes joined to pg_class for size. Anything with zero scans and non-trivial size goes on a drop candidate list. I exclude brand-new indexes and unique constraints that enforce correctness even if rarely used for reads.',
                    'I drop one at a time during low traffic, watch APM for a week, then continue. Never bulk-drop six indexes before a holiday weekend.',
                ],
                'code': "SELECT\n  schemaname || '.' || relname AS table,\n  indexrelname AS index,\n  idx_scan,\n  pg_size_pretty(pg_relation_size(indexrelid)) AS size\nFROM pg_stat_user_indexes\nJOIN pg_class ON pg_class.oid = indexrelid\nWHERE idx_scan = 0\nORDER BY pg_relation_size(indexrelid) DESC\nLIMIT 20;",
                'code_lang': 'sql',
            },
            {
                'h2': 'Unique constraints are indexes too',
                'paragraphs': [
                    'A UNIQUE constraint creates a unique B-tree. I do not also add a redundant non-unique index on the same columns. I have reviewed migrations that created both and paid double write cost for no gain.',
                    'Partial unique indexes are excellent for soft-delete: unique on email where deleted_at is null lets you reuse emails after delete without complicated application checks. That pattern replaced a flaky app-level race we had for years.',
                ],
                'code': 'CREATE UNIQUE INDEX CONCURRENTLY idx_users_email_active\n  ON users (email)\n  WHERE deleted_at IS NULL;',
                'code_lang': 'sql',
            },
            {
                'h2': 'Maintenance I schedule',
                'paragraphs': [
                    'Autovacuum usually keeps things healthy; bloated indexes after bulk deletes sometimes need REINDEX CONCURRENTLY. We alert when table bloat estimates cross a threshold rather than reindexing on a fixed calendar.',
                    'Foreign keys deserve indexes on the referencing column — not only for reads, but so ON DELETE cascades do not seq-scan children. Missing FK indexes caused a 40-second delete of a parent org row in one tenancy cleanup job.',
                ],
            },
            {
                'h2': 'Staging with production-shaped data',
                'paragraphs': [
                    'Plans flip with scale. On 50k rows almost everything looks fine. On 20M rows the planner chooses differently. I refresh a sanitized staging DB from production weekly for index experiments, with PII scrubbed.',
                    'I run EXPLAIN ANALYZE at least three times and discard the coldest run when comparing. Then I test under a light write load because an index that helps a read-only session can still hurt the API when inserts contend on the same pages. Uniform random foreign keys produce unrealistically perfect indexes; real customers cluster.',
                ],
            },
            {
                'h2': 'Monitoring after ship',
                'paragraphs': [
                    'After creating an index I watch query p95 from APM, insert and update p95 on the table, index size growth, and vacuum activity. A week of green metrics earns a note in the runbook; a write regression earns a revert even if the read looks prettier.',
                    'I also check whether the planner actually uses the new index. Creating an index that never gets selected is pure cost. Sometimes statistics are stale — running ANALYZE on the table fixed a stubborn seq scan after a bulk import more than once.',
                ],
            },
            {
                'h2': 'A small decision framework',
                'paragraphs': [
                    'Slow query in APM, capture SQL, run EXPLAIN ANALYZE, if seq scan on large table and selective filter then design minimal index, create concurrently on staging, compare plans and write p95, then ship. If the filter returns more than 20 to 30 percent of the table, rethink; a seq scan may already be optimal.',
                    'Ship the smallest index that changes the plan. You can always add INCLUDE columns later; removing a wide unused index under write load is harder socially than technically. After creating an index I watch query p95, insert p95, index size growth, and whether the planner actually uses it — ANALYZE after bulk imports if plans look stuck.',
                ],
            },
        ],
        'takeaways': [
            'Indexes speed reads and tax writes — prove the trade with EXPLAIN ANALYZE.',
            'Composite column order should follow equality filters then range or sort.',
            'Partial and expression indexes beat scattershot single-column indexes.',
            'Use CREATE INDEX CONCURRENTLY in production.',
            'Audit idx_scan and remove indexes that never earn their keep.',
            'Index foreign key columns so deletes and joins do not seq-scan children.',
        ],
    },
    {
        'slug': 'git-rebase-vs-merge',
        'title': 'Git Rebase vs Merge: A Safe Workflow We Use on Feature Branches',
        'description': 'When I rebase, when I merge, how we avoid rewriting shared history, and the exact commands for a clean PR timeline.',
        'category': 'Developer Tools',
        'date': '2026-06-25',
        'read_min': 12,
        'keywords': 'git rebase vs merge, interactive rebase, feature branch workflow, git pull --rebase, safe git history',
        'excerpt': 'Rebase versus merge is not religion on our team. It is about whether the commits are private and whether we want a linear PR.',
        'sections': [
            {
                'h2': 'The rule that prevents disasters',
                'paragraphs': [
                    'Never rebase commits that other people already pulled. Rebase rewrites SHAs. If main or a shared long-lived branch gets rebased, teammates must recover with reset and rebase gymnastics. We only rebase local feature branches that we own.',
                    'Merge commits preserve exact history and branching topology. Rebase replays your commits on top of an updated base for a straight-line story. Both are valid; mixing them without a team convention is what hurts.',
                    'We wrote this as a one-page CONTRIBUTING rule after a shared-branch rewrite burned about four engineer-hours in a single afternoon. Conventions beat cleverness here.',
                ],
            },
            {
                'h2': 'Daily sync: pull --rebase on feature branches',
                'paragraphs': [
                    'While building a feature, I keep my branch current with git fetch origin and git rebase origin/main, or git pull --rebase origin main. That surfaces conflicts early in small chunks instead of one monster merge at PR time.',
                    'We set pull.rebase true locally for feature work. Shared release branches still merge.',
                    'I rebase at least once a day on long features. Waiting a week means resolving the same conflict across many commits. Early rebases took me about 5 minutes; late ones took over an hour on a billing branch that touched shared types.',
                ],
                'code': '# Update feature branch onto latest main\ngit fetch origin\ngit switch feature/billing-retry\ngit rebase origin/main\n\n# If conflicts: fix files, then\ngit add .\ngit rebase --continue\n\n# Abort if it goes sideways\ngit rebase --abort',
                'code_lang': 'bash',
            },
            {
                'h2': 'Cleaning the story before review',
                'paragraphs': [
                    'Before requesting review I often run interactive rebase onto origin/main and squash wip and fix typo commits into logical units. Reviewers get 3 commits that mean something instead of 27 noise commits. Force-push is required afterward — only on my feature branch, and we use --force-with-lease so I do not clobber unexpected remote commits.',
                    'I aim for commits that each leave tests green. Reviewers can bisect later if something regresses. A single giant squash of a week of work is fine for tiny PRs; for multi-day features I keep a short narrative.',
                ],
                'code': 'git rebase -i origin/main\n# mark commits as squash/fix/reword\n\ngit push --force-with-lease origin feature/billing-retry',
                'code_lang': 'bash',
            },
            {
                'h2': 'Merging into main',
                'paragraphs': [
                    'On GitHub we usually Squash and merge for small PRs so main stays linear with one commit per feature. For larger multi-commit PRs that tell a deliberate story, we use merge commits or rebase-and-merge depending on the repo setting.',
                    'I avoid rebasing main onto a feature branch in public view. The integration direction is: update feature onto main, then merge feature into main via the PR UI.',
                    'Release branches freeze with merge-only. Hotfixes branch from the release tag, merge back to release and to main. Trying to rebase a hotfix that QA already tested is how you get works-on-my-machine checksum mismatches.',
                ],
            },
            {
                'h2': 'When merge is the better tool',
                'paragraphs': [
                    'Long-running release branches, hotfixes already shared, and any branch multiple people push to — merge. Also when you need to preserve the exact fact that two lines of development coexisted; compliance and audit trails sometimes care.',
                    'A teammate once rebased a shared develop branch to clean history and burned half a day of engineering time. We wrote the rule down after that.',
                ],
                'bullets': [
                    'Private feature branch — rebase onto main is fine',
                    'Shared branch — merge only',
                    'Force push only with --force-with-lease on your branch',
                    'Resolve conflicts during rebase carefully; abort when unsure',
                    'Prefer early rebases over one giant conflict at the end',
                    'Release and hotfix branches stay merge-only',
                ],
            },
            {
                'h2': 'Recovering when a rebase goes wrong',
                'paragraphs': [
                    'git rebase --abort is the first escape hatch if you are still mid-rebase. If you already finished and force-pushed something bad, git reflog usually still has the previous tip for a while. I restore with git reset --hard ORIG_HEAD immediately after a bad rebase, or HEAD@{1} from reflog when ORIG_HEAD is gone.',
                    'Tell anyone who pulled the bad tip to reset to the restored SHA. Communication matters more than the exact command once history diverged on a shared remote.',
                ],
                'code': '# Still in a rebase?\ngit rebase --abort\n\n# Just finished a bad rebase, not pushed yet\ngit reset --hard ORIG_HEAD\n\n# Already pushed; recover tip from reflog, then force-with-lease\ngit reflog\ngit reset --hard HEAD@{1}\ngit push --force-with-lease origin feature/billing-retry',
                'code_lang': 'bash',
            },
            {
                'h2': 'What we tell new teammates on day one',
                'paragraphs': [
                    'Update your feature branch with rebase onto main. Open PRs from feature into main. Never force-push main. Never rebase a branch two people are committing to. When unsure, merge and ask in Slack — a merge commit is cheap compared with rewriting shared history.',
                    'We pair on the first interactive rebase. Squash, fixup, and reword are muscle memory after one guided session; without that session people either never clean history or force-push scared. CI must be green after rebase before review.',
                ],
            },
            {
                'h2': 'PR UI settings we standardize',
                'paragraphs': [
                    'Repos that prefer a linear main enable Allow squash merging and disable merge commits, or enable rebase-merging carefully. Mixed settings across repos confused people about whether they should clean locally.',
                    'Required status checks on main mean a force-pushed feature branch re-runs CI. That is good. I wait for green after force-with-lease before pinging reviewers again so they do not review an already-superseded SHA. Branch protection on main rejects force pushes; feature branches stay unprotected so rebase workflows work.',
                ],
                'bullets': [
                    'Protect main against force push and direct commits',
                    'Allow force-with-lease on personal feature branches',
                    'Re-run CI after every rebase push',
                    'Agree repo-wide on squash versus merge versus rebase-merge',
                ],
            },
            {
                'h2': 'Bisect loves clean history',
                'paragraphs': [
                    'When a production bug lands, git bisect across squash-merged main finds the PR quickly. Across a week of WIP commits on a long-lived branch, bisect lands on wip fix again and wastes time. That is a practical reason we clean feature history before merge, not an aesthetic one.',
                    'If you must keep fine-grained commits on main for blame archaeology, say so in the repo guide and use merge or rebase-merge consistently. Silent policy differences between teams sharing a monorepo cause the worst arguments. Default stance on our team: rebase privately, merge publicly through the PR button, recover with reflog, and optimize for bisectable main.',
                ],
            },
            {
                'h2': 'Conflict survival tips',
                'paragraphs': [
                    'During rebase, conflicted files are your commit applied onto newer main. Read both sides. Run tests after continue. If the same conflict repeats across commits, consider squashing first so you fix it once.',
                    'For binary files or generated lockfile hell, sometimes aborting, merging main into the feature branch once, and fixing lockfiles in a single merge commit is less painful than rebasing 15 lockfile bumps. Pragmatism beats purity.',
                    'I keep a sticky note of files that always conflict such as generated GraphQL types and lockfiles. For those, I regenerate from source after resolving rather than hand-merging thousands of lines. Bisect loves clean history on main — that is a practical reason we clean feature history before merge, not an aesthetic one.',
                ],
            },
        ],
        'takeaways': [
            'Rebase private feature branches; never rewrite shared history.',
            'Pull with rebase to catch conflicts early while commits are fresh.',
            'Interactive rebase before review to remove WIP noise.',
            'Use --force-with-lease, not bare --force, when updating a feature remote.',
            'Choose squash, merge, or rebase-merge at PR time based on the story you want on main.',
            'Know rebase --abort and reflog recovery before you need them under pressure.',
        ],
    },
    {
        'slug': 'typescript-generics-practical-guide',
        'title': 'Practical TypeScript Generics for APIs and React Props',
        'description': 'Generics that earn their keep: typed API clients, reusable React list props, constraints, and the mistakes that made our types worse than any.',
        'category': 'Frontend',
        'date': '2026-06-28',
        'read_min': 12,
        'keywords': 'TypeScript generics, React props generics, typed fetch, generic constraints, TypeScript API client',
        'excerpt': 'I ignored generics for years and sprinkled as casts instead. Once we typed our API client and a few shared components properly, a whole class of production bugs became compile errors.',
        'sections': [
            {
                'h2': 'Start from a pain point, not from theory',
                'paragraphs': [
                    'Our untyped api.get to /users returned Promise any. Call sites assumed name existed; the backend renamed it to fullName. Runtime crash, green CI. A generic get T would have forced the call site to declare the expected shape — still a contract, but now checked when we updated shared types from OpenAPI.',
                    'Generics are functions and types parameterized by other types. I introduce them when the same logic works for multiple shapes and I want the output type to follow the input.',
                    'After we generated types from OpenAPI and threaded them through apiGet User, that class of rename bugs became tsc failures in CI. We caught three similar mismatches in the first month — all would have been production 500s before.',
                ],
            },
            {
                'h2': 'Typed fetch wrapper',
                'paragraphs': [
                    'This is the first generic I add to every TypeScript frontend. The caller passes the response type; errors stay explicit.',
                    'I also add apiPost with body and response type parameters so request bodies are checked. Without that, we typed responses carefully and still sent wrong payloads.',
                ],
                'code': "export class ApiError extends Error {\n  constructor(public status: number, message: string) {\n    super(message);\n  }\n}\n\nexport async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {\n  const res = await fetch(path, {\n    ...init,\n    headers: { Accept: 'application/json', ...init?.headers },\n  });\n  if (!res.ok) {\n    throw new ApiError(res.status, await res.text());\n  }\n  return res.json() as Promise<T>;\n}\n\n// usage\ntype User = { id: string; fullName: string };\nconst user = await apiGet<User>('/api/users/me');\nconsole.log(user.fullName);",
                'code_lang': 'typescript',
            },
            {
                'h2': 'Constraints beat unconstrained T',
                'paragraphs': [
                    'If you need to read id inside the generic function, constrain T. Unconstrained T cannot safely access properties — and if you cast anyway, you lied to the compiler.',
                    'Multiple constraints use intersection types. Keep them readable; if the constraint needs three lines, extract a named interface.',
                ],
                'code': "function byId<T extends { id: string }>(items: T[], id: string): T | undefined {\n  return items.find((item) => item.id === id);\n}\n\nconst users = [\n  { id: '1', fullName: 'Ram' },\n  { id: '2', fullName: 'Ada' },\n];\nconst found = byId(users, '2'); // type includes fullName",
                'code_lang': 'typescript',
            },
            {
                'h2': 'React props that preserve item types',
                'paragraphs': [
                    'Shared Select and Table components often erase types with items any array. A generic component keeps item type through render props.',
                    'Inference usually works when items is passed inline. If TypeScript widens to a useless type, pass an explicit type argument once. Prefer inference first.',
                ],
                'code': 'type ListProps<T> = {\n  items: T[];\n  keyOf: (item: T) => string;\n  children: (item: T) => React.ReactNode;\n};\n\nexport function List<T>({ items, keyOf, children }: ListProps<T>) {\n  return (\n    <ul>\n      {items.map((item) => (\n        <li key={keyOf(item)}>{children(item)}</li>\n      ))}\n    </ul>\n  );\n}\n\n// inference works — item is User inside children\n<List\n  items={users}\n  keyOf={(u) => u.id}\n  children={(u) => <span>{u.fullName}</span>}\n/>;',
                'code_lang': 'tsx',
            },
            {
                'h2': 'Defaults and keyof patterns',
                'paragraphs': [
                    'Generic defaults help when most call sites share a type. keyof plus mapped types power type-safe sorting helpers. I keep these shallow — deep conditional type wizardry slowed our compile times and confused juniors more than it helped.',
                    'A Pick or Omit wrapper around API responses is often clearer than a custom conditional type. Reach for the built-ins before inventing a new type-level DSL.',
                ],
                'code': "function sortBy<T, K extends keyof T>(items: T[], key: K): T[] {\n  return [...items].sort((a, b) => (a[key] > b[key] ? 1 : -1));\n}\n\nsortBy(users, 'fullName');\n// sortBy(users, 'nope'); // compile error",
                'code_lang': 'typescript',
            },
            {
                'h2': 'Result types instead of throwing everywhere',
                'paragraphs': [
                    'Another place generics shine is a small Result T E for expected failures. Call sites must handle ok false instead of hoping a try/catch exists three layers up.',
                    'We use this for form validation and for API calls that can 404 without being exceptional. Throwing remains for truly unexpected failures.',
                ],
                'code': "type Result<T, E = string> =\n  | { ok: true; value: T }\n  | { ok: false; error: E };\n\nasync function loadUser(id: string): Promise<Result<User, 'not_found' | 'network'>> {\n  try {\n    const user = await apiGet<User>(`/api/users/${id}`);\n    return { ok: true, value: user };\n  } catch (err) {\n    if (err instanceof ApiError && err.status === 404) {\n      return { ok: false, error: 'not_found' };\n    }\n    return { ok: false, error: 'network' };\n  }\n}",
                'code_lang': 'typescript',
            },
            {
                'h2': 'Generic hooks without pain',
                'paragraphs': [
                    'Custom hooks benefit from generics the same way components do. useLocalStorage T should return T or undefined and accept values that know T. Without that, every call site casts.',
                    'I keep hook generics to one or two type parameters. When a hook needs four type params, it is usually doing too much and should split into smaller hooks or accept a typed adapter object.',
                ],
                'code': "function useLocalStorage<T>(key: string, initial: T) {\n  const [value, setValue] = useState<T>(() => {\n    if (typeof window === 'undefined') return initial;\n    const raw = window.localStorage.getItem(key);\n    return raw ? (JSON.parse(raw) as T) : initial;\n  });\n\n  useEffect(() => {\n    window.localStorage.setItem(key, JSON.stringify(value));\n  }, [key, value]);\n\n  return [value, setValue] as const;\n}\n\nconst [draft, setDraft] = useLocalStorage<{ fullName: string }>('draft', { fullName: '' });",
                'code_lang': 'typescript',
            },
            {
                'h2': 'Mapping API DTOs to domain types',
                'paragraphs': [
                    'Generated OpenAPI types are often noisy. I write small mappers such as toUser from UserDto. Generics help for lists when composed, but inventing a hyper-abstract Mapper with four type params helped nobody. We deleted one of those frameworks after onboarding stalled.',
                    'Zod schemas can infer types with z.infer typeof schema, which often removes the need for a hand-written interface plus a generic parse helper. I prefer schema-first when validation already exists at the boundary.',
                ],
            },
            {
                'h2': 'Mistakes that made types worse',
                'paragraphs': [
                    'Defaulting T to any silently undoes safety. Over-generic components with five type params nobody can invoke. Returning T or any from a helper. Using generics where a simple union of two shapes was clearer.',
                    'We also abused React.FC with generics inconsistently; nowadays we type props directly on the function. Measure complexity: if the generic needs a paragraph of explanation in the PR, consider two named functions instead.',
                    'Compile-time cost is real. A few heavy conditional types in hot paths added seconds to tsc on our monorepo. We simplified and CI got about 20 percent faster on the typecheck job. My bar for merging a new generic helper: at least three call sites, a constraint that matches real field access, and a PR description that shows a before/after compile error it prevents.',
                ],
                'bullets': [
                    'Add generics when output types should track input types',
                    'Constrain with extends when you read properties',
                    'Prefer inference at call sites over mandatory type arguments',
                    'Avoid defaulting T to any',
                    'Generate API types when possible instead of hand-rolling large interfaces',
                    'Prefer Result or union handling for expected failures over unchecked throws',
                ],
            },
        ],
        'takeaways': [
            'A generic apiGet T turns silent any into checked contracts at call sites.',
            'Use extends constraints when the generic body reads fields.',
            'Generic React list and select components preserve item types through callbacks.',
            'keyof patterns catch invalid field names at compile time.',
            'Keep generics shallow — unclear type params are worse than a bit of duplication.',
            'Result T E makes expected failure paths visible at the type level.',
        ],
    },
]
