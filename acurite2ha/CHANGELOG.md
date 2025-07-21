# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.30]
- Changed all references to skip to avoid conflict with original source.

## [0.3.26]
- Pulling in latest RTL_433 changes

## [0.3.25] 
- Nothing to see here, previous update was good, but some changes upstream happened.
- verbosity of the rtl_433 messages changed, so not everything you are use to seeing at startup in the log are happening.

## [0.3.24] - Borked...Maybe....
ROLLED THIS BACK
- Bump the version to update 433 Library to grab all the new protocols
- Setting rain guages back to total_increasing to fix issue with my rain guages. 

## [0.3.23]
- Updating default Channel at init.

## [0.3.22]
- Fixing wind speed unit of measurement
- Fixing Rain sensor unit of measurement


## [0.3.20b]
- Fixed issue where debug and whitelist_enable are incorrectly marked as being on when they are off.
- When whitelist_enabled is on, any Device ID and Models not in whitelist will be listed in the log. This will 
  only be listed once, until the add-on is restarted. Debug not required.
  * whitelist only prevents Home Assistant Auto Discovery - devices will still show up in MQTT *
- If no instance is found, device will be assigned an instance of 0 to try and fix that 
  add-on crash when no instance is found. 
- Fix bug where whitelist_enabled is sometimes ignored. 
- Switch to an actual logger for log messages. 
- Added device class to sensors
- Removed any "unit of measurement" that was empty to prevent errors after 2023.5 update
- state_class is now defined for each device instead of globally set to measurement to reduce errors after 2023.5 update. 
- auto discovery can now be turned off in the configuration for anyone that doesn't want devices to be auto added to home assistant
- Some bug fixes by @doozers-do
  - Channel now defaults to A instead of 0
  - Channel sensor now defined as a enum device with options as A, B, or C
  
## [0.3.19b]
- Bump to make sure latest 433_rtl is grabbed.
- New Statistic Attributes from @curtismuntz

## [0.3.18b]
- Some major improvements/security enhancements thanks to @HalideGlow
- Updated battery percentage value...thanks @TomWS1

## [0.3.16b]
- Bump to make sure latest 433_rtl is grabbed.

## [0.3.15b]
### Bug fixing
- Typo...I swear

## [0.3.14b]
### Bug fixing
- Removed null device ID from new channel definition

## [0.3.13b]
### Added
- Added Definition for Temp from Thermopro TP12

## [0.3.12b]
### Changed
- Updated Autodiscovery to handle model values that were not in manufacturer-model format. 

## [0.3.11b]
### Added
- Added last_seen enity which should be the last time Home Assistant saw an update from 
  rtl_433.
- Added Freq definition to autodiscovery which reports device frequency
- Added channel definition to autodiscovery which report device channel 
- Added wind_max_km_h definition to autodiscovery

## [0.3.10b]
### Added
- Added consumption definition for gas meters
- Update rtl_433 to version 21.12-63-g2d041b5d

## [0.3.9b]
### Added
- Added port option in the config so now you can use other ports than the default 1883

## [0.3.8b]
### Added
- Added new definition for light_klx value from Brersser 7in1

## [0.3.7b]
### Added
- Added new whitelist option. Thanks to [@pdhruska](https://github.com/pdhruska) for the code.

## [0.3.6b]
### Added
- Added a definition for pressure in inHG 

## [0.3.5b]
### Changed
- More Rain gauge bug fixes. 

## [0.3.4b]
### Changed
- Updated Rain Gauge unit of measurements in device definition.

## [0.3.3b]
### Added
- Units to the config so you can set to metric or customary/imperial  

## [0.3.2b]
### Added
- Brightness defintion to attempt fix for #10. 
- KPa definition to auto discovery. 

## [0.3.1b]
### Changed
- Updated USB Condif to correct usb error. 
- Modified startup config
- Thanks @staniel1881 for the assist!

## [0.3.1]
### Changed
- Added Debug option to print messages to log
- Reverted back to old method of naming devices

## [0.3.0]
### Added
- this change log
### Changed
- Removed the weather device classes from mappings
- Switched Moisture mapping to humidity device class
- Added support for Subtypes in an attempt to fix the issue with not reading all the 5n1 sensors. 


## [0.2.0]
### Changed
- Updated repro url to fix Add-on store links
