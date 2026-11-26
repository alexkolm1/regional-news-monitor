const region = document.querySelector('#region');
const source = document.querySelector('#source');
const empty = document.querySelector('#empty');
const articles = [...document.querySelectorAll('article[data-region]')];

const preferredOrder = ['Pan-Arab and Gulf', 'Israel and Levant', 'North Africa', 'Russia, Ukraine and Balkans'];
const regionNames = new Set([...region.options].map(option => option.value).filter(Boolean));
const names = [...preferredOrder.filter(name => regionNames.delete(name)), ...regionNames];
const filters = region.closest('.filters');
const regionControls = document.createElement('div');
regionControls.className = 'region-controls';
regionControls.setAttribute('role', 'group');
regionControls.setAttribute('aria-label', 'Filter by region');
filters.before(regionControls);
region.closest('label').hidden = true;

const result = document.createElement('p');
result.className = 'result-count';
result.setAttribute('role', 'status');
filters.after(result);

const regions = new Map();
for (const name of names) {
  const section = document.createElement('section');
  section.className = 'region-section';
  const header = document.createElement('div');
  header.className = 'region-heading';
  const heading = document.createElement('h2');
  heading.textContent = name;
  const count = document.createElement('span');
  count.className = 'region-count';
  header.append(heading, count);
  section.append(header);
  empty.before(section);
  regions.set(name, { section, count, articles: [] });
}

for (const article of articles) {
  const group = regions.get(article.dataset.region);
  group.section.append(article);
  group.articles.push(article);
  const headline = article.querySelector('h2');
  if (headline) {
    const heading = document.createElement('h3');
    heading.append(...headline.childNodes);
    headline.replaceWith(heading);
  }
}

const buttons = new Map();
for (const name of ['', ...names]) {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = name || 'All regions';
  button.addEventListener('click', () => {
    region.value = name;
    filterArticles();
  });
  regionControls.append(button);
  buttons.set(name, button);
}

function articleCount(count) {
  return count.toLocaleString('en') + (count === 1 ? ' article' : ' articles');
}

function filterArticles() {
  for (const [name, button] of buttons) {
    button.setAttribute('aria-pressed', String(name === region.value));
  }
  let total = 0;
  for (const [name, group] of regions) {
    let count = 0;
    const regionMatches = !region.value || region.value === name;
    for (const article of group.articles) {
      const show = regionMatches && (!source.value || article.dataset.source === source.value);
      article.hidden = !show;
      if (show) count += 1;
    }
    group.section.hidden = count === 0;
    group.count.textContent = articleCount(count);
    total += count;
  }
  result.textContent = articleCount(total);
  empty.hidden = total > 0;
}

source.addEventListener('change', filterArticles);
filterArticles();
