# 🛍️ Too Good To Go — Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/Steppedrengen/ha-tgtg?style=flat-square)](https://github.com/Steppedrengen/ha-tgtg/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1%2B-41BDF5.svg)](https://www.home-assistant.io)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)

A custom Home Assistant integration that pulls your **Too Good To Go** favourite stores as sensors — including real-time availability, pickup windows, pricing, and **distance from your HA home coordinates**.

---

## ✨ Features

- 📦 **One sensor per store** — state = number of available magic bags
- 📍 **Distance sorting** — calculates km from your HA home location using the Haversine formula
- 🕐 **Pickup window** — formatted pickup time shown as a sensor attribute
- 💰 **Pricing** — price including taxes exposed per store
- ❤️ **Favourites only** — only your TGTG favourite stores are fetched
- 🔔 **Automation-ready** — trigger push notifications when bags become available
- 🌐 **Bilingual** — UI available in English and Danish (`da`)
- ♻️ **Configurable polling** — set your own update interval (1–60 min)

---

## 📋 Requirements

| Requirement | Version |
|---|---|
| Home Assistant | 2023.1+ |
| HACS | 1.x |
| Python package | `tgtg >= 0.17.0` *(auto-installed)* |
| TGTG account | Free account with ≥ 1 favourite store |

---

## 🚀 Installation

### Option A — Via HACS *(recommended)*

1. Open **HACS → Integrations**
2. Click the **⋮ menu → Custom repositories**
3. Add:
   - **URL:** `https://github.com/Steppedrengen/ha-tgtg`
   - **Category:** Integration
4. Search for **"Too Good To Go"** in HACS and click **Download**
5. **Restart Home Assistant**

### Option B — Manual

1. Download the [latest release](https://github.com/Steppedrengen/ha-tgtg/releases/latest)
2. Extract and copy the `custom_components/tgtg/` folder to your HA config:
   ```
   config/
   └── custom_components/
       └── tgtg/          ← copy here
   ```
3. **Restart Home Assistant**

---

## ⚙️ Configuration

Authentication uses a **PIN code sent to your email** — no password needed.

### Step-by-step

**1. Add the integration**

Go to **Settings → Devices & Services → Add Integration** and search for **Too Good To Go**.

**2. Enter your email address**

Type the email address linked to your Too Good To Go account and press **Submit**.

> ⚠️ The email must already be registered in the TGTG app. If you don't have an account yet, sign up in the app first.

**3. Check your email for a PIN code**

Too Good To Go will send an email to your inbox with a **6-digit PIN code**. It looks like this:

```
Subject: Your Too Good To Go login code
Your login PIN: 123456
```

> 📬 Check your spam folder if you don't see it within a minute or two.

**4. Enter the PIN in Home Assistant**

Go back to the Home Assistant config flow and type the **6-digit PIN** into the PIN field, then press **Submit**.

**5. Set your update interval**

Choose how often HA should poll Too Good To Go for new availability (default: every 5 minutes). Press **Submit** to finish.

**6. Done!**

Your favourite TGTG stores will appear as sensor entities within a few seconds.

---

## 📊 Sensor Reference

Each favourite store creates one sensor entity:

```
sensor.tgtg_lagkagehuset_norreport
```

**State:** Number of available magic bags (`0` = sold out)

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `store_name` | `str` | Store name |
| `store_branch` | `str` | Branch / location name |
| `store_address` | `str` | Street address |
| `store_latitude` | `float` | Store GPS latitude |
| `store_longitude` | `float` | Store GPS longitude |
| `distance_km` | `float` | Distance from HA home (km) |
| `item_name` | `str` | Magic bag display name |
| `items_available` | `int` | Bags currently available |
| `items_max` | `int` | Maximum bags per slot |
| `pickup_start` | `str` | Pickup window start (ISO 8601) |
| `pickup_end` | `str` | Pickup window end (ISO 8601) |
| `pickup_display` | `str` | Pickup window formatted (e.g. `17/06 19:30 – 20:30`) |
| `price` | `str` | Price excl. taxes |
| `price_including_taxes` | `str` | Price incl. taxes |
| `currency` | `str` | Currency code (e.g. `DKK`) |
| `description` | `str` | Bag description |
| `favorite` | `bool` | Marked as favourite in TGTG |
| `sold_out` | `bool` | `true` if no bags available |
| `rating` | `float` | Store average rating |
| `store_logo` | `str` | URL to store logo image |
| `item_cover_image` | `str` | URL to bag cover image |

### Distance Calculation

The `distance_km` attribute is calculated automatically using the [Haversine formula](https://en.wikipedia.org/wiki/Haversine_formula) between:

- **Your HA home coordinates** — set under *Settings → System → General → Home location*
- **The store's GPS coordinates** — provided by the TGTG API

This attribute is used to sort stores by proximity in the Lovelace dashboard.

---

## 🖥️ Lovelace Dashboard

### Quick start (requires [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) from HACS)

```yaml
type: custom:auto-entities
card:
  type: entities
  title: Too Good To Go – Available
filter:
  include:
    - domain: sensor
      entity_id: "sensor.tgtg_*"
      state: "> 0"
      options:
        secondary_info: last-updated
sort:
  method: attribute
  attribute: distance_km
  numeric: true
show_empty: false
```

### Mushroom card (requires [mushroom-cards](https://github.com/piitaya/lovelace-mushroom))

```yaml
type: custom:mushroom-template-card
entity: sensor.tgtg_YOUR_STORE
primary: "{{ state_attr(entity, 'store_name') }}"
secondary: >
  {% set n = states(entity) | int %}
  {% set d = state_attr(entity, 'distance_km') %}
  {% if n > 0 %}
    🎉 {{ n }} bag{{ 's' if n != 1 }} available
    · {{ state_attr(entity, 'price_including_taxes') }} DKK
    {% if d %}· 📍 {{ d }} km{% endif %}
  {% else %}
    😔 Sold out{% if d %} · 📍 {{ d }} km{% endif %}
  {% endif %}
icon: >
  {{ 'mdi:shopping-outline' if states(entity) | int > 0 else 'mdi:shopping-remove' }}
icon_color: >
  {{ 'green' if states(entity) | int > 0 else 'red' }}
badge_icon: "{{ 'mdi:heart' if state_attr(entity, 'favorite') }}"
badge_color: pink
tap_action:
  action: more-info
```

---

## 🔔 Automation Examples

### Push notification when bags become available

```yaml
alias: "TGTG – Notify when bags available"
trigger:
  - platform: state
    entity_id:
      - sensor.tgtg_lagkagehuset_norreport
      - sensor.tgtg_sushi_tai_vesterbro
    from: "0"
condition:
  - condition: numeric_state
    entity_id: "{{ trigger.entity_id }}"
    above: 0
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "🛍️ Too Good To Go"
      message: >
        {{ state_attr(trigger.entity_id, 'store_name') }} has
        {{ states(trigger.entity_id) }} bag(s) available!
        📍 {{ state_attr(trigger.entity_id, 'distance_km') }} km away
        🕐 Pick up: {{ state_attr(trigger.entity_id, 'pickup_display') }}
      data:
        push:
          sound: default
```

### Notify only for nearby stores

```yaml
alias: "TGTG – Notify nearby stores only"
trigger:
  - platform: state
    entity_id: sensor.tgtg_*
    from: "0"
condition:
  - condition: template
    value_template: >
      {{ state_attr(trigger.entity_id, 'distance_km') | float(99) < 2.0
         and states(trigger.entity_id) | int > 0 }}
action:
  - service: notify.mobile_app_your_phone
    data:
      title: "🛍️ Nearby TGTG bag!"
      message: >
        {{ state_attr(trigger.entity_id, 'store_name') }}
        ({{ state_attr(trigger.entity_id, 'distance_km') }} km) –
        {{ states(trigger.entity_id) }} bag(s) available
        🕐 {{ state_attr(trigger.entity_id, 'pickup_display') }}
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| **No PIN email received** | Check your spam folder. Make sure the email is registered in the TGTG app. Wait 1–2 minutes and try again. |
| **"Incorrect PIN"** | PIN codes expire after a short time — restart the setup flow to request a new one |
| **"Too many login attempts"** | Wait 5–10 minutes before trying again |
| **"Email not registered"** | Sign up via the Too Good To Go app first, then return to HA setup |
| **No sensors created** | Add stores as favourites in the TGTG app — only favourites are fetched |
| **Rate limit / blocked** | Increase the update interval to 10–15 minutes minimum |
| **`distance_km` missing** | Set your home location in *HA Settings → System → General* |
| **Sensors go unavailable** | TGTG may have rotated your tokens — delete and re-add the integration |

### Enable debug logging

Add to `configuration.yaml` to see detailed API responses in the HA log:

```yaml
logger:
  default: warning
  logs:
    custom_components.tgtg: debug
```

---

## 🤝 Contributing

Pull requests and issues are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

Please open an [issue](https://github.com/Steppedrengen/ha-tgtg/issues) before starting large changes.

---

## ⚖️ Legal

This integration uses the **unofficial** Too Good To Go API via the [`tgtg`](https://github.com/ahivert/tgtg-python) library. It is not affiliated with, endorsed by, or supported by Too Good To Go. Use responsibly — set a reasonable polling interval to avoid being rate-limited.

---

## 📄 License

[MIT License](LICENSE) — © 2024 Steppedrengen
