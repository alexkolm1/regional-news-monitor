const region = document.querySelector('#region');
const source = document.querySelector('#source');
const articles = [...document.querySelectorAll('article[data-source]')];
function filterArticles() {
  let shown = 0;
  for (const article of articles) {
    article.hidden = Boolean(
      (region.value && article.dataset.region !== region.value) ||
      (source.value && article.dataset.source !== source.value)
    );
    if (!article.hidden) shown += 1;
  }
  document.querySelector('#empty').hidden = shown > 0;
}
region.addEventListener('change', filterArticles);
source.addEventListener('change', filterArticles);
filterArticles();
