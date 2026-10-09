# 07. Pokemon FireRed and LeafGreen

FireRed and LeafGreen need two timed presses: one on the title screen that picks the seed, and one that creates the Pokemon. The device does both, plus every menu press in between, so the person only navigates menus where nothing moves. Everything below was done on the reference build with an English LeafGreen and an existing save.

## How FRLG's RNG behaves

- **The seed comes from the title screen press.** The game reads a hardware timer (Timer1) when A is pressed on the title screen and uses its 16-bit value as the seed. Every frame you press later gives a different seed, and neighbouring frames do not differ by a fixed step: on the reference build a seed predicted that way was wrong on its first test. The likely reason is that the work done before the timer read, such as the sound engine's, varies from frame to frame. A formula does not predict the seed for a frame. A table does.
- **The seed table depends on Sound (Mono/Stereo), Button mode (Help/LR/L=A) and the title button.** Ten Lines ships precomputed tables for each combination: `lg_eng.bin` holds 14 tables of about 2,430 frames each, covering title presses from 34 to 75 seconds after power-on. With the right table, picking a seed is picking a press time.
- **The RNG advances once per frame** from the VBlank interrupt, the same as Emerald.
- **NPCs that move call the RNG**, and how many calls they make depends on the seed, because they draw their delays and directions from it. Script text boxes (`lock`) and the Start menu freeze them.
- **Ambient cries call the RNG.** On maps with wild Pokemon, the overworld plays a random cry every 1200 to 2400 frames (20 to 40 s) while the player has control, and each cry draws three numbers: pan, volume and the next delay. A text box or the Start menu pauses this, because it locks the player's controls. So any long wait belongs in a text box or the Start menu, never in the free overworld.
- **The Trainer ID is the seed of a new game.** Leaving the name screen re-seeds the RNG with the Trainer ID, and the game draws the Secret ID a fixed delay later. That makes the Secret ID of an existing save recoverable, see below.

## What you need

- A FireRed or LeafGreen cartridge and a save. Keep Sound and Button mode unchanged once calibrated; changing them switches to a different seed table.
- The Ten Lines seed tables (`https://lincoln-lm.github.io/ten-lines/generated/lg_eng.bin`, `fr_eng.bin` for FireRed) and a searcher: Ten Lines itself, PokeFinder, or your own script. The Gen 3 RNG is `state = state * 0x41C64E6D + 0x6073`, each call returns the upper 16 bits.
- The firmware in `mode frlg`, see [04-firmware.md](04-firmware.md).
- Optional, the scripts used for the reference run, in `tools/`: `tl_parse.py` (reads a Ten Lines table), `frlg_find.py` (seed and advance for a gift or static from its nature and stats), `frlg_wild.py` (shiny Sweet Scent targets over a whole table), `frlg_sid.py` (Secret ID candidates from a Trainer ID). Python 3 with numpy.

## Procedure with the device

### 1. Find your table and your time offset (one gift Pokemon)

1. Save in front of a gift you can take repeatedly without saving, for example the Game Corner prize clerk.
2. Pick a title press time in the table range, for example `seed 42000`, and run the prize routine below with any `adv`.
3. Read the Pokemon's nature and stats and search all 65536 seeds for it near the expected advance. Look the matching seed up in the tables; on the reference build it appeared in exactly one table, at one frame. That tells you your Sound, Button mode and title button, and links the device's milliseconds to the table's frames.
4. Confirm with a second press time about a second away: its Pokemon must match the seed the table lists for that frame.

From then on, the press time for any table frame is:

```
seed_ms = ref_ms + (frame - ref_frame) * 16.7427 * (1 + ppm / 1e6)
```

On the reference build `ref_ms = 42000` matched frame 2524 of `stereo_a_a` (Stereo, L=A, A on the title). Ten Lines' own conversion for a GBA, `frame * 16.7427 - 260` ms, gives 41998.6 ms for that frame, so the SP matched it within 2 ms.

### 2. Calibrate each spot once

Every place you hunt gets its own offset: the difference between the device's `adv` (frames since the seed press) and the advance at which the game actually creates the Pokemon. It bundles everything the device does not count: loading, the frames between the target press and the generation, and NPC calls. Measure it rather than derive it:

1. Save at the spot, set the routine with `step`, run one attempt with `adv 3000`.
2. Catch or receive the Pokemon, read its nature and stats, find the advance it came from on your seed.
3. offset = found advance - 3000.

Calibrate on the seed you will hunt with if any NPC on screen moves on its own: their RNG calls differ per seed. Where nothing moves, the offset carries over to other seeds.

### 3. Pick a target

Search every seed of your table for the Pokemon you want: shiny, nature, IVs, and for wild encounters the species. Then set `seed` to that frame's press time and `adv` to target advance minus offset. Shift the menu steps by the same amount as the seed press when it moves by more than a second or so.

### 4. Attempt

`arm`, power on, hands off until the device has done its menu presses, navigate where the routine says, wait. If the result misses, its stats tell you which advance it was.

## Spots used on the reference build

Times are ms after power-on, for a seed press around 42 to 43 seconds. The quest log ("Previously on your quest") plays after CONTINUE; B ends it, A only skips to its next scene.

### Celadon Game Corner prize room (Abra)

Save facing the Pokemon prize clerk.

| Step | Press | Does |
|---|---|---|
| `47000 a` | A | CONTINUE |
| `50000 b` | B | end the quest log |
| `58000 a` | A | talk to the clerk |
| `61000 a` | A | close "We exchange your COINS for prizes." |
| `64000 a` | A | pick ABRA, the menu cursor starts on it |
| target | A | YES on "So, you want the ABRA?" |

The Pokemon is created right after YES (`givemon`). A wandering man and an old man who looks around move until the clerk talks, so the offset depends on the seed: -87 on two seeds, -85 on a third. LeafGreen's Abra is level 7, FireRed's level 9.

### Route 16 Snorlax (static)

Save facing Snorlax. The script freezes NPCs with `lock`, and the bikers on this route are too far away to be loaded.

| Step | Press | Does |
|---|---|---|
| `47000 a` | A | CONTINUE |
| `50000 b` | B | end the quest log |
| `58000 a` | A | talk to Snorlax |
| `61000 a` | A | YES on "Want to use the POKé FLUTE?" |
| `70000 a` | A | first page of "SNORLAX woke up!" |
| target | A | second page, "It attacked in a grumpy rage!" |

`setwildbattle` follows the second page directly. Offset -99. The Route 12 Snorlax runs the same script.

### Route 8 tall grass with Sweet Scent (wild)

Save standing in tall grass with no NPC on screen; two NPCs at the top of Route 8 look around at random. You need a party Pokemon that knows Sweet Scent. In LeafGreen, Bellsprout learns it at level 30 and Weepinbell at 33; wild Bellsprout are past their evolution level, so press B on every evolution until it has learned the move. In FireRed, Oddish learns it at level 7.

| Step | Press | Does |
|---|---|---|
| `61500 a` | A | CONTINUE (seed press at 57.1 s here) |
| `64500 b` | B | end the quest log |
| `72500 start` | Start | open the menu, which freezes NPCs |
| | person | POKEMON, the Sweet Scent user, cursor on SWEET SCENT, stop |
| target | A | SWEET SCENT |

The encounter is generated 64 frames after the screen fades. Offset +159 and +160 on two seeds.

### Power Plant Zapdos (static, waiting in the Start menu)

Save facing Zapdos. The script runs `lock`, `faceplayer` and `setwildbattle` straight away, so the Pokemon is created by the A that talks to Zapdos in the overworld, before "Gyaoo!" appears. Nothing in the Power Plant moves, but the map has wild Pokemon, so the wait happens in the Start menu.

| Step | Press | Does |
|---|---|---|
| `78000 a` | A | CONTINUE (seed press at 73.7 s here) |
| `81000 b` | B | end the quest log |
| `90000 start` | Start | open the menu: pauses cries, freezes NPCs |
| target - 1500 ms | B | close the menu |
| target | A | talk to Zapdos |

The close step moves with the target; keep it at the same distance before the target in calibration and attempt. Offset -98 with this routine. Catch rate 3: use the Master Ball for the calibration catch and reset without saving, it comes back.

## Wild encounter generation

From `wild_encounter.c` and `pokemon.c`, starting at the generation advance:

1. slot: `Random() % 100` against the area's slot table
2. level: one `Random()` call, even when the slot has a single level
3. nature: `Random() % 25`
4. personality value: pairs of calls (low half, high half) until its nature matches
5. IVs: two calls

PokeFinder calls this method H. Its variants H-2 and H-4 have one extra call before the first or second IV word. On the reference build a calibration Meowth needed 49 personality tries and came out as H-4. The likely cause is the VBlank interrupt's own `Random()` call landing inside the generation, because the generation starts about 100 calls before VBlank. Targets that need few personality tries finish before VBlank and come out as plain H-1. The shiny Vulpix needed 5.

## Finding the Secret ID of an existing save

The Secret ID is not shown in game, but a shiny result reveals it.

1. Seed = your Trainer ID. The Secret ID is the RNG output a fixed number of advances later, set by when you pressed A on "Your very own POKéMON legend is about to unfold!". With the retailrng guide's timer that is advance 1150 for English, 1106 for French and 1095 for Japanese, so a save started with the guide's timer has its Secret ID within a few advances of that.
2. List the candidates: the upper 16 bits of the state after N + 1 steps from the Trainer ID, for N around 1150.
3. For each candidate, find a gift advance on your calibrated seed where that Secret ID makes the Pokemon shiny, and run it. Test the most likely and the quickest first.
4. A predicted Pokemon that is not shiny rules out that candidate; a shiny one confirms it.

On the reference save the fourth test was shiny: the name screen press had been one advance late, at 1151.

## Reference run

LeafGreen, 2026-10-07 and 2026-10-08, one existing save, `ppm -76` from the Emerald calibration:

| Item | Result |
|---|---|
| Hand-timed overworld | three Abras with the person walking to the clerk fit no common offset. With the device doing every overworld press, the same `adv` gave the identical Abra twice |
| Seed table | seed 0x99DE at 42000 ms appeared only in `stereo_a_a`, frame 2524. 42954 ms gave frame 2581's seed 0x16E4, 42653 ms frame 2563's seed 0xE1D5, as listed |
| Secret ID | four shiny tests, each hit its predicted advance exactly, targets up to 5.6 minutes. The fourth was shiny |
| Snorlax | best shiny in the whole table: Impish, IVs 30/30/28/28/30/17, frame 2563, advance 30607, an 8.6-minute wait. One calibration catch, then hit on the first attempt |
| Sweet Scent | shiny Timid Vulpix, level 17, IVs 30/30/3/31/29/28, frame 3427, advance 6594. One calibration, then hit on the first attempt |
| Zapdos | shiny Timid, IVs 29/21/31/28/28/31, frame 4416, advance 92135, a 25.7-minute wait. Waiting in the overworld missed by 150 (ambient cries); waiting in the Start menu then missed by one frame, `adv` one lower sat on the frame edge (hit once, one early once), and `caladv 8` centred it and hit |

What went wrong along the way:

- **NPCs in the prize room.** Same cause as Route 101 in Emerald, fixed the same way: the device presses everything in the overworld.
- **A dropped first line.** Twice, the first line of a block pasted into the serial monitor did not reach the device (`adv 30706`, `seed 57118`), and the attempt ran with the old value. Start pasted blocks with a throwaway `show`, and check `show` before `arm`.
- **A wrong seed model.** A guess that each later frame adds a fixed amount to the seed failed on its first test. The measured table did not.
- **Ambient cries.** The first 26-minute Zapdos wait in the open overworld landed 150 advances late: 50 cries of three calls each. A simulation of the cry timer on the real seed predicts 45 to 55 cries for that wait. Waiting in the Start menu brought the miss down to one frame. Every earlier long wait had been in a text box or menu.
- **The frame edge on a 26-minute target.** Clock drift moved the press by most of a frame over the long wait. Shifting by a whole frame put it on the edge, where it hit once and missed once; half a frame more with `caladv 8` centred it. On long targets expect one correction like this, and read the neighbours' natures to see which way to go.

## Device notes

- Never press anything during the intro or before the seed press: it changes the seed.
- Every attempt is a power cycle with `arm`. Run on battery, see [05-build-and-calibration.md](05-build-and-calibration.md).
- Select is not wired on the reference unit, so key items registered to Select are unavailable. The Town Map is opened from the bag.
- Catching a level 30 Snorlax: catch rate 25. With red HP and sleep, an Ultra Ball catches about 39% of the time, a Great Ball about 29%. A Master Ball used for a calibration catch comes back after the reset without saving.

## Sources

- [pokefirered decompilation](https://github.com/pret/pokefirered): `src/main.c` (`SeedRngAndSetTrainerId`, `Random()` in `VBlankIntr`), `src/new_game.c` (Secret ID), `src/naming_screen.c`, `src/wild_encounter.c` (slot, level, nature, Sweet Scent encounter), `src/pokemon.c` (`CreateMonWithNature`), `src/fldeff_sweetscent.c` (64-frame wait), `src/start_menu.c` (`FreezeObjectEvents`, `LockPlayerFieldControls`), `src/field_tasks.c` (`Task_RunTimeBasedEvents`), `src/overworld.c` (`UpdateAmbientCry`, `PlayAmbientCry`), `src/scrcmd.c` (`lock`), `src/event_object_movement.c` (look-around and wander call `Random()`), `src/quest_log.c` (A and B during playback), `data/maps/CeladonCity_GameCorner_PrizeRoom`, `Route16`, `Route12`, `Route8`, `PowerPlant`, `src/data/wild_encounters.json`, `src/data/pokemon/level_up_learnsets.h`
- [Ten Lines](https://github.com/Lincoln-LM/ten-lines) by Lincoln-LM: precomputed FRLG seed tables and their format (`src/wasm/src/initial_seed.hpp`), console timing offsets (`src/tenLines/index.ts`)
- [PokeFinder](https://github.com/Admiral-Fish/PokeFinder): `Core/Gen3/Generators/WildGenerator3.cpp` (method H and its H-2 and H-4 variants)
- retailrng.com, [FR/LG Starter Manip and SID Deduction](https://retailrng.com/frlg/beginner/frlgstarter/) (Secret ID advance per language)
- blisy.net, [Fire Red / Leaf Green Initial Seed Guide](https://blisy.net/g3/frlg-initial-seed.html) (Timer1 seed, factors that change it)
