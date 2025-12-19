<p align="center">
  <img src="images/d878_icon.png" />
</p>

# anytone-878uvii-cps-py
An open-source, cross-platform Customer Programming Software (CPS) for the AnyTone 878UVII series radios, written in Python.

This project aims to provide a modern, scriptable, and community-maintained alternative to the stock AnyTone CPS, while keeping the workflow familiar for existing users.

Currently, this project is in Alpha stage and is a work is progress. Not all functionality has been added but will be updated as soon as feature become available. Only FW version 4.00 is supported. Once the CPS is in Beta, I will expand to include future FW versions.

> **Note**  
> This project is not affiliated with, endorsed by, or supported by AnyTone / Qixiang. All trademarks are the property of their respective owners.

---

## Working Serial Features
### Read
- Auto Repeater Offset Frequencies
- Alert Settings
- Channels
- Digital Contacts
- FM Channels
- GPS Roaming
- Master ID
- Optional Settings
- Prefabricated SMS
- Radio IDs
- Roaming Channels
- Roaming Zones
- Scan Lists
- TalkGroups
- Zones

### Write
- Channels
- FM Channels
- GPS Roaming
- Radio IDs
- Scan Lists
- TalkGroups
- Zones

## Serial Features To Implement
- 2Tone Encode/Decode
- 5Tone Encode/Decode
- AES Encryption Code
- Analog Address Book
- APRS
- ARC4 Encryption Code
- DTMF Encode/Decode
- HotKey HotKey
- HotKey Quick Call
- HotKey State

## Working Import Features
- Auto Repeater Offset Frequencies
- Channels
- Digital Contacts
- FM Channels
- Prefabricated SMS
- Radio IDs
- Roaming Channels
- Roaming Zones
- Scan Lists
- TalkGroups
- Zones

## Import Features To Implement
- 2Tone Encode
- 5Tone Encode
- AES Encryption Code
- Alert Tone
- Analog Address Book
- APRS
- ARC4 Encryption Code
- DTMF Encode
- GPS Roaming
- HotKey HotKey
- HotKey Quick Call
- HotKey State
- Optional Settings

## Working Export Features
- Nothing

## Planned Updates
- Remaing OEM CPS features
- Repeater Book Import
- Expert Options (AT_OPTIONS)
- Expansion to other radio models (D878UV, D168UV)

## Supported Devices
- D878UVII

## Why?
The stock CPS for the 878UVII:

- Is Windows-only and does not run using WINE
- Is not scriptable or easy to automate
- Makes bulk edits and codeplug management harder than it needs to be

# Reporting Bugs & Requesting Features

- **Bugs**: Please include:
    - OS and version
    - Python version
    - Radio model and firmware version
    - Exact command you ran
    - Error output / stack trace
- **Feature requests**: Explain:
    - What problem you’re trying to solve
    - How you currently work around it (if at all)
    - Any reference code / examples that might help

# Installation
This project uses some additional libraries. To install them, run this line:

    pip install pyside6, pyaudio, pyserial, pandas, qt-material, darkdetect

This can also be compiles to a single executable using pyinstaller and the included spec file.

For full download and build,

    git clone https://github.com/xbenkozx/anytone-cps-py.git
    cd anytone-878uvii-cps-py
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    pyinstaller D878UVII_4.00_CPS.spec

The compiled executable can be found in the *dist* folder

# Donations
As this project take a quite a bit of time as well as costs to purchase new radios to be able to support them, donations are appreciated but not required.
You can send money via paypal to k7dmg@protonmail.com.

# Troubleshooting

If you are having issues where the  COM port cannot be opened, you may need to add yourself to the dialout user group.
    sudo usermod -a -G dialout <username>
After running the command, logout then back in and the serial ports should now be accessible.

# License
anytone-878uvii-cps-py - A multi-platform GUI for Anytone D878UVII Radios.

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.