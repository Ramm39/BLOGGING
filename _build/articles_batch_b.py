ARTICLES = [{'slug': 'css-flexbox-vs-grid',
  'title': 'Flexbox vs CSS Grid: When I Use Each in Production Layouts',
  'description': 'A practical decision guide for Flexbox vs CSS Grid with real layout patterns, '
                 'common mistakes, and copy-paste CSS from production UIs.',
  'category': 'Frontend',
  'date': '2026-07-01',
  'read_min': 7,
  'keywords': 'css flexbox vs grid, css grid layout, flexbox tutorial, responsive layout css, css '
              'layout guide',
  'excerpt': 'I wasted weeks fighting Flexbox for two-dimensional pages before Grid existed in my '
             'muscle memory. Here is the rule I use now, with the layouts people actually search '
             'for.',
  'sections': [{'h2': 'The one-line rule that stopped my layout thrashing',
                'paragraphs': ['If content flows in one direction—a nav row, a toolbar, a stack of '
                               'cards that wrap—I reach for Flexbox. If I need to control rows and '
                               'columns together—a dashboard, a form with aligned labels, a media '
                               'object with a sidebar—I reach for Grid. Mixing both is fine; '
                               'treating every page as a Flexbox puzzle is not.',
                               'I learned this the hard way on a SaaS settings page. I nested flex '
                               'containers four deep to align a label column with inputs. Every '
                               'breakpoint needed new magic numbers. Rewriting the same markup '
                               'with CSS Grid cut the stylesheet by about 40% and removed three '
                               'media-query special cases.',
                               'The mental model that stuck: Flexbox distributes leftover space '
                               'along an axis. Grid places items into a coordinate system. When '
                               'you catch yourself calculating widths so column two lines up with '
                               'column two on the next row, you are doing Grid’s job by hand.',
                               'When a designer hands me a Figma frame, I mark axes in my head '
                               'first. One axis of alignment usually means Flexbox in the '
                               'component. Two axes of alignment across the page means Grid at the '
                               'layout root. That 30-second skim prevents a day of nested '
                               'wrappers.']},
               {'h2': 'Flexbox layouts I ship constantly',
                'paragraphs': ['Navbar with logo left and actions right is still Flexbox '
                               'territory. Space-between, gap, and align-items:center get you 90% '
                               'of the way without a grid template. Same for button groups, tag '
                               'chips, and avatar-plus-name rows.',
                               'Wrapping card rows also work well with flex-wrap. The catch: '
                               'equal-height columns across a wrap line are awkward in Flexbox. If '
                               'your cards must share a row height and align internal footers, '
                               'Grid usually wins.',
                               'Another Flexbox win: sticky footers inside a card. Column '
                               'direction, flex:1 on the body, footer sits at the bottom even when '
                               'content is short. I used to absolute-position footers and break '
                               'when titles wrapped to three lines.',
                               'Flexbox also wins for equal-width button rows inside modals and '
                               'for icon+label pairs in side navigation. I keep max-width on the '
                               'flex container rather than fighting flex-basis on every child when '
                               'the design calls for a centered compact group.'],
                'code': '.nav {\n'
                        '  display: flex;\n'
                        '  align-items: center;\n'
                        '  justify-content: space-between;\n'
                        '  gap: 1rem;\n'
                        '}\n'
                        '\n'
                        '.nav__actions {\n'
                        '  display: flex;\n'
                        '  align-items: center;\n'
                        '  gap: 0.75rem;\n'
                        '}\n'
                        '\n'
                        '.card {\n'
                        '  display: flex;\n'
                        '  flex-direction: column;\n'
                        '  min-height: 100%;\n'
                        '}\n'
                        '\n'
                        '.card__body { flex: 1; }',
                'code_lang': 'css'},
               {'h2': 'Grid layouts people actually search for',
                'paragraphs': ['Holy grail / app shell: header, sidebar, main, footer. Define '
                               'named areas once and stop fighting float leftovers. Card grids '
                               'with consistent gutters: repeat(auto-fit, minmax(280px, 1fr)) is '
                               'my default for marketing feature grids and blog indexes.',
                               'Form layouts where labels and fields must line up across rows are '
                               'Grid’s sweet spot. I used to fake this with fixed-width flex '
                               'children and got broken layouts when labels wrapped in German and '
                               'French locales.',
                               'Media objects (thumbnail left, copy right) can be either tool. I '
                               'use Grid when the image column must stay a fixed track while text '
                               'wraps cleanly: `grid-template-columns: 96px 1fr`. Flex works too '
                               'until someone asks for the image to span two text rows.',
                               'Search pages with filters on the left and results on the right are '
                               'textbook Grid. On mobile I collapse to a single column and move '
                               'filters into a drawer—still Grid areas, just remapped. Trying to '
                               'encode that remapping with Flex order alone becomes unreadable.'],
                'code': '.app-shell {\n'
                        '  display: grid;\n'
                        '  grid-template-columns: 240px 1fr;\n'
                        '  grid-template-rows: auto 1fr auto;\n'
                        '  grid-template-areas:\n'
                        '    "header header"\n'
                        '    "sidebar main"\n'
                        '    "footer footer";\n'
                        '  min-height: 100vh;\n'
                        '}\n'
                        '\n'
                        '.header { grid-area: header; }\n'
                        '.sidebar { grid-area: sidebar; }\n'
                        '.main { grid-area: main; }\n'
                        '.footer { grid-area: footer; }\n'
                        '\n'
                        '@media (max-width: 768px) {\n'
                        '  .app-shell {\n'
                        '    grid-template-columns: 1fr;\n'
                        '    grid-template-areas:\n'
                        '      "header"\n'
                        '      "main"\n'
                        '      "footer";\n'
                        '  }\n'
                        '  .sidebar { display: none; }\n'
                        '}',
                'code_lang': 'css'},
               {'h2': 'Mistakes that burned hours',
                'paragraphs': ['Mistake one: using Flexbox percentage widths plus margin for '
                               'gutters. Gap exists. Use it. Mistake two: putting display:flex on '
                               'every wrapper “just in case.” That breaks shrink/grow expectations '
                               'and makes overflow bugs hard to find.',
                               'Mistake three: fighting Grid with nested absolute positioning for '
                               '“one cell that spans.” Learn grid-column: span 2 and grid-row '
                               'before inventing overlays. Mistake four: forgetting min-width: 0 '
                               'on flex/grid children that hold long URLs or code—those children '
                               'refuse to shrink and blow out the page.',
                               'Mistake five: using justify-content when I meant justify-items (or '
                               'the reverse). Flex and Grid share vocabulary but not all '
                               'properties. I still keep a tiny cheatsheet in the repo wiki '
                               'because that mixup is embarrassing in code review.',
                               'A subtler bug: flex items default to min-width:auto, which '
                               'respects content size. Tables and pre blocks inside flex children '
                               'are frequent offenders. Setting min-width:0 on the scrolling pane '
                               'is the fix I look for first when horizontal overflow appears only '
                               'in production content.'],
                'bullets': ['Prefer gap over margin hacks for spacing between siblings',
                            'Add min-width: 0 (or min-height: 0) on scrollable flex/grid children',
                            'Use Grid for two-axis alignment; Flex for one-axis distribution',
                            'Avoid nesting more than two layout systems deep without a reason',
                            'Name grid areas for app shells—future you will thank present you']},
               {'h2': 'A hybrid pattern I use on dashboards',
                'paragraphs': ['Outer page structure is Grid. Inside each panel, the toolbar and '
                               'list are Flexbox. That split keeps templates readable: Grid owns '
                               'placement, Flex owns content alignment.',
                               'For a metric card row that must stay three-up on desktop and stack '
                               'on mobile, I use Grid with auto-fit. For the card’s internal '
                               'header (title left, badge right), Flexbox. Do not force one tool '
                               'to do both jobs.',
                               'When a designer asks for “this card spans two columns on the third '
                               'row only,” that is Grid. Encoding that with Flex order tricks is '
                               'how stylesheets become haunted houses.',
                               'Design systems should document which primitive owns which pattern. '
                               'Our internal rule is: layout primitives export Grid shells; '
                               'molecules use Flex for their internals. Contributors stop '
                               'inventing a third approach per feature.'],
                'code': '.metrics {\n'
                        '  display: grid;\n'
                        '  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));\n'
                        '  gap: 1rem;\n'
                        '}\n'
                        '\n'
                        '.metric-card__header {\n'
                        '  display: flex;\n'
                        '  align-items: baseline;\n'
                        '  justify-content: space-between;\n'
                        '  gap: 0.5rem;\n'
                        '}\n'
                        '\n'
                        '.metric-card--wide {\n'
                        '  grid-column: span 2;\n'
                        '}\n'
                        '\n'
                        '@media (max-width: 640px) {\n'
                        '  .metric-card--wide { grid-column: auto; }\n'
                        '}',
                'code_lang': 'css'},
               {'h2': 'Quick decision checklist',
                'paragraphs': ['Ask: am I distributing items along a single axis, or placing items '
                               'into a 2D map? Single axis → Flex. Two axes or named regions → '
                               'Grid. Need both → Grid outside, Flex inside.',
                               'If you are rewriting the same alignment rules at three '
                               'breakpoints, stop and try Grid areas. If you only need '
                               'space-between on a row, do not open a grid template. Ship the '
                               'boring choice.',
                               'Teach the rule to juniors with two exercises: rebuild a toolbar in '
                               'Flex only, rebuild a dashboard shell in Grid only. After that, '
                               'arguments about “which is better” tend to quiet down.',
                               'If you remember nothing else: stop using Flexbox as a '
                               'general-purpose page framework. It is excellent at rows and '
                               'columns of content flow. It is a poor substitute for a '
                               'two-dimensional template.'],
                'bullets': ['Nav, toolbars, chip rows → Flexbox',
                            'App shells, dashboards, aligned forms → Grid',
                            'Card galleries → Grid auto-fit/auto-fill',
                            'Component internals → often Flexbox even inside a Grid parent']},
               {'h2': 'Testing layouts without guessing',
                'paragraphs': ['I resize to 320, 768, and 1280 and paste a long German string into '
                               'every label before calling a layout done. Localization and narrow '
                               'phones expose Flex/Grid mistakes faster than pixel-perfect desktop '
                               'review.',
                               'Chrome’s flex/grid overlays in DevTools are worth learning. When '
                               'something refuses to shrink, the overlay usually shows which child '
                               'is the stubborn one within a minute.'],
                'bullets': ['Test with long content and small viewports before shipping',
                            'Use DevTools overlay to find the non-shrinking child',
                            'Prefer rem/gap tokens over magic pixel margins']}],
  'takeaways': ['Flexbox for one-dimensional distribution; Grid for two-dimensional placement',
                'Use gap and min-width: 0 to avoid classic overflow bugs',
                'Hybrid layouts (Grid shell + Flex components) stay maintainable',
                'auto-fit + minmax is the default card grid pattern I ship',
                'If alignment needs multi-breakpoint hacks, reconsider Grid areas']},
 {'slug': 'nginx-reverse-proxy-setup',
  'title': 'Nginx Reverse Proxy for Node Apps (With SSL Notes That Matter)',
  'description': 'How I put Nginx in front of Node.js apps: upstream config, proxy headers, '
                 "WebSockets, Let's Encrypt pitfalls, and production checklist items.",
  'category': 'DevOps',
  'date': '2026-07-05',
  'read_min': 8,
  'keywords': 'nginx reverse proxy nodejs, nginx ssl letsencrypt, proxy_pass node, nginx '
              'websocket, deploy node behind nginx',
  'excerpt': 'Exposing Node on port 3000 to the internet is fine for a demo and a liability in '
             'production. Here is the Nginx reverse proxy setup I reuse, plus SSL mistakes that '
             'cost me overnight outages.',
  'sections': [{'h2': 'Why Node should not face the public internet alone',
                'paragraphs': ['Node can terminate TLS, but I still put Nginx in front for static '
                               'assets, rate limiting at the edge, predictable certificate '
                               'renewal, and one place to terminate HTTP/2. It also lets me run '
                               'multiple Node processes on different ports behind one hostname.',
                               'On an early project I bound Express to 0.0.0.0:443 with a '
                               'hand-rolled cert reload. Renewal failed silently; browsers showed '
                               'a scary interstitial for six hours before anyone noticed. Nginx + '
                               'certbot’s deploy hook would have been boring and correct.',
                               'Another reason: connection handling. Nginx absorbs slow clients '
                               'and keeps Node focused on app work. Under a modest bot scrape, '
                               'that difference showed up as stable API latency instead of '
                               'event-loop stalls.',
                               'Security groups and firewalls should only expose 80/443 on the '
                               'public interface. Developers who SSH tunnel to :3000 for debugging '
                               'sometimes leave the port open “for a bit.” That bit becomes '
                               'months. Bind localhost and use a VPN or SSH tunnel instead.']},
               {'h2': 'Minimal reverse proxy that actually works',
                'paragraphs': ['Bind Node to 127.0.0.1:3000. Nginx listens on 80/443 and proxies '
                               'to that upstream. Always set Host, X-Real-IP, and '
                               'X-Forwarded-For/Proto so your app logs and absolute URL builders '
                               'see the real client and scheme.',
                               'If you forget X-Forwarded-Proto, OAuth redirect URIs and secure '
                               'cookies break in subtle ways—HTTPS in the browser, http:// in your '
                               'app’s redirect logic.',
                               'I keep upstream in its own block so I can add a second Node '
                               'instance later without rewriting every location. keepalive on the '
                               'upstream reduces churn for busy JSON APIs.',
                               'proxy_redirect and trailing slashes on proxy_pass matter. A slash '
                               'at the end of proxy_pass changes path rewriting. I keep a comment '
                               'above each location explaining whether paths are preserved. Silent '
                               'path bugs waste more time than SSL.'],
                'code': 'upstream node_app {\n'
                        '  server 127.0.0.1:3000;\n'
                        '  keepalive 32;\n'
                        '}\n'
                        '\n'
                        'server {\n'
                        '  listen 80;\n'
                        '  server_name api.example.com;\n'
                        '  return 301 https://$host$request_uri;\n'
                        '}\n'
                        '\n'
                        'server {\n'
                        '  listen 443 ssl http2;\n'
                        '  server_name api.example.com;\n'
                        '\n'
                        '  ssl_certificate     '
                        '/etc/letsencrypt/live/api.example.com/fullchain.pem;\n'
                        '  ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;\n'
                        '\n'
                        '  location / {\n'
                        '    proxy_pass http://node_app;\n'
                        '    proxy_http_version 1.1;\n'
                        '    proxy_set_header Host $host;\n'
                        '    proxy_set_header X-Real-IP $remote_addr;\n'
                        '    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n'
                        '    proxy_set_header X-Forwarded-Proto $scheme;\n'
                        '    proxy_set_header Connection "";\n'
                        '  }\n'
                        '}',
                'code_lang': 'nginx'},
               {'h2': 'WebSockets and long requests',
                'paragraphs': ['Socket.IO and similar need Upgrade headers. Without them, the '
                               'handshake falls back or fails. I also bump proxy_read_timeout for '
                               'long-lived connections instead of accepting Nginx’s default 60s '
                               'cutoffs.',
                               'File uploads and slow exports need higher proxy_read_timeout and '
                               'client_max_body_size. I set body size per location so a public '
                               'marketing site does not inherit a 50m upload limit meant for an '
                               'admin API.',
                               'Health checks from a load balancer should hit Nginx, which then '
                               'hits Node—or hit Node on a private interface. Do not open a second '
                               'public port just for /health unless you know why.'],
                'code': 'location /socket.io/ {\n'
                        '  proxy_pass http://node_app;\n'
                        '  proxy_http_version 1.1;\n'
                        '  proxy_set_header Upgrade $http_upgrade;\n'
                        '  proxy_set_header Connection "upgrade";\n'
                        '  proxy_set_header Host $host;\n'
                        '  proxy_read_timeout 86400;\n'
                        '}\n'
                        '\n'
                        'location /api/uploads {\n'
                        '  client_max_body_size 25m;\n'
                        '  proxy_pass http://node_app;\n'
                        '  proxy_request_buffering off;\n'
                        '  proxy_read_timeout 300;\n'
                        '}',
                'code_lang': 'nginx'},
               {'h2': 'SSL notes I write down for every server',
                'paragraphs': ['Use certbot with the nginx plugin or webroot. Prefer '
                               'fullchain.pem, not cert.pem alone—missing intermediates cause '
                               'mobile clients to fail while desktop Chrome looks fine. Enable a '
                               'modern cipher suite and turn on OCSP stapling when you have time; '
                               'HSTS only after you are sure HTTPS works everywhere.',
                               'Reload Nginx after renewals. Certbot usually installs a timer, but '
                               'I still verify with `sudo nginx -t && sudo systemctl reload nginx` '
                               'after the first issuance. I once had a valid new cert on disk '
                               'while Nginx kept serving the expired one until a manual reload.',
                               'For staging, use a real subdomain certificate, not a permanent '
                               'exception in every teammate’s browser. Fake SSL in staging trains '
                               'people to ignore warnings in production.',
                               'TLS 1.2+ only. Disable ancient ciphers. Mozilla’s intermediate '
                               'profile is a sane default for most business apps. I keep a '
                               'calendar reminder to revisit cipher config yearly because defaults '
                               'rot.',
                               'I keep certificate expiry in monitoring with a 14-day warning. '
                               'Calendars fail; alerts do not. The overnight outage I mentioned '
                               'earlier would have been a daytime ticket with a simple probe.'],
                'bullets': ['Redirect HTTP→HTTPS at Nginx, not only in Express',
                            "Trust proxy in Express: app.set('trust proxy', 1)",
                            'Serve static files from Nginx when possible to free Node',
                            'Limit body size explicitly (client_max_body_size) for upload APIs',
                            'Test certificate chain on a phone, not only desktop Chrome']},
               {'h2': 'Static files and gzip',
                'paragraphs': ['Let Nginx serve `/public` or `/dist` directly. Node should handle '
                               'API routes. Enable gzip (or brotli if you install the module) for '
                               'text assets. This alone dropped p95 TTFB on a marketing site I '
                               'inherited because Node had been streaming every CSS file through '
                               'Express middleware.',
                               'Fingerprinted assets get long cache headers. HTML stays '
                               'short-cached or no-store if it bootstraps a SPA. Mixing those '
                               'policies is how users run old JS against a new API.',
                               'Access logs at Nginx tell you the truth about bots and slow '
                               'endpoints before app metrics do. Sample or ship them to your log '
                               'stack; do not discover a scrape only when the disk fills.'],
                'code': 'location /assets/ {\n'
                        '  alias /var/www/app/dist/assets/;\n'
                        '  access_log off;\n'
                        '  expires 7d;\n'
                        '  add_header Cache-Control "public";\n'
                        '}\n'
                        '\n'
                        'gzip on;\n'
                        'gzip_types text/css application/javascript application/json '
                        'image/svg+xml;',
                'code_lang': 'nginx'},
               {'h2': 'Deploy checklist I actually run',
                'paragraphs': ['Confirm Node listens on localhost only. Confirm `nginx -t` passes. '
                               'Hit health endpoints through the public hostname, not '
                               'localhost:3000. Check certificates with SSL Labs or `openssl '
                               's_client`. Watch error.log during the first traffic spike—502s '
                               'usually mean Node crashed or the upstream port is wrong.',
                               'Keep a second upstream server line ready if you run two Node '
                               'instances for zero-downtime restarts. Rolling restarts without a '
                               'proxy is how I used to drop websocket clients mid-deploy.',
                               'Document the server inventory in the repo: ports, unit files, cert '
                               'domains. Future-you on a page at 2am should not reconstruct the '
                               'topology from `ps aux`.',
                               'After every deploy, curl -I https://your.domain and confirm the '
                               'certificate dates and HSTS header if enabled. Automate that check '
                               'in the deploy job if you can spare thirty seconds of CI.']},
               {'h2': 'Rate limits and basic hardening',
                'paragraphs': ['limit_req_zone at Nginx stops the dumbest floods from reaching '
                               'Node. It is not a WAF, but it buys time. I rate-limit login and '
                               'password-reset locations more tightly than public GETs.',
                               'Hide version tokens in Server headers if your threat model cares. '
                               'More importantly, return custom 502/504 pages so users see “we are '
                               'redeploying” instead of a raw upstream error during restarts.'],
                'code': 'limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;\n'
                        '\n'
                        'location /api/ {\n'
                        '  limit_req zone=api_limit burst=20 nodelay;\n'
                        '  proxy_pass http://node_app;\n'
                        '  proxy_set_header Host $host;\n'
                        '  proxy_set_header X-Forwarded-Proto $scheme;\n'
                        '}',
                'code_lang': 'nginx'}],
  'takeaways': ['Bind Node to localhost; let Nginx own 80/443',
                'Always forward Host, X-Forwarded-For, and X-Forwarded-Proto',
                'WebSockets need Upgrade headers and longer timeouts',
                'Use fullchain.pem and reload Nginx after cert renewals',
                'Serve static assets from Nginx when you can']},
 {'slug': 'redis-caching-patterns',
  'title': 'Redis Caching Patterns I Use: Cache-Aside, TTL, and Stampede Prevention',
  'description': 'Practical Redis cache-aside patterns for Node apps: TTL strategy, stampedes, '
                 'null caching, and invalidation mistakes from production incidents.',
  'category': 'Backend',
  'date': '2026-07-08',
  'read_min': 8,
  'keywords': 'redis cache aside, redis ttl, cache stampede, redis nodejs caching, cache '
              'invalidation patterns',
  'excerpt': 'Caching is easy until a key expires and a thousand requests hammer Postgres at once. '
             'These are the Redis patterns I use in production Node services, including how I '
             'prevent stampedes.',
  'sections': [{'h2': 'Cache-aside is the default for a reason',
                'paragraphs': ['Cache-aside (lazy loading) means the app reads Redis first, and on '
                               'miss loads from the database, then writes the cache. I prefer it '
                               'over write-through for most product APIs because the cache stays '
                               'out of the write path and failed Redis does not block mutations.',
                               'I wrap this in a small helper so every endpoint does not reinvent '
                               'JSON serialization and key naming. Keys look like '
                               '`user:v1:42`—include a version prefix so schema changes are a '
                               'deploy, not a silent poison.',
                               'Write-through and read-through layers have their place in '
                               'platforms with a dedicated cache service team. For a typical Node '
                               'monolith or modular service, cache-aside keeps behavior visible in '
                               'application code where I can debug it.',
                               'I treat Redis as an optimization layer, not the source of truth, '
                               'for almost every product entity. The exception is ephemeral state '
                               'that would be wrong to persist—presence, locks, rate-limit '
                               'counters. Mixing those roles in one mental model causes bad '
                               'invalidation designs.'],
                'code': 'async function getUser(userId) {\n'
                        '  const key = `user:v1:${userId}`;\n'
                        '  const cached = await redis.get(key);\n'
                        '  if (cached) return JSON.parse(cached);\n'
                        '\n'
                        '  const user = await db.users.findById(userId);\n'
                        '  if (!user) {\n'
                        '    await redis.set(key, "null", "EX", 30); // negative cache briefly\n'
                        '    return null;\n'
                        '  }\n'
                        '\n'
                        '  await redis.set(key, JSON.stringify(user), "EX", 300);\n'
                        '  return user;\n'
                        '}',
                'code_lang': 'javascript'},
               {'h2': 'TTL is a product decision, not a constant',
                'paragraphs': ['Session-ish data: minutes. Public product pages: 5–15 minutes with '
                               'explicit invalidation on publish. Rarely changing config: hours, '
                               'but still a TTL so a bug cannot live forever. I avoid “no TTL” '
                               'keys unless there is a hard invalidation path and monitoring for '
                               'memory.',
                               'A mistake I made: caching search results for 24 hours with no '
                               'purge. Merchants updated inventory; customers saw ghost stock. We '
                               'cut TTL to 60 seconds and invalidated on stock writes. Support '
                               'tickets dropped the same day.',
                               'Another mistake: identical TTL for every key type. User profiles '
                               'and homepage fragments do not share a lifecycle. Group keys by '
                               'freshness requirements and document the matrix next to the Redis '
                               'client module.',
                               'Clock skew between app servers does not matter for Redis TTL the '
                               'way people fear, but logical time in soft-TTL payloads does. Store '
                               'expiry timestamps from Redis TIME or from a single source if you '
                               'implement soft TTL in application code.'],
                'bullets': ['Short TTL for user-specific or frequently mutated data',
                            'Longer TTL only with a clear invalidation story',
                            'Negative-cache misses briefly to stop DB hammering on 404 bots',
                            'Version key prefixes when response shapes change']},
               {'h2': 'Stampede prevention that is good enough',
                'paragraphs': ['When a hot key expires, many processes miss at once and all hit '
                               'the DB. That is a cache stampede. My pragmatic fix: single-flight '
                               'locking with a short Redis lock, plus probabilistic early refresh '
                               'on soft TTL.',
                               'The lock approach: on miss, SET lock key NX EX 5. Winner loads DB '
                               'and fills cache. Losers wait briefly and retry Redis. It is not '
                               'perfect under extreme load, but it stopped a thundering herd on a '
                               'homepage fragment that used to spike Postgres CPU every five '
                               'minutes.',
                               'Soft TTL means storing `{ value, expiresAt }` and refreshing early '
                               'when a random chance fires near expiry. That spreads recompute '
                               'load instead of aligning every process on the same second.',
                               'If the lock holder crashes before releasing, the EX on the lock '
                               'saves you. Never use locks without a short expiry. I have seen '
                               'indefinite locks freeze homepage rendering after a bad deploy.'],
                'code': 'async function getWithLock(key, ttlSec, loader) {\n'
                        '  const cached = await redis.get(key);\n'
                        '  if (cached) return JSON.parse(cached);\n'
                        '\n'
                        '  const lockKey = `lock:${key}`;\n'
                        '  const gotLock = await redis.set(lockKey, "1", "EX", 5, "NX");\n'
                        '  if (!gotLock) {\n'
                        '    await new Promise((r) => setTimeout(r, 50));\n'
                        '    const retry = await redis.get(key);\n'
                        '    if (retry) return JSON.parse(retry);\n'
                        '    return loader(); // last resort\n'
                        '  }\n'
                        '\n'
                        '  try {\n'
                        '    const value = await loader();\n'
                        '    await redis.set(key, JSON.stringify(value), "EX", ttlSec);\n'
                        '    return value;\n'
                        '  } finally {\n'
                        '    await redis.del(lockKey);\n'
                        '  }\n'
                        '}',
                'code_lang': 'javascript'},
               {'h2': 'Invalidation without lying to yourself',
                'paragraphs': ['Delete keys on write when you know them. For lists and fan-out '
                               'views (`feed:user:9`), invalidation gets messy—prefer short TTLs '
                               'over trying to delete every derived key. I once built an elaborate '
                               'tag-based purge system; it was wrong more often than a 90-second '
                               'TTL.',
                               'Never assume Redis is always up. Time out commands (e.g., '
                               '50–100ms) and fall through to the database. A hung Redis client '
                               'with infinite waits takes down the whole API faster than a cold '
                               'DB.',
                               'When you invalidate, delete the exact key you write. Pattern '
                               'DELETEs in production (`KEYS user:*`) are how you freeze Redis on '
                               'a large keyspace. Maintain explicit key lists or use Redis '
                               'Cluster-friendly designs from day one.',
                               'Transactional outbox patterns help when writes must invalidate '
                               'reliably. Publish “user.updated” and let a consumer delete keys. '
                               'In-process deletes after write are fine for monoliths; they get '
                               'racy in multi-service setups.']},
               {'h2': 'What I measure',
                'paragraphs': ['Hit rate alone is vanity. I watch miss latency, DB QPS on hot '
                               'endpoints, Redis memory, and eviction counts. A 99% hit rate with '
                               'multi-second miss latency still fails users during expiry storms.',
                               'Also log cache key cardinality. Unbounded keys like '
                               '`search:${rawQuery}` will fill Redis with one-off garbage. Hash or '
                               'normalize queries, or do not cache them.',
                               'Alert on eviction spikes and on sustained miss latency, not only '
                               'on Redis CPU. Memory pressure shows up as subtle correctness bugs '
                               'when hot keys disappear under maxmemory policies.',
                               'Separate Redis logical DBs or key prefixes per environment. '
                               'Pointing staging at production Redis “just for a read” is an '
                               'incident waiting to happen. I namespace keys with env only as a '
                               'last resort—separate instances are clearer.',
                               'Export Redis info metrics to the same dashboard as API latency. '
                               'Correlating eviction spikes with p95 is how we found a cardinality '
                               'bug in a week instead of a quarter.']},
               {'h2': 'Serialization and payload size',
                'paragraphs': ['JSON is fine until values get large. I strip unused fields before '
                               'caching API responses and avoid caching entire ORM graphs. A 200KB '
                               'cached user object that grows with every relation is a tax on '
                               'every hit.',
                               'If you need compression, measure first. For small objects, CPU '
                               'cost can exceed network savings on localhost Redis. For '
                               'multi-kilobyte HTML fragments, compression sometimes pays.',
                               'When hit rate falls after a deploy, check for accidental key '
                               'version bumps and for serialization changes that make every read '
                               'look like a miss after parse errors. Log parse failures '
                               'explicitly.']},
               {'h2': 'Multi-layer caching without confusion',
                'paragraphs': ['HTTP cache headers, CDN edge cache, and Redis application cache '
                               'solve different hops. I label each layer in architecture notes so '
                               'engineers do not “fix caching” by clearing the wrong place.',
                               'Browser caches and Redis can disagree after a publish. For '
                               'user-specific HTML I avoid long CDN TTLs. For public product JSON, '
                               'CDN plus short Redis TTL can both exist if invalidation paths are '
                               'documented.'],
                'bullets': ['Name the layer you are caching at before changing TTLs',
                            'Do not clear Redis to fix a CDN problem',
                            'Document who owns invalidation for each hot key family']}],
  'takeaways': ['Cache-aside keeps Redis off the critical write path',
                'Pick TTLs from data volatility, not habit',
                'Prevent stampedes with short locks or early refresh',
                'Negative-cache missing keys briefly',
                'Fail open to the DB if Redis is slow or down',
                'Prefer short TTL over complex fan-out invalidation when unsure']},
 {'slug': 'github-actions-ci-cd',
  'title': 'GitHub Actions CI/CD for Node Apps: Test, Build, Deploy',
  'description': 'A production-minded GitHub Actions workflow for Node.js: install caching, tests, '
                 'build artifacts, and deploy patterns that avoid common CI pitfalls.',
  'category': 'DevOps',
  'date': '2026-07-12',
  'read_min': 7,
  'keywords': 'github actions nodejs, cicd github actions, deploy node github actions, npm ci '
              'cache, github actions workflow',
  'excerpt': 'I want every push to main to run tests and every green build to be deployable '
             'without SSH archaeology. This is the GitHub Actions setup I use for Node apps, '
             'including the mistakes that wasted CI minutes.',
  'sections': [{'h2': 'What “done” looks like for a Node pipeline',
                'paragraphs': ['On pull requests: install, lint, typecheck, unit tests. On main: '
                               'same checks, then build, then deploy to staging or production with '
                               'an explicit environment approval if the blast radius is high. '
                               'Artifacts should be reproducible—same commit, same build output.',
                               'I used to deploy from a developer laptop with a checklist in '
                               'Notion. That “process” shipped a debug flag to production. CI is '
                               'not bureaucracy; it is how I stop trusting my memory at 11pm.',
                               'Done also means failed checks block merges. A yellow optional '
                               'workflow that nobody watches is decoration. Protect the main '
                               'branch and require the CI job by name.',
                               'Preview environments for pull requests are optional sugar. Correct '
                               'mainline CI is mandatory. I add preview apps only after the basic '
                               'test/build/deploy path is boringly reliable.',
                               'I also require that package-lock.json is committed and that CI '
                               'fails if the lockfile would change under npm ci. Drift between '
                               'package.json and the lockfile is a silent portability bug.']},
               {'h2': 'A solid PR workflow',
                'paragraphs': ['Use `npm ci` with a lockfile, not `npm install`. Cache the npm '
                               'directory keyed on package-lock.json. Fail fast on Node version '
                               'mismatch by pinning with actions/setup-node.',
                               'I run lint and typecheck before tests when they are cheap. If '
                               'tests are the slow part, keep them parallel later. The goal is a '
                               'clear signal in under a few minutes for typical PRs.',
                               'Commit the Node version in .nvmrc and engines in package.json so '
                               'local, CI, and production agree. Version drift caused a native '
                               'module failure that only appeared on the server image.',
                               'For monorepos, scope workflows with path filters so a docs-only '
                               'change does not rebuild every package. Broad workflows feel '
                               'thorough and train people to ignore forty-minute waits.'],
                'code': 'name: ci\n'
                        'on:\n'
                        '  pull_request:\n'
                        '  push:\n'
                        '    branches: [main]\n'
                        '\n'
                        'jobs:\n'
                        '  test:\n'
                        '    runs-on: ubuntu-latest\n'
                        '    steps:\n'
                        '      - uses: actions/checkout@v4\n'
                        '      - uses: actions/setup-node@v4\n'
                        '        with:\n'
                        '          node-version: "20"\n'
                        '          cache: npm\n'
                        '      - run: npm ci\n'
                        '      - run: npm run lint\n'
                        '      - run: npm run typecheck\n'
                        '      - run: npm test -- --coverage',
                'code_lang': 'yaml'},
               {'h2': 'Build and deploy without mystery meat',
                'paragraphs': ['Separate jobs: test → build → deploy. Pass the build as an '
                               'artifact or rebuild in deploy with the same commit SHA. I prefer '
                               'building once and uploading `dist/` so production runs exactly '
                               'what CI verified.',
                               'Secrets live in GitHub Environments. Production deploy needs a '
                               'reviewer. SSH keys and cloud tokens never belong in the workflow '
                               'file—yes, I have seen tokens committed “temporarily.”',
                               'For container deploys, push an image tagged with the git SHA, then '
                               'deploy that digest. Latest tags are how we once rolled back to the '
                               'wrong build during an incident.',
                               'When deploy needs a process restart, the workflow should call a '
                               'script that reloads systemd or cycles containers healthily. Ad-hoc '
                               'SSH commands in YAML become untestable folklore.'],
                'code': '  build:\n'
                        '    needs: test\n'
                        "    if: github.ref == 'refs/heads/main'\n"
                        '    runs-on: ubuntu-latest\n'
                        '    steps:\n'
                        '      - uses: actions/checkout@v4\n'
                        '      - uses: actions/setup-node@v4\n'
                        '        with:\n'
                        '          node-version: "20"\n'
                        '          cache: npm\n'
                        '      - run: npm ci\n'
                        '      - run: npm run build\n'
                        '      - uses: actions/upload-artifact@v4\n'
                        '        with:\n'
                        '          name: dist\n'
                        '          path: dist\n'
                        '\n'
                        '  deploy:\n'
                        '    needs: build\n'
                        '    runs-on: ubuntu-latest\n'
                        '    environment: production\n'
                        '    steps:\n'
                        '      - uses: actions/download-artifact@v4\n'
                        '        with:\n'
                        '          name: dist\n'
                        '          path: dist\n'
                        '      - name: Rsync to server\n'
                        '        env:\n'
                        '          SSH_KEY: ${{ secrets.DEPLOY_SSH_KEY }}\n'
                        '          HOST: ${{ secrets.DEPLOY_HOST }}\n'
                        '        run: |\n'
                        '          install -m 600 /dev/null ~/.ssh/id_ed25519\n'
                        '          echo "$SSH_KEY" > ~/.ssh/id_ed25519\n'
                        '          rsync -az --delete dist/ deploy@$HOST:/var/www/app/dist/',
                'code_lang': 'yaml'},
               {'h2': 'Mistakes that burned CI time and nerves',
                'paragraphs': ['Running `npm install` without a lockfile made “green on CI, broken '
                               'on server” a monthly event. Skipping `npm ci` in deploy and '
                               'installing again with different optional dependencies did the '
                               'same.',
                               'Another classic: tests that depend on a developer’s local `.env`. '
                               'Inject test env in the workflow. And do not run deploys on every '
                               'branch push—protect main and require PR checks.',
                               'Flaky tests taught the team to re-run until green. I quarantine '
                               'flakes ruthlessly. A pipeline that lies is worse than no pipeline.',
                               'Concurrency groups cancel outdated runs on the same branch. '
                               'Without them, an older slow workflow can deploy after a newer '
                               'commit and roll you backward. I set concurrency per ref for deploy '
                               'jobs.'],
                'bullets': ['Pin Node version in setup-node and .nvmrc',
                            'Cache dependencies; do not cache node_modules blindly across OS '
                            'changes',
                            'Use environments for production approvals',
                            'Keep deploy scripts idempotent (rsync --delete, migrations once)',
                            'Fail the job on soft warnings you actually care about (type errors, '
                            'audit critical)']},
               {'h2': 'Migrations and zero-downtime reality',
                'paragraphs': ['App deploys and DB migrations need an order. Expand-contract: add '
                               'nullable columns first, deploy code that reads both shapes, then '
                               'backfill, then enforce constraints. I burned a release by running '
                               'a destructive migration in the same job as a rolling restart.',
                               'If migrations run in CI, use a dedicated step with locked '
                               'credentials and a clear failure page. Do not hide `ALTER TABLE` '
                               'inside the Node process boot—two instances booting will race.',
                               'For risky migrations, ship a feature flag that stops writes to the '
                               'old path before you drop a column. CI cannot save you from a '
                               'one-way data loss without a backup plan.',
                               'Backup before migrate. Even expand-only migrations deserve a '
                               'snapshot on production the first few times a team adopts CI-driven '
                               'schema changes. Trust is earned.']},
               {'h2': 'Signal over theater',
                'paragraphs': ['A pipeline that takes 25 minutes teaches people to ignore it. '
                               'Parallelize lint and tests when possible. Fail on the first '
                               'meaningful error. Slack noise on every success is useless; alert '
                               'on failed main deploys.',
                               'Start simple: one workflow file, two jobs, one environment. Add '
                               'matrix builds and preview apps when the team feels the pain—not '
                               'before.',
                               'I review workflow YAML in PRs the same way I review app code. '
                               'Copy-pasted actions with unpinned versions are supply-chain debt. '
                               'Prefer major-version tags you consciously upgrade.',
                               'Track mean time from merge to production. If it grows past what '
                               'your product needs, simplify jobs before adding more checks. '
                               'Throughput is a feature of the pipeline.',
                               'Publish a short CONTRIBUTING note that links the required checks. '
                               'New contributors should not discover merge blockers by trial and '
                               'error on their first PR.']},
               {'h2': 'Smoke tests after deploy',
                'paragraphs': ['A green unit suite does not prove the site is up. I add a '
                               'post-deploy step that curls /health and a critical HTML route, '
                               'failing the job if status is not 200. That caught DNS and Nginx '
                               'misconfigs unit tests never see.',
                               'For APIs, hit an authenticated smoke endpoint with a scoped CI '
                               'token. Keep the token read-only. If smoke fails, page a human '
                               'before customers do.'],
                'code': '      - name: Smoke check\n'
                        '        run: |\n'
                        '          curl -fsS "https://example.com/health" | grep -q \'"ok":true\'\n'
                        '          curl -fsSI "https://example.com/" | head -n1 | grep -q 200',
                'code_lang': 'yaml'}],
  'takeaways': ['npm ci + lockfile + pinned Node version is non-negotiable',
                'Separate test, build, and deploy jobs',
                'Store deploy secrets in GitHub Environments',
                'Build once; deploy the same artifact when possible',
                'Keep pipelines fast enough that people trust them']},
 {'slug': 'rest-api-design-best-practices',
  'title': 'REST API Design I Stick To: Status Codes, Pagination, and Errors',
  'description': 'Concrete REST API design rules from shipping Node services: HTTP status codes, '
                 'cursor pagination, consistent error bodies, and versioning choices.',
  'category': 'Backend',
  'date': '2026-07-15',
  'read_min': 8,
  'keywords': 'rest api best practices, http status codes api, api pagination cursor, api error '
              'format, rest api design',
  'excerpt': 'Clients should not need tribal knowledge to use your API. These are the REST '
             'conventions I enforce on Node services—status codes, pagination, and errors that do '
             'not invent a private dialect.',
  'sections': [{'h2': 'Resources, not RPC soup',
                'paragraphs': ['Prefer nouns and HTTP verbs: `GET /orders`, `POST /orders`, `GET '
                               '/orders/:id`, `PATCH /orders/:id`. When an action is not a clean '
                               'CRUD shape (`POST /orders/:id/cancel`), that is fine—document it '
                               'as a sub-resource action—but do not invent `POST /doCancelOrder`.',
                               'I inherited an API where everything was `POST /api` with a '
                               '`method` field in JSON. Debugging required reading application '
                               'logs for every 200 response that contained `{ ok: false }`. HTTP '
                               'already has a status line; use it.',
                               'Consistency beats purity. If your team already uses '
                               '`/v1/users/:id/deactivate`, keep the pattern. The crime is mixing '
                               'RPC, REST, and random verbs in one surface.',
                               'Collect related routes under clear prefixes: /v1/billing, '
                               '/v1/catalog. Gateway routing and docs generation both get easier. '
                               'Flat bags of unrelated endpoints at the root become impossible to '
                               'navigate by month six.',
                               'Plural nouns for collections keep clients predictable: /users not '
                               '/user. Singular resources by id sit underneath. Bike-shedding '
                               'plurals is less costly than mixing both in one API.']},
               {'h2': 'Status codes that mean what they say',
                'paragraphs': ['200 for successful GET/PATCH with a body. 201 for created '
                               'resources, ideally with Location. 204 for successful DELETE with '
                               'no body. 400 for malformed input. 401 unauthenticated. 403 '
                               'authenticated but not allowed. 404 missing. 409 conflict. 422 when '
                               'JSON parses but business validation fails (I use 400 if the team '
                               'hates 422—pick one and stay consistent). 429 when rate limited. '
                               '5xx only for unexpected server failure.',
                               'Returning 200 with `{ error: "..." }` trains clients to ignore '
                               'status codes. I have done it under deadline pressure; every time '
                               'it came back as a support tax.',
                               'For batch endpoints, avoid inventing a special “multi-status '
                               'everything is fine” unless you truly need 207. Most product APIs '
                               'are better with one resource per request and clear codes.',
                               '204 responses should truly have empty bodies. Some HTTP clients '
                               'mishandle 204 with JSON. Be strict in tests. Likewise, never '
                               'return 201 without creating something durable.'],
                'bullets': ['Do not overload 200 for failures',
                            'Use 401 vs 403 correctly—clients handle them differently',
                            'Prefer 404 over 403 for private resources if you want to avoid '
                            'existence leaks—document the choice',
                            'Include Retry-After on 429 responses']},
               {'h2': 'Error bodies clients can parse',
                'paragraphs': ['One shape everywhere: code, message, details, requestId. '
                               'Machine-readable `code` stays stable; `message` can be '
                               'human-friendly. `details` holds field-level validation arrays. '
                               '`requestId` ties to logs.',
                               'I reject free-form string errors as the only payload. Mobile apps '
                               'and web clients both need to branch on `code` without regexing '
                               'English sentences.',
                               'Map unexpected exceptions to 500 with a generic message and log '
                               'the stack keyed by requestId. Leaking SQL or filesystem paths in '
                               'error.message is a gift to attackers and a nightmare in '
                               'screenshots.',
                               'Localization belongs in the client when possible. Return stable '
                               'codes and optionally a default English message. Translating every '
                               'error on the server couples releases to copy changes.'],
                'code': '{\n'
                        '  "error": {\n'
                        '    "code": "VALIDATION_FAILED",\n'
                        '    "message": "Email is invalid",\n'
                        '    "details": [\n'
                        '      { "field": "email", "issue": "format" }\n'
                        '    ],\n'
                        '    "requestId": "req_01J5..."\n'
                        '  }\n'
                        '}',
                'code_lang': 'json'},
               {'h2': 'Pagination: why I default to cursors',
                'paragraphs': ['Offset pagination (`?page=3&limit=20`) is easy and breaks under '
                               'inserts: page 2 shifts while the user scrolls. For feeds and large '
                               'tables I use cursor pagination: opaque `next_cursor`, stable sort '
                               'key (usually `(created_at, id)`).',
                               'Always cap `limit` server-side (I use max 100). Return `has_more` '
                               'or a null cursor when done. Document sort order; changing it later '
                               'breaks clients mid-scroll.',
                               'Offset is still fine for small admin tables with stable ordering '
                               'and low write rates. Do not dogma your way out of a simple UI.',
                               'Cursor tokens should be opaque and signed or encrypted if they '
                               'embed internal IDs and timestamps. Clients must not be able to '
                               'mint arbitrary offsets into other tenants’ data.',
                               'Include the limit the server actually applied in the response. '
                               'Clients that ask for 1000 and silently receive 100 will mis-render '
                               '“end of list” unless you tell them what happened.'],
                'code': '// GET /items?limit=20&cursor=eyJpZCI6IjEyMyJ9\n'
                        '{\n'
                        '  "data": [ /* ... */ ],\n'
                        '  "paging": {\n'
                        '    "next_cursor": "eyJpZCI6IjE0NSJ9",\n'
                        '    "limit": 20\n'
                        '  }\n'
                        '}\n'
                        '\n'
                        '// SQL sketch (Postgres)\n'
                        '// WHERE (created_at, id) < ($cursorCreatedAt, $cursorId)\n'
                        '// ORDER BY created_at DESC, id DESC\n'
                        '// LIMIT $limit',
                'code_lang': 'javascript'},
               {'h2': 'Idempotency and partial updates',
                'paragraphs': ['POST create endpoints that can be retried by flaky mobile networks '
                               'need Idempotency-Key. Store the key with the response for 24h. '
                               'PATCH is partial; PUT replaces. Mixing them casually is how we '
                               'duplicated charges once when a client retried a non-idempotent '
                               'POST.',
                               'Document which fields are optional on PATCH. Silent no-ops on '
                               'unknown fields are safer than hard failures for forward-compatible '
                               'clients—but log unknowns during migrations so typos do not vanish.',
                               'For webhooks you emit, use the same error and versioning '
                               'discipline. Partners will copy your style. Inconsistent outbound '
                               'and inbound conventions multiply support load.']},
               {'h2': 'Versioning without drama',
                'paragraphs': ['I prefer URL prefixes (`/v1/`) for public APIs because they are '
                               'obvious in logs and gateways. Header versioning works but gets '
                               'lost in support tickets. Do not break v1; add fields tolerantly '
                               'and remove only in v2.',
                               'Deprecation means a header + changelog date + time for clients to '
                               'migrate—not a surprise 404 on Monday morning.',
                               'Internal-only APIs can be stricter. Public partner APIs need a '
                               'compatibility promise written down. If it is not written, partners '
                               'will assume forever.',
                               'Publish an OpenAPI document generated from the source of truth—or '
                               'carefully maintained by hand if generation is immature. Stale docs '
                               'are worse than sparse docs because they create confident wrong '
                               'clients.',
                               'When v2 launches, keep v1 online with a published sunset date. '
                               'Overlap beats a flag day. I budget engineering time for '
                               'dual-running, not only for building v2 features.']},
               {'h2': 'Filtering, sorting, and sparse fieldsets',
                'paragraphs': ['Allowlist sort fields. Never pass raw client strings into ORDER '
                               'BY. The same goes for filter operators—whitelist equals, in, and a '
                               'few ranges. Open-ended query languages belong in analytics tools, '
                               'not public product APIs.',
                               'Sparse fieldsets (?fields=id,name) help mobile clients when '
                               'payloads grow. Implement them only when measured payload size '
                               'hurts; premature field selectors complicate caching and '
                               'authorization checks.'],
                'bullets': ['Allowlist sort and filter fields server-side',
                            'Keep default payloads small; add expand parameters intentionally',
                            'Document default sort order next to each list route'],
                'code': '// Allowlisted sort example\n'
                        'const SORTS = {\n'
                        '  created_at: { column: "created_at", dir: "desc" },\n'
                        '  name: { column: "name", dir: "asc" },\n'
                        '};\n'
                        '\n'
                        'function resolveSort(param) {\n'
                        '  return SORTS[param] || SORTS.created_at;\n'
                        '}',
                'code_lang': 'javascript'}],
  'takeaways': ['Use HTTP status codes honestly; stop stuffing errors into 200',
                'Standardize one error envelope with code, message, details, requestId',
                'Prefer cursor pagination for large or realtime-ish lists',
                'Cap page sizes server-side',
                'Add Idempotency-Key for risky POSTs',
                'Version publicly and deprecate with a timeline']},
 {'slug': 'sql-vs-nosql-when-to-choose',
  'title': 'SQL vs NoSQL: A Decision Guide From Real Project Scenarios',
  'description': 'When to choose Postgres vs MongoDB or similar: consistency needs, query shapes, '
                 'team skills, and scenarios from shipping production web apps.',
  'category': 'Databases',
  'date': '2026-07-19',
  'read_min': 7,
  'keywords': 'sql vs nosql, postgres vs mongodb, when to use nosql, database decision guide, '
              'relational vs document store',
  'excerpt': 'The database choice shows up in every later decision. Here is how I pick SQL vs '
             'NoSQL for web apps, with scenarios I have shipped—and one choice I regret.',
  'sections': [{'h2': 'Start from access patterns, not fashion',
                'paragraphs': ['I ask: What are the writes? What are the reads? Do we need '
                               'multi-row transactions? How often will the shape change? Who will '
                               'run migrations at 2am? Marketing tweets about “web scale” do not '
                               'answer those questions.',
                               'Default bias: Postgres (or another mature relational DB) unless a '
                               'documented access pattern clearly favors a document or key-value '
                               'store. That bias has saved me more often than it has slowed me.',
                               'Write the top ten queries on a whiteboard before picking a store. '
                               'If you cannot name them, you are not ready to choose a '
                               'database—you are ready to prototype on Postgres.',
                               'Prototype speed matters, but so does the cost of being wrong. '
                               'Postgres lets me change my mind with migrations. A document store '
                               'that encouraged schemaless chaos made reverse-engineering the real '
                               'schema a forensic exercise.']},
               {'h2': 'When SQL is the obvious win',
                'paragraphs': ['Billing, inventory, permissions, anything with invariants across '
                               'tables: relational + transactions. Ad-hoc reporting and joins '
                               '(“orders with items for users in region X last week”) stay sane in '
                               'SQL. Strong constraints (foreign keys, unique indexes) catch bugs '
                               'before they become support tickets.',
                               'On a marketplace, we briefly considered Mongo for “flexible '
                               'listings.” Listing fields were flexible; money movement was not. '
                               'Split brain between two stores without a clear boundary became the '
                               'actual problem. One Postgres database with JSONB for the flexible '
                               'attributes would have been enough.',
                               'Team familiarity counts. A competent Postgres setup beats an '
                               'exotic store nobody can tune when replication lag shows up on a '
                               'Friday.',
                               'Foreign keys are not bureaucracy. They are executable '
                               'documentation. When I drop them “for speed” without measuring, I '
                               'usually regret the orphaned rows more than I celebrate the '
                               'microbenchmark.'],
                'bullets': ['Multi-entity invariants → SQL transactions',
                            'Heavy relational reporting → SQL',
                            'Mature ORMs/query tooling and hiring pool → SQL often cheaper '
                            'operationally',
                            'JSONB in Postgres covers many “document” needs without a second '
                            'system']},
               {'h2': 'When NoSQL earns its keep',
                'paragraphs': ['High-volume event or session data with simple key lookup, large '
                               'semi-structured payloads, or workloads where you intentionally '
                               'denormalize for read speed. Content CMS blobs, feature-flag dumps, '
                               'IoT ingest buffers, and certain feed fan-outs can fit document or '
                               'wide-column stores well.',
                               'I used Redis as a primary store for ephemeral multiplayer room '
                               'state—correct call. I used Mongo as the primary for an app with '
                               'lots of joins-in-application-code—wrong call. We spent months '
                               'reinventing relational integrity poorly.',
                               'If your “documents” are mostly relational rows with a JSON column, '
                               'stay on SQL. Document databases shine when the document is the '
                               'unit of consistency and you rarely need cross-document joins.',
                               'Key-value and document stores excel when you can name the primary '
                               'key for every read you care about. If you keep inventing secondary '
                               'indexes that look relational, listen to that signal.']},
               {'h2': 'Scenario walkthroughs',
                'paragraphs': ['SaaS billing and seats: Postgres. Social activity stream with '
                               'millions of tiny writes and read-by-user-key: often a specialized '
                               'store or carefully denormalized SQL plus cache—not “Mongo because '
                               'social.” Product catalog with rare schema change and complex '
                               'filtering: Postgres + indexes, maybe search engine alongside.',
                               'Analytics events: append-only store or warehouse '
                               '(BigQuery/Snowflake/ClickHouse), not your OLTP Mongo cluster. '
                               'Mixing analytics and transactional traffic is a classic '
                               'slow-motion outage.',
                               'Multi-tenant SaaS with row-level isolation: Postgres plus careful '
                               'indexing (and sometimes schema-per-tenant for extreme cases). Do '
                               'not assume a document store gives you tenancy for free.',
                               'Search is its own problem. Elasticsearch/OpenSearch or a hosted '
                               'search product next to Postgres is a normal architecture. Using a '
                               'document DB as a pseudo-search engine produces mediocre relevance '
                               'and operational pain.'],
                'code': '-- Postgres: flexible attributes without leaving SQL\n'
                        'CREATE TABLE listings (\n'
                        '  id           bigserial PRIMARY KEY,\n'
                        '  seller_id    bigint NOT NULL REFERENCES users(id),\n'
                        '  title        text NOT NULL,\n'
                        '  price_cents  integer NOT NULL CHECK (price_cents >= 0),\n'
                        "  attrs        jsonb NOT NULL DEFAULT '{}',\n"
                        '  created_at   timestamptz NOT NULL DEFAULT now()\n'
                        ');\n'
                        '\n'
                        'CREATE INDEX listings_attrs_gin ON listings USING gin (attrs);',
                'code_lang': 'sql'},
               {'h2': 'Operational questions people skip',
                'paragraphs': ['Backups, point-in-time recovery, migrations, local dev story, '
                               'observability. A shiny DB with weak backup tooling is a future '
                               'incident report. Also ask: can the team query it under pressure? '
                               'If only one person understands the data model, you do not have a '
                               'database strategy—you have a bus factor.',
                               'Multi-model polyglot persistence is fine when boundaries are sharp '
                               '(Postgres for core, Redis for cache/ephemeral, S3 for blobs). It '
                               'is painful when every feature picks a new store because someone '
                               'watched a talk.',
                               'Cost models differ. Managed Mongo and managed Postgres both bill '
                               'for ignorance—oversized clusters, no indexes, bad data models. '
                               'Pick the model that matches the queries, then right-size.',
                               'Compliance and audit trails lean relational. Immutable event '
                               'tables with clear joins to actors and resources map cleanly to '
                               'SQL. Bolting audit onto an unstructured blob store usually means '
                               'incomplete history.']},
               {'h2': 'My decision cheat sheet',
                'paragraphs': ['Unknown domain early on → Postgres. Need transactions and '
                               'relations → Postgres. Need crazy write throughput with simple keys '
                               'and TTL → Redis or similar. Truly document-shaped, rarely joined '
                               'data with a clear key → document DB can be justified. Need search '
                               'relevance → use a search engine, do not pretend LIKE or regex is '
                               'search.',
                               'Regret I still remember: choosing Mongo to “move faster” on a '
                               'relational problem. We moved slower after month two.',
                               'Revisit the choice when access patterns change. Migrating is '
                               'expensive, but living forever on the wrong store is more '
                               'expensive. Schedule an honest review when QPS or join complexity '
                               'jumps an order of magnitude.',
                               'If leadership asks for NoSQL to attract hires, push back with a '
                               'workload brief. Hiring fashion is not a query planner.',
                               'Write the decision down in the repo ADR folder. Future debates '
                               'should start from recorded constraints, not from whoever argues '
                               'loudest in Slack.']},
               {'h2': 'Hybrid designs that worked for me',
                'paragraphs': ['Postgres for core entities, Redis for hot keys and rate limits, '
                               'object storage for binaries, and a warehouse for analytics. That '
                               'quartet covers most product companies I work with without '
                               'introducing a document DB.',
                               'When we did use Mongo, it sat behind a bounded context: '
                               'notification templates and provider payloads with wildly different '
                               'shapes per channel. Core accounts and billing stayed in Postgres. '
                               'The boundary was enforced in code review.'],
                'bullets': ['Prefer clear boundaries over one mega-store',
                            'Put binaries in object storage, not in documents or rows',
                            'Revisit the map when a context outgrows its store']}],
  'takeaways': ['Choose from access patterns and invariants, not trends',
                'Default to Postgres unless NoSQL clearly fits the workload',
                'JSONB often replaces a second document database',
                'Keep analytics out of your OLTP primary when possible',
                'Polyglot persistence needs hard boundaries',
                'Team operability matters as much as theoretical scale']},
 {'slug': 'debounce-throttle-javascript',
  'title': 'Debounce vs Throttle in JavaScript (With Code You Can Paste)',
  'description': 'Working debounce and throttle implementations, when to use each for search, '
                 'scroll, and resize, plus React-friendly notes from production UI work.',
  'category': 'Frontend',
  'date': '2026-07-22',
  'read_min': 7,
  'keywords': 'debounce vs throttle javascript, debounce javascript, throttle scroll, lodash '
              'debounce, input debounce react',
  'excerpt': 'Debounce and throttle both limit how often a function runs, but they fix different '
             'UX problems. Here are the implementations I use and the call sites that broke when I '
             'mixed them up.',
  'sections': [{'h2': 'The difference in one sentence each',
                'paragraphs': ['Debounce: wait until events stop arriving, then run once. '
                               'Throttle: run at most once per time window while events keep '
                               'arriving. Search-as-you-type wants debounce. Scroll position '
                               'syncing often wants throttle.',
                               'I once debounced a scroll handler for a reading progress bar. The '
                               'bar jumped only after the user stopped scrolling—useless. '
                               'Switching to throttle made it track continuously without firing on '
                               'every pixel.',
                               'Both techniques are about respecting the main thread and the '
                               'network. They are not interchangeable spices you sprinkle until '
                               'jank disappears.',
                               'Think in terms of the signal: bursty discrete intent (typing a '
                               'query) versus continuous streams (scroll position). That framing '
                               'picks the tool before you debate millisecond constants.',
                               'If you only remember the scroll progress mistake and the search '
                               'typeahead pattern, you already outrank most copy-paste snippets '
                               'that treat both tools as synonyms.']},
               {'h2': 'Debounce you can trust',
                'paragraphs': ['Trailing debounce is the common case for inputs. Leading+trailing '
                               'variants exist; start with trailing. Always cancel on unmount in '
                               'SPA components or you will setState on dead trees.',
                               'Pick wait times from UX, not habit. 300ms feels right for search. '
                               '600ms can feel sluggish. 100ms may still hammer an expensive '
                               'endpoint. Measure request rates with a real typer, not a synthetic '
                               'loop.',
                               'Leading debounce is useful when you want an immediate reaction '
                               'then silence—rare for search, more common for “save draft” buttons '
                               'that should fire once on first click then ignore chatter.',
                               'Expose cancel() and flush() if your UX needs “run now on blur.” '
                               'Forms often debounce input but should flush pending saves when the '
                               'field loses focus.'],
                'code': 'function debounce(fn, wait = 300) {\n'
                        '  let timer;\n'
                        '  function debounced(...args) {\n'
                        '    const context = this;\n'
                        '    clearTimeout(timer);\n'
                        '    timer = setTimeout(() => fn.apply(context, args), wait);\n'
                        '  }\n'
                        '  debounced.cancel = () => clearTimeout(timer);\n'
                        '  return debounced;\n'
                        '}\n'
                        '\n'
                        '// Usage: typeahead\n'
                        'const onQuery = debounce(async (q) => {\n'
                        '  const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);\n'
                        '  renderResults(await res.json());\n'
                        '}, 300);\n'
                        '\n'
                        'input.addEventListener("input", (e) => onQuery(e.target.value));',
                'code_lang': 'javascript'},
               {'h2': 'Throttle for continuous signals',
                'paragraphs': ['Throttle guarantees periodic updates during a burst. I use a '
                               'trailing call so the last event is not lost—important for resize '
                               'and scroll end positions.',
                               'For pointer-move annotations on a canvas, throttle to '
                               'animation-frame cadence or ~16–32ms. Throttling to 200ms makes '
                               'drawing feel drunk.',
                               'requestAnimationFrame is sometimes a better throttle for visual '
                               'updates. It aligns work to paint. For network or analytics, '
                               'time-based throttle remains clearer.',
                               'Document whether your throttle is leading, trailing, or both. '
                               'Callers who assume leading behavior will swear your helper is '
                               'broken when the first event waits for the window.'],
                'code': 'function throttle(fn, wait = 100) {\n'
                        '  let last = 0;\n'
                        '  let timer;\n'
                        '  let lastArgs;\n'
                        '  let lastContext;\n'
                        '\n'
                        '  function invoke() {\n'
                        '    last = Date.now();\n'
                        '    timer = null;\n'
                        '    fn.apply(lastContext, lastArgs);\n'
                        '  }\n'
                        '\n'
                        '  function throttled(...args) {\n'
                        '    lastArgs = args;\n'
                        '    lastContext = this;\n'
                        '    const now = Date.now();\n'
                        '    const remaining = wait - (now - last);\n'
                        '\n'
                        '    if (remaining <= 0 || remaining > wait) {\n'
                        '      if (timer) {\n'
                        '        clearTimeout(timer);\n'
                        '        timer = null;\n'
                        '      }\n'
                        '      invoke();\n'
                        '    } else if (!timer) {\n'
                        '      timer = setTimeout(invoke, remaining);\n'
                        '    }\n'
                        '  }\n'
                        '\n'
                        '  throttled.cancel = () => {\n'
                        '    clearTimeout(timer);\n'
                        '    timer = null;\n'
                        '  };\n'
                        '  return throttled;\n'
                        '}\n'
                        '\n'
                        'window.addEventListener(\n'
                        '  "scroll",\n'
                        '  throttle(() => {\n'
                        '    progress.style.width = `${scrollPercent()}%`;\n'
                        '  }, 100),\n'
                        '  { passive: true }\n'
                        ');',
                'code_lang': 'javascript'},
               {'h2': 'Call-site cheat sheet',
                'paragraphs': ['Autocomplete / server search: debounce 200–400ms. Window resize '
                               'layout recalculation: throttle ~100–150ms. Button spam prevention: '
                               'often a simple disabled flag or leading throttle of 1s—not '
                               'debounce, which would delay the first click.',
                               'Analytics “track mouse moves”: throttle heavily. Form save '
                               'indicators: debounce. Mixing these up creates APIs that feel laggy '
                               'or backends that melt.',
                               'Infinite scroll fetch triggers: throttle or a sentinel '
                               'IntersectionObserver. Debouncing scroll for infinite load feels '
                               'broken because users pause mid-page and nothing happens until they '
                               'stop.',
                               'Server-side rate limits do not replace client debounce. Both '
                               'belong. Debounce protects UX and your bill; rate limits protect '
                               'the service from clients that ignore good manners.'],
                'bullets': ['Debounce → “run after things calm down”',
                            'Throttle → “run steadily during the storm”',
                            'Cancel timers on component unmount',
                            'Prefer passive listeners for scroll/touch when you do not '
                            'preventDefault']},
               {'h2': 'React notes without a library lecture',
                'paragraphs': ['Creating debounce inside render re-creates timers every '
                               'paint—store the debounced function in useRef or useMemo with '
                               'stable deps. Better: debounce in an event handler factory created '
                               'once.',
                               'For data fetching, pair debounce with abort controllers so an '
                               'older response cannot overwrite a newer query. That bug looked '
                               'like “search flickers wrong results” until we aborted in-flight '
                               'fetches.',
                               'useDeferredValue can replace some debounce for pure UI lag. It '
                               'does not replace debounce for network calls—you still need to gate '
                               'fetches.',
                               'In tests, fake timers. Debounce bugs appear as intermittent '
                               'failures when wall clocks vary. I assert call counts under '
                               'jest.useFakeTimers or equivalent.'],
                'code': 'import { useEffect, useMemo, useState } from "react";\n'
                        '\n'
                        'function useDebouncedValue(value, wait = 300) {\n'
                        '  const [debounced, setDebounced] = useState(value);\n'
                        '  useEffect(() => {\n'
                        '    const id = setTimeout(() => setDebounced(value), wait);\n'
                        '    return () => clearTimeout(id);\n'
                        '  }, [value, wait]);\n'
                        '  return debounced;\n'
                        '}\n'
                        '\n'
                        '// In component:\n'
                        '// const debouncedQuery = useDebouncedValue(query, 300);\n'
                        '// useEffect(() => { fetchSearch(debouncedQuery); }, [debouncedQuery]);',
                'code_lang': 'javascript'},
               {'h2': 'Libraries vs hand-rolled',
                'paragraphs': ['Lodash debounce/throttle are fine and well-tested. For a design '
                               'system I still paste a 20-line helper to avoid pulling lodash into '
                               'a critical path bundle. Either way, understand leading/trailing '
                               'options before arguing about packages.',
                               'Measure: if your input handler triggers network, debounce is a '
                               'product requirement, not a micro-optimization.',
                               'Write two unit tests: rapid calls only invoke once for debounce '
                               'after wait, and throttle invokes immediately then respects the '
                               'window. Those tests catch the off-by-one bugs that make UX feel '
                               'haunted.',
                               'Bundle size arguments aside, copying a well-understood 20-line '
                               'helper into a repo is fine. Just put it in one module so you do '
                               'not end up with five slightly different throttles.',
                               'Whatever you choose, keep one implementation per app. Five '
                               'slightly different throttles guarantee one of them forgets to '
                               'cancel on unmount.']},
               {'h2': 'Real incident: search stampede from the browser',
                'paragraphs': ['We shipped typeahead without debounce on a Black Friday microsite. '
                               'Each keypress hit Elasticsearch. A burst of traffic plus fast '
                               'typers multiplied into a nasty queue. Adding 250ms debounce and '
                               'abortable fetches cut search QPS by roughly 70% with no complaints '
                               'about lag.',
                               'The complementary fix was a 429-aware client that backed off. '
                               'Client-side pacing and server-side limits together kept the search '
                               'cluster boring—which is what you want on sale day.'],
                'bullets': ['Debounce before you scale the search cluster',
                            'Abort stale requests when the query changes',
                            'Handle 429 with backoff even on first-party UIs']}],
  'takeaways': ['Debounce waits for quiet; throttle paces a storm',
                'Search inputs → debounce; scroll/resize → throttle',
                'Always cancel timers on unmount',
                'Abort in-flight fetches when debounced queries change',
                'Do not recreate debounced functions every React render']},
 {'slug': 'optimize-images-webp-avif',
  'title': 'WebP and AVIF Image Optimization That Actually Improves LCP',
  'description': 'Practical WebP/AVIF workflow for better LCP: encoding settings, picture '
                 'elements, preload pitfalls, CDN tips, and mistakes that made LCP worse.',
  'category': 'Web Performance',
  'date': '2026-07-28',
  'read_min': 8,
  'keywords': 'webp avif optimization, improve lcp images, picture element webp, image compression '
              'web performance, avif vs webp',
  'excerpt': 'Hero images dominate LCP on most marketing pages I audit. Switching to AVIF/WebP '
             'helps only if sizing, priority, and encoding are right—here is the workflow that '
             'moved real numbers.',
  'sections': [{'h2': 'LCP is usually an image problem',
                'paragraphs': ['On content and landing pages, the largest contentful paint is '
                               'often a hero image or a big poster frame. Compressing that asset, '
                               'serving a modern format, and helping the browser discover it early '
                               'beats most framework tricks.',
                               'I once “optimized” a site by lazy-loading the hero. LCP got worse '
                               'because the browser deprioritized the most important paint. Rule: '
                               'LCP image gets eager loading and high fetch priority; everything '
                               'below the fold can be lazy.',
                               'Confirm the LCP element in field data or a throttled lab run '
                               'before you spend a week converting a thousand blog thumbnails. Fix '
                               'the winner first.',
                               'Lighthouse lab scores on desktop hid our mobile LCP pain. Always '
                               'throttle CPU and network or use field data. Optimizing for an '
                               'unthrottled MacBook creates false confidence.',
                               'Fonts can also be LCP, but on the marketing pages I audit, images '
                               'win. Still check: if LCP is a text block, your image work will not '
                               'move the metric no matter how clever the codec.']},
               {'h2': 'Encode once, serve many',
                'paragraphs': ['Generate AVIF and WebP from a high-quality source (not from an '
                               'already crushed JPEG). Keep a JPEG/PNG fallback for ancient '
                               'clients. I aim for visually lossless enough at the sizes we '
                               'actually display—not a 2400px asset in a 600px slot.',
                               'Typical starting points: AVIF quality around 45–60, WebP 70–80, '
                               'then eyeball on a real phone. Automate with Squoosh CLI, sharp, or '
                               'your CDN’s transformer so humans do not hand-export every blog '
                               'thumbnail.',
                               'Screenshots with UI chrome often need higher quality than photos. '
                               'Watch for banding in gradients—AVIF can look great at small sizes '
                               'and weird on flat brand colors if you push too hard.',
                               'Preserve ICC profiles when color accuracy matters for brand '
                               'assets. Blind conversion pipelines sometimes shift colors enough '
                               'that design rejects the “optimized” hero.',
                               'Keep the source asset in the repo or DAM at full quality. '
                               'Re-encoding from a previously compressed WebP stacks generation '
                               'loss and makes future recompression ugly.'],
                'code': '# Example with sharp in Node\n'
                        'import sharp from "sharp";\n'
                        '\n'
                        'await sharp("hero.png")\n'
                        '  .resize({ width: 1600, withoutEnlargement: true })\n'
                        '  .webp({ quality: 75 })\n'
                        '  .toFile("hero-1600.webp");\n'
                        '\n'
                        'await sharp("hero.png")\n'
                        '  .resize({ width: 1600, withoutEnlargement: true })\n'
                        '  .avif({ quality: 50 })\n'
                        '  .toFile("hero-1600.avif");',
                'code_lang': 'javascript'},
               {'h2': 'Markup that negotiates formats correctly',
                'paragraphs': ['Use `<picture>` with AVIF first, then WebP, then fallback. Include '
                               'width/height or aspect-ratio CSS to stop layout shift. Match '
                               '`sizes` to your real CSS breakpoints—wrong sizes downloads a huge '
                               'file on mobile.',
                               'Art direction (different crop on mobile) belongs in separate '
                               '`<source media>` entries. Do not stretch a desktop wide crop into '
                               'a phone hero and call it responsive.',
                               'Decode cost matters on low-end Androids. A slightly larger WebP '
                               'that decodes faster can beat a tiny AVIF for LCP in the wild. '
                               'Spot-check on a cheap device, not only on your flagship.'],
                'code': '<link\n'
                        '  rel="preload"\n'
                        '  as="image"\n'
                        '  href="/images/hero-1600.avif"\n'
                        '  type="image/avif"\n'
                        '  imagesrcset="/images/hero-800.avif 800w, /images/hero-1600.avif 1600w"\n'
                        '  imagesizes="100vw"\n'
                        '  fetchpriority="high"\n'
                        '/>\n'
                        '\n'
                        '<picture>\n'
                        '  <source\n'
                        '    type="image/avif"\n'
                        '    srcset="/images/hero-800.avif 800w, /images/hero-1600.avif 1600w"\n'
                        '    sizes="100vw"\n'
                        '  />\n'
                        '  <source\n'
                        '    type="image/webp"\n'
                        '    srcset="/images/hero-800.webp 800w, /images/hero-1600.webp 1600w"\n'
                        '    sizes="100vw"\n'
                        '  />\n'
                        '  <img\n'
                        '    src="/images/hero-1600.jpg"\n'
                        '    width="1600"\n'
                        '    height="900"\n'
                        '    alt="Product dashboard on a laptop"\n'
                        '    fetchpriority="high"\n'
                        '    decoding="async"\n'
                        '  />\n'
                        '</picture>',
                'code_lang': 'html'},
               {'h2': 'Mistakes that made LCP worse',
                'paragraphs': ['Preloading a WebP while the page actually paints an AVIF from '
                               '`<picture>` wastes bandwidth and confuses prioritization—preload '
                               'the same URL the LCP element will use. Shipping only a 3000px AVIF '
                               '“because AVIF is small” still decodes slowly on mid-range phones.',
                               'Another miss: CSS background-image heroes. They are harder to '
                               'preload and often invisible to LCP candidates the way you expect. '
                               'Prefer an `<img>` in the document for the true LCP media.',
                               'Third miss: putting the hero behind a client-only framework render '
                               'with no SSR/HTML placeholder. The browser cannot preload what does '
                               'not exist in the first HTML byte.',
                               'Priority hints are hints. If the HTML discovers the hero late '
                               'because it sits under a banner injected by JS, fix discovery order '
                               'before tweaking quality dials.'],
                'bullets': ['Never lazy-load the LCP image',
                            'Set explicit dimensions to protect CLS',
                            'Serve responsive widths, not one giant file',
                            'Preload must match the resource that actually paints',
                            'Compress art direction crops separately when the mobile crop '
                            'differs']},
               {'h2': 'CDN and caching practicalities',
                'paragraphs': ['If your CDN can convert on the fly (`format=auto`), great—still '
                               'set sane max widths. Cache-Control should be long-lived with '
                               'fingerprinted filenames. I measure before/after with WebPageTest '
                               'or CrUX, not only Lighthouse on a cable connection.',
                               'On one brochure site, AVIF cut hero transfer from ~450KB JPEG to '
                               '~90KB AVIF. LCP dropped about 0.8s on mid-tier mobile once we also '
                               'fixed `sizes` and removed lazy-loading. Format alone was not the '
                               'whole win.',
                               'Watch Content-Type headers from origin. Serving AVIF as '
                               'octet-stream breaks negotiation in some setups. Be explicit.',
                               'SVGs for simple illustrations beat photos encoded as AVIF. Do not '
                               'rasterize logos. I still find PNG logos in heroes that should have '
                               'been SVG five years ago.',
                               'Vary on Accept only if you truly negotiate at the CDN and '
                               'understand cache key explosion. Many teams are safer generating '
                               'distinct URLs per format and width.']},
               {'h2': 'A short production checklist',
                'paragraphs': ['Identify the LCP element in field data. Encode AVIF+WebP+fallback '
                               'at correct widths. Wire `<picture>` + dimensions + fetchpriority. '
                               'Preload carefully. Re-measure on a throttled mobile profile. Then '
                               'optimize the rest of the page.',
                               'Do not boil the ocean converting every archive thumbnail before '
                               'fixing the hero. LCP cares about one dominant element first.',
                               'Automate encoding in CI so new marketing pages cannot ship a 2MB '
                               'PNG “temporary” asset that becomes permanent.',
                               'Make image budgets part of PR review. A 1.5MB hero should fail CI '
                               'the same way a failing test does. Cultural enforcement beats wiki '
                               'pages nobody reads.',
                               'Record before/after LCP in the PR description with a WebPageTest '
                               'link. Performance work without numbers regresses the first time '
                               'someone swaps in a new brand photo.']},
               {'h2': 'Below-the-fold images after the hero is fixed',
                'paragraphs': ['Once LCP is healthy, lazy-load the rest with loading="lazy" and '
                               'sensible widths. Native lazy loading is enough for most article '
                               'pages; custom IntersectionObserver loaders are rarely worth it '
                               'now.',
                               'For carousels, do not load every slide’s full AVIF up front. Load '
                               'the active slide eagerly and hydrate neighbors on interaction or '
                               'near-viewport approach.'],
                'code': '<img\n'
                        '  src="/images/article-1.webp"\n'
                        '  width="800"\n'
                        '  height="450"\n'
                        '  alt=""\n'
                        '  loading="lazy"\n'
                        '  decoding="async"\n'
                        '/>',
                'code_lang': 'html'}],
  'takeaways': ['Fix the LCP image first: format, size, priority, discovery',
                'Serve AVIF → WebP → JPEG/PNG via picture',
                'Never lazy-load the LCP asset',
                'Match preload to the actual painted resource',
                'Responsive widths matter as much as codec choice',
                'Validate with mobile field or throttled lab data']}]

if __name__ == "__main__":
    print("OK")
