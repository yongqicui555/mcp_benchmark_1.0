# Demo assets

This directory will hold the demo GIF referenced in the main `README.md`
as `assets/demo.gif`. Until the GIF is recorded, the README points here
but the file doesn't exist.

## To record the demo (5-10 min)

1. Run a fresh audit against a vibe-coded app you control (your own
   project, or one of the test fixtures in `tests/golden_site/`).
2. Use Kap (macOS, free, https://getkap.co) or similar screencast tool.
3. Record a 30-second capture showing:
   - The agent prompt: `> audit https://my-vibe-coded-app.com`
   - The audit completing in ~25 seconds
   - 3 critical findings listed (a broken pixel, a missing consent
     signal, a console error)
   - The "view full report" link
4. Export as `demo.gif` and drop it here.
5. Commit:
   ```bash
   git add assets/demo.gif
   git commit -m "docs: add 30s demo GIF"
   git push origin main
   ```

## Using ffmpeg (CLI alternative)

If you already have a screen recording (e.g. `.mov` from QuickTime):

```bash
ffmpeg -i ~/Desktop/screencast.mov \
  -vf "fps=15,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  -loop 0 \
  ~/gtm-packaging/prufa-mcp/assets/demo.gif
```

Adjust `fps=15` and `scale=800` to taste.
