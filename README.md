# LIMODOR AirOdor AD-UV HomeAssistant integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![Community Forum][forum-shield]][forum]

_Integration to control multiple [AirOdor][limodor_airodor] home ventilation fans via the control unit [AirOdor AD-UV][limodor_airodor_ad_uv] from the company LIMODOR/LIMOT._

**STILL WORK IN PROGRESS**

- use serial device from config
- error handling

**This integration will set up the following platforms.**

| Platform | Description     |
| -------- | --------------- |
| `fan`    | LIMODOR AirOdor |

## Installation

1. Add this repository to HACS by clicking the following button
   [![Open this repository in HACS][hacsbadge]][hacs_my]
2. Restart Home Assistant
3. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "LIMODOR AirOdor"

## Configuration is done in the UI

Only the serial device connected to the [AirOdor AD-UV][limodor_airodor_ad_uv] needs to be configured via the UI.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[integration_repo]: https://github.com/jschroeter/HomeAssistant-Limodor-AirOdor
[limodor_airodor]: https://limot.de/de/produkte/?category=24&id=328
[limodor_airodor_ad_uv]: https://limot.de/de/produkte/?category=20&id=368
[commits-shield]: https://img.shields.io/github/commit-activity/y/jschroeter/HomeAssistant-Limodor-AirOdor.svg?style=for-the-badge
[commits]: https://github.com/jschroeter/HomeAssistant-Limodor-AirOdor/commits/main
[hacs_my]: https://my.home-assistant.io/redirect/hacs_repository/?owner=jschroeter&repository=HomeAssistant-Limodor-AirOdor&category=integration
[hacsbadge]: https://my.home-assistant.io/badges/hacs_repository.svg
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/jschroeter/HomeAssistant-Limodor-AirOdor.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Jakob%20Schr%C3%B6ter%20%40jschroeter-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jschroeter/HomeAssistant-Limodor-AirOdor.svg?style=for-the-badge
[releases]: https://github.com/jschroeter/HomeAssistant-Limodor-AirOdor/releases
