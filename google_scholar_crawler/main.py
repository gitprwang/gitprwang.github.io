from scholarly import scholarly
import jsonpickle
import json
from datetime import datetime
import os

author: dict = scholarly.search_author_id(os.environ['GOOGLE_SCHOLAR_ID'])
author = scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
name = author['name']
author['updated'] = str(datetime.now())

# Index publications by `author_pub_id`, then fill each publication entry so we
# also get fields like authors / journal / conference / pub_url.
author['publications'] = {v['author_pub_id']: v for v in author['publications']}
for pub_id, pub in list(author['publications'].items()):
    # Avoid re-filling if already marked as filled.
    if pub.get('filled'):
        continue
    try:
        filled_pub = scholarly.fill(pub)

        # Reduce payload size: we only need fields used by the homepage UI.
        bib = filled_pub.get('bib') or {}
        bib.pop('abstract', None)
        bib.pop('pages', None)

        filled_pub.pop('cites_per_year', None)
        filled_pub.pop('cites_id', None)
        filled_pub.pop('url_related_articles', None)
        filled_pub.pop('url_add_sclib', None)
        filled_pub.pop('url_scholarbib', None)
        filled_pub.pop('eprint_url', None)

        filled_pub['bib'] = bib
        author['publications'][pub_id] = filled_pub
    except Exception:
        # Some publications may fail due to parsing issues / anti-bot.
        # We'll keep the partially-filled entry instead.
        pass
print(json.dumps(author, indent=2))
os.makedirs('results', exist_ok=True)
with open(f'results/gs_data.json', 'w', encoding='utf-8') as outfile:
    json.dump(author, outfile, ensure_ascii=False)

shieldio_data = {
  "schemaVersion": 1,
  "label": "citations",
  "message": f"{author['citedby']}",
}
with open(f'results/gs_data_shieldsio.json', 'w') as outfile:
    json.dump(shieldio_data, outfile, ensure_ascii=False)
