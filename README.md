# Watts

An Omarchy bar widget that shows your laptop's live power draw in watts.

- **Bar:** the current draw, for example `7W`. On battery it is the whole laptop's draw
  (`power_now` summed over all batteries, battery icon). On AC no sysfs sensor measures the
  whole system, so it shows the CPU package power from Intel RAPL instead (chip icon).
- **Tooltip and panel:** battery time left, estimated from a roughly 10-minute moving average
  of the on-battery drain (kept across reboots, so an estimate is ready on AC too), the charge
  per battery, the USB-C supply wattage when the UCSI driver reports it, and the charge limit.
- **Click (or Return in the panel):** switches the battery charge limit between 80% and 100%.
  At 80% charging stops at 80% and resumes below 75%. The new limit flashes in the bar for two
  seconds as confirmation.

Laptops with two batteries (for example ThinkPads with an internal and an external battery)
are listed as "Internal" and "External"; a single battery is "Battery". Desktops without a
battery show CPU power only.

> Screenshot: add a `preview.png` to the repository root before submitting it to the
> marketplace.

## Requirements

- Omarchy 4.5 or later (Quattro shell, plugin manifest schema 1)
- Python 3 (standard library only; no other dependencies)
- A battery driver that exposes `/sys/class/power_supply/BAT*`
- For the charge limit: firmware support for `charge_control_end_threshold` (ThinkPads and
  many other recent laptops) and **write access** to it. By default these files are writable
  only by root, so the widget shows the limit as read-only until you grant access (see below).
- For CPU watts on AC: Intel RAPL (`/sys/class/powercap/intel-rapl:0`). Since Linux 5.10
  `energy_uj` is readable only by root, so without the rule below the bar shows `-W` on AC.

### Optional: grant access with a udev rule

The repository includes `udev/99-watts.rules`. It lets members of the `wheel` group (the
default admin group on Arch and Omarchy) write the charge thresholds and read the RAPL energy
counter. The plugin never installs it for you. Read it, then install it yourself:

```sh
sudo install -m 644 udev/99-watts.rules /etc/udev/rules.d/
sudo udevadm control --reload
sudo udevadm trigger --subsystem-match=power_supply --subsystem-match=powercap
```

Check that your user is in `wheel` (`id -nG`). Reading RAPL leaks fine-grained CPU power
information to that group, which is the reason the kernel restricted it; only add the rule if
you accept that on your machine. Remove it with
`sudo rm /etc/udev/rules.d/99-watts.rules` and a reboot.

## Install

With the Omarchy plugin manager:

```sh
omarchy plugin add https://github.com/soyakaai-studio/omarchy-watts.git --enable
```

Or manually:

```sh
git clone https://github.com/soyakaai-studio/omarchy-watts.git ~/.config/omarchy/plugins/soyaka.watts
omarchy-shell shell rescanPlugins
omarchy plugin enable soyaka.watts
```

Move it within the bar if you like, for example `omarchy bar move soyaka.watts --section right`.

## Remove

```sh
omarchy plugin remove soyaka.watts
```

The widget keeps two small state files, which you can delete afterwards:
`~/.local/state/watts-drain` (the average drain) and `$XDG_RUNTIME_DIR/watts-rapl` (cleared on
logout). If you installed the udev rule, remove it as described above. The charge limit you
last set stays in the firmware; set it back to 100% with a click before removing, if you want.

## How it works

`Watts.qml` runs `python3 -I watts.py` every 3 seconds and on click (`watts.py toggle`). The
script reads sysfs only, writes nothing outside the two state files and, on toggle, the charge
threshold files, and prints one JSON line:

```json
{"watts": 7, "source": "battery", "limit": 80, "error": false, "tip": "..."}
```

## License

MIT, copyright (c) 2026 Sonat Yalcinkaya. See [LICENSE](LICENSE).
