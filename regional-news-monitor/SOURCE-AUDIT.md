# Regional News Monitor — preliminary source audit

26 November 2026. All 18 publications from the brief are listed below. The probes made direct HTTP requests and parsed publisher responses as XML. Dates are UTC and represent the newest dated entry returned. A successful probe establishes availability at the time of the check.

| Publication | Candidate feed | Observed result |
| --- | --- | --- |
| [Asharq Al-Awsat](https://english.aawsat.com/) | [Endpoint](https://english.aawsat.com/feed) | RSS, 300 entries, newest 2026-11-26 10:10 |
| [Arab News](https://www.arabnews.com/) | [Endpoint](https://www.arabnews.com/rss.xml) | RSS, 50 entries, newest 2026-11-26 09:56 |
| [Middle East Eye](https://www.middleeasteye.net/) | [Endpoint](https://www.middleeasteye.net/rss) | RSS, 20 entries, newest 2026-11-26 09:33 |
| [The National](https://www.thenationalnews.com/) | [Endpoint](https://www.thenationalnews.com/arc/outboundfeeds/rss-latest/?outputType=xml&_website=the-national) | RSS, 30 entries, newest 2026-11-26 10:04 |
| [Gulf News](https://gulfnews.com/) | [Endpoint](https://gulfnews.com/stories.rss) | RSS, 54 entries, newest 2026-11-26 09:53 |
| [Haaretz](https://www.haaretz.com/) | [Endpoint](https://www.haaretz.com/srv/all-headlines-rss) | RSS, 100 entries, newest 2026-11-26 09:44 |
| [The Times of Israel](https://www.timesofisrael.com/) | [Endpoint](https://www.timesofisrael.com/feed/) | RSS, 14 entries, newest 2026-11-26 09:54 |
| [L’Orient Today](https://today.lorientlejour.com/) | — | Feed discovery pending |
| [Enab Baladi](https://english.enabbaladi.net/) | [Endpoint](https://english.enabbaladi.net/feed/) | RSS, 20 entries, newest 2026-11-25 19:00 |
| [The Jordan Times](https://jordantimes.com/) | [Endpoint](https://jordantimes.com/rss) | HTTP 403 |
| [Ahram Online](https://english.ahram.org.eg/) | [Endpoint](https://english.ahram.org.eg/News/RSSFeed.aspx) | HTTP 200, HTML |
| [Libya Herald](https://libyaherald.com/) | [Endpoint](https://libyaherald.com/rss.xml) | RSS, 0 entries |
| [Business News Tunisia](https://www.businessnews.com.tn/) | [Endpoint](https://businessnews.com.tn/feed/) | RSS, 10 entries, newest 2026-11-26 09:55 |
| [TSA Algérie](https://www.tsa-algerie.com/) | [Endpoint](https://www.tsa-algerie.com/feed/) | RSS, 10 entries, newest 2026-11-26 08:20 |
| [TASS](https://tass.com/) | [Endpoint](https://tass.com/rss/v2.xml) | RSS, 100 entries, newest 2026-11-26 10:08 |
| [The Moscow Times](https://www.themoscowtimes.com/) | [Endpoint](https://www.themoscowtimes.com/rss/news) | RSS, 50 entries, newest 2026-11-26 09:14 |
| [Balkan Insight](https://balkaninsight.com/) | [Endpoint](https://balkaninsight.com/feed/) | RSS, 90 entries, newest 2026-11-26 10:08 |
| [Ukrainska Pravda](https://www.pravda.com.ua/eng/) | [Endpoint](https://www.pravda.com.ua/eng/rss/view_news/) | RSS, 20 entries, newest 2026-11-26 08:58 |

## Source configuration notes

- **Middle East Eye**. Cloud browser confirmed the English homepage, a prominent editorial lead and a separate News section. Feed response requires gzip decoding.
- **Haaretz**. Use public feed metadata and direct links. Respect article subscription prompts.
- **L’Orient Today**. English homepage returned HTTP 200 and advertised no RSS or Atom alternate in the fetched markup. Check publisher guidance and permitted News-section collection.
- **The Jordan Times**. Both the homepage and the candidate RSS URL returned HTTP 403 from this environment. Check for a publisher-supported syndication route.
- **Ahram Online**. The candidate returned an HTML page. Inspect publisher links for actual category XML and assess permitted collection.
- **Libya Herald**. The master stream parsed but contained zero articles. The government and politics category returned 50 entries on the first probe and HTTP 404 on retest.
- **Business News Tunisia**. French headlines and descriptions require English translation.
- **TSA Algérie**. French headlines and descriptions require English translation.
- **Ukrainska Pravda**. The publisher also lists a separate most-important-news feed for the newsletter fallback.

## Additional feed probes

- Libya Herald government-politics returned HTTP Error 404: Not Found. [Endpoint](https://libyaherald.com/rss/government-politics)
- Libya Herald business-investment returned 0 entries. [Endpoint](https://libyaherald.com/rss/business-investment)
- Libya Herald economy-policy returned HTTP Error 404: Not Found. [Endpoint](https://libyaherald.com/rss/economy-policy)
- Libya Herald energy-climate returned HTTP Error 404: Not Found. [Endpoint](https://libyaherald.com/rss/energy-climate)
- Libya Herald security-risk returned 0 entries. [Endpoint](https://libyaherald.com/rss/security-risk)
- Libya Herald culture-society returned 0 entries. [Endpoint](https://libyaherald.com/rss/culture-society)
- Ukrainska Pravda top stories returned 20 entries, newest 2026-11-26 07:18 UTC. [Endpoint](https://www.pravda.com.ua/eng/rss/view_mainnews/)

## Remaining verification

The next pass needs to verify link and date coverage, source-specific categories and exclusions, publication terms for public metadata reuse and automated access, and editorial lead selectors over multiple observations. Test repeated fetches from the eventual scheduler and compare the results with this one-time probe.

The combined feed should use publisher news feeds and deduplicate by publication and stable article identity. The daily edition should follow the homepage, relevant section, official top-stories feed, and latest relevant feed article in that order. Each fallback needs a visible label. The site, DNS, scheduled runs, email delivery, and operating cost remain unverified.
