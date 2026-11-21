# Program illustrations

Original artwork for the website's program cards (1200×750, 16:10), in the site's purple-and-gold style (matching the University logo).
No people or faces are depicted.

Regenerate (needs Google Chrome and internet for the Amiri / Cormorant / Inter web fonts):

```bash
mkdir -p /tmp/prog/html /tmp/prog/png
python3 make_html.py /tmp/prog/html
node render.mjs /tmp/prog/html /tmp/prog/png      # then convert to .jpg into ../
```

`seed_demo` attaches `../<slug>.jpg` to each Program with the same slug.
