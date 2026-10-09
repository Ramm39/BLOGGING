ARTICLES = [{'slug': 'how-to-fix-cors-errors',
  'title': 'How to Fix CORS Errors in Browser APIs (Preflight, Credentials, and Proxies)',
  'description': 'A practical playbook for diagnosing Access-Control-Allow-Origin failures, fixing OPTIONS '
                 'preflight, cookie credentials, and Vite/Express proxy setups.',
  'category': 'Backend',
  'date': '2026-06-02',
  'updated': '2026-10-09',
  'read_min': 11,
  'keywords': 'CORS errors, Access-Control-Allow-Origin, preflight OPTIONS, credentials cookies, Express '
              'CORS, Vite proxy',
  'excerpt': 'CORS can turn a 20-minute feature into a two-hour rabbit hole. Here is a checklist for when '
             'the browser blocks a fetch that works fine in curl.',
  'sections': [{'h2': 'What the browser actually blocked',
                'paragraphs': ['The typical report: a dashboard works in Postman and fails in Chrome with '
                               '“blocked by CORS policy” on https://api.example.com/me from origin '
                               'http://localhost:5173. Curl returns 200. The API is fine. The browser is '
                               'enforcing the same-origin policy on a cross-origin fetch.',
                               'CORS is not authentication. It is a browser gate: the server must opt in to '
                               'being readable by a specific origin. If you only test with curl, Insomnia, '
                               'or server-to-server calls, you will never see the failure. Reproduce every '
                               'failing request in DevTools Network with Preserve log on before you touch '
                               'middleware.',
                               'Read the Console message carefully. Chrome often says the response to the '
                               'preflight request does not pass access control, which means you are '
                               'debugging OPTIONS, not GET. Note the exact Origin header so you do not fix '
                               'the wrong host after a port change from 5173 to 5174.']},
               {'h2': 'Simple requests vs preflight',
                'paragraphs': ['A GET or POST with Content-Type application/x-www-form-urlencoded, '
                               'multipart/form-data, or text/plain, and no custom headers, can be a simple '
                               'request. Everything else triggers a preflight: an OPTIONS request before the '
                               'real method.',
                               'JSON APIs almost always preflight, because they send Content-Type: '
                               'application/json and often Authorization. If OPTIONS is not handled, Chrome '
                               'shows a CORS error even though the real route would have returned 200. The '
                               'fix is an OPTIONS handler or CORS middleware that answers preflight.',
                               'Watch for frameworks that only register GET/POST and return 404 for OPTIONS. '
                               'NestJS, Express routers with strict method lists, and API gateways that '
                               'block unknown methods all produce the same symptom. A load balancer can also '
                               'return 405 for OPTIONS before Node ever sees the request — then the fix '
                               'belongs at the load balancer, not in Express.'],
                'code': '// Express: answer preflight explicitly if you are not using cors()\n'
                        '// Express 5 requires a named wildcard (*splat); a bare /api/* throws at startup\n'
                        "app.options('/api/*splat', (req, res) => {\n"
                        "  res.setHeader('Access-Control-Allow-Origin', 'http://localhost:5173');\n"
                        "  res.setHeader('Access-Control-Allow-Methods', "
                        "'GET,POST,PUT,PATCH,DELETE,OPTIONS');\n"
                        "  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');\n"
                        "  res.setHeader('Access-Control-Max-Age', '7200'); // Chromium caps at 7200s; "
                        'Firefox at 86400s\n'
                        '  res.sendStatus(204);\n'
                        '});',
                'code_lang': 'javascript'},
               {'h2': 'The credentials trap',
                'paragraphs': ['When the frontend needs cookies with credentials include in fetch, or '
                               'withCredentials true in Axios, the server cannot respond with '
                               'Access-Control-Allow-Origin as a wildcard. It must echo a specific origin '
                               'and set Access-Control-Allow-Credentials true.',
                               'Two easy misses: setting origin: true in the cors package but forgetting '
                               'credentials on the client, so cookies never arrive; or configuring both '
                               'sides correctly but leaving SameSite=Strict on a cross-site cookie, so CORS '
                               'looks fixed while the session stays empty. Check Set-Cookie attributes in '
                               'the response headers, not only ACAO.',
                               '“Logged in, then immediately logged out” reports on a SPA are very often '
                               'cookie-attribute mismatches rather than bad JWT secrets, and DevTools '
                               'usually shows a SameSite warning. For a genuinely cross-site API host, the '
                               'cookie needs SameSite=None; Secure.'],
                'code': '// Client\n'
                        "fetch('https://api.example.com/me', {\n"
                        "  method: 'GET',\n"
                        "  credentials: 'include',\n"
                        '  // No Content-Type on a bodiless GET: it would force a preflight for nothing\n'
                        '});\n'
                        '\n'
                        '// Server (cors package)\n'
                        "import cors from 'cors';\n"
                        'app.use(cors({\n'
                        "  origin: ['http://localhost:5173', 'https://app.example.com'],\n"
                        '  credentials: true,\n'
                        "  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],\n"
                        "  allowedHeaders: ['Content-Type', 'Authorization'],\n"
                        '}));',
                'code_lang': 'javascript'},
               {'h2': 'Local fix: Vite proxy instead of fighting CORS',
                'paragraphs': ['For local development, prefer same-origin requests through a Vite or Next '
                               'proxy. The browser talks to http://localhost:5173/api/... and Vite forwards '
                               'to the real API. No CORS headers are required locally because the page '
                               'origin matches the request origin.',
                               'It is a good default for any greenfield SPA. Production still needs real '
                               'CORS or a gateway on the same domain. The proxy is a developer-ergonomics '
                               'tool, not a production security model.',
                               'One footgun: if your API already prefixes routes with /api and Vite also '
                               'mounts at /api, you may double-prefix after a rewrite. Log the proxied URL '
                               'once at startup. Also set changeOrigin: true when the upstream checks Host '
                               'headers; without it some frameworks reject the request before CORS '
                               'middleware runs.'],
                'code': '// vite.config.ts\n'
                        "import { defineConfig } from 'vite';\n"
                        "import react from '@vitejs/plugin-react';\n"
                        '\n'
                        'export default defineConfig({\n'
                        '  plugins: [react()],\n'
                        '  server: {\n'
                        '    proxy: {\n'
                        "      '/api': {\n"
                        "        target: 'http://localhost:4000',\n"
                        '        changeOrigin: true,\n'
                        '      },\n'
                        '    },\n'
                        '  },\n'
                        '});',
                'code_lang': 'typescript'},
               {'h2': 'Allowlists that do not bite you in staging',
                'paragraphs': ['Hardcoding http://localhost:5173 works until someone uses 5174, a preview '
                               'deploy URL, or 127.0.0.1 instead of localhost. Browsers treat those as '
                               'different origins. Keep an allowlist in env and reject unknown origins '
                               'rather than reflecting whatever the client sends.',
                               'Reflecting arbitrary Origin values with credentials enabled lets any website '
                               'read authenticated responses. Keep the allowlist in an env var such as '
                               'CORS_ORIGINS and fail closed in production. In development, allow a '
                               'shortlist of localhost ports so preview branches still work.'],
                'code': '// cors calls this with the Origin header value (or undefined), not the request\n'
                        'function corsOrigin(origin, callback) {\n'
                        "  const allowed = (process.env.CORS_ORIGINS || '')\n"
                        "    .split(',')\n"
                        '    .map((s) => s.trim())\n'
                        '    .filter(Boolean);\n'
                        '  if (!origin) return callback(null, false);\n'
                        '  if (allowed.includes(origin)) return callback(null, true);\n'
                        '  return callback(new Error(`Origin ${origin} not allowed`), false);\n'
                        '}\n'
                        '\n'
                        'app.use(cors({ origin: corsOrigin, credentials: true }));',
                'code_lang': 'javascript'},
               {'h2': 'A 10-minute diagnosis checklist',
                'paragraphs': ['Open the failed request in Network. If you see a red OPTIONS with 404 or '
                               '405, fix preflight first. If OPTIONS is 204 but the real request fails CORS, '
                               'compare Origin with Access-Control-Allow-Origin character-for-character — '
                               'trailing slashes and http versus https matter.',
                               'Confirm you did not set a wildcard with credentials. Confirm custom headers '
                               'are listed in Access-Control-Allow-Headers. If you use a CDN or API gateway, '
                               'check that it forwards OPTIONS and does not strip ACA headers—or cache a '
                               'preflight response without the right headers, which makes every cookie-auth '
                               'user look broken until the cache is purged.'],
                'bullets': ['Reproduce in the browser Network tab, not only curl',
                            'Fix OPTIONS before debugging the real method',
                            'Never combine a wildcard ACAO with credentials',
                            'Prefer a local proxy for SPA plus separate API in development',
                            'Verify gateway or CDN does not strip or cache bad CORS responses',
                            'Diff Origin versus ACAO including scheme and port']},
               {'h2': 'A production pattern that holds up',
                'paragraphs': ['Allowlist exact frontend origins from env. Reject unknown origins. Keep '
                               'credentials only if you truly need cookie sessions; Bearer tokens in '
                               'Authorization avoid the cookie and credentials side of CORS for many SPAs, '
                               'though the Authorization header still triggers a preflight and must be '
                               'listed in Access-Control-Allow-Headers.',
                               'For mobile WebViews and multiple subdomains, consider serving API and app '
                               'from one host and terminating TLS at a reverse proxy so browsers see '
                               'same-origin requests. Same-site alone is not enough: sibling subdomains such '
                               'as app.example.com and api.example.com are same-site but still cross-origin, '
                               'so the proxy has to serve both from one host. That removes an entire class '
                               'of CORS problems—many “the API is down” reports turn out to be CORS '
                               'misconfiguration.',
                               'Document the matrix in the README: which env, which origin, cookie or '
                               'bearer, proxy or direct. The next person debugging at 11 p.m. should not '
                               'have to rediscover these rules from stack traces.']}],
  'takeaways': ['CORS failures are browser-only; curl success proves nothing about the frontend.',
                'JSON plus custom headers means OPTIONS preflight must succeed first.',
                'Credentials require a concrete ACAO origin, never a wildcard.',
                'Use a Vite or Next proxy locally; configure real CORS for production.',
                'Gateways can strip or cache CORS headers — inspect the final response.',
                'Allowlist origins from env; never reflect arbitrary Origin with credentials.']},
 {'slug': 'core-web-vitals-guide',
  'title': 'Core Web Vitals Guide: Practical LCP, INP, and CLS Checklist',
  'description': 'Practical ways to improve Largest Contentful Paint, Interaction to Next Paint, and '
                 'Cumulative Layout Shift, with a checklist you can run before every release.',
  'category': 'Web Performance',
  'date': '2026-06-05',
  'updated': '2026-10-09',
  'read_min': 12,
  'keywords': 'Core Web Vitals, LCP, INP, CLS, web performance, fetchpriority, font-display',
  'excerpt': 'Treat Core Web Vitals as a release gate, not a buzzword. This is a checklist to run before '
             'shipping marketing pages and authenticated dashboards.',
  'sections': [{'h2': 'The targets that matter',
                'paragraphs': ["Google's “good” thresholds are LCP at or under 2.5s, INP at or under 200ms, "
                               'and CLS at or under 0.1, at the 75th percentile of field data. Lab scores '
                               'from Lighthouse on a fast connection can mislead. Prioritize CrUX and Search '
                               'Console field data, then RUM from your own web-vitals beacons.',
                               'Lab and field numbers often disagree sharply. A storefront can score a green '
                               'lab LCP while its field p75 is well over the threshold, because real users '
                               'are on mid-range Android phones over mobile networks. When that happens, '
                               'stop celebrating Lighthouse and work on the hero image and TTFB.',
                               'Split dashboards from marketing pages in reporting. Authenticated apps often '
                               'look poor on LCP because the largest paint waits on an API. Mixing those '
                               'cohorts can hide a homepage regression for weeks.']},
               {'h2': 'LCP: make the largest element arrive early',
                'paragraphs': ['Find the LCP element in the Performance panel or the Web Vitals overlay. It '
                               'is usually a hero img, an H1 block with a web font, or a product card image. '
                               'Set explicit width and height or aspect-ratio, compress to AVIF or WebP, and '
                               'add fetchpriority=high on the LCP image only — never on every image.',
                               'Preload that image in the head when it is not discoverable early. CSS '
                               'background heroes are the worst offenders, because the browser cannot find '
                               'them until the CSS has loaded; moving the hero into an img element is often '
                               'one of the biggest single LCP wins.',
                               'The changes compound: cutting hero weight (a large JPEG to a much smaller '
                               'AVIF), adding a preload, and removing lazy-loading from the LCP image '
                               'together can move field p75 from failing to passing. loading=lazy on the '
                               'hero image is one of the most common mistakes in PRs.'],
                'code': '<!-- In <head> for known LCP image -->\n'
                        '<link rel="preload" as="image" href="/hero.avif" type="image/avif" '
                        'fetchpriority="high" />\n'
                        '\n'
                        '<img\n'
                        '  src="/hero.avif"\n'
                        '  width="1280"\n'
                        '  height="720"\n'
                        '  alt="Product dashboard"\n'
                        '  fetchpriority="high"\n'
                        '  decoding="async"\n'
                        '/>',
                'code_lang': 'html'},
               {'h2': 'INP: keep the main thread free after clicks',
                'paragraphs': ['INP replaced FID. It observes every click, tap, and keypress during the '
                               'visit, measures each from input until the next frame is painted, and reports '
                               'roughly the worst one (ignoring rare outliers on pages with many '
                               'interactions). A typical culprit is a filters panel that re-renders a table '
                               'of thousands of rows synchronously on every checkbox toggle.',
                               'Fixes that move p75 INP: debounce expensive handlers (around 150ms), '
                               'virtualize long lists, break up work with scheduler.postTask or '
                               'requestIdleCallback for non-urgent updates, and avoid layout thrashing in '
                               'event handlers. Profile with the Performance panel’s Interactions track '
                               'instead of guessing.',
                               'Another common pattern: opening a modal that synchronously parses a large '
                               'JSON blob and builds a chart. Moving parse and chart construction behind '
                               'startTransition in React keeps the click responsive; the chart fills in a '
                               'frame later. Users prefer a fast open over a frozen button.'],
                'code': '// Bad: sync filter of huge list on every keystroke\n'
                        "input.addEventListener('input', (e) => {\n"
                        '  renderRows(filterAll(rows, e.target.value)); // freezes UI\n'
                        '});\n'
                        '\n'
                        '// Better: debounce + yield\n'
                        "import { debounce } from './debounce';\n"
                        '\n'
                        'const onFilter = debounce((value) => {\n'
                        '  const filtered = filterAll(rows, value);\n'
                        '  requestAnimationFrame(() => renderRows(filtered));\n'
                        '}, 150);\n'
                        '\n'
                        "input.addEventListener('input', (e) => onFilter(e.target.value));",
                'code_lang': 'javascript'},
               {'h2': 'CLS: reserve space before paint',
                'paragraphs': ['CLS spikes when ads, late fonts, or images without dimensions shove content '
                               'around. Set image dimensions, use font-display: optional or swap with a '
                               'close fallback metric, and reserve min-height for async embeds.',
                               'Cookie banners are a frequent CLS source: one injected above the fold '
                               'without reserved space can push mobile CLS well past 0.1 on its own. Render '
                               'a fixed-height placeholder for it in the initial HTML so nothing moves when '
                               'it appears.',
                               'Web fonts are the other villain. A swap without matched metrics causes a '
                               'visible jump of the H1. A fallback font with a similar x-height, tuned with '
                               'size-adjust, makes the shift hard to notice.'],
                'bullets': ['Always set width/height or aspect-ratio on images and video',
                            'Avoid inserting DOM above existing content without a reserved slot',
                            'Prefer transform animations over top/left that trigger layout',
                            'Load webfonts with a fallback that has similar metrics',
                            'Test CLS with throttling and ad slots enabled — empty lab pages hide it']},
               {'h2': 'Wire RUM so arguments end',
                'paragraphs': ['Ship the web-vitals library’s attribution build and POST LCP, INP, and CLS '
                               'to your analytics endpoint with route name, connection type, and device '
                               'class. Without attribution, “LCP is bad” is not actionable — you need the '
                               'element and the phase, such as TTFB versus resource load versus render '
                               'delay.',
                               'Sample at 100 percent on low-traffic marketing sites; on high-traffic apps, '
                               "5 to 10 percent still gives a stable p75 within a day. Alert when a route's "
                               'p75 LCP rises sharply week-over-week after a deploy.'],
                'code': "import { onLCP, onINP, onCLS } from 'web-vitals/attribution';\n"
                        '\n'
                        'function send(metric) {\n'
                        '  const body = JSON.stringify({\n'
                        '    name: metric.name,\n'
                        '    value: metric.value,\n'
                        '    id: metric.id,\n'
                        '    route: location.pathname,\n'
                        '    navType: metric.navigationType,\n'
                        '  });\n'
                        "  navigator.sendBeacon('/rum', body);\n"
                        '}\n'
                        '\n'
                        'onLCP(send);\n'
                        'onINP(send);\n'
                        'onCLS(send);',
                'code_lang': 'javascript'},
               {'h2': 'Images beyond the hero',
                'paragraphs': ['Below the fold, use responsive srcset with 1x and 2x candidates and modern '
                               'formats, and lazy-load everything that is not the LCP candidate. A product '
                               'grid that eagerly loads a dozen large JPEGs competes with the hero for '
                               'bandwidth and pushes LCP out.',
                               'Cap decoded size too. Serving a 4000px-wide asset into a 400px slot wastes '
                               'memory and decode time on mobile; an image CDN can enforce max width by '
                               'breakpoint. When a page insists on a video background, treat the poster '
                               'frame as the LCP image and defer the video until after load or first '
                               'interaction.']},
               {'h2': 'Server and cache levers that move field LCP',
                'paragraphs': ['Many LCP regressions are really TTFB regressions. Edge-caching HTML for '
                               'anonymous marketing pages with a 30–60s stale-while-revalidate, and keeping '
                               'the API origin in the same region as users, often matters more than shaving '
                               '4KB of JS.',
                               'Audit third parties. A tag-manager container can add hundreds of '
                               'milliseconds to mobile LCP. Defer non-essential tags until after '
                               'requestIdleCallback or first interaction, and measure before and after with '
                               'the same RUM dashboard — Lighthouse screenshots alone do not convince '
                               'stakeholders.']},
               {'h2': 'A release checklist to paste into PRs',
                'paragraphs': ['Before merge on customer-facing routes: identify LCP element; confirm '
                               'preload and fetchpriority; no layout shift from fonts or banners; '
                               'interaction handlers under about 50ms of sync work on mid-tier CPU; bundle '
                               'diff does not add a new blocking script in head.',
                               'Fail the PR if lab LCP on a throttled mobile profile jumps by more than a '
                               'set amount (say 300ms) without a documented reason. A rule like that catches '
                               'accidental full-page client hydration of marketing content.',
                               'Keep a soft JavaScript budget for marketing routes (for example around 170KB '
                               'gzipped). Crossing it requires a comment explaining the trade—enough social '
                               'pressure to stop a charting library from sneaking onto the homepage. Paste '
                               'lab LCP, INP, and CLS on a throttled mid-range phone profile next to the '
                               'diff so reviewers stop arguing about vibes.']}],
  'takeaways': ['Trust field p75 from CrUX or RUM over a single Lighthouse run on desktop cable.',
                'LCP usually needs a discoverable, prioritized, correctly sized hero image.',
                'INP improves when you cut sync main-thread work after clicks and keypresses.',
                'CLS is mostly reserved space: dimensions, banners, and font fallbacks.',
                'TTFB and third-party tags often dominate real-user LCP more than micro-optimizations.',
                'Ship RUM with attribution so you know which element and phase regressed.']},
 {'slug': 'jwt-authentication-nodejs',
  'title': 'JWT Access and Refresh Tokens in Node/Express with httpOnly Cookies',
  'description': 'How to implement short-lived access JWTs and rotating refresh tokens in Express, stored in '
                 'httpOnly cookies, with concrete rotation and revocation notes.',
  'category': 'Backend',
  'date': '2026-06-08',
  'updated': '2026-10-09',
  'read_min': 12,
  'keywords': 'JWT authentication, refresh token, httpOnly cookie, Node.js Express, access token, token '
              'rotation',
  'excerpt': 'JWTs in localStorage are one XSS bug away from stolen sessions. Here is an access-plus-refresh '
             'cookie pattern for Express apps that limits the damage.',
  'sections': [{'h2': 'Threat model in one paragraph',
                'paragraphs': ['Access tokens in localStorage are trivial to steal if any XSS lands. Tokens '
                               'in memory-only JS are safer but disappear on refresh. httpOnly cookies keep '
                               'tokens off document.cookie, and Secure plus SameSite reduce drive-by sends. '
                               "XSS can still trigger authenticated requests from the victim's browser — "
                               'cookies are not magic — but they stop simple token exfiltration scripts.',
                               'Use a short-lived access JWT of 5 to 15 minutes and a longer refresh token '
                               'of 7 to 30 days that is rotated and stored hashed server-side. Stolen '
                               'refresh tokens should not live forever.',
                               'The difference shows up clearly in a security test: with localStorage JWTs, '
                               'a single reflected XSS payload can read the tokens and send them to an '
                               'attacker’s machine, where they work from anywhere. With httpOnly cookies, '
                               'the same payload can still act as the user inside that browser tab, but it '
                               'cannot exfiltrate a reusable bearer token. That trade is worth the CSRF '
                               'work.']},
               {'h2': 'Issuing tokens',
                'paragraphs': ['On login, verify the password with bcrypt at cost 12, then mint an access '
                               'JWT signed with HS256—or RS256/EdDSA in larger systems. Keep claims minimal: '
                               'sub, role, iat, exp. No PII blobs. The refresh token is a random 32-plus '
                               'byte string; store the sha256 of the token in Postgres with user_id, '
                               'expires_at, replaced_by, replaced_at, and revoked_at.',
                               'Clock skew between API instances can make tokens look expired early. Allow a '
                               'small clockTolerance (around 30 seconds) on verify, and keep the fleet '
                               'NTP-synced. Rotate JWT_ACCESS_SECRET only with a dual-key verify window so '
                               'deploys do not log everyone out at once.'],
                'code': "import jwt from 'jsonwebtoken';\n"
                        "import crypto from 'crypto';\n"
                        '\n'
                        "const ACCESS_TTL = '10m';\n"
                        'const REFRESH_DAYS = 14;\n'
                        '\n'
                        'export function signAccessToken(user) {\n'
                        '  return jwt.sign(\n'
                        '    { sub: user.id, role: user.role },\n'
                        '    process.env.JWT_ACCESS_SECRET,\n'
                        '    { expiresIn: ACCESS_TTL }\n'
                        '  );\n'
                        '}\n'
                        '\n'
                        'export function createRefreshToken() {\n'
                        "  return crypto.randomBytes(48).toString('base64url');\n"
                        '}\n'
                        '\n'
                        'export function hashToken(token) {\n'
                        "  return crypto.createHash('sha256').update(token).digest('hex');\n"
                        '}\n'
                        '\n'
                        'export function setAuthCookies(res, accessToken, refreshToken) {\n'
                        '  const common = {\n'
                        '    httpOnly: true,\n'
                        "    secure: process.env.NODE_ENV === 'production',\n"
                        "    sameSite: 'lax',\n"
                        "    path: '/',\n"
                        '  };\n'
                        "  res.cookie('access_token', accessToken, { ...common, maxAge: 10 * 60 * 1000 });\n"
                        "  res.cookie('refresh_token', refreshToken, {\n"
                        '    ...common,\n'
                        "    path: '/auth',\n"
                        '    maxAge: REFRESH_DAYS * 24 * 60 * 60 * 1000,\n'
                        '  });\n'
                        '}',
                'code_lang': 'javascript'},
               {'h2': 'Middleware that reads the cookie',
                'paragraphs': ['Do not accept access tokens from query strings: use a cookie, or '
                               'Authorization: Bearer for API clients. Scope the refresh cookie’s path to '
                               '/auth so it is not sent with every request—if both cookies use path /, every '
                               'image and asset request carries the refresh token.',
                               'Query-string tokens also end up in access logs, Referer headers, browser '
                               'history, and CDN logs. Ban them outright.'],
                'code': "import cookieParser from 'cookie-parser';\n"
                        '\n'
                        'app.use(cookieParser());\n'
                        '\n'
                        'export function requireAuth(req, res, next) {\n'
                        '  const header = req.headers.authorization;\n'
                        '  const token =\n'
                        "    (header && header.startsWith('Bearer ') && header.slice(7)) ||\n"
                        '    req.cookies.access_token;\n'
                        '\n'
                        "  if (!token) return res.status(401).json({ error: 'unauthenticated' });\n"
                        '\n'
                        '  try {\n'
                        '    req.user = jwt.verify(token, process.env.JWT_ACCESS_SECRET);\n'
                        '    next();\n'
                        '  } catch {\n'
                        "    return res.status(401).json({ error: 'invalid_token' });\n"
                        '  }\n'
                        '}',
                'code_lang': 'javascript'},
               {'h2': 'Refresh with rotation',
                'paragraphs': ['POST /auth/refresh reads the refresh cookie, hashes it, looks up a '
                               'non-revoked row, issues a new access plus refresh pair, marks the old '
                               'refresh as replaced, and sets cookies again. If a previously replaced '
                               'refresh is presented again, revoke the whole family — classic reuse '
                               'detection for token theft.',
                               'Without rotation, a leaked refresh token works until it expires—potentially '
                               'for weeks. With rotation and reuse detection, the abuse window shrinks to '
                               'the moment either the attacker or the real user refreshes again.',
                               'Race condition note: two parallel tabs can refresh in the same millisecond. '
                               'One wins; the other looks like reuse. Solve this with a short grace window '
                               'of about 10 seconds in which the previous refresh still works if replaced_by '
                               'was set recently within the same family, or by serializing refresh with a '
                               'per-user lock.'],
                'code': 'const REUSE_GRACE_MS = 10_000; // replaced_at is set by rotate()\n'
                        '\n'
                        "app.post('/auth/refresh', async (req, res) => {\n"
                        '  const raw = req.cookies.refresh_token;\n'
                        "  if (!raw) return res.status(401).json({ error: 'no_refresh' });\n"
                        '\n'
                        '  const row = await db.refreshTokens.findByHash(hashToken(raw));\n'
                        '  if (!row || row.revoked_at || row.expires_at < new Date()) {\n'
                        "    return res.status(401).json({ error: 'invalid_refresh' });\n"
                        '  }\n'
                        '  const user = await db.users.findById(row.user_id);\n'
                        '\n'
                        '  if (row.replaced_by) {\n'
                        '    // Grace window: a parallel tab may have rotated this token moments ago.\n'
                        '    // Its response already set the new refresh cookie, so only reissue access.\n'
                        '    if (row.replaced_at && Date.now() - row.replaced_at.getTime() < REUSE_GRACE_MS) '
                        '{\n'
                        "      res.cookie('access_token', signAccessToken(user), {\n"
                        '        httpOnly: true,\n'
                        "        secure: process.env.NODE_ENV === 'production',\n"
                        "        sameSite: 'lax',\n"
                        "        path: '/',\n"
                        '        maxAge: 10 * 60 * 1000,\n'
                        '      });\n'
                        '      return res.json({ ok: true });\n'
                        '    }\n'
                        '    await db.refreshTokens.revokeFamily(row.family_id);\n'
                        "    return res.status(401).json({ error: 'reuse_detected' });\n"
                        '  }\n'
                        '\n'
                        '  const access = signAccessToken(user);\n'
                        '  const nextRefresh = createRefreshToken();\n'
                        '  await db.refreshTokens.rotate(row.id, hashToken(nextRefresh), REFRESH_DAYS);\n'
                        '  setAuthCookies(res, access, nextRefresh);\n'
                        '  res.json({ ok: true });\n'
                        '});',
                'code_lang': 'javascript'},
               {'h2': 'Silent refresh on the client',
                'paragraphs': ['The SPA keeps a fetch interceptor: on 401, try /auth/refresh once, retry the '
                               'original request, and if refresh fails redirect to login. Without a '
                               'single-flight mutex, five parallel 401s spawn five refreshes and trigger '
                               'reuse detection. Gate refresh behind a shared promise.'],
                'code': 'let refreshPromise = null;\n'
                        '\n'
                        'async function refreshOnce() {\n'
                        '  if (!refreshPromise) {\n'
                        "    refreshPromise = fetch('/auth/refresh', {\n"
                        "      method: 'POST',\n"
                        "      credentials: 'include',\n"
                        '    }).finally(() => {\n'
                        '      refreshPromise = null;\n'
                        '    });\n'
                        '  }\n'
                        '  return refreshPromise;\n'
                        '}\n'
                        '\n'
                        'async function apiFetch(input, init) {\n'
                        "  const res = await fetch(input, { ...init, credentials: 'include' });\n"
                        '  if (res.status !== 401) return res;\n'
                        '  const refreshed = await refreshOnce();\n'
                        "  if (!refreshed.ok) throw new Error('session_expired');\n"
                        "  return fetch(input, { ...init, credentials: 'include' });\n"
                        '}',
                'code_lang': 'javascript'},
               {'h2': 'CSRF when cookies are involved',
                'paragraphs': ['Cookie auth reintroduces CSRF for state-changing requests. SameSite=Lax is a '
                               'good default for most apps, plus a double-submit CSRF token for mutating '
                               'routes; SameSite=Strict suits sensitive admin tools that can tolerate '
                               'harsher UX.',
                               'SPA on app.example.com and API on api.example.com needs careful cookie '
                               'Domain and CORS credentials. Those two hosts are already same-site (same '
                               'registrable domain) but cross-origin; serving the API from the same origin, '
                               'for example app.example.com/api behind a reverse proxy, is simpler when you '
                               'can afford it.']},
               {'h2': 'Cookie attributes to verify in staging',
                'paragraphs': ['Before calling a release done, open Application → Cookies on staging and '
                               'confirm: httpOnly checked, Secure on HTTPS, SameSite as designed, path '
                               'scoped for refresh, and expiry matching the TTL. A missing Secure flag is '
                               'easy to miss because everything works on localhost over HTTP.',
                               'Cross-subdomain cookies need Domain=.example.com carefully. Too broad and '
                               'every subdomain receives the session cookie. Native mobile clients can '
                               'receive Bearer access tokens in the JSON body and skip cookies, with the '
                               'same signing keys and refresh tables backing both clients.',
                               'Log refresh outcomes as counters: success, expired, reuse_detected, missing. '
                               'A spike in reuse_detected without a security incident usually means the '
                               'client double-refresh race. Never log raw tokens — log a truncated hash '
                               'prefix if you need correlation.']},
               {'h2': 'Mistakes to avoid',
                'paragraphs': ['Storing refresh tokens plaintext in the DB. Using a 7-day access JWT to '
                               'avoid refresh complexity. Putting secrets in the JWT payload and expecting '
                               'them to stay secret. Forgetting to clear cookies on logout while only '
                               'deleting the client store.',
                               'Logout must clear cookies with res.clearCookie and revoke the refresh row. '
                               'For “sign out of all devices,” revoke all refresh families for that user_id '
                               'and expose it as a security settings action. Document the token TTLs in the '
                               'security runbook so on-call can answer session questions without reading '
                               'code at 2 a.m.'],
                'bullets': ['Access JWT: minutes, not days',
                            'Refresh: random opaque token, hashed at rest, rotated',
                            'httpOnly plus Secure plus scoped path',
                            'Reuse detection on refresh',
                            'Logout revokes server-side state, not only cookies',
                            'Single-flight client refresh to avoid false reuse alarms']}],
  'takeaways': ['Prefer httpOnly cookies over localStorage for browser session tokens.',
                'Keep access JWTs short-lived; persist opaque refresh tokens hashed in the DB.',
                'Rotate refresh tokens and revoke the family on reuse.',
                'Cookie auth needs a CSRF strategy with SameSite plus tokens for mutations.',
                'Logout and sign out everywhere must revoke server-side refresh rows.',
                'Serialize client silent-refresh so parallel 401s do not look like theft.']},
 {'slug': 'docker-compose-for-developers',
  'title': 'Docker Compose for Local Node, Postgres, and Redis',
  'description': 'A practical Compose file for day-to-day Node development with Postgres and Redis, '
                 'including volumes, healthchecks, and the mistakes that waste whole afternoons.',
  'category': 'DevOps',
  'date': '2026-06-11',
  'updated': '2026-10-09',
  'read_min': 12,
  'keywords': 'Docker Compose, Node.js, Postgres, Redis, local development, healthcheck, volumes',
  'excerpt': 'One command should bring up the API, Postgres, and Redis the same way on every laptop. This is '
             'a Compose setup you can copy into new services.',
  'sections': [{'h2': 'Why Compose instead of five terminal tabs',
                'paragraphs': ['Without Compose, onboarding means: install Postgres 16, install Redis 7, '
                               'create a role, resolve the port conflict with another project. New '
                               'developers can lose a day. Compose gives reproducible ports, versions, and '
                               'seed scripts. Running the Node process on the host with hot reload is still '
                               'the fastest loop; containerize Node only when you need parity with '
                               'production images.',
                               'Two modes: full stack in Compose for demos and CI, and docker compose up db '
                               'redis while npm run dev hits localhost mapped ports. Both share the same '
                               'compose.yaml.',
                               'The alternative is a wiki page with a dozen manual steps that differ by '
                               'operating system. With Compose, getting a new laptop to a working stack is '
                               'mostly clone, copy .env.example, and one command.']},
               {'h2': 'A Compose file that survives Monday mornings',
                'paragraphs': ['Pin image tags: postgres:latest can jump a major version overnight. Named '
                               'volumes keep data across restarts. Healthchecks stop the API from racing '
                               'migrations before Postgres accepts connections — a classic source of flaky '
                               'CI.',
                               'Set restart: unless-stopped on db and redis for long-lived laptops, and keep '
                               'resource limits light so a runaway migration cannot freeze Docker Desktop. '
                               '512M of memory for Postgres is enough for local datasets of a few GB.'],
                'code': 'services:\n'
                        '  db:\n'
                        '    image: postgres:16-alpine\n'
                        '    environment:\n'
                        '      POSTGRES_USER: app\n'
                        '      POSTGRES_PASSWORD: app\n'
                        '      POSTGRES_DB: app_dev\n'
                        '    ports:\n'
                        '      - "5432:5432"\n'
                        '    volumes:\n'
                        '      - pgdata:/var/lib/postgresql/data\n'
                        '      - ./docker/db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro\n'
                        '    healthcheck:\n'
                        '      test: ["CMD-SHELL", "pg_isready -U app -d app_dev"]\n'
                        '      interval: 5s\n'
                        '      timeout: 5s\n'
                        '      retries: 10\n'
                        '    restart: unless-stopped\n'
                        '    deploy:\n'
                        '      resources:\n'
                        '        limits:\n'
                        '          memory: 512M\n'
                        '\n'
                        '  redis:\n'
                        '    image: redis:7.4-alpine\n'
                        '    restart: unless-stopped\n'
                        '    ports:\n'
                        '      - "6379:6379"\n'
                        '    command: ["redis-server", "--save", "60", "1", "--loglevel", "warning"]\n'
                        '    healthcheck:\n'
                        '      test: ["CMD", "redis-cli", "ping"]\n'
                        '      interval: 5s\n'
                        '      timeout: 3s\n'
                        '      retries: 10\n'
                        '\n'
                        '  api:\n'
                        '    build:\n'
                        '      context: .\n'
                        '      dockerfile: Dockerfile.dev\n'
                        '    env_file: .env.docker\n'
                        '    environment:\n'
                        '      DATABASE_URL: postgres://app:app@db:5432/app_dev\n'
                        '      REDIS_URL: redis://redis:6379\n'
                        '    ports:\n'
                        '      - "4000:4000"\n'
                        '    volumes:\n'
                        '      - .:/app\n'
                        '      - /app/node_modules\n'
                        '    depends_on:\n'
                        '      db:\n'
                        '        condition: service_healthy\n'
                        '      redis:\n'
                        '        condition: service_healthy\n'
                        '\n'
                        'volumes:\n'
                        '  pgdata:',
                'code_lang': 'yaml'},
               {'h2': 'Networking and .env gotchas',
                'paragraphs': ['Inside the Compose network, the hostname is the service name—db or redis—not '
                               'localhost. Pasting localhost into a containerized API is one of the most '
                               'common mistakes: connection refused, followed by half an hour of blaming '
                               'Postgres.',
                               'Host-run Node must use localhost:5432. Container-run Node must use db:5432. '
                               'Keep two env files—.env for the host and .env.docker for Compose—or template '
                               'DATABASE_URL in scripts. Document it in bold in the README; it is the '
                               'question everyone asks.',
                               'Port collisions are the other regular pain. If another project already bound '
                               '5432, Compose fails in a cryptic way. Map host 5433 to container 5432 for '
                               'secondary projects and put the host port in .env so nobody hardcodes it.']},
               {'h2': 'Anonymous volumes for node_modules',
                'paragraphs': ['The trick of bind-mounting . to /app plus an anonymous volume at '
                               '/app/node_modules prevents the host from overwriting Linux node_modules with '
                               'macOS binaries or an empty folder. Without the anonymous volume, native '
                               'modules like bcrypt crash with invalid ELF headers.',
                               'When dependencies change, run docker compose run --rm api npm ci or rebuild. '
                               'A cold npm ci inside the image can take a minute or more; mounting source '
                               'keeps edit-reload under a second with nodemon.'],
                'code': '# Dockerfile.dev\n'
                        'FROM node:22-alpine\n'
                        'WORKDIR /app\n'
                        'COPY package.json package-lock.json ./\n'
                        'RUN npm ci\n'
                        'COPY . .\n'
                        'CMD ["npm", "run", "dev"]',
                'code_lang': 'dockerfile'},
               {'h2': 'Migrations that wait for healthy Postgres',
                'paragraphs': ['Even with depends_on healthchecks, wrap migration commands in a tiny retry '
                               'script for CI. Postgres can accept connections and still reject the first '
                               'migration if the role setup from init.sql is mid-flight on a slow disk.',
                               'Run migrations as a one-shot Compose service in CI, not as a side effect of '
                               'API boot, so failed migrations fail the job clearly instead of leaving a '
                               'half-booted API.'],
                'code': '# scripts/wait-and-migrate.sh\n'
                        'set -euo pipefail\n'
                        'for i in $(seq 1 30); do\n'
                        '  if pg_isready -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE"; then\n'
                        '    npx prisma migrate deploy\n'
                        '    exit 0\n'
                        '  fi\n'
                        '  sleep 2\n'
                        'done\n'
                        'echo "Postgres never became ready" >&2\n'
                        'exit 1',
                'code_lang': 'bash'},
               {'h2': 'Seeding data without fighting init.sql',
                'paragraphs': ['init.sql runs only when the volume is first created. For day-to-day seed '
                               'data, use a Make target that runs a Node script against localhost after '
                               'Compose is healthy. Make that script idempotent—upsert by natural key—so '
                               're-running it does not duplicate rows.',
                               'For a clean slate, explicitly run docker compose down -v, bring db and redis '
                               'back, then migrate and seed. Teaching that reset stops people from editing '
                               'init.sql and wondering why nothing changed. Large dumps belong outside git '
                               'on object storage.']},
               {'h2': 'Resetting state without drama',
                'paragraphs': ['docker compose down keeps volumes. docker compose down -v wipes Postgres '
                               'data — useful for migration experiments, catastrophic if you thought it was '
                               'a soft stop. Only alias a reset command after confirming the project name.',
                               'For shared laptops, set COMPOSE_PROJECT_NAME so volume names do not collide '
                               'with another repo also calling its service db.'],
                'bullets': ['Pin image tags to a release line (postgres:16, redis:7.4), never latest',
                            'Healthcheck before depends_on',
                            'Use service DNS names inside the network',
                            'Anonymous volume for node_modules on bind mounts',
                            'Know the difference between down and down -v',
                            'Remap host ports when 5432 or 6379 are already taken']},
               {'h2': 'CI uses the same Compose file',
                'paragraphs': ['In GitHub Actions, run docker compose up -d db redis, wait for health, then '
                               'run tests on the runner against the published ports. Sharing the Compose '
                               'file means local and CI Postgres majors cannot drift.',
                               'Cache the Postgres image layers and avoid building the API image in '
                               'unit-test jobs. Integration jobs that need the API container should build '
                               'with BuildKit cache mounts so npm ci is not cold every time. Gate the test '
                               'start on healthchecks rather than a fixed sleep, which is sometimes too '
                               'short on busy runners.']},
               {'h2': 'What to leave out of local Compose',
                'paragraphs': ['Never put production secrets in compose files. Local passwords like app/app '
                               'are fine as long as they are never reused. Do not emulate a full Kubernetes '
                               'mesh locally unless you are debugging mesh-specific bugs — Compose is for '
                               'data stores and optional API parity.',
                               'Redis persistence is optional locally; light RDB saves let cache warmups '
                               'survive a reboot during a long feature branch. Postgres init scripts run '
                               'only on empty volumes — after the first boot, change schema with migrations, '
                               'not by editing init.sql and expecting it to re-run.',
                               'Finally, publish a one-line happy path in the README: compose up db redis, '
                               'copy env, npm i, npm run dev.']}],
  'takeaways': ['Compose the databases; optionally run Node on the host for faster reload.',
                'Pin image versions and wait on healthchecks before starting the API.',
                'localhost versus service name depends on whether the process is in a container.',
                'Bind-mount source with an anonymous node_modules volume to avoid native binary clashes.',
                'Treat down -v as destructive; use a unique COMPOSE_PROJECT_NAME per repo.',
                'Run migrations as an explicit step with retries, not as a silent boot side effect.']},
 {'slug': 'react-useeffect-common-mistakes',
  'title': 'React useEffect Mistakes That Keep Showing Up in Code Review',
  'description': 'Dependency arrays, cleanup, fetch races, and infinite loops — concrete useEffect '
                 'anti-patterns and how to fix them.',
  'category': 'Frontend',
  'date': '2026-06-14',
  'read_min': 12,
  'keywords': 'React useEffect, dependency array, cleanup function, infinite loop, Strict Mode, fetch race',
  'excerpt': 'Most useEffect bugs are not exotic. They are missing deps, missing cleanup, or effects that '
             'should have been event handlers.',
  'sections': [{'h2': 'Effect vs event: the first question to ask',
                'paragraphs': ['If something happens because the user clicked, put it in the click handler. '
                               'If something synchronizes React with an external system such as document '
                               'title, a WebSocket, or a non-React widget, use an effect. A common '
                               'anti-pattern is a useEffect that saves a draft form on every keystroke and '
                               'hammers the API — that belongs behind a debounce in an event handler or a '
                               'dedicated autosave hook with clear intent.',
                               'The React docs push this mental model hard, and it is the single most useful '
                               'review question: what external system is this effect syncing?',
                               'Autosave-via-effect is a good illustration: with an effect keyed on the form '
                               'value, every keystroke can fire a request — dozens per minute of typing. A '
                               'debounced save, or saving on blur, reduces that to a handful and keeps the '
                               'draft endpoint well inside its rate limit.']},
               {'h2': 'The infinite loop starter pack',
                'paragraphs': ['Classic: effect sets state that is also in the dependency array, without a '
                               'guard. Or depending on an object or array literal created each render. Or '
                               'depending on a function prop that the parent recreates every render.',
                               'When you suspect a loop, log render counts for a short while. Hundreds of '
                               'renders per second in Strict Mode is a strong signal before the tab locks '
                               'up.'],
                'code': '// Loop: new options object every render → effect → setState → render → ...\n'
                        'function Chart({ data }) {\n'
                        '  const [series, setSeries] = useState([]);\n'
                        '  const options = { animate: true }; // new reference each time\n'
                        '\n'
                        '  useEffect(() => {\n'
                        '    setSeries(transform(data, options));\n'
                        '  }, [data, options]);\n'
                        '\n'
                        '  return <Canvas series={series} />;\n'
                        '}\n'
                        '\n'
                        '// Fix: depend on primitives / stable values\n'
                        'useEffect(() => {\n'
                        '  setSeries(transform(data, { animate: true }));\n'
                        '}, [data]);',
                'code_lang': 'javascript'},
               {'h2': 'Fetch without cleanup equals race',
                'paragraphs': ['The user switches from product 1 to product 2 quickly. Request 1 finishes '
                               'after request 2 and overwrites state, so the page shows the wrong product '
                               'name. AbortController in cleanup is the default fix.',
                               'If you cannot abort, at least ignore stale responses with an incrementing '
                               'request id or a cancelled flag. This bug easily slips past QA, because it '
                               'only appears when someone clicks quickly.'],
                'code': 'useEffect(() => {\n'
                        '  const controller = new AbortController();\n'
                        '  let cancelled = false;\n'
                        '\n'
                        '  async function load() {\n'
                        '    try {\n'
                        '      const res = await fetch(`/api/products/${id}`, { signal: controller.signal '
                        '});\n'
                        '      const json = await res.json();\n'
                        '      if (!cancelled) setProduct(json);\n'
                        '    } catch (err) {\n'
                        "      if (err.name !== 'AbortError') setError(err);\n"
                        '    }\n'
                        '  }\n'
                        '\n'
                        '  load();\n'
                        '  return () => {\n'
                        '    cancelled = true;\n'
                        '    controller.abort();\n'
                        '  };\n'
                        '}, [id]);',
                'code_lang': 'javascript'},
               {'h2': 'Strict Mode double mount is not your enemy',
                'paragraphs': ['In React 18-plus development, effects mount, clean up, and mount again to '
                               'surface missing cleanup. Developers fix this by removing Strict Mode. That '
                               'hides bugs. If your effect opens a socket or increments an analytics counter '
                               'twice in dev, add proper cleanup and idempotent setup.',
                               'Missing cleanup does not stay a dev-only problem: a remount path nobody '
                               'tested can double-call a metering or billing API in production. Strict '
                               'Mode’s double invoke exists to surface exactly that in development.']},
               {'h2': 'Derived state that should not be state',
                'paragraphs': ['If you can compute fullName from first and last during render, do not store '
                               'it in state updated by an effect. Effects for pure derivation add an extra '
                               'paint and drift bugs. Same for filtering a list: derive during render, and '
                               'memoize only when the list is genuinely large (thousands of rows) and '
                               'profiling shows it matters.',
                               'Prop-to-state sync effects are another smell. Prefer fully controlled '
                               'components or remount with key equals id when you truly need fresh local '
                               'state per entity.'],
                'bullets': ['Empty deps means once per mount — confirm that is intentional',
                            'Omit deps only with a documented eslint-disable and a reason',
                            'Cleanup subscriptions, timers, and in-flight fetches',
                            'Do not put React Query or SWR fetch solely in raw useEffect if the library '
                            'already owns cache',
                            'Prefer keying a child to reset state instead of syncing props to state in '
                            'effects']},
               {'h2': 'Subscriptions done right',
                'paragraphs': ['Window listeners, IntersectionObserver, and media queries need subscribe in '
                               'the effect and unsubscribe in cleanup. Keep the handler stable, or read the '
                               'latest values via a ref when the listener must stay registered once.',
                               'Forums still recommend empty deps plus eslint-disable for listeners that '
                               'close over state. Prefer a ref for latest state: register once, read '
                               'ref.current inside the handler. That avoids resubscribing on every render '
                               'without lying about dependencies.'],
                'code': 'useEffect(() => {\n'
                        '  function onResize() {\n'
                        '    setWidth(window.innerWidth);\n'
                        '  }\n'
                        "  window.addEventListener('resize', onResize);\n"
                        '  onResize();\n'
                        "  return () => window.removeEventListener('resize', onResize);\n"
                        '}, []);',
                'code_lang': 'javascript'},
               {'h2': 'Timers and intervals that leak',
                'paragraphs': ['Polling with setInterval inside an effect without clearing it on unmount or '
                               'dependency change leaks timers. In an SPA shell, soft navigation can leave a '
                               'tab running dozens of intervals.',
                               'Prefer setTimeout chains when the interval should wait for the previous '
                               'fetch to finish, or use a library that owns polling. Always return '
                               'clearInterval or clearTimeout from the effect cleanup.'],
                'code': 'useEffect(() => {\n'
                        '  let timer = null;\n'
                        '  let stopped = false;\n'
                        '\n'
                        '  async function tick() {\n'
                        '    await refreshInbox();\n'
                        '    if (!stopped) timer = setTimeout(tick, 15000);\n'
                        '  }\n'
                        '\n'
                        '  tick();\n'
                        '  return () => {\n'
                        '    stopped = true;\n'
                        '    if (timer) clearTimeout(timer);\n'
                        '  };\n'
                        '}, []);',
                'code_lang': 'javascript'},
               {'h2': 'Data libraries versus hand-rolled effects',
                'paragraphs': ['If the team already uses React Query or SWR, avoid new useEffect fetches for '
                               'server state unless there is a clear gap. Those libraries handle caching, '
                               'dedupe, retries, and cancellation. Re-implementing them poorly is how one '
                               'app ends up with three different loading-state conventions.',
                               'Effects still make sense for wiring: syncing a query result into a non-React '
                               'map SDK, or writing document.title. Keep the boundary clear — server state '
                               'in the library, external sync in effects. When migrating, replace one screen '
                               'at a time and delete the old effect rather than leaving both paths.']},
               {'h2': 'Measuring before micro-optimizing effects',
                'paragraphs': ['Not every effect that runs twice in Strict Mode is a production bug. It '
                               'matters when it hits the network, writes to analytics, or mutates a '
                               'third-party widget. Cosmetic double logs in development are noise.',
                               'For expensive sync work after render, check the Profiler first. Moving '
                               'derived data into an effect “to keep render pure” usually makes the UI worse '
                               'by delaying paint—computing during render is often faster. Profile first, '
                               'then decide whether an effect earns its keep.']},
               {'h2': 'Three review questions',
                'paragraphs': ['Is this syncing an external system? If not, move it to the event handler. '
                               'Will this race when the id changes? What cleans this up under Strict Mode’s '
                               'double invoke? Those three questions catch most useEffect defects before '
                               'merge.',
                               'If the author cannot answer in one sentence, deleting the effect and trying '
                               'again often produces the better design within minutes. A short internal doc '
                               'with before-and-after snippets of these patterns, linked from the PR '
                               'template, saves writing the same review comment over and over.']}],
  'takeaways': ['Use effects for external synchronization, not for ordinary user-event logic.',
                'Unstable object or function dependencies are a common infinite-loop source.',
                'Abort in-flight fetches on cleanup to prevent racey setState.',
                'Strict Mode double mounting highlights missing cleanup — fix cleanup, do not remove Strict '
                'Mode.',
                'Prefer derived values during render over prop-to-state mirroring effects.',
                'Always clear timers and intervals in effect cleanup.'],
  'updated': '2026-10-09'},
 {'slug': 'nextjs-app-router-data-fetching',
  'title': 'Next.js App Router Data Fetching: fetch, Cache, and revalidate Patterns',
  'description': 'Practical App Router patterns for cached fetch, revalidate, no-store dynamic data, and '
                 'when to reach for Server Actions in Next.js 14/15 apps.',
  'category': 'Frontend',
  'date': '2026-06-18',
  'updated': '2026-10-09',
  'read_min': 12,
  'keywords': 'Next.js App Router, fetch cache, revalidate, no-store, Server Components, Server Actions',
  'excerpt': 'App Router caching can surprise you in production: a live admin page quietly serving stale '
             'inventory for 60 seconds. Here is how to choose fetch options on purpose.',
  'sections': [{'h2': 'Default mental model',
                'paragraphs': ['In the App Router, fetch in Server Components can be cached and '
                               'deduplicated. That is great for marketing pages and terrible for per-user '
                               'dashboards if you leave defaults wrong. Treat every fetch as needing an '
                               'explicit caching policy in code review.',
                               'A rule of thumb: public, slow-changing content gets cache plus revalidate. '
                               "User-specific or money-adjacent data gets cache: 'no-store' or export const "
                               "dynamic = 'force-dynamic'. Mixed pages get segment config plus tagged "
                               'revalidation.',
                               'Next.js upgrades have changed default caching behavior more than once—Next '
                               '15, for example, stopped caching fetch by default. A route that was dynamic '
                               'can become cached after an upgrade, or the reverse. Assert cache headers in '
                               'an integration test for account routes so upgrades cannot silently flip the '
                               'policy.']},
               {'h2': 'Static-ish content with time-based revalidation',
                'paragraphs': ['Blog indexes and pricing pages tolerate slight staleness. revalidate: 60 '
                               'means an ISR-style refresh at most once per minute. Caching a slow CMS fetch '
                               'this way typically cuts TTFB on a landing page dramatically, because most '
                               'requests are served from cache.',
                               'Do not use a 60-second window for content that editors expect to appear '
                               'instantly. Either shorten revalidate for that segment or use on-demand tags. '
                               'Mixing feels-live marketing copy with a 5-minute revalidate creates trust '
                               'issues with the content team.'],
                'code': '// app/blog/page.tsx\n'
                        'async function getPosts() {\n'
                        "  const res = await fetch('https://cms.example.com/posts', {\n"
                        "    next: { revalidate: 60, tags: ['posts'] },\n"
                        '  });\n'
                        "  if (!res.ok) throw new Error('Failed to load posts');\n"
                        '  return res.json();\n'
                        '}\n'
                        '\n'
                        'export default async function BlogIndex() {\n'
                        '  const posts = await getPosts();\n'
                        '  return (\n'
                        '    <ul>\n'
                        '      {posts.map((p) => (\n'
                        '        <li key={p.slug}>{p.title}</li>\n'
                        '      ))}\n'
                        '    </ul>\n'
                        '  );\n'
                        '}',
                'code_lang': 'typescript'},
               {'h2': 'On-demand revalidation with tags',
                'paragraphs': ['When editors publish, waiting 60 seconds is awkward. Tag fetches and call '
                               "revalidateTag('posts') from a webhook route handler or Server Action after "
                               'the CMS publishes. That removes most “where is my post?” questions from the '
                               'content team.',
                               'Protect the webhook with a shared secret and rate limiting. An open '
                               'revalidate endpoint is a cheap DoS against your origin and cache.'],
                'code': '// app/api/revalidate/route.ts\n'
                        "import { revalidateTag } from 'next/cache';\n"
                        "import { NextRequest, NextResponse } from 'next/server';\n"
                        '\n'
                        'export async function POST(req: NextRequest) {\n'
                        "  const secret = req.headers.get('x-revalidate-secret');\n"
                        '  if (secret !== process.env.REVALIDATE_SECRET) {\n'
                        '    return NextResponse.json({ ok: false }, { status: 401 });\n'
                        '  }\n'
                        '  // Next.js 16: second argument required; { expire: 0 } expires immediately for '
                        'webhooks\n'
                        "  revalidateTag('posts', { expire: 0 });\n"
                        '  return NextResponse.json({ revalidated: true });\n'
                        '}',
                'code_lang': 'typescript'},
               {'h2': 'Dynamic user data',
                'paragraphs': ["Account pages that read session cookies must never serve another user's "
                               "cache entry. Use cache: 'no-store' on those fetches and read auth in the "
                               "server component, or set dynamic = 'force-dynamic' at the route segment.",
                               'The inventory example from the intro: a cached fetch to /api/stock on a '
                               'route that turns out to be shared. Different users can briefly see each '
                               "other's warehouse counts. The fix is no-store plus moving stock behind an "
                               'authenticated route handler.',
                               'After a fix like that, add a regression test that fetches the same route as '
                               'two sessions and asserts different bodies. Cache bugs are silent without '
                               'tests like that.'],
                'code': 'async function getBalance(userId: string) {\n'
                        '  const res = await fetch(`${process.env.API_URL}/balance/${userId}`, {\n'
                        "    cache: 'no-store',\n"
                        '    headers: { Authorization: `Bearer ${process.env.INTERNAL_TOKEN}` },\n'
                        '  });\n'
                        '  return res.json();\n'
                        '}',
                'code_lang': 'typescript'},
               {'h2': 'Server Actions for mutations',
                'paragraphs': ['Server Actions suit form posts that do not need a separate REST surface: '
                               'update profile, create comment, toggle a flag. Keep them thin — validate '
                               'with Zod, call a service function, revalidate tags, redirect.',
                               'Do not put complex business logic only inside the action file if other entry '
                               'points such as API routes and jobs need the same rules. Extract a shared '
                               'service so authorization checks stay consistent.'],
                'code': "'use server';\n"
                        '\n'
                        "import { z } from 'zod';\n"
                        "import { revalidatePath } from 'next/cache';\n"
                        "import { updateDisplayName } from '@/server/users';\n"
                        '\n'
                        'const schema = z.object({\n'
                        '  displayName: z.string().trim().min(2).max(80),\n'
                        '});\n'
                        '\n'
                        'export async function saveProfile(formData: FormData) {\n'
                        '  const parsed = schema.safeParse({\n'
                        "    displayName: formData.get('displayName'),\n"
                        '  });\n'
                        "  if (!parsed.success) return { error: 'invalid_name' };\n"
                        '\n'
                        '  await updateDisplayName(parsed.data.displayName);\n'
                        "  revalidatePath('/settings/profile');\n"
                        '  return { ok: true };\n'
                        '}',
                'code_lang': 'typescript'},
               {'h2': 'Streaming and Suspense boundaries',
                'paragraphs': ['For pages with a fast shell and a slow panel, wrap the slow Server Component '
                               'in Suspense so the shell streams first. Users see navigation chrome and a '
                               'skeleton while the slow fetch completes. That improves perceived performance '
                               'even when total time-to-full-content stays similar.',
                               'Avoid putting the entire page behind one slow await at the top of the tree. '
                               'A single blocking await getEverything() defeats streaming. Split fetches by '
                               'section. Error boundaries around streamed sections stop one failing '
                               'widget—say, a recommendations panel returning 500—from blanking the whole '
                               'product page.']},
               {'h2': 'Auth cookies and the cache',
                'paragraphs': ['Reading cookies in a layout opts routes into dynamic rendering. That is '
                               'correct for dashboards and easy to forget on a shared root layout that also '
                               'wraps marketing pages. Split layouts so public marketing stays statically '
                               'cacheable while app routes stay dynamic.',
                               'If you must read cookies deep in a tree, be intentional about which segments '
                               'inherit dynamic behavior. Accidental dynamic marketing pages raised origin '
                               'load and erased the TTFB wins from ISR.'],
                'code': '// app/(marketing)/layout.tsx — no cookies(), cache-friendly\n'
                        'export default function MarketingLayout({ children }) {\n'
                        '  return <div className="marketing">{children}</div>;\n'
                        '}\n'
                        '\n'
                        '// app/(app)/layout.tsx — auth-aware, dynamic\n'
                        "import { cookies } from 'next/headers';\n"
                        '\n'
                        'export default async function AppLayout({ children }) {\n'
                        "  const session = (await cookies()).get('access_token');\n"
                        '  return <AppShell signedIn={Boolean(session)}>{children}</AppShell>;\n'
                        '}',
                'code_lang': 'typescript'},
               {'h2': 'Client fetch versus Server Components',
                'paragraphs': ['Keep initial data on the server when SEO or first paint matters. Client '
                               'components can use SWR or React Query for interactive polling and filters. '
                               'Duplicating the same REST call on server and client without a shared '
                               'contract causes drift — generate types from OpenAPI and share the path '
                               'helpers.',
                               'Server Actions work well for mutations with progressive enhancement. Still '
                               'validate on the server with Zod; never trust the action payload shape '
                               'alone.'],
                'bullets': ['Be explicit: revalidate, no-store, or force-dynamic',
                            'Tag cached fetches for webhook-driven updates',
                            'Never cache personalized responses under a shared key',
                            'Prefer Server Components for first paint; client libraries for live '
                            'interactivity',
                            'Protect revalidate endpoints with a secret',
                            'Regression-test personalized routes across two sessions']},
               {'h2': 'Debugging why is this stale',
                'paragraphs': ['Check whether you are looking at the Full Route Cache, the Data Cache, or '
                               'the browser cache. The Next.js dev overlay and logging fetch cache hits in '
                               'development help. A CDN in front of Next can also cache HTML despite '
                               'no-store on fetch — in that case set Cache-Control on the route’s response '
                               'headers.',
                               'Document the caching choice in a one-line comment above non-obvious fetches. '
                               'A good incident checklist order: response headers in the browser, Next fetch '
                               'cache tags, CDN purge, and whether the deploy rolled out to all regions. '
                               'Skipping the CDN step is the most common way to lose an hour. When in doubt, '
                               'draw three boxes — Data Cache, Full Route Cache, CDN — and mark where the '
                               'stale bytes live.']}],
  'takeaways': ['Treat every App Router fetch as needing an explicit cache policy.',
                'Use time-based revalidate for public content; tags for editor-driven updates.',
                'Personalized and financial data should use no-store or force-dynamic.',
                'Server Components for initial HTML; client caches for interactive freshness.',
                'Stale bugs can live in Next caches, the browser, or your CDN — check all three.',
                'Validate Server Action input with Zod and share business logic with other entry points.']},
 {'slug': 'postgresql-indexes-explained',
  'title': 'PostgreSQL Indexes Explained: When B-tree Helps, When It Hurts',
  'description': 'How to decide when to add B-tree indexes, read EXPLAIN ANALYZE, and avoid write-heavy '
                 'indexes that slow an API more than they help.',
  'category': 'Databases',
  'date': '2026-06-21',
  'updated': '2026-10-09',
  'read_min': 12,
  'keywords': 'PostgreSQL indexes, B-tree, EXPLAIN ANALYZE, query performance, index selectivity, Postgres',
  'excerpt': 'Adding indexes in a panic can make writes several times slower. Ship only the indexes backed '
             'by EXPLAIN ANALYZE and a note about the workload they serve.',
  'sections': [{'h2': 'What a B-tree index is paying for',
                'paragraphs': ['A B-tree index is a sorted structure Postgres maintains beside the heap '
                               'table. Point lookups and range scans on the indexed columns become '
                               'logarithmic instead of sequential. The cost: every INSERT, UPDATE, and '
                               'DELETE must update matching indexes. Indexing six columns of a busy events '
                               'table “just in case” can multiply insert latency.',
                               'Low-cardinality columns such as is_active boolean alone rarely deserve a '
                               'standalone B-tree. Postgres may still seq-scan if half the rows match. '
                               'Composite or partial indexes are usually smarter.',
                               'Keep a list of candidate indexes with the query from APM, current p95, '
                               'estimated rows, the proposed definition, and the write-path impact. If you '
                               'cannot fill those cells, do not create the index yet.']},
               {'h2': 'EXPLAIN ANALYZE before and after',
                'paragraphs': ['Never argue about indexes without plans. EXPLAIN (ANALYZE, BUFFERS) on a '
                               'production-sized copy or anonymized dump shows actual time and whether an '
                               'Index Scan or Bitmap Index Scan appeared.',
                               'Watch for Seq Scan on multi-million-row tables with a selective WHERE, and '
                               'for Index Scan that still filters most rows because the index does not match '
                               'the predicate well. Also compare shared hit versus read buffers — an index '
                               'that lives in RAM behaves differently under cold cache.'],
                'code': 'EXPLAIN (ANALYZE, BUFFERS)\n'
                        'SELECT *\n'
                        'FROM orders\n'
                        'WHERE customer_id = 48291\n'
                        "  AND created_at >= NOW() - INTERVAL '30 days'\n"
                        'ORDER BY created_at DESC\n'
                        'LIMIT 50;',
                'code_lang': 'sql'},
               {'h2': 'Composite order matters',
                'paragraphs': ['For the query above, customer_id then created_at DESC matches equality then '
                               'sort or range. created_at then customer_id is weaker for that filter '
                               'pattern. The leftmost-prefix rule familiar from MySQL still applies to the '
                               'default B-tree.',
                               'Build that index with CREATE INDEX CONCURRENTLY on orders (customer_id, '
                               'created_at DESC). On a multi-million-row table, a query like this typically '
                               'drops from a sequential scan taking hundreds of milliseconds to an index '
                               'scan taking a few. CONCURRENTLY matters because a plain CREATE INDEX blocks '
                               'writes to the table for the whole build.',
                               'INCLUDE columns can help a report query avoid heap fetches: include status '
                               'and total_cents so an index-only scan answers the list view. Check heap '
                               'fetches in EXPLAIN before celebrating.'],
                'code': '-- Prefer concurrent builds in production\n'
                        'CREATE INDEX CONCURRENTLY idx_orders_customer_created\n'
                        '  ON orders (customer_id, created_at DESC);\n'
                        '\n'
                        '-- Partial index: only open tickets (smaller, faster)\n'
                        'CREATE INDEX CONCURRENTLY idx_tickets_open_assignee\n'
                        '  ON tickets (assignee_id)\n'
                        "  WHERE status = 'open';",
                'code_lang': 'sql'},
               {'h2': 'When indexes hurt',
                'paragraphs': ['Write-heavy tables with indexes unused by queries are pure overhead. '
                               'Functions wrapping columns such as LOWER(email) cannot use a plain email '
                               'index unless you create an expression index on LOWER(email). Leading '
                               'wildcards in LIKE will not use a normal B-tree; consider pg_trgm when search '
                               'needs it.',
                               'Too many overlapping indexes confuse the planner and waste cache. Audit '
                               'pg_stat_user_indexes for idx_scan = 0 after a meaningful period of weeks, '
                               'not hours.',
                               'On write-heavy tables, dropping indexes that no query uses often improves '
                               'insert latency more than any read path suffers, and frees significant disk.'],
                'bullets': ['Measure with EXPLAIN ANALYZE on realistic data volumes',
                            'Match composite column order to filter plus sort patterns',
                            'Prefer partial indexes for common status filters',
                            'Build CONCURRENTLY in prod to avoid long write locks',
                            'Drop unused indexes after watching idx_scan']},
               {'h2': 'Finding dead indexes in production',
                'paragraphs': ['After a couple of weeks of real traffic, query pg_stat_user_indexes together '
                               'with pg_relation_size. Anything with zero scans and non-trivial size goes on '
                               'a drop-candidate list. Exclude brand-new indexes and unique constraints that '
                               'enforce correctness even if rarely used for reads.',
                               'Drop one at a time during low traffic, watch APM for a week, then continue. '
                               'Never bulk-drop six indexes before a holiday weekend.'],
                'code': 'SELECT\n'
                        "  schemaname || '.' || relname AS table,\n"
                        '  indexrelname AS index,\n'
                        '  idx_scan,\n'
                        '  pg_size_pretty(pg_relation_size(indexrelid)) AS size\n'
                        'FROM pg_stat_user_indexes\n'
                        'WHERE idx_scan = 0\n'
                        'ORDER BY pg_relation_size(indexrelid) DESC\n'
                        'LIMIT 20;',
                'code_lang': 'sql'},
               {'h2': 'Unique constraints are indexes too',
                'paragraphs': ['A UNIQUE constraint creates a unique B-tree. Do not also add a redundant '
                               'non-unique index on the same columns—migrations that create both pay double '
                               'write cost for no gain.',
                               'Partial unique indexes are excellent for soft-delete: unique on email where '
                               'deleted_at is null lets you reuse emails after delete without complicated '
                               'application checks, and removes the race conditions of app-level uniqueness '
                               'checks.'],
                'code': 'CREATE UNIQUE INDEX CONCURRENTLY idx_users_email_active\n'
                        '  ON users (email)\n'
                        '  WHERE deleted_at IS NULL;',
                'code_lang': 'sql'},
               {'h2': 'Maintenance to schedule',
                'paragraphs': ['Autovacuum usually keeps things healthy; bloated indexes after bulk deletes '
                               'sometimes need REINDEX CONCURRENTLY. Alert when table bloat estimates cross '
                               'a threshold rather than reindexing on a fixed calendar.',
                               'Foreign keys deserve indexes on the referencing column — not only for reads, '
                               'but so ON DELETE cascades do not seq-scan child tables. A missing FK index '
                               'can turn deleting one parent row into a multi-second operation.']},
               {'h2': 'Staging with production-shaped data',
                'paragraphs': ['Plans flip with scale. On 50k rows almost everything looks fine. On 20M rows '
                               'the planner chooses differently. Refresh a sanitized staging database from '
                               'production regularly for index experiments, with PII scrubbed.',
                               'Run EXPLAIN ANALYZE at least three times and discard the coldest run when '
                               'comparing. Then test under a light write load, because an index that helps a '
                               'read-only session can still hurt the API when inserts contend on the same '
                               'pages. Uniform random foreign keys produce unrealistically perfect indexes; '
                               'real customers cluster.']},
               {'h2': 'Monitoring after ship',
                'paragraphs': ['After creating an index, watch query p95 from APM, insert and update p95 on '
                               'the table, index size growth, and vacuum activity. A week of green metrics '
                               'earns a note in the runbook; a write regression earns a revert even if the '
                               'read looks prettier.',
                               'Also check whether the planner actually uses the new index. An index that '
                               'never gets selected is pure cost. Sometimes statistics are stale — running '
                               'ANALYZE on the table after a bulk import often fixes a stubborn seq scan.']},
               {'h2': 'A small decision framework',
                'paragraphs': ['Slow query in APM, capture SQL, run EXPLAIN ANALYZE, if seq scan on large '
                               'table and selective filter then design minimal index, create concurrently on '
                               'staging, compare plans and write p95, then ship. If the filter returns more '
                               'than 20 to 30 percent of the table, rethink; a seq scan may already be '
                               'optimal.',
                               'Ship the smallest index that changes the plan. You can always add INCLUDE '
                               'columns later; removing a wide unused index under write load is harder '
                               'socially than technically.']}],
  'takeaways': ['Indexes speed reads and tax writes — prove the trade with EXPLAIN ANALYZE.',
                'Composite column order should follow equality filters then range or sort.',
                'Partial and expression indexes beat scattershot single-column indexes.',
                'Use CREATE INDEX CONCURRENTLY in production.',
                'Audit idx_scan and remove indexes that never earn their keep.',
                'Index foreign key columns so deletes and joins do not seq-scan children.']},
 {'slug': 'git-rebase-vs-merge',
  'title': 'Git Rebase vs Merge: A Safe Workflow for Feature Branches',
  'description': 'When to rebase, when to merge, how to avoid rewriting shared history, and the exact '
                 'commands for a clean PR timeline.',
  'category': 'Developer Tools',
  'date': '2026-06-25',
  'updated': '2026-10-09',
  'read_min': 12,
  'keywords': 'git rebase vs merge, interactive rebase, feature branch workflow, git pull --rebase, safe git '
              'history',
  'excerpt': 'Rebase versus merge is not religion. It comes down to whether the commits are private and '
             'whether you want a linear PR history.',
  'sections': [{'h2': 'The rule that prevents disasters',
                'paragraphs': ['Never rebase commits that other people already pulled. Rebase rewrites SHAs. '
                               'If main or a shared long-lived branch gets rebased, everyone else must '
                               'recover with reset and rebase gymnastics. Only rebase local feature branches '
                               'that you own.',
                               'Merge commits preserve exact history and branching topology. Rebase replays '
                               'your commits on top of an updated base for a straight-line story. Both are '
                               'valid; mixing them without a team convention is what hurts.',
                               'Write this down as a one-page CONTRIBUTING rule before a shared-branch '
                               'rewrite costs the team an afternoon of recovery. Conventions beat cleverness '
                               'here.']},
               {'h2': 'Daily sync: pull --rebase on feature branches',
                'paragraphs': ['While building a feature, keep the branch current with git fetch origin and '
                               'git rebase origin/main, or git pull --rebase origin main. That surfaces '
                               'conflicts early in small chunks instead of one monster merge at PR time.',
                               'Set pull.rebase true locally for feature work. Shared release branches still '
                               'merge.',
                               'Rebase at least once a day on long features. Waiting a week means resolving '
                               'the same conflict across many commits: early rebases take minutes, while a '
                               'late rebase of a branch that touches shared types can take far longer.'],
                'code': '# Update feature branch onto latest main\n'
                        'git fetch origin\n'
                        'git switch feature/billing-retry\n'
                        'git rebase origin/main\n'
                        '\n'
                        '# If conflicts: fix files, then\n'
                        'git add .\n'
                        'git rebase --continue\n'
                        '\n'
                        '# Abort if it goes sideways\n'
                        'git rebase --abort',
                'code_lang': 'bash'},
               {'h2': 'Cleaning the story before review',
                'paragraphs': ['Before requesting review, run an interactive rebase onto origin/main and '
                               'squash wip and fix-typo commits into logical units. Reviewers get 3 commits '
                               'that mean something instead of 27 noise commits. A force-push is required '
                               'afterward — only on your own feature branch, and with --force-with-lease so '
                               'you do not clobber unexpected remote commits.',
                               'Aim for commits that each leave tests green, so anyone can bisect later if '
                               'something regresses. A single squash of a week of work is fine for tiny PRs; '
                               'for multi-day features, keep a short narrative.'],
                'code': 'git rebase -i origin/main\n'
                        '# mark commits as squash/fix/reword\n'
                        '\n'
                        'git push --force-with-lease origin feature/billing-retry',
                'code_lang': 'bash'},
               {'h2': 'Merging into main',
                'paragraphs': ['On GitHub, Squash and merge suits small PRs: main stays linear with one '
                               'commit per feature. For larger multi-commit PRs that tell a deliberate '
                               'story, use merge commits or rebase-and-merge depending on the repo setting.',
                               'Avoid rebasing main onto a feature branch in public view. The integration '
                               'direction is: update the feature onto main, then merge the feature into main '
                               'via the PR UI.',
                               'Release branches freeze with merge-only. Hotfixes branch from the release '
                               'tag, merge back to release and to main. Trying to rebase a hotfix that QA '
                               'already tested is how you get works-on-my-machine checksum mismatches.']},
               {'h2': 'When merge is the better tool',
                'paragraphs': ['Long-running release branches, hotfixes already shared, and any branch '
                               'multiple people push to — merge. Also when you need to preserve the exact '
                               'fact that two lines of development coexisted; compliance and audit trails '
                               'sometimes care.',
                               'Rebasing a shared develop branch “to clean up history” is the classic way to '
                               'lose half a day of everyone’s time. Write the rule down before it happens, '
                               'not after.'],
                'bullets': ['Private feature branch — rebase onto main is fine',
                            'Shared branch — merge only',
                            'Force push only with --force-with-lease on your branch',
                            'Resolve conflicts during rebase carefully; abort when unsure',
                            'Prefer early rebases over one giant conflict at the end',
                            'Release and hotfix branches stay merge-only']},
               {'h2': 'Recovering when a rebase goes wrong',
                'paragraphs': ['git rebase --abort is the first escape hatch if you are still mid-rebase. If '
                               'you already finished and force-pushed something bad, git reflog usually '
                               'still has the previous tip for a while. Restore with git reset --hard '
                               'ORIG_HEAD immediately after a bad rebase, or the branch reflog entry '
                               '(feature/billing-retry@{1}) when ORIG_HEAD is gone. HEAD@{1} does not work '
                               "here: HEAD's reflog records every step of the rebase, so it usually points "
                               'at the last replayed commit.',
                               'Tell anyone who pulled the bad tip to reset to the restored SHA. '
                               'Communication matters more than the exact command once history diverged on a '
                               'shared remote.'],
                'code': '# Still in a rebase?\n'
                        'git rebase --abort\n'
                        '\n'
                        '# Just finished a bad rebase, not pushed yet\n'
                        'git reset --hard ORIG_HEAD\n'
                        '\n'
                        '# Already pushed; recover the pre-rebase tip from the branch reflog, then '
                        'force-with-lease\n'
                        'git reflog show feature/billing-retry\n'
                        'git reset --hard feature/billing-retry@{1}\n'
                        'git push --force-with-lease origin feature/billing-retry',
                'code_lang': 'bash'},
               {'h2': 'What to tell new teammates on day one',
                'paragraphs': ['Update your feature branch with rebase onto main. Open PRs from feature into '
                               'main. Never force-push main. Never rebase a branch two people are committing '
                               'to. When unsure, merge and ask in Slack — a merge commit is cheap compared '
                               'with rewriting shared history.',
                               'Pair on the first interactive rebase. Squash, fixup, and reword become '
                               'muscle memory after one guided session; without that session people either '
                               'never clean history or force-push scared. CI must be green after a rebase '
                               'before review.']},
               {'h2': 'PR settings worth standardizing',
                'paragraphs': ['Repos that prefer a linear main enable Allow squash merging and disable '
                               'merge commits, or enable rebase-merging carefully. Mixed settings across '
                               'repos leave people unsure whether they should clean history locally.',
                               'CI workflows triggered on push and pull request updates re-run on a '
                               'force-pushed feature branch, and required status checks on main block the '
                               'merge until they pass. That is good. Wait for green after a force-with-lease '
                               'before pinging reviewers again so they do not review an already-superseded '
                               'SHA. Branch protection on main rejects force pushes; feature branches stay '
                               'unprotected so rebase workflows work.'],
                'bullets': ['Protect main against force push and direct commits',
                            'Allow force-with-lease on personal feature branches',
                            'Re-run CI after every rebase push',
                            'Agree repo-wide on squash versus merge versus rebase-merge']},
               {'h2': 'Bisect loves clean history',
                'paragraphs': ['When a production bug lands, git bisect across squash-merged main finds the '
                               'PR quickly. Across a week of WIP commits on a long-lived branch, bisect '
                               'lands on “wip fix again” and wastes time. That is a practical reason to '
                               'clean feature history before merge, not an aesthetic one.',
                               'If you must keep fine-grained commits on main for blame archaeology, say so '
                               'in the repo guide and use merge or rebase-merge consistently. Silent policy '
                               'differences between teams sharing a monorepo cause the worst arguments. A '
                               'sound default: rebase privately, merge publicly through the PR button, '
                               'recover with reflog, and optimize for a bisectable main.']},
               {'h2': 'Conflict survival tips',
                'paragraphs': ['During rebase, conflicted files are your commit applied onto newer main. '
                               'Read both sides. Run tests after continue. If the same conflict repeats '
                               'across commits, consider squashing first so you fix it once.',
                               'For binary files or generated lockfile hell, sometimes aborting, merging '
                               'main into the feature branch once, and fixing lockfiles in a single merge '
                               'commit is less painful than rebasing 15 lockfile bumps. Pragmatism beats '
                               'purity.',
                               'Keep a list of files that always conflict, such as generated GraphQL types '
                               'and lockfiles. For those, regenerate from source after resolving rather than '
                               'hand-merging thousands of lines.']}],
  'takeaways': ['Rebase private feature branches; never rewrite shared history.',
                'Pull with rebase to catch conflicts early while commits are fresh.',
                'Interactive rebase before review to remove WIP noise.',
                'Use --force-with-lease, not bare --force, when updating a feature remote.',
                'Choose squash, merge, or rebase-merge at PR time based on the story you want on main.',
                'Know rebase --abort and reflog recovery before you need them under pressure.']},
 {'slug': 'typescript-generics-practical-guide',
  'title': 'Practical TypeScript Generics for APIs and React Props',
  'description': 'Generics that earn their keep: typed API clients, reusable React list props, constraints, '
                 'and the mistakes that make types worse than any.',
  'category': 'Frontend',
  'date': '2026-06-28',
  'read_min': 12,
  'keywords': 'TypeScript generics, React props generics, typed fetch, generic constraints, TypeScript API '
              'client',
  'excerpt': 'It is tempting to skip generics and sprinkle as-casts instead. Once an API client and a few '
             'shared components are typed properly, a whole class of runtime bugs becomes compile errors.',
  'sections': [{'h2': 'Start from a pain point, not from theory',
                'paragraphs': ["A typical failure: an untyped api.get('/users') returns Promise<any>. Call "
                               'sites assume name exists; the backend renames it to fullName. Runtime crash, '
                               'green CI. A generic get<T> forces the call site to declare the expected '
                               'shape — still a contract, but one that is checked when shared types are '
                               'regenerated from OpenAPI.',
                               'Generics are functions and types parameterized by other types. Introduce '
                               'them when the same logic works for multiple shapes and you want the output '
                               'type to follow the input.',
                               'Once types are generated from OpenAPI and threaded through apiGet<User>, '
                               'that class of rename bug becomes a tsc failure in CI instead of a production '
                               '500.']},
               {'h2': 'Typed fetch wrapper',
                'paragraphs': ['This is usually the first generic worth adding to a TypeScript frontend. The '
                               'caller passes the response type; errors stay explicit.',
                               'Add apiPost with body and response type parameters too, so request bodies '
                               'are checked. Typing responses carefully while sending untyped payloads only '
                               'solves half the problem.'],
                'code': 'export class ApiError extends Error {\n'
                        '  constructor(public status: number, message: string) {\n'
                        '    super(message);\n'
                        '  }\n'
                        '}\n'
                        '\n'
                        'export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {\n'
                        '  const res = await fetch(path, {\n'
                        '    ...init,\n'
                        "    headers: { Accept: 'application/json', ...init?.headers },\n"
                        '  });\n'
                        '  if (!res.ok) {\n'
                        '    throw new ApiError(res.status, await res.text());\n'
                        '  }\n'
                        '  return res.json() as Promise<T>;\n'
                        '}\n'
                        '\n'
                        '// usage\n'
                        'type User = { id: string; fullName: string };\n'
                        "const user = await apiGet<User>('/api/users/me');\n"
                        'console.log(user.fullName);',
                'code_lang': 'typescript'},
               {'h2': 'Constraints beat unconstrained T',
                'paragraphs': ['If you need to read id inside the generic function, constrain T. '
                               'Unconstrained T cannot safely access properties — and if you cast anyway, '
                               'you lied to the compiler.',
                               'Multiple constraints use intersection types. Keep them readable; if the '
                               'constraint needs three lines, extract a named interface.'],
                'code': 'function byId<T extends { id: string }>(items: T[], id: string): T | undefined {\n'
                        '  return items.find((item) => item.id === id);\n'
                        '}\n'
                        '\n'
                        'const users = [\n'
                        "  { id: '1', fullName: 'Ram' },\n"
                        "  { id: '2', fullName: 'Ada' },\n"
                        '];\n'
                        "const found = byId(users, '2'); // type includes fullName",
                'code_lang': 'typescript'},
               {'h2': 'React props that preserve item types',
                'paragraphs': ['Shared Select and Table components often erase types with items any array. A '
                               'generic component keeps item type through render props.',
                               'Inference usually works when items is passed inline. If TypeScript widens to '
                               'a useless type, pass an explicit type argument once. Prefer inference '
                               'first.'],
                'code': 'type ListProps<T> = {\n'
                        '  items: T[];\n'
                        '  keyOf: (item: T) => string;\n'
                        '  children: (item: T) => React.ReactNode;\n'
                        '};\n'
                        '\n'
                        'export function List<T>({ items, keyOf, children }: ListProps<T>) {\n'
                        '  return (\n'
                        '    <ul>\n'
                        '      {items.map((item) => (\n'
                        '        <li key={keyOf(item)}>{children(item)}</li>\n'
                        '      ))}\n'
                        '    </ul>\n'
                        '  );\n'
                        '}\n'
                        '\n'
                        '// inference works — item is User inside children\n'
                        '<List\n'
                        '  items={users}\n'
                        '  keyOf={(u) => u.id}\n'
                        '  children={(u) => <span>{u.fullName}</span>}\n'
                        '/>;',
                'code_lang': 'tsx'},
               {'h2': 'Defaults and keyof patterns',
                'paragraphs': ['Generic defaults help when most call sites share a type. keyof plus mapped '
                               'types power type-safe sorting helpers. Keep these shallow — deep conditional '
                               'type wizardry slows compile times and confuses newer developers more than it '
                               'helps.',
                               'A Pick or Omit wrapper around API responses is often clearer than a custom '
                               'conditional type. Reach for the built-ins before inventing a new type-level '
                               'DSL.'],
                'code': 'function sortBy<T, K extends keyof T>(items: T[], key: K): T[] {\n'
                        '  return [...items].sort((a, b) => (a[key] > b[key] ? 1 : -1));\n'
                        '}\n'
                        '\n'
                        "sortBy(users, 'fullName');\n"
                        "// sortBy(users, 'nope'); // compile error",
                'code_lang': 'typescript'},
               {'h2': 'Result types instead of throwing everywhere',
                'paragraphs': ['Another place generics shine is a small Result T E for expected failures. '
                               'Call sites must handle ok false instead of hoping a try/catch exists three '
                               'layers up.',
                               'Use it for form validation and for API calls that can 404 without being '
                               'exceptional. Keep throwing for truly unexpected failures.'],
                'code': 'type Result<T, E = string> =\n'
                        '  | { ok: true; value: T }\n'
                        '  | { ok: false; error: E };\n'
                        '\n'
                        "async function loadUser(id: string): Promise<Result<User, 'not_found' | 'network'>> "
                        '{\n'
                        '  try {\n'
                        '    const user = await apiGet<User>(`/api/users/${id}`);\n'
                        '    return { ok: true, value: user };\n'
                        '  } catch (err) {\n'
                        '    if (err instanceof ApiError && err.status === 404) {\n'
                        "      return { ok: false, error: 'not_found' };\n"
                        '    }\n'
                        "    return { ok: false, error: 'network' };\n"
                        '  }\n'
                        '}',
                'code_lang': 'typescript'},
               {'h2': 'Generic hooks without pain',
                'paragraphs': ['Custom hooks benefit from generics the same way components do. '
                               'useLocalStorage T should return T or undefined and accept values that know '
                               'T. Without that, every call site casts.',
                               'Keep hook generics to one or two type parameters. When a hook needs four '
                               'type params, it is usually doing too much and should split into smaller '
                               'hooks or accept a typed adapter object.'],
                'code': 'function useLocalStorage<T>(key: string, initial: T) {\n'
                        '  const [value, setValue] = useState<T>(() => {\n'
                        "    if (typeof window === 'undefined') return initial;\n"
                        '    const raw = window.localStorage.getItem(key);\n'
                        '    return raw ? (JSON.parse(raw) as T) : initial;\n'
                        '  });\n'
                        '\n'
                        '  useEffect(() => {\n'
                        '    window.localStorage.setItem(key, JSON.stringify(value));\n'
                        '  }, [key, value]);\n'
                        '\n'
                        '  return [value, setValue] as const;\n'
                        '}\n'
                        '\n'
                        "const [draft, setDraft] = useLocalStorage<{ fullName: string }>('draft', { "
                        "fullName: '' });",
                'code_lang': 'typescript'},
               {'h2': 'Mapping API DTOs to domain types',
                'paragraphs': ['Generated OpenAPI types are often noisy. Write small mappers such as '
                               'toUser(dto: UserDto). Generics help for lists when composed, but a '
                               'hyper-abstract Mapper with four type params rarely helps anyone and tends to '
                               'slow onboarding.',
                               'Zod schemas can infer types with z.infer<typeof schema>, which often removes '
                               'the need for a hand-written interface plus a generic parse helper. Prefer '
                               'schema-first when validation already exists at the boundary.']},
               {'h2': 'Mistakes that made types worse',
                'paragraphs': ['Defaulting T to any silently undoes safety. Over-generic components with '
                               'five type params nobody can invoke. Returning T or any from a helper. Using '
                               'generics where a simple union of two shapes was clearer.',
                               'Using React.FC with generics is awkward and inconsistent; type props '
                               'directly on the function instead. Measure complexity: if the generic needs a '
                               'paragraph of explanation in the PR, consider two named functions instead.',
                               'Compile-time cost is real. A few heavy conditional types in hot paths can '
                               'add noticeable seconds to tsc in a monorepo; simplify them and the typecheck '
                               'job gets faster. A reasonable bar for merging a new generic helper: at least '
                               'three call sites, a constraint that matches real field access, and a PR '
                               'description that shows a before/after compile error it prevents.'],
                'bullets': ['Add generics when output types should track input types',
                            'Constrain with extends when you read properties',
                            'Prefer inference at call sites over mandatory type arguments',
                            'Avoid defaulting T to any',
                            'Generate API types when possible instead of hand-rolling large interfaces',
                            'Prefer Result or union handling for expected failures over unchecked throws']}],
  'takeaways': ['A generic apiGet T turns silent any into checked contracts at call sites.',
                'Use extends constraints when the generic body reads fields.',
                'Generic React list and select components preserve item types through callbacks.',
                'keyof patterns catch invalid field names at compile time.',
                'Keep generics shallow — unclear type params are worse than a bit of duplication.',
                'Result T E makes expected failure paths visible at the type level.'],
  'updated': '2026-10-09'}]
