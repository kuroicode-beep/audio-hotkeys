# Landing page

Source for the GitHub Pages site at
<https://kuroicode-beep.github.io/audio-hotkeys/>.

`index.html` is self-contained — no build step, no CDN, no external requests.
Edit it here on `main`, then publish:

```powershell
.\publish_site.ps1
```

That force-pushes this folder to the `gh-pages` branch, which is what Pages
serves. `.nojekyll` stops GitHub from running Jekyll over it.

The download button points at `releases/latest/download/audio-hotkeys.exe`, so
it keeps working across releases as long as each release attaches the exe under
that exact name.
