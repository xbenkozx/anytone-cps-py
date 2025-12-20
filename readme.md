<p align="center">
  <img src="images/d878_icon.png" />
</p>

# anytone-878uvii-cps-py
An open-source, cross-platform Customer Programming Software (CPS) for the AnyTone 878UVII series radios, written in Python.

This project aims to provide a modern, scriptable, and community-maintained alternative to the stock AnyTone CPS, while keeping the workflow familiar for existing users.

Currently, this project is in Alpha stage and is a work is progress. Make sure you have a backup of your codeplug in the event that you need to factory reset your radio. Not all functionality has been added but will be updated as soon as features become available. Only FW version 4.00 is supported. Once the CPS is in Beta, I will expand to include future FW versions.

> **Note**  
> This project is not affiliated with, endorsed by, or supported by AnyTone / Qixiang. All trademarks are the property of their respective owners.

---

## Progress

![53%](https://progress-bar.xyz/53?title=UI)
![57%](https://progress-bar.xyz/57?title=Serial)
![19%](https://progress-bar.xyz/19?title=Import/Export)


## Supported Devices
- D878UVII

## Why?
The stock CPS for the 878UVII:

- Is Windows-only and does not run using WINE
- Is not scriptable or easy to automate
- Makes bulk edits and codeplug management harder than it needs to be

## Planned Updates
- Remaing OEM CPS features
- Repeater Book Import
- Expert Options (AT_OPTIONS)
- Expansion to other radio models (D878UV, D168UV)

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

---

# Feature Set
## Serial Data
These are not fully tested.
| Data | Read/Write |
| - | :---: |
| Boot Image | R/W |
| BK Image 1 | R/W |
| BK Image 2 | R/W |
| 2Tone Encode/Decode | |
| 5Tone Encode/Decode | |
| AES Encryption Code | |
| Analog Address Book | |
| APRS | |
| ARC4 Encryption Code | |
| Auto Repeater Offset Frequencies | R/W |
| Alarm Settings | R/W |
| Channels | R/W |
| Digital Contacts | R |
| DTMF Encode/Decode | |
| Local Information/Expert Options(AT_OPTIONS) | R |
| FM Channels | R/W |
| GPS Roaming | R/W |
| HotKey HotKey | |
| HotKey Quick Call | |
| HotKey State | |
| Local Information | |
| Master ID | R |
| Optional Settings | R/W |
| Prefabricated SMS | R |
| Radio IDs | R/W |
| Roaming Channels | R/W |
| Roaming Zones | R/W |
| Scan Lists | R/W |
| TalkGroups | R/W |
| Zones | R/W |

## CSV Import/Export
| Data | Import/Export |
| - | :---: |
| 2Tone Encode | |
| 5Tone Encode | |
| AES Encryption Code | |
| Alert Tone | |
| Analog Address Book | |
| APRS | |
| ARC4 Encryption Code | |
| Auto Repeater Offset Frequencies | I |
| Channels | I |
| Digital Contacts | I |
| DTMF Encode | |
| FM Channels | I |
| GPS Roaming | |
| HotKey HotKey | |
| HotKey Quick Call | |
| HotKey State | |
| Optional Settings | |
| Prefabricated SMS | I |
| Radio IDs | I |
| Roaming Channels | I |
| Roaming Zones | I |
| Scan Lists | I |
| TalkGroups | I |
| Zones | I |

---

# Installation
This project uses some additional libraries. To install them, run this line:

    pip install pyside6, pyaudio, pyserial, pandas, qt-material, darkdetect, pillow

This can also be compiles to a single executable using pyinstaller and the included spec file.

For full download and build,

    git clone https://github.com/xbenkozx/anytone-cps-py.git
    cd anytone-cps-py
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    pyinstaller anytone-cps.spec

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
