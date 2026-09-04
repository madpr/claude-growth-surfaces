/* Reproduces the entry-point table in entry-points.md.
 *
 *   1. Sign in to claude.ai.
 *   2. Open the account menu, or Settings, so the links are mounted.
 *   3. Paste this into the browser console.
 *
 * Prints link text, path, and which UTM parameters are present. It never prints a
 * parameter value, an email, a name, or an organization id, so the finding can be
 * reproduced without publishing your own account.
 */

(() => {
  const PLATFORM = /platform\.claude\.com|console\.anthropic\.com/;

  const links = Array.from(document.querySelectorAll('a[href]'))
    .filter((a) => PLATFORM.test(a.href))
    .map((a) => {
      const u = new URL(a.href);
      return {
        text: a.innerText.replace(/\s+/g, ' ').trim(),
        path: u.pathname,
        opensNewTab: a.target === '_blank',
        utmKeys: Array.from(u.searchParams.keys())
          .filter((k) => k.startsWith('utm_'))
          .sort()
          .join(','),
      };
    });

  console.log('platform links mounted on this view:', links.length);
  console.table(links);

  const toDashboard = links.filter((l) => l.path === '/dashboard').length;
  const toKeys = links.filter((l) => l.path === '/settings/keys').length;
  console.log(`  -> /settings/keys : ${toKeys}`);
  console.log(`  -> /dashboard     : ${toDashboard}`);
  console.log(
    toDashboard === 0
      ? '  no link reaches the dashboard from this view.'
      : '  a dashboard link exists; entry-points.md is out of date.'
  );

  // The left rail, for the placement claim. Labels only.
  const rail = Array.from(document.querySelectorAll('nav a, aside a'))
    .map((a) => a.innerText.replace(/\s+/g, ' ').trim())
    .filter((t) => t && t.length < 24);
  console.log('left rail labels:', rail.slice(0, 12));

  return { links, toKeys, toDashboard };
})();
