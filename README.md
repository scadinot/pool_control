# Pool Pump Manager

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]

_Component developed by using the amazing development template [blueprint][blueprint]._

This custom component for Home Assistant can be used to automatically control
a pool pump that is turned on/off by a switch that Home Assistant can control.

This component is based on the work of [@scadinot](https://github.com/exxamalte/home-assistant-customisations/tree/master/pool-pump).

On top of the original version by @exxamalte, this version can be installed by HACS
and you can use the [blueprint][blueprint] feature to quickly fork this repo and
have a working development environment in a container.

I will adapt it to my needs. At completion this plugin will compute the filtering
schedule taking into account the pool water temperature.

## Minimum requirements

* A switch supported in Home Assistant that can turn on/off power to your pool pump.
