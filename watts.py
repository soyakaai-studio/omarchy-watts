#!/usr/bin/env python3
# Watts for the Omarchy bar: prints one JSON line with the live power draw, the charge limit
# and a tooltip with the battery-life estimate. With "toggle" it first flips the battery charge
# limit between 80% and 100%.
#
# On battery the draw is the whole laptop: power_now summed over all batteries. On AC nothing
# in sysfs measures the whole system, so it falls back to the CPU package power from Intel RAPL,
# averaged since the previous poll. Reading RAPL and writing the charge thresholds both need
# extra permissions on most systems; see the README for the udev rule.
import glob, json, math, os, sys, time

PS = "/sys/class/power_supply"
BATS = sorted(b for b in glob.glob(f"{PS}/BAT*") if os.path.isdir(b))
LIMIT, RESUME = 80, 75  # stop charging at 80%, start again below 75%
RAPL = "/sys/class/powercap/intel-rapl:0"

RUNTIME = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
STATE_HOME = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
RAPL_STATE = os.path.join(RUNTIME, "watts-rapl")
# Average on-battery draw, kept across reboots so the estimate is ready on AC too.
DRAIN = os.path.join(STATE_HOME, "watts-drain")
DRAIN_WINDOW = 600  # seconds the moving average roughly spans
DEFAULT_DRAIN = 8.0  # W, a typical light-use laptop draw, used until history exists


def read(path, default=0):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return default


def num(path):
    try:
        return int(read(path, ""))
    except ValueError:
        return None


def write(path, value):
    with open(path, "w") as f:
        f.write(str(value))


def battery_name(b):
    if len(BATS) == 1:
        return "Battery"
    if len(BATS) == 2:
        return "Internal" if b == BATS[0] else "External"
    return os.path.basename(b)


def battery_watts(b):
    """Battery power in W, from power_now or, where the driver lacks it, current x voltage."""
    p = num(f"{b}/power_now")
    if p is not None:
        return abs(p) / 1e6
    i, v = num(f"{b}/current_now"), num(f"{b}/voltage_now")
    return abs(i) * v / 1e12 if i is not None and v is not None else 0.0


def battery_wh(b, kind):
    """energy_now / energy_full in Wh, or charge_* (uAh) x design voltage on charge-based drivers."""
    e = num(f"{b}/energy_{kind}")
    if e is not None:
        return e / 1e6
    c, v = num(f"{b}/charge_{kind}"), num(f"{b}/voltage_min_design") or num(f"{b}/voltage_now")
    return c * v / 1e12 if c is not None and v is not None else 0.0


def on_ac():
    """True when any mains or USB supply (not a battery-powered peripheral) is online."""
    for s in glob.glob(f"{PS}/*"):
        if read(f"{s}/type", "") in ("Mains", "USB") and read(f"{s}/scope", "") != "Device":
            if read(f"{s}/online") == "1":
                return True
    return False


def usbc_supply_watts():
    """Most the USB-C supply offers (its top voltage x current), when the UCSI driver reports it."""
    for u in glob.glob(f"{PS}/ucsi-source-psy-*"):
        if read(f"{u}/online") == "1":
            w = round((num(f"{u}/voltage_max") or 0) * (num(f"{u}/current_max") or 0) / 1e12)
            if w:
                return w
    return None


def avg_drain(now_watts, discharging):
    """Time-weighted moving average of draw while on battery; returns (watts, measured)."""
    try:
        w, t0 = map(float, read(DRAIN, "").split())
        measured = True
    except ValueError:
        w, t0, measured = DEFAULT_DRAIN, None, False
    t = time.time()
    if discharging and now_watts > 0.5:
        dt = min(t - t0, 30) if t0 else DRAIN_WINDOW
        a = 1 - math.exp(-dt / DRAIN_WINDOW)
        w = now_watts if not measured else w + a * (now_watts - w)
        try:
            os.makedirs(os.path.dirname(DRAIN), exist_ok=True)
            with open(DRAIN, "w") as f:
                f.write(f"{w} {t}")
        except OSError:
            pass
        measured = True
    return w, measured


def hours(h):
    return f"{int(h)}h {round(h % 1 * 60):02d}m"


def cpu_watts():
    """CPU package power from RAPL, averaged since the last poll; None if RAPL is not readable."""
    energy, now = num(f"{RAPL}/energy_uj"), time.monotonic()
    wrap = num(f"{RAPL}/max_energy_range_uj")
    if energy is None or not wrap:
        return None
    try:
        e0, t0 = map(float, read(RAPL_STATE, "").split())
    except ValueError:
        e0, t0 = None, None
    try:
        with open(RAPL_STATE, "w") as f:
            f.write(f"{energy} {now}")
    except OSError:
        pass
    if e0 is None or now - t0 < 0.5 or now - t0 > 30:
        # No usable previous sample: take a short one-off reading.
        time.sleep(0.5)
        e0, t0, energy, now = energy, now, num(f"{RAPL}/energy_uj"), time.monotonic()
        if energy is None:
            return None
    return ((energy - e0) % wrap) / 1e6 / (now - t0)


def threshold_files():
    return [f"{b}/charge_control_{k}_threshold" for b in BATS for k in ("start", "end")
            if os.path.exists(f"{b}/charge_control_{k}_threshold")]


def limit():
    """Current end threshold, or None when the hardware has no charge limit."""
    return num(f"{BATS[0]}/charge_control_end_threshold") if BATS else None


def toggle():
    to80 = (limit() or 100) >= 100
    for b in BATS:
        end, start = f"{b}/charge_control_end_threshold", f"{b}/charge_control_start_threshold"
        has_start = os.path.exists(start)
        # Firmware usually requires start < end, so the order matters in each direction.
        if to80:
            write(end, LIMIT)
            if has_start:
                write(start, RESUME)
        else:
            if has_start:
                write(start, 0)
            write(end, 100)


error = ""
if sys.argv[1:] == ["toggle"]:
    try:
        if limit() is None:
            raise OSError(0, "this battery has no charge limit")
        toggle()
    except OSError as e:
        error = f"Can't set the limit: {e.strerror}"

ac = on_ac() or not BATS
bat_w = sum(battery_watts(b) for b in BATS)
source = "cpu" if ac else "battery"
watts = cpu_watts() if ac else bat_w
lim = limit()
writable = bool(threshold_files()) and all(os.access(p, os.W_OK) for p in threshold_files())

lines = []
if not BATS:
    lines.append("No battery found · showing CPU power")
else:
    discharging = any(read(f"{b}/status", "") == "Discharging" for b in BATS)
    drain, measured = avg_drain(bat_w, discharging and not ac)
    energy = {b: battery_wh(b, "now") for b in BATS}
    full = sum(battery_wh(b, "full") for b in BATS)
    pct = round(100 * sum(energy.values()) / full) if full else num(f"{BATS[0]}/capacity") or 0
    sources = sorted(((wh / drain, battery_name(b), f"{wh:.1f} Wh left, {num(f'{b}/capacity') or 0}%")
                      for b, wh in energy.items()), reverse=True)
    lines.append(f"{hours(sum(h for h, _, _ in sources))} left · {pct}%")
    if ac:
        sw = usbc_supply_watts()
        lines.append(f"Plugged in · {sw} W USB-C supply" if sw else "Plugged in")
        if watts is not None:
            lines.append(f"Showing CPU power ({round(watts)} W); the whole-system draw is unmeasured on AC")
    lines.append("")
    if len(sources) > 1:
        lines.extend(f"{hours(h):>7}  {name} · {why}" for h, name, why in sources)
    else:
        lines.append(sources[0][2])
    lines.append(f"Estimate from a ~10 min average drain of {drain:.1f} W"
                 + ("" if measured else " (default until measured on battery)"))
    lines.append("")
    if lim is None:
        lines.append("No charge limit on this battery")
    elif writable:
        lines.append(f"Charge limit {lim}% · click for {'100' if lim < 100 else str(LIMIT)}%")
    else:
        lines.append(f"Charge limit {lim}% · read-only (see README to enable)")
if ac and watts is None:
    lines.append("CPU power unavailable: RAPL is not readable (see README)")
if error:
    lines.insert(0, error)

print(json.dumps({"watts": None if watts is None else round(watts), "source": source,
                  "limit": 100 if lim is None else lim, "error": bool(error),
                  "tip": "\n".join(lines)}))
