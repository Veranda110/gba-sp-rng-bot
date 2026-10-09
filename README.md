# GBA SP RNG Manip Bot

An ESP32 that presses the buttons of a Game Boy Advance SP with sub-millisecond timing, so RNG manipulation in the Gen 3 Pokemon games no longer depends on human reaction time.

RNG manipulation needs presses that land in a 16.7 ms frame window, often minutes after the console was switched on. Humans hit them with practice and luck. This device hits them every time, and after a miss you correct it with a single number.

**Supported now: Pokemon Emerald and FireRed / LeafGreen**, both tested on the reference build up to chosen shinies: a starter in Emerald; a gift, a static and a wild encounter in LeafGreen. More games are meant to follow.

## How it works in one paragraph

You switch the SP on. The device senses the console powering on through an isolated wire and starts its clock. You skip the intro and get to your save, the device presses the menu buttons that have to happen at fixed times, and then it presses A on exactly the frame that creates your target Pokemon. Emerald's RNG always starts from the same seed and advances once per frame, so that one press decides the Pokemon.

## Status

| Part | State |
|---|---|
| Design and schematic | done, see [docs/03-hardware.md](docs/03-hardware.md) |
| Firmware (serial controlled) | Emerald mode, verified on the Game Boy. Press timing error under 20 us. Only tested features are kept |
| SP wiring | done: GND, 3.3 V, A, B and Start on a 6-pin Dupont tail. The Select via tore off during soldering, Select is not wired. |
| Protoboard with optocouplers | done: A, B and Start presses and power detection verified on the Game Boy |
| Calibration | Emerald done: boot offset, routine and clock drift calibrated, see [docs/06-emerald.md](docs/06-emerald.md) |
| First shiny | **Emerald shiny starter Treecko on 2026-10-07**, Secret ID found with the device's new-game timing |
| Chosen shiny | **Shiny Timid Treecko, Sp. Atk 30, picked in advance** from the computed list and hit after a 17-minute wait |
| FireRed / LeafGreen | **done on an existing LeafGreen save**: seed table matched, Secret ID found through shiny tests, shiny Impish Snorlax (30/30/28/28/30/17) and shiny Timid Vulpix via Sweet Scent, each on the first attempt after one calibration, and shiny Timid Zapdos (29/21/31/28/28/31) after a 26-minute wait. See [docs/07-firered-leafgreen.md](docs/07-firered-leafgreen.md) |
| OLED + encoder UI (v2) | planned |

## Repository layout

```
.
├── README.md                    this file
├── CLAUDE.md                    handoff notes for AI-assisted work on this repo
├── platformio.ini               PlatformIO project (board: esp32dev, framework: arduino)
├── src/main.cpp                 firmware
├── tools/                       drawing generators for docs/img, FRLG seed and target search scripts
└── docs/
    ├── img/                     protoboard layout and soldering drawings
    ├── 01-background.md         how FireRed / LeafGreen seed their RNG, with sources
    ├── 02-system-design.md      the original FireRed / LeafGreen design: states, timeline, calibration
    ├── 03-hardware.md           schematic, bill of materials, pin map, SP solder points
    ├── 04-firmware.md           firmware architecture and serial command reference
    ├── 05-build-and-calibration.md   step-by-step build, test and calibration procedure
    ├── 06-emerald.md            Pokemon Emerald: seed 0, one timed press, procedure
    └── 07-firered-leafgreen.md  FireRed / LeafGreen: seed tables, per-spot calibration, Secret ID, Sweet Scent
```

## Quick start

1. Build and flash: `py -m platformio run -t upload` (or the PlatformIO checkmark in VS Code)
2. Open the serial monitor at 115200 baud: `py -m platformio device monitor`
3. Type `help`

Full procedure in [docs/05-build-and-calibration.md](docs/05-build-and-calibration.md).

## Safety

The SP side and the ESP32 side are galvanically isolated by optocouplers. There is no shared ground and no path for 5 V to reach the SP's 3.3 V logic. Still: you are soldering thin wires to 20-year-old test pads. Read the hardware doc before opening the console.

## License

Code (`src/`, `tools/`, `platformio.ini`): MIT, see [LICENSE](LICENSE). Documentation (`docs/`, this README): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The Ten Lines seed tables are not included; download them from the Ten Lines project.
