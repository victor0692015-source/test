# Local asset checklist (offline-ready)

Put these files into your project so `index.html` has no external CDN dependencies.

## 1) CSS dependencies

Place files:
- `assets/vendor/css/tailwind.min.css`
- `assets/vendor/css/fontawesome.min.css`

Source URLs (download on your machine):
- `https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css`
- `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css`

Then rename `all.min.css` to `fontawesome.min.css`.

## 2) Font Awesome webfonts

From Font Awesome package, copy these to `assets/vendor/webfonts/`:
- `fa-solid-900.woff2`
- `fa-regular-400.woff2`
- `fa-brands-400.woff2`
- (optionally matching `.ttf` files)

If needed, update paths inside `assets/vendor/css/fontawesome.min.css` from:
`../webfonts/...` to `../webfonts/...` (already correct for current layout).

## 3) Google fonts local files

Download these `.woff2` font files and place into `assets/vendor/fonts/`:
- `montserrat-v26-latin-ext_latin_cyrillic-ext_cyrillic-300.woff2`
- `montserrat-v26-latin-ext_latin_cyrillic-ext_cyrillic-400.woff2`
- `montserrat-v26-latin-ext_latin_cyrillic-ext_cyrillic-600.woff2`
- `montserrat-v26-latin-ext_latin_cyrillic-ext_cyrillic-700.woff2`
- `montserrat-v26-latin-ext_latin_cyrillic-ext_cyrillic-800.woff2`
- `montserrat-v26-latin-ext_latin_cyrillic-ext_cyrillic-900.woff2`
- `open-sans-v40-latin-ext_latin_cyrillic-ext_cyrillic-400.woff2`
- `open-sans-v40-latin-ext_latin_cyrillic-ext_cyrillic-600.woff2`

`assets/vendor/fonts/fonts.css` is already prepared with matching `@font-face` declarations.

## 4) Local images

Ensure these exist:
- `assets/images/hero-it.webp`
- `assets/images/backup-cloud.webp`
