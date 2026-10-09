# 01. Background: how FireRed / LeafGreen seed their RNG

This document explains why the device does what it does. Everything here comes from the retail RNG community's published guides, listed at the bottom. Nothing in this document was invented for this project.

## The RNG

Gen 3 Pokemon games use a 32-bit linear congruential generator. Its state at any moment is fully determined by the initial seed and the number of advances since. If you know the seed and the advance, you know the next Pokemon's personality value, IVs, nature and shininess.

## How FRLG picks the initial seed

1. On power-on the console boots, the game plays its intro (copyright screen, Game Freak logo, the cinematic). Button presses during the intro change how long it takes, which is why you must not touch anything during it.
2. After the intro finishes, the game starts counting processor clock cycles.
3. When you press the "seed button" (A, Start or L) on the title screen, the cycle count is converted to a 16-bit number. That number is the initial seed.
4. Because inputs are only read once per frame, the effective seed changes about 60 times per second. The seed is therefore a function of *when, in frames, you press the button*. Milliseconds of precision is enough.

Consequences:

- The seed is reproducible if the time from power-on to the seed button press is reproducible. That is the whole premise of this device.
- The seed also depends on game version, language, the save file's sound setting (mono/stereo) and button mode (Help / LR / L=A). Keep those fixed once calibrated.
- **A soft reset (A+B+Start+Select) does not reset the cycle counter.** Soft resets give inconsistent seeds. Every attempt needs a real power cycle. This is why the device *senses* power-on instead of trying to reset the game itself.
- Holding Start, Select, B or a D-pad direction during boot shifts the seed by a fixed offset. The device presses nothing until the title screen, so this never comes into play.

## How the target Pokemon is picked

After the seed is locked, the RNG advances roughly once per frame. Tools like PokeFinder search for a seed and an advance count that produce the Pokemon you want (for example a shiny with good IVs). The result is a pair: *target seed* and *target advance*.

The manual procedure the community uses with EonTimer:

1. Flip the power switch and click Start on EonTimer at the same moment.
2. Do not press anything during the intro.
3. Timer 1 ends: press and hold A on the title screen until the file-select screen appears. The seed is now locked.
4. Load the save, go to the encounter, get to the text box or menu right before the Pokemon is generated.
5. Timer 2 ends: press A. The Pokemon is generated at (ideally) the target advance.
6. Check the Pokemon's nature and stats, find which seed and advance you actually hit, enter those into the timer's calibration fields, retry.

Step 1 and 3 and 5 are the three human timing problems. Step 1 has slack of a few hundred milliseconds that gets absorbed by calibration, but it adds run-to-run jitter. Step 3 and 5 are the two frame-perfect inputs.

## What the device replaces

| Manual step | Device |
|---|---|
| Start timer when flipping the switch | Senses the SP's 3.3 V rail coming up. Zero human jitter. |
| Press and hold A at timer 1 | Optocoupler closes the A button line at t0 + seed_ms, holds it for seed_hold_ms |
| Press A at timer 2 | Optocoupler taps A at t_seed + advance * frame_duration |
| Calibrate after a miss | Type the hit seed and hit advance into the device, it corrects itself |

Loading the save and walking to the encounter stays manual. It does not need precision.

## Numbers used in this project

| Quantity | Value | Note |
|---|---|---|
| GBA frame rate | 59.7275 Hz | fixed by hardware, 280896 cycles per frame at 16.78 MHz |
| Frame duration | 16.7427 ms | 1000 / 59.7275 |
| Seed change rate | about 1 per frame | after the intro |
| Intro length to title screen | about 35 s | version and language dependent, calibration absorbs it |

## Sources

- blisy.net, Fire Red / Leaf Green Initial Seed Guide: https://blisy.net/g3/frlg-initial-seed.html (clock cycle counter, soft reset behaviour, factors that affect the seed)
- retailrng.com, FR/LG RNG Manip Introduction: https://retailrng.com/frlg/beginner/introduction/ (two frame-perfect inputs, once-per-frame input reading)
- retailrng.com, FR/LG Starter Manip and SID Deduction: https://retailrng.com/frlg/beginner/frlgstarter/ (full EonTimer procedure, press-and-hold seed input, calibration workflow)
- Smogon, RNG Manipulation in FireRed/LeafGreen: https://www.smogon.com/forums/threads/rng-manipulation-in-firered-leafgreen-wild-pok%C3%A9mon-supported-in-rng-reporter-9-93.62357/
- pokefirered decompilation, for the seeding code itself (`SeedRngAndSetTrainerId` in `src/main.c`): https://github.com/pret/pokefirered
