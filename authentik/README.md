<p align="center">
  <img src="docs/images/login.png" alt="authentik login page in the AstraLabs theme: the lockup over a carbon card on a dot grid, an uppercase title over an acid measurement rule, and an acid Log in button with a cut corner" width="100%">
</p>

<h1 align="center">AstraLabs for authentik</h1>

<p align="center">
  Custom CSS and brand assets that put <a href="https://auth.astralabs.dev">auth.astralabs.dev</a> in the AstraLabs style:<br>
  carbon ground, Bone text, Acid for interaction, square corners, hairline rules and mono labels.
</p>

<p align="center">
  <a href="#install"><b>Install</b></a>
  &nbsp;·&nbsp;
  <a href="#whats-styled">What's styled</a>
  &nbsp;·&nbsp;
  <a href="#editing-the-css">Editing the CSS</a>
  &nbsp;·&nbsp;
  <a href="#recovery">Recovery</a>
</p>

---

## What's in here

| File | Purpose |
|---|---|
| `astralabs.css` | The theme. Paste it into the brand's **Custom CSS** field. |
| `branding/astralabs-lockup.svg` | Mark and `[ASTRA/LABS]` wordmark, used as the brand logo. |
| `branding/astralabs-favicon.svg` | White mark on a carbon square, used as the favicon. |
| `branding/astralabs-mark.svg` | The mark on its own, for anywhere a square logo fits better. |

Tested on authentik **2025.10.3**. The CSS also sets the variables newer releases use (2026.x and the semantic `--ak-color-*` set), but those versions haven't been tested.

---

## Install

### 1. Copy the logos into the branding volume

The compose file already mounts a `branding` volume at `/web/dist/assets/icons/branding`, which authentik serves at `/static/dist/assets/icons/branding/`. From this folder, on the Docker host:

```bash
docker compose -f /path/to/authentik/docker-compose.yml cp branding/. server:/web/dist/assets/icons/branding/
```

Check one loads:

```bash
curl -I https://auth.astralabs.dev/static/dist/assets/icons/branding/astralabs-lockup.svg
```

### 2. Set up the brand

In the admin interface, go to **System → Brands** and edit your brand (the default one, unless you've made another for `auth.astralabs.dev`).

| Field | Value |
|---|---|
| Title | `AstraLabs` |
| Logo | `/static/dist/assets/icons/branding/astralabs-lockup.svg` |
| Favicon | `/static/dist/assets/icons/branding/astralabs-favicon.svg` |
| Custom CSS | the whole of `astralabs.css` |

Then expand **Other global settings** and set **Attributes** to force dark mode. The theme is dark only, and without this a visitor whose browser prefers light mode gets authentik's light base under it:

```yaml
settings:
  theme:
    base: dark
```

Save, then open the login page in a private window to skip any cached copy.

### Or apply it with the API

If you'd rather keep it in version control and push changes from the command line, set `AK_TOKEN` to an API token with permission to edit brands (**Directory → Tokens and App passwords**) and run:

```bash
BRAND=$(curl -s -H "Authorization: Bearer $AK_TOKEN" "https://auth.astralabs.dev/api/v3/core/brands/?default=true" | python3 -c "import sys,json; print(json.load(sys.stdin)['results'][0]['brand_uuid'])")
```

```bash
python3 -c "import json; print(json.dumps({'branding_custom_css': open('astralabs.css').read()}))" | curl -s -X PATCH -H "Authorization: Bearer $AK_TOKEN" -H "Content-Type: application/json" --data @- "https://auth.astralabs.dev/api/v3/core/brands/$BRAND/"
```

---

## What's styled

**Login and enrolment flows**
- Carbon background with a faint 16px dot grid, replacing the flow background image.
- The card is a plate panel with a hairline border and bone corner ticks, and no shadow.
- The stage title is heavy uppercase Archivo over a measurement rule (an Acid index segment, then a hairline with end ticks).
- Field labels are mono uppercase. Required markers are Acid.
- Inputs are square on carbon with an Acid focus ring. Invalid fields turn the "down" red.
- The primary button is Acid with dark mono text and the brand's single 60° cut in the top-right corner. Secondary buttons are outlined, and links are Bone with an Acid underline.
- "Powered by authentik" and your brand links are small mono labels.
- Alerts use a plate background with a coloured left edge.

**User library**
- Carbon background with the dot grid, square plate application cards with hairline borders and an Acid edge on hover.
- Uppercase page title, mono labels for application groups.

**Admin interface**
- The same palette, fonts and square corners. The current sidebar item gets an Acid bar instead of authentik's orange.

**Fonts**
Archivo and Martian Mono load from Google Fonts through two `@import` lines at the top of the CSS. If a reverse proxy in front of authentik sets a Content-Security-Policy, allow `fonts.googleapis.com` and `fonts.gstatic.com`. Authentik itself doesn't set one.

---

## Editing the CSS

Authentik copies the brand CSS into every web component's shadow root, and into a `<style>` element in the page head. A few things follow from that:

- **Don't use the less-than, greater-than or ampersand characters.** The page-head copy escapes them, which breaks any rule that uses them. That rules out child combinators (use a descendant selector instead) and a single Google Fonts URL that loads two families (hence two `@import` lines).
- **Variables are set three ways** so the theme survives upgrades: authentik 2025.x builds its dark theme from `--ak-dark-*`, 2026.x adds `--ak-font-family-*` and `--ak-v2-*`, and PatternFly 4 `--pf-global--*` variables sit underneath both.
- **Page-level rules need extra specificity.** Authentik's own stylesheets are adopted after the page `<style>`, so the tokens use `html:root` and the background uses `html body` to win there.
- **Upgrades can move things.** Rules that target PatternFly classes (`.pf-c-login__main`, `.pf-c-button.pf-m-primary`, …) depend on authentik's markup. After an upgrade, check the login page, the library and the admin interface.

---

## Recovery

If a CSS change locks you out of the login page, create a recovery link. Logging in with it disables custom CSS for that session, so you can fix or clear the brand's CSS:

```bash
docker compose run --rm server create_recovery_key 10 akadmin
```

---

## A note on the compose file

The `server` service defaults to `AUTHENTIK_TAG` `2025.10.23`, which doesn't exist, while `worker` defaults to `2025.10.3`. If `stack.env` sets `AUTHENTIK_TAG`, both use that and it doesn't matter. If it doesn't, the server can't pull its image. Use the same tag for both.

---

## Licence

Copyright © 2026 Emily Astranova. Licensed under the [GNU Affero General Public License v3.0](../LICENSE).
