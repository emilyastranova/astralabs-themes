<h1 align="center">AstraLabs Themes</h1>

<p align="center">
  The AstraLabs look for the self-hosted web services behind <a href="https://astralabs.dev">astralabs.dev</a>.<br>
  One folder per service, each with its stylesheet, brand assets and setup instructions.
</p>

<p align="center">
  <a href="#themes"><b>Themes</b></a>
  &nbsp;·&nbsp;
  <a href="#the-design-in-brief">The design in brief</a>
  &nbsp;·&nbsp;
  <a href="#adding-a-service">Adding a service</a>
</p>

---

## Themes

<table>
  <tr>
    <td width="45%">
      <a href="authentik/"><img src="authentik/docs/images/login.png" alt="authentik login page in the AstraLabs theme"></a>
    </td>
    <td>
      <h3><a href="authentik/">authentik</a></h3>
      Single sign-on at <code>auth.astralabs.dev</code>. Brand custom CSS for the login and enrolment flows, the app library and the admin interface, plus the logo and favicon.<br><br>
      Tested on authentik 2025.10.3.
    </td>
  </tr>
</table>

---

## The design in brief

Every theme here follows the same rules, so the services read as one system. The full brand guide, tokens and logo files live in the AstraLabs design repo.

| Token | Hex | Role |
|---|---|---|
| Void | `#0A0909` | Page background |
| Plate | `#131212` | Raised surfaces, cards, panels |
| Rule | `#2C2A29` | Hairline borders and dividers |
| Bone | `#EDE6E1` | Text and line work |
| Ash | `#8E8380` | Secondary text and labels |
| Acid | `#B6FF2E` | Primary actions, focus, selection, with Void text on top |
| OK / Warn / Down | `#4DFF88` / `#FFA21F` / `#FF2E3A` | Status only, always with a label |

- **Type.** Archivo for headings and body; Martian Mono for labels, data and code. Headings are heavy uppercase; labels are small mono uppercase with wide tracking.
- **Geometry.** Square corners everywhere. The one exception is a 60° cut on the filled primary button, and there is only one per view.
- **Line work.** Hairline rules, corner ticks, a measurement rule under page titles, and a faint 16px dot grid behind pages. No drop shadows, no glows.
- **Links.** Bone with an Acid underline, turning Acid on hover.
- **Focus.** A 2px Acid ring. Drawn inside the element where a container would clip it.
- **Dark only.** Force each service's dark mode where it has one, so the theme never sits on a light base.

---

## Adding a service

Give each service its own folder, named after the service in lowercase:

```
<service>/
  README.md          what it styles, install steps, version tested, how to recover from a broken theme
  astralabs.css      the stylesheet (or whatever format the service takes)
  branding/          logos and favicons in the form the service wants them
  docs/images/       screenshots for the README
```

Then add a row to the [Themes](#themes) table above.

Before calling a theme done, run the service locally at the version you're targeting and check the login page, the main logged-in screen and any admin area, including the focus, error and empty states. Note the tested version in the service's README; themes that override a service's markup can break when it upgrades.

---

## Licence

Copyright © 2026 Emily Astranova. Licensed under the [GNU Affero General Public License v3.0](LICENSE).
