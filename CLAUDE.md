# GBA SP RNG manip bot: handoff notes

ESP32 presses Game Boy Advance SP buttons with sub-millisecond timing for Gen 3 Pokemon RNG manipulation on retail hardware. Owner: Raymond. The documentation in `docs/` is written to be published, keep it accurate and sourced.

## Read first

- [README.md](README.md): overview, status table, repo layout
- [docs/01-background.md](docs/01-background.md), [docs/02-system-design.md](docs/02-system-design.md): the original FireRed/LeafGreen background and design (not in the current firmware)
- [docs/03-hardware.md](docs/03-hardware.md): schematic, BOM, pin map, SP test points, connector, protoboard layout
- [docs/04-firmware.md](docs/04-firmware.md): architecture and serial commands
- [docs/05-build-and-calibration.md](docs/05-build-and-calibration.md): build and bench test, troubleshooting
- [docs/06-emerald.md](docs/06-emerald.md): Emerald procedure and the reference run, with every finding from the decompilation
- [docs/07-firered-leafgreen.md](docs/07-firered-leafgreen.md): FRLG procedure (Ten Lines seed tables, per-spot offsets, Secret ID from shiny tests, Sweet Scent) and the LeafGreen reference run

## Settled decisions (do not reopen without new evidence)

- t0 = SP 3.3 V rail detected through an optocoupler (SENSE).
- Optocouplers (PC817) on every line, no shared ground between ESP32 and SP.
- The SENSE 330 ohm resistor sits in the SP's 3.3 V wire before the plug, so no fault at the plug, in the cable or on the protoboard can load the SP's rail. On the reference build it goes in the tail, just outside the notch.
- The SP connects through a 6-pin Dupont (2.54 mm) connector on a short tail, female housing on the SP side. Order: GND, 3.3 V, A, B, Start, Select (empty). Unkeyed, but a reversed plug is harmless.
- Firmware keeps only features tested on the reference build (cleanup 2026-10-07). Game selection stays, so Ruby, Sapphire and FireRed/LeafGreen can be added as modes later. Removed: the FRLG seed-press logic, the BOOT button, Select output, `hit`, `caladv`, `preb`, `namef`, `tap`/`hold`. The pre-cleanup firmware is not kept in the repo.
- 2026-10-07: FRLG mode re-added (`mode frlg`: seed hold at `seed` ms after power-on for `hold` ms, menu steps after the hold, target at seed press + `caladv` + `adv` frames), tested on Raymond's existing LeafGreen save. Settings are per-game profiles (NVS key `cfg2`), `ppm` shared; the old Emerald-only blob migrates automatically.
- Trainer ID manipulation via frame-exact name screen presses does not work: the Trainer ID is Timer1 at 16.78 MHz and its start and read move by thousands of cycles between runs. Documented in doc 06.
- Serial controlled. OLED + encoder is v2; the run task stays the same.

## Reference unit facts

- Select is dead: its via tore off during soldering, and a jumper repair kept shorting to ground. No soft reset, no Startup Select seeds.
- Speaker removed for cable clearance, so no sound. The cartridge battery is dead, so Emerald shows a battery message after the title screen.
- Two-board build: ESP32 board plus optocoupler board. ESP32 is an ELEGOO USB-C DevKit (CP2102, ESP32-D0WD-V3); its GPIO 5 is pulled up on the board, so the self-test skips it.
- Charger plugged in with the tail connected caused random button presses with the original, swollen battery. With the replacement battery charging looked fine on 2026-10-07 (one observation). Still run attempts on battery.

## Pin map

A 33 (moved from 25 after its pad was damaged), B 26, Start 27, SENSE 32 (input, pull-up, active low). Select 14 reserved, unused. OLED 21/22 and encoder 13/4/23 reserved for v2.

## Build

PlatformIO is installed as a Python module only: `py -m platformio run`, `-t upload`, `device monitor`. No `pio` on PATH. Board esp32dev, stock espressif32 platform, Arduino core 3.1.3 at time of writing. The ESP32 shows up as COM3 (CP210x). The monitor holds the port, so Ctrl+C before flashing. `platformio.ini` enables local echo and send-on-enter.

Settings live in NVS namespace `gbabot`. The cleanup changed the layout, so after flashing it the settings start at defaults and have to be entered again.

## Emerald state (2026-10-07)

- Save in front of Birch's bag: TID 3387, SID 29177 (step 1000 confirmed by a shiny). The shiny Hardy Treecko at advance 14507 was not saved; Raymond chose to go for a better one.
- Attempt at 61682 with `ppm -93`: hit 61681 (Adamant), one frame early, so the drift is smaller than 93 ppm. All hits so far fit drift of 67 to 86 ppm with the press phase at 3198 near 7.9 ms into the frame; best estimate 76 ppm.
- Calibration for this unit: `ppm -76`, `calboot 4517` (keeps short targets centered too), `step 23000 a` (CONTINUE), `step 25500 a` (bag). Routine: Start right after power-on, A on the title, A on the battery message, stop on the main menu; device presses CONTINUE and the bag; Raymond picks Treecko and stops on YES.
- DONE 2026-10-07: shiny Timid Treecko at advance 61682 (IVs 5/18/30/30/19/22) on the second 17-minute attempt with `ppm -76`, `calboot 4517`. This confirms the drift estimate.
- Target was: advance 61682, shiny Timid Treecko, IVs 5/18/30/30/19/22, about 17 minutes. Alternatives: 47696 Mild 29/31/10/17/24/30 (13 min). `ppm` was measured from shorter targets, so expect one or two misses on a 17-minute target; correct ppm or calboot from the hit.
- To find the hit advance: method 1 from seed 0, Gen 3 LCRNG `s = s * 0x41C64E6D + 0x6073`, PID low then high, then IV words, from consecutive outputs (upper 16 bits). Treecko base stats 40/45/35/65/55/70, level 5.

## LeafGreen state (2026-10-07)

Full procedure and findings in doc 07; this is the save-specific part.

- Save: English LeafGreen, Stereo + Button mode L=A, title press with A, so Ten Lines table `stereo_a_a` (lg_eng.bin). TID 37033, **SID 20230** (name screen press at advance 1151, found by shiny Abra tests). TSV 7157.
- Time reference: frame 2524 (seed 0x99DE) = `seed 42000`. Press time for any frame: 42000 + (frame - 2524) * 16.7427 * (1 - 76e-6) ms, `ppm -76`.
- Offsets: prize room -87 (0x99DE, 0xE1D5) / -85 (0x16E4), Route 16 Snorlax -99 (0xE1D5), Route 8 Sweet Scent +159 (0x10FB) / +160 (0xE1D5). Step routines per spot are in doc 07.
- Caught and saved: shiny Hardy Abra (IVs 26/17/27/27/18/31), shiny Impish Snorlax from Route 16 (30/30/28/28/30/17, frame 2563, advance 30607), shiny Timid Vulpix from Route 8 (30/30/3/31/29/28, frame 3427, advance 6594).
- Route 12 Snorlax still asleep, same script as Route 16; best alternative from the table search: frame 3578 (`seed 59646`, seed 0x49EC) advance 58423 Brave 31/30/27/19/30/16. Needs its own calibration catch.
- Party has a Bellsprout that knows Sweet Scent.
- Zapdos (Power Plant, level 50): script is `lock`, `faceplayer`, `setwildbattle` right away, so the target is the overworld A that talks to Zapdos; all Power Plant objects face down (no walkers). Target: frame 4416, `seed 73675`, seed 0xD088, advance 92135 (25.7 min), shiny Timid 164/94/105/144/109/132 (IVs 29/21/31/28/28/31). Neighbours 92134 Serious 152/109/101/140/110/119, 92136 Modest 165/98/104/147/102/113. Steps `78000 a` (CONTINUE), `81000 b` (quest log). Calibration catch with the Master Ball (comes back on reset), adv 3000: Adamant 162/107/94/122/99/111 = advance 2905 on 0xD088, offset -95. Shiny attempt `adv 92230` hit advance 92285 (Impish 163/95/105/126/107/119), 150 late: ambient cries. pokefirered field_tasks.c `Task_RunTimeBasedEvents` runs `UpdateAmbientCry` (overworld.c) whenever field controls are unlocked and no quest log plays: every (Random() % 1200) + 1200 frames a cry draws pan and volume (2 calls) plus the next delay (1 call), about 150 calls in 26 min. Text boxes and the Start menu (`LockPlayerFieldControls`) pause it. New routine: `90000 start` (menu), B close 1.5 s before the target, target A. Needs a new calibration with that routine; doc 07 needs this finding. Calibration with steps `78000 a`, `81000 b`, `90000 start`, `122400 b`, adv 3000: Impish 156/10x/105/118/102/118 (reported Atk 106, advance 2902 gives 108, the other five exact) = advance 2902, offset -98. Shiny attempt: `adv 92233`, close step `1616288 b` (1499 ms before the target, same as calibration). Result: Modest 165/98/104/147/102/113 = advance 92136, one frame late. Cry fix confirmed (miss went from +150 to +1); the remaining frame is drift or press phase over 25.8 min. `adv 92232`, close step `1616271 b`: first run shiny (sparkle) but Raymond knocked it out (not saved); second run Serious = advance 92134. So with adv 92232 the press sits on the 92134/92135 frame edge, and adv 92233 gave 92136. `caladv 8` (half a frame later), close step `1616279 b`: DONE 2026-10-08, shiny Timid Zapdos caught and saved (Master Ball was the plan). Doc 07 updated with ambient cries and the Zapdos routine. If the Master Ball is used up, Articuno and Moltres calibration catches need Ultra Balls (catch rate 3).
- Perfect-IV search over all 2403 `stereo_a_a` seeds, method 1 (gifts and statics), advances up to 430000 (2 h): one 6x31, frame 2870 (`seed 47793`), seed 0x9E2E, advance 170537 (48 min), Modest, not shiny. No shiny 6x31; the only shiny with every IV >= 27 is frame 3902 (`seed 65070`), seed 0xE759, advance 47515 (13 min), Naive 29/29/31/27/27/31. Shiny 6x31 has odds of about 1 in 8.8 trillion per advance.
- Paste issue: the first line of a pasted block sometimes does not reach the device. Start blocks with `show`, check `show` before `arm`.
- Scripts in `tools/`: `tl_parse.py`, `frlg_find.py`, `frlg_wild.py` (TID SID table key slots range [natures]), `frlg_sid.py`. The Ten Lines table itself is not in the repo; download lg_eng.bin from lincoln-lm.github.io/ten-lines/generated/.

## Next session

- 2026-10-09: project paused. Raymond plays LeafGreen and Emerald through, then wants to move on to the next generation; he also has a ribbon challenge running. His ordered connectors arrived; he may swap the 6-pin Dupont tail for them so the Game Boy plugs in more easily. Keep the settled wiring rules (330 ohm on the SP side, isolation) and rerun `selftest` plus the SENSE check after rewiring.
- LeafGreen 6th team slot (Raymond prefers no legendaries; Zapdos is boxed): Exeggutor via Sweet Scent in Three Island's Berry Forest (Exeggcute 5%, after Blaine), same routine as the Route 8 Vulpix. Scoring script was scratchpad research/team6.py (team weak to Ground x3, Water x2; Grass types resist both). Lapras gift already taken.
- Raymond asked about other targets: Eevee (Celadon Mansion roof), Hitmonlee/Hitmonchan, Lapras (Silph Co.), Zapdos, Articuno, later Moltres and Mewtwo. Gifts calibrate for free; statics need one catch. Game Corner prizes need coins he does not have.
- 2026-10-07: the SP's original battery was found swollen and replaced by a spare.
- Sapphire: Raymond owns it too. Ruby/Sapphire use a fixed seed only with a dead cartridge battery (seed 0x5A0); with a live battery the seed comes from the real-time clock. Check for the dry-battery message at boot. SID likely unknown on an existing save as well; the doc 07 shiny-test method applies once a seed is known.

## Open items

- SP test points: confirm with Raymond's photo and add it to doc 03.
- Static and wild Emerald encounters are documented from the guides but not tested.
- 2026-10-09: published as a public GitHub repo (Veranda110/gba-sp-rng-bot). License: MIT for code, CC BY 4.0 for docs (LICENSE).
- Keep the README status table current.

## Working style

Answer first, numbered steps, concrete time estimates, one next step at the end. No em dashes. Code, comments and docs in English; Raymond chats in Dutch or English, follow his lead per message. Verify game-mechanics claims against sources before putting them in docs.
