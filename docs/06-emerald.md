# 06. Pokemon Emerald

Emerald is the easiest Gen 3 game to manipulate on retail hardware, and the device needs only one timed press for it.

## How Emerald's RNG behaves

- **The initial seed is always 0.** Game Freak left out the code that picks a starting seed, so the RNG starts from the same point on every boot. Unlike Ruby and Sapphire, this works with a live cartridge battery.
- **The RNG advances once per frame** outside battles, from the VBlank interrupt, and faster inside battles (the Battle Frontier is an exception).
- **NPCs that move call the RNG too.** That is why some guides open the Start menu before the final press: it freezes NPCs.
- **One timed input is enough.** Because the seed is fixed, the target is just an advance count from reset. The A press that generates the Pokemon has to land on that advance.

Community guides start EonTimer at a soft reset (A+B+Start+Select). The reference unit cannot soft reset because its Select line is dead, so the device starts its clock at power-on through SENSE instead. A power cycle also starts from seed 0. The GBA boot logo adds a constant delay before the game starts counting, and the `calboot` calibration absorbs it.

## What you need

- An Emerald cartridge and a save you are willing to overwrite. Finding your Secret ID (SID) requires a new game.
- JS-Finder (SID candidates) and Ten Lines (target search and calibration), linked from the retailrng guides below. Or compute it: the Gen 3 RNG is `state = state * 0x41C64E6D + 0x6073`, and each call returns the upper 16 bits.
- The firmware in `mode emerald`, see [04-firmware.md](04-firmware.md).

## Procedure with the device

### 1. New game: Trainer ID and Secret ID

1. Start a new game, enter your name and leave the cursor on OK (Start jumps there), so the next A press leaves the name screen.
2. On the device: `mode emerald`, `adv 950`.
3. Type `go`. The device presses A immediately, leaving the name screen, and presses A again 950 frames later. In between, answer YES to "So it's ...?", click through Birch's lines yourself and stop on the final text box: "Well, I'll be expecting you later. Come see me in my POKéMON LAB." The device presses A on it. (Text from the [pokeemerald decompilation](https://github.com/pret/pokeemerald/blob/master/data/text/birch_speech.inc).)
4. Read your Trainer ID from the trainer card. Leaving the name screen seeds the RNG with the Trainer ID, and the game draws the Secret ID at the start of the new game, a fixed delay after the last press. With `adv 950` the Secret ID is the RNG output at step 1000 from that seed, confirmed on the reference build: the upper 16 bits of the state after 1001 steps.

The guides list candidates from step 995 to 1005 because a human press varies. The device's press does not, so step 1000 is the one.

### 2. Shiny starter

1. Find the advance of a shiny starter for your Trainer ID and Secret ID: Ten Lines (Calibration tab, game "Emerald Painting Seed", target seed 0000, method Static 1, category Starters, shiny Star/Square), or compute it. The starter is method 1: personality value low half, high half, then two IV words, from consecutive RNG calls.
2. Play until you stand in front of Birch's bag on Route 101, and save.
3. Set the routine and the target, see "Keeping attempts identical" below: `adv <that advance>`, then `arm` and switch the Game Boy on.
4. Check the starter's nature and stats and find the advance you hit. Adjust `calboot` by the difference: one frame is 16.74 ms.

The first attempt misses by roughly the length of the boot logo. That is expected, and one correction fixes it.

### Keeping attempts identical

Two attempts with the same calibration can land a few advances apart. The device's press is accurate to microseconds, so differences come from extra RNG calls during the part done by hand. On Route 101 the cause is NPCs (see the reference run below), so the device presses CONTINUE and the bag itself at fixed times with `step`:

```
step 23000 a
step 25500 a
```

The person skips the intro, presses A on the title screen and the dead-battery message, and stops on the main menu. After the device opens the bag, the person picks the starter and stops on YES. Adapt the step times to your console; after changing them, run one calibration attempt again.

### 3. Static and wild encounters

Not done on the reference build yet. The approach from the guides:

- **Static with a text box** (gift Pokemon, legendaries that speak a line): same as the starter. Stop on the last text box, the device presses A.
- **Static without a text box** (overworld sprites): the guides open the Start menu to freeze NPCs and close it shortly before the final press. With the device that B press is a `step ... b` at least 1 s before the target (steps closer to the target are skipped); not tested yet.
- **Wild with Sweet Scent:** in the party menu, hover over Sweet Scent. The target press uses it. Ten Lines method Wild 2, category Grass or Surfing.
- Do not battle between power-on and the target press: battles advance the RNG faster.

## Reference run

The first full run on the reference build, 2026-10-06 and 2026-10-07, ending in a shiny Treecko:

| Item | Result |
|---|---|
| Boot offset | 270 frames from power-on to the game's first frame, so `calboot` around 4512 ms |
| Frame edge | `calboot` 4504 and 4521 landed one frame either side of the target, 4512 sits in the middle of the frame |
| Routine | the device presses CONTINUE at 23 s and the bag at 25.5 s. The person does the intro skip, title screen and dead-battery message, then only picks the starter and waits on YES |
| Clock drift | the Game Boy runs faster than the ESP32. Targets up to 4 minutes suggested about 93 ppm; the first 17-minute target, which measures it far more precisely, landed one frame early and narrowed it to about 76 ppm. Settings: `ppm -76` with `calboot 4517`, which keeps short and long targets centered in their frame |
| Secret ID | at step 1000 exactly, as the guide's 950-frame timer predicts for a perfect press. 18 attempts in total, including calibration |
| Chosen shiny | with Trainer ID and Secret ID known, a shiny Timid Treecko was picked from the computed list: advance 61682, IVs 5/18/30/30/19/22, a 17-minute wait. First attempt one frame early, second attempt with `ppm -76` hit it |

What caused the misses along the way, all confirmed in the [pokeemerald decompilation](https://github.com/pret/pokeemerald):

- **The press on a frame edge.** SENSE detects power-on within about 1 ms, which flips the hit by one when the press sits right on the edge. Centering `calboot` in the frame fixes it.
- **NPCs on Route 101.** Birch's bag and a youngster use a look-around movement that calls `Random()` twice per cycle, and a boy wanders. The time between loading the save and pressing A on the bag therefore varies the advance count. Device-timed CONTINUE and bag presses fix it. If a look-around cycle lands right at the bag press, results alternate by exactly 2, so move the bag press by half a second.
- **Clock drift**, see the table above.
- **Not a cause:** the intro always makes exactly one call, because the copyright screen cannot be skipped and the bike rider's random wobble only starts after the first scene. The title screen, main menu, battery message and starter selection make no RNG calls.

### Tried and dropped: choosing the Trainer ID

The Trainer ID is Timer1, started when the player naming screen opens and read when it closes, ticking at the full CPU clock of 16.78 MHz. The idea was to press both moments with the device, so a fixed frame count would give a predictable Trainer ID, and then pick the Secret ID so a chosen high-IV Treecko becomes shiny. A measuring new game and a planned one gave Trainer IDs that differ by a non-multiple of 64 from the frame model. The timer start and read sit at slightly different points within their frames from run to run, probably because the sound engine's interrupt load depends on when the person started the sequence. So the Trainer ID is not predictable this way, and the feature was removed from the firmware.

### What is reachable

From seed 0 the first Treecko with 31 in every IV is at advance 176,562,488, 34 days of waiting, so in practice the best you can do is pick the best shiny among the advances your Trainer ID and Secret ID make shiny.

## Device notes

- Up is not wired. Encounters that the guides start with Up can be started with A instead.
- Every attempt is a power cycle with `arm`, since this unit cannot soft reset.
- Run attempts on battery, with the charger out: the charger's noise on the long button wires causes random presses.
- Waits are long but harmless: 10,000 advances take about 2.8 minutes.

## Sources

- retailrng.com, [Emerald RNG Manip Introduction](https://retailrng.com/emerald/beginner/introduction/) (seed 0, live battery)
- retailrng.com, [Emerald Starter Manip](https://retailrng.com/emerald/beginner/starter-rng/) (TID timer of 950 frames, SID candidates at advances 995 to 1005, Ten Lines settings)
- retailrng.com, [Emerald Static Manip](https://retailrng.com/emerald/beginner/emerald-static/) (Start menu to freeze NPCs, B on the 3rd beep, A on the 6th)
- retailrng.com, [Emerald Wild Manip](https://retailrng.com/emerald/beginner/emerald-wild/) (Sweet Scent, method Wild 2)
- Smogon, [Emerald RNG introduction](https://www.smogon.com/ingame/rng/emerald_rng_intro) (seed always 0, advance rate in and out of battle, NPC calls)
- [pokeemerald decompilation](https://github.com/pret/pokeemerald): `main.c` (RNG call in the VBlank interrupt, Trainer ID seeding), `naming_screen.c` (Timer1 start and read), `new_game.c` (Secret ID), `intro.c`, `data/maps/Route101`
