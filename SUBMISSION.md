# Marketplace submission: Watts (soyaka.watts)

Form: https://github.com/omacom/omarchy-plugin-marketplace/issues/new?template=submit-plugin.yml
(the marketplace moved from HANCORE-linux to omacom; the old link redirects).

Plugin ID `soyaka.watts` was free in the marketplace registry on 6 Nov 2026. Taken nearby:
`neno.power-watts`, `io.github.rr-codebase.wattage`.

Before submitting: create the public repo, push, and add a `preview.png` (optional, recommended).

## Issue title

```
[Plugin]: Watts
```

## Form fields

| Field | Value |
|---|---|
| Repository URL | `https://github.com/soyakaai-studio/omarchy-watts` |
| Category | `System` |
| Tags | `Bar`, `Power management`, `Quickshell` |
| Suggest a missing tag | (leave empty) |
| Maintainer notes | see below |

Maintainer notes:

```
Bar widget: live power draw in watts, battery-life estimate from a ~10 min average drain, and a click that switches the charge limit between 80% and 100% via /sys/class/power_supply/BAT*/charge_control_{start,end}_threshold. Dependencies: Python 3 standard library only. Those files and Intel RAPL energy_uj are root-only by default; without access the widget shows the limit as read-only and CPU watts as "-" on AC. An optional udev rule (udev/99-watts.rules) is included for the user to install manually; the plugin never installs it, runs no sudo, and makes no network calls. State files: ~/.local/state/watts-drain and $XDG_RUNTIME_DIR/watts-rapl.
```

Submission checklist (tick all five, each must be true):

- [x] The repository is public and contains installation and removal instructions.
- [x] I have documented the plugin license and any external dependencies.
- [x] I confirm that I own or have permission to submit this plugin and its preview assets.
- [x] The plugin does not overwrite user configuration without explicit consent.
- [x] I understand that approval is for listing and is not a security review.

## Same thing as a CLI issue body (marketplace SUBMISSION.md format)

```
### Repository URL

https://github.com/soyakaai-studio/omarchy-watts

### Category

System

### Tags

power-management, bar, quickshell

### Suggest a missing tag

_No response_

### Maintainer notes

Bar widget: live power draw in watts, battery-life estimate from a ~10 min average drain, and a click that switches the charge limit between 80% and 100% via /sys/class/power_supply/BAT*/charge_control_{start,end}_threshold. Dependencies: Python 3 standard library only. Those files and Intel RAPL energy_uj are root-only by default; without access the widget shows the limit as read-only and CPU watts as "-" on AC. An optional udev rule (udev/99-watts.rules) is included for the user to install manually; the plugin never installs it, runs no sudo, and makes no network calls. State files: ~/.local/state/watts-drain and $XDG_RUNTIME_DIR/watts-rapl.

### Submission checklist

- [x] The repository is public and contains installation and removal instructions.
- [x] I have documented the plugin license and any external dependencies.
- [x] I confirm that I own or have permission to submit this plugin and its preview assets.
- [x] The plugin does not overwrite user configuration without explicit consent.
- [x] I understand that approval is for listing and is not a security review.
```
