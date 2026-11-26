# Regional News Monitor

The collector builds a static dashboard, a seven-day combined news RSS feed, a daily press review archive and a separate daily RSS feed. It stores the rolling collection and archive on the `monitor-state` branch. GitHub Pages serves the generated files.

## Maintenance

- Edit `sources.json` to maintain the approved publisher list, news feeds and any official newspaper top-stories feeds. Validate XML, publication dates and publisher access before enabling a new route. Source failures appear on the Sources page. See [SOURCE-AUDIT.md](SOURCE-AUDIT.md).
- In Actions, open **Update Regional News Monitor** and choose **Run workflow** to collect articles manually. Select **Generate today's edition** to create an archived preview without sending email.
- Edit the workflow cron schedules to change collection frequency or edition time. Daily scheduling uses `Europe/Nicosia`. GitHub may delay scheduled runs.
- Under repository **Settings → Secrets and variables → Actions**, set `NEWS_SMTP_USER`, `NEWS_SMTP_PASSWORD` and `NEWS_RECIPIENTS` as secrets when ready to enable email. Use an account-authorized SMTP credential and comma-separated recipients. The default server is Gmail SSL on port 465. Other servers can use repository variables `NEWS_SMTP_HOST` and `NEWS_SMTP_PORT`.
- Review failed Actions runs and the dashboard's source status. The workflow commits an email attempt marker before sending to avoid duplicate delivery on reruns. If SMTP fails, review delivery with the email account owner before resending. Partial delivery or a failed send after claiming the date requires manual review.

## Coverage

Four collection routes remain pending. French feeds require a successfully installed Argos Translate model. The daily edition currently attempts the audited Middle East Eye homepage lead and the official Ukrainska Pravda top-stories feed. Other available selections are labelled latest RSS article. Additional homepage and news-section selectors, publisher-specific editorial filters and publication reuse checks remain outstanding.

The project targets €0 per month using a public repository, standard GitHub-hosted runners and GitHub Pages, open-source local translation, and an eligible existing SMTP account. Delivery is subject to the account's service limits. No paid services are required by the code.
