# Aperçus motion

Film de 16 s (1280×720) qui montre le rôle du sélecteur.

- Vidéo : [jev-memory-selector.mp4](jev-memory-selector.mp4)
- Page live : `jev-memory serve` puis http://127.0.0.1:8080/preview

Réenregistrer :

```bash
uv run jev-memory serve
cd docs/preview
npm install
npx playwright install chromium
node record.mjs
ffmpeg -y -i jev-memory-selector.webm -c:v libx264 -pix_fmt yuv420p -movflags +faststart jev-memory-selector.mp4
```
