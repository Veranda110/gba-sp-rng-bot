# 04. Firmware

Single file, [src/main.cpp](../src/main.cpp). PlatformIO, board `esp32dev`, Arduino framework, stock `espressif32` platform. No external libraries.

Games: **Emerald**, tested on the reference build, see [06-emerald.md](06-emerald.md). **FireRed / LeafGreen**, tested on the reference build, see [07-firered-leafgreen.md](07-firered-leafgreen.md). Each game keeps its own settings profile, so switching games does not lose calibration. To add a game such as Ruby or Sapphire: add a value to `Game`, its name to `GAME_NAMES` and a run function next to `runEmerald()` and `runFrlg()`.

## Architecture

Two FreeRTOS tasks:

| Task | Core | Priority | Job |
|---|---|---|---|
| Arduino `loop()` | 1 | normal | reads serial commands |
| `runTask` | 1 | maximum | executes one attempt: waits for SENSE, times the presses |

`runTask` is created by `arm` or `go` and deletes itself when the attempt ends or is aborted. During the final 2.5 ms before each press it spin-waits on `esp_timer_get_time()`, which gives press timing within tens of microseconds. Between presses it sleeps, so serial still works.

Every press is a 50 ms tap, three frames, long enough for the game's once-per-frame input read.

## Emerald runs

| Command | Sequence |
|---|---|
| `arm` | wait for the SP to power on (t0), tap the menu steps at their fixed times after t0, then tap A at t0 + `calboot` + `adv` frames |
| `go` | tap A now, then tap A again `adv` frames later. Used for the Secret ID timing in a new game |

## FireRed / LeafGreen runs

| Command | Sequence |
|---|---|
| `arm` | wait for the SP to power on (t0). Hands off through the intro. Hold A from t0 + `seed` ms for `hold` ms: that title screen press sets the seed. Then the menu steps, then tap A at the seed press + `caladv` + `adv` frames |

Menu steps that fall before the end of the seed hold are skipped, because any press during the intro changes the seed.

All frame counts are corrected by `ppm` for the clock drift between the Game Boy and the ESP32.

## Configuration

Stored in NVS (flash) under namespace `gbabot`, key `cfg2`, loaded at boot, written on `save`. Settings from the earlier Emerald-only layout are migrated automatically.

| Field | Scope | Default | Meaning |
|---|---|---|---|
| `mode` | | emerald | current game |
| `ppm` | all games | 0 | clock drift correction applied to every frame count. Negative when the Game Boy runs fast |
| `adv` | per game | 1000 | target advance in frames |
| `steps` | per game | none | up to 8 taps at fixed times after power-on, for `arm` runs |
| `calboot` | Emerald | 0 | ms from power-on to the game's first frame, plus centering of the press in its frame |
| `seed` | FRLG | 35000 | ms from power-on to the seed press on the title screen |
| `hold` | FRLG | 3000 | how long the seed press holds A |
| `caladv` | FRLG | 0 | correction of the target press, counted from the seed press |

## Serial command reference

115200 baud, newline terminated, case insensitive.

| Command | Effect |
|---|---|
| `arm` | wait for the SP to power on, then run the sequence. Refuses if the SP is already on |
| `go` | run the `go` sequence immediately |
| `abort` | stop, release all buttons |
| `status` | state, SENSE, time since t0 |
| `mode emerald\|frlg` | select the game; each game keeps its own settings |
| `adv <frames>` | set the target advance |
| `ppm <n>` | set the clock drift correction, shared by all games |
| `calboot <ms>` | Emerald: set the power-on calibration |
| `seed <ms>` | FRLG: set the seed press time after power-on |
| `hold <ms>` | FRLG: set how long the seed press holds A |
| `caladv <ms>` | FRLG: set the target press correction |
| `step <ms> <a\|b\|start>` | add a tap at that many ms after power-on, kept sorted. Steps closer than 1 s to the target are skipped |
| `steps [clear]` | list the taps, or remove them all |
| `test <a\|b\|start> [ms]` | press that button for 300 ms, or for the given time up to 10000 ms, long enough to read a multimeter |
| `selftest` | check a freshly soldered DevKit: every reachable GPIO is tested for a short to GND, a short to 3V3 and bridges to other pins. Run it before resistors and optocouplers go on the board, and not while the board sits in anti-static foam: the foam conducts enough to fake shorts. GPIO 0, 2 and 5 are skipped because many boards pull them up or hang an LED on them |
| `show` | print configuration |
| `save` | write configuration to flash |
| `help` | command list |

## Attempt output

Every attempt prints what actually happened, in microseconds from t0, so misses can be diagnosed:

```
ARMED, waiting for SP power (SENSE). Switch it on.
t0: SP powered on
  STEP 1 A in 10 s
STEP 1 A press at 23000011 us (planned 23000000, error +11)
STEP 2 A press at 25500009 us (planned 25500000, error +9)
target press in 216.4 s
  TARGET in 10 s
TARGET press at 247435012 us (planned 247435000, error +12)
Check the Pokemon's nature and stats.
DONE
```

Errors above about 100 us mean something is starving the run task. That should not happen.

While waiting, the monitor counts down to each press: every 10 s, then every second for the last 10. The countdown stops printing 300 ms before the press, so it never affects the timing.

## Timing details worth knowing

- SENSE is sampled every millisecond while armed. t0 is the first of three consecutive low samples. That leaves up to 1 ms of jitter, which only matters when a press sits on a frame edge: center `calboot` in the frame, see [06-emerald.md](06-emerald.md).
- A press at a fixed time after power-on always lands on the same game frame, because the Game Boy starts the game a fixed time after power-on.
- The GBA frame is 16742.7 us (59.7275 Hz). The ESP32 and Game Boy crystals differ slightly. On the reference build the Game Boy ran about 93 ppm fast, so `ppm -93`.

## Building

```
py -m platformio run                 # compile
py -m platformio run -t upload       # flash
py -m platformio device monitor      # serial monitor, Ctrl+C to exit
```

The monitor holds the serial port, so close it with Ctrl+C before flashing.

## v2 plan: standalone UI

Add the SSD1306 OLED (I2C 21/22) and a rotary encoder. Screens: target advance, calibration, armed/countdown. The run task does not change; the UI replaces the serial parser. Keep serial working for logging.
