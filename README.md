# LIMODOR AirOdor AD-UV HomeAssistant integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]

[![Community Forum][forum-shield]][forum]
[![Open this repository in HACS][hacsbadge]][hacs_my]

_Integration to integrate with [limodor_airodor][limodor_airodor]._

**This integration will set up the following platforms.**

Platform | Description
-- | --
`binary_sensor` | Show something `True` or `False`.
`sensor` | Show info from blueprint API.
`switch` | Switch something `True` or `False`.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `limodor_airodor`.
1. Download _all_ the files from the `custom_components/limodor_airodor/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "LIMODOR AirOdor"

## Configuration is done in the UI

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[limodor_airodor]: https://github.com/jschroeter/HomeAssistant-Limodor-AirOdor
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
