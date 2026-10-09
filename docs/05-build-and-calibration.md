# 05. Build, test and calibration procedure

Time estimates assume the parts are on the table.

## Phase 1: bench test (30 min)

1. Solder the ESP32 to the protoboard, flash the firmware and run `selftest`. Fix any reported short or bridge before anything else goes on the board. Then build the rest per [03-hardware.md](03-hardware.md). Do not connect the SP yet.
2. Temporarily wire an LED and a 1k resistor in series from the ESP32's 3V3 pin to pin 4 of the A optocoupler, and its pin 3 to ESP32 GND. Only for this test: it breaks isolation, remove it afterwards.
3. Flash the firmware, open the serial monitor.
4. `test a`: the LED lights for 300 ms. Move the LED to the B and Start optocouplers and repeat with `test b` and `test start`.
5. Temporarily wire the ESP32's 3V3 pin through a spare 330 R to pin 1 of the SENSE optocoupler, and its pin 2 to ESP32 GND: `status` shows SENSE active. Remove both wires afterwards, they break isolation.
6. `adv 120`, then `go`: watch the serial output. The device taps A right away and again 120 frames (about 2 s) later, each with its timing error in microseconds.
7. Remove the test LEDs. Confirm with the multimeter that there is no continuity between the two grounds.

## Phase 2: open the SP and solder (2 h)

Teardown follows the [iFixit SP motherboard guide](https://documents.cdn.ifixit.com/pdf/ifixit/guide_12788_en.pdf). Screws: JIS 00 for the battery cover and the board, tri-point Y0 for the bottom shell. JIS heads strip easily under a regular Phillips driver: press firmly and turn slowly.

1. Power off, cartridge out. Loosen the captive screw of the battery cover, remove the cover and the battery.
2. Remove the six bottom shell screws: four 6.3 mm recessed and two 4.6 mm. Keep the two lengths apart. Lift the bottom shell straight up.
3. Lift off the loose power switch cover. Remove the three 4.1 mm screws holding the board.
4. Flip the board over the hinge side like a page and prop it up. The button side with the test points now faces up. The screen cable stays connected and has very little slack: do not pull on the board.
5. Locate TP0 (A), TP1 (B) and the Start via. Continuity-test each against the signal contact of its button. Locate a ground point. Positions are described in [03-hardware.md](03-hardware.md). Take a photo of the button side.
6. Free the board so soldering cannot strain the screen cable (iFixit steps 10 to 17): lift off the silicone button pads, lift the speaker out of its recess and keep the round mesh, push the two tabs on the screen cable connector to unlocked, slide the cable out with tweezers.
7. Find the 3.3 V point by continuity, since the board cannot be powered while it is out: it must beep against pin 1 (VCC) of the cartridge slot. Pin 32 at the other end beeps steadily against ground.
8. Cut a notch of about 3 mm in the side wall between the shoulder button and the power switch.
9. Cut five wires of about 25 cm. Solder the bottom points first (Start, 3.3 V), then A and B, GND last, so finished wires stay out of the way. Tin the pad and the wire first, join in under one second, and tack each wire down right away: the Start and Select vias lift easily. The 3.3 V wire gets the 330 R inline, covered with heat shrink. Check for shorts between neighbouring pads.
10. Twist the wires into a tail through the notch, hot glue at the notch. Crimp female Dupont contacts onto the ends and push them into a 6-pin housing in the order listed in [03-hardware.md](03-hardware.md). Beep-test the housing pins against each other: no pair may beep.
11. Test before the final screws: reconnect the screen cable and lock its tabs, put the speaker and button pads back, flip the board back and refit its three screws. Place the power switch cover notched side up with its cutout around the switch, or the console will not power on. Fit the bottom shell, insert the battery, switch on. A, B and Start must work by hand and none may act as held. Plug pin 2 must read about 3.3 V against pin 1 with the switch on, and 0 V with it off.
12. Fit the six shell screws, the long ones in the recessed holes, and the battery cover.

## Phase 3: calibrate and hunt

From here on the procedure depends on the game. The full procedures, calibration and reference runs are in [06-emerald.md](06-emerald.md) for Emerald and [07-firered-leafgreen.md](07-firered-leafgreen.md) for FireRed and LeafGreen.

Keep a log of every attempt: target advance, `calboot`, `ppm`, the advance you hit and the Pokemon. A one-frame miss tells you which way to move `calboot`, and a pattern of misses tells you whether something in your routine varies.

| Date | Target | calboot | ppm | Hit | Pokemon | Shiny |
|---|---|---|---|---|---|---|
| | | | | | | |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| SENSE never triggers | 3.3 V wire on the wrong point, or optocoupler #1 turned the wrong way | with the SP on, measure optocoupler #1 pin 1 against pin 2: about 1.2 V means the LED is lit |
| A press does nothing in game | wire on the ground contact instead of the signal contact | continuity test again |
| Game sees A as held permanently | phototransistor leaking or wires shorted | check GPIO 33 is low at idle, check for solder bridges |
| Hit jumps by one between attempts | the press sits on a frame edge | move `calboot` by half a frame, about 8 ms |
| Hit jumps by two or more between attempts | the hand-done part of the routine varies, for example time in the overworld with moving NPCs | let the device do those presses with `step`, see [06-emerald.md](06-emerald.md) |
| Long targets land one or more frames off while short ones hit | clock drift between the Game Boy and the ESP32 | set `ppm`, see [06-emerald.md](06-emerald.md) |
| Target press timing error above 100 us in the log | run task starved | report, should not happen |
| Random button presses while the SP charger is plugged in and the tail is connected, even with the ESP32 unpowered | charger noise couples into the long button wires, which only have the SP's weak internal pull-ups. On the reference build the original battery turned out to be swollen; with a healthy replacement battery, charging with the tail connected no longer caused presses | check the battery first: a swollen or worn-out battery smooths the supply much worse. Run attempts on battery anyway. Optional: a 100 nF ceramic capacitor from each button pin of the protoboard header to its GND pin |
