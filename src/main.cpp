#include <Arduino.h>
#include <Preferences.h>
#include "esp_timer.h"

// ---------------------------------------------------------------------------
// GBA SP button bot for Pokemon RNG manipulation on retail hardware.
// Controlled over USB serial, 115200 baud. See docs/04-firmware.md.
//
// mode emerald (seed always 0, docs/06-emerald.md), tested:
//   arm  -> wait for the SP to power on (SENSE)                          = t0
//           tap the menu steps at fixed times after t0
//           tap A at t0 + calboot + adv frames: the press that creates the Pokemon
//   go   -> tap A now, and again adv frames later (new game: Secret ID timing)
//
// mode frlg (FireRed / LeafGreen, docs/01-background.md), in testing:
//   arm  -> t0 = power-on, hands off through the intro
//           hold A from t0 + seed ms for hold ms: the title screen press sets the seed
//           tap the menu steps at fixed times after t0
//           tap A at the seed press + caladv + adv frames
//
// Each game keeps its own settings profile; ppm is per console and shared.
// More games: add a value to Game, its name to GAME_NAMES and a run function.
//
// Hardware: docs/03-hardware.md. GPIO high = button pressed (optocoupler LED on).
// SENSE is active low: the optocoupler pulls the pin down while the SP is on.
// ---------------------------------------------------------------------------

// ---- pins ------------------------------------------------------------------
#define PIN_A       33   // GPIO 25 also works; the reference build moved A after damaging the 25 pad
#define PIN_B       26
#define PIN_START   27
#define PIN_SENSE   32   // SP 3.3 V present, active low

#define BTN_A       0x01
#define BTN_B       0x02
#define BTN_START   0x04

static const int PINS[3] = { PIN_A, PIN_B, PIN_START };

// ---- constants -------------------------------------------------------------
#define GBA_FPS        59.7275
#define FRAME_US       (1000000.0 / GBA_FPS)   // 16742.7 us
#define SENSE_DEBOUNCE 3                        // consecutive 1 ms samples
#define TAP_MS         50                       // a normal press is a 3-frame tap
#define MAX_STEPS      8

// ---- configuration (persisted in NVS) -------------------------------------
enum Game : uint8_t { GAME_EMERALD = 0, GAME_FRLG = 1 };
static const char* GAME_NAMES[] = { "emerald", "frlg" };
#define GAME_COUNT (sizeof(GAME_NAMES) / sizeof(GAME_NAMES[0]))

struct Step { uint32_t ms; uint8_t mask; };   // menu tap at ms after power-on

struct Profile {
    uint32_t advance;     // target advance in frames
    int32_t  calBootMs;   // emerald: power-on to the game's first frame, plus centering in the frame
    uint32_t seedMs;      // frlg: seed press, ms after power-on
    uint16_t holdMs;      // frlg: how long the seed press holds A
    int32_t  calAdvMs;    // frlg: correction of the target press, counted from the seed press
    uint8_t  nSteps;
    Step     steps[MAX_STEPS];
};

struct Config {
    uint8_t game;
    int32_t ppm;          // clock drift on every frame count, negative when the Game Boy runs fast
    Profile prof[GAME_COUNT];
};

static Config cfg;
static Preferences prefs;

static Profile& P() { return cfg.prof[cfg.game]; }

static void defaultCfg() {
    memset(&cfg, 0, sizeof(cfg));
    cfg.game = GAME_EMERALD;
    for (unsigned g = 0; g < GAME_COUNT; g++) cfg.prof[g].advance = 1000;
    cfg.prof[GAME_FRLG].seedMs = 35000;
    cfg.prof[GAME_FRLG].holdMs = 3000;
}

// ---- run state -------------------------------------------------------------
enum State { IDLE, ARMED, RUNNING };
static const char* STATE_NAMES[] = { "IDLE", "ARMED", "RUNNING" };

static volatile State state = IDLE;
static volatile bool  abortRun = false;
static int64_t t0_us = 0;

// ---- helpers ---------------------------------------------------------------
static void applyMask(uint8_t mask) {
    for (int i = 0; i < 3; i++) digitalWrite(PINS[i], (mask >> i) & 1);
}

static bool senseActive() { return digitalRead(PIN_SENSE) == LOW; }

static double framesUs(double frames) { return frames * FRAME_US * (1.0 + cfg.ppm * 1e-6); }

static const char* maskName(uint8_t m) {
    return m == BTN_A ? "A" : m == BTN_B ? "B" : m == BTN_START ? "START" : "?";
}

static uint8_t channelMask(const String& ch) {
    if (ch == "a") return BTN_A;
    if (ch == "b") return BTN_B;
    if (ch == "start") return BTN_START;
    return 0;
}

static void setupPins() {
    for (int i = 0; i < 3; i++) { digitalWrite(PINS[i], LOW); pinMode(PINS[i], OUTPUT); }
    pinMode(PIN_SENSE, INPUT_PULLUP);
}

// ---- configuration ---------------------------------------------------------
// Layout before per-game profiles (Emerald only), migrated on first boot.
struct ConfigV1 {
    uint8_t  game;
    uint32_t advance;
    int32_t  calBootMs;
    int32_t  ppm;
    uint8_t  nSteps;
    Step     steps[MAX_STEPS];
};

static void saveCfg() {
    prefs.begin("gbabot", false);
    prefs.putBytes("cfg2", &cfg, sizeof(cfg));
    prefs.end();
}

static void loadCfg() {
    defaultCfg();
    prefs.begin("gbabot", true);
    if (prefs.getBytesLength("cfg2") == sizeof(cfg)) {
        prefs.getBytes("cfg2", &cfg, sizeof(cfg));
    } else if (prefs.getBytesLength("cfg") == sizeof(ConfigV1)) {
        ConfigV1 old;
        prefs.getBytes("cfg", &old, sizeof(old));
        Profile& em = cfg.prof[GAME_EMERALD];
        em.advance = old.advance;
        em.calBootMs = old.calBootMs;
        em.nSteps = old.nSteps <= MAX_STEPS ? old.nSteps : 0;
        memcpy(em.steps, old.steps, sizeof(em.steps));
        cfg.ppm = old.ppm;
        Serial.println("settings migrated from the Emerald-only layout");
    }
    prefs.end();
    if (cfg.game >= GAME_COUNT) cfg.game = GAME_EMERALD;
    for (unsigned g = 0; g < GAME_COUNT; g++)
        if (cfg.prof[g].nSteps > MAX_STEPS) cfg.prof[g].nSteps = 0;
}

static void listSteps() {
    const Profile& p = P();
    if (p.nSteps == 0) { Serial.println("steps     = none"); return; }
    Serial.println("steps     (taps after power-on, arm runs):");
    for (int i = 0; i < p.nSteps; i++)
        Serial.printf("  %d. %lu ms  %s\n", i + 1, (unsigned long)p.steps[i].ms, maskName(p.steps[i].mask));
}

static void showCfg() {
    const Profile& p = P();
    double advMs = framesUs(p.advance) / 1000.0;
    Serial.printf("mode      = %s\n", GAME_NAMES[cfg.game]);
    Serial.printf("ppm       = %ld (all games)\n", (long)cfg.ppm);
    Serial.printf("adv       = %lu frames (%.1f ms)\n", (unsigned long)p.advance, advMs);
    if (cfg.game == GAME_EMERALD) {
        Serial.printf("calboot   = %ld ms\n", (long)p.calBootMs);
        listSteps();
        Serial.printf("arm: target press %.1f ms after power-on\n", p.calBootMs + advMs);
        Serial.printf("go:  A now, target press %.1f ms later\n", advMs);
    } else {
        Serial.printf("seed      = %lu ms after power-on\n", (unsigned long)p.seedMs);
        Serial.printf("hold      = %u ms\n", p.holdMs);
        Serial.printf("caladv    = %ld ms\n", (long)p.calAdvMs);
        listSteps();
        Serial.printf("arm: seed press %lu ms after power-on, target press %.1f ms after the seed press\n",
                      (unsigned long)p.seedMs, advMs + p.calAdvMs);
    }
}

// ---- timing ----------------------------------------------------------------
// Sleep until 2.5 ms before target, then spin. Returns false on abort.
static bool waitUntil(int64_t target_us) {
    while (true) {
        if (abortRun) return false;
        int64_t left = target_us - esp_timer_get_time();
        if (left <= 0) return true;
        if (left > 2500) vTaskDelay(1);
    }
}

// Countdown on the serial monitor: every 10 s, then every second for the last 10.
// Hands over 300 ms before the press, so printing never disturbs the timing.
static bool countdown(const char* label, int64_t target_us) {
    int lastShown = -1;
    while (true) {
        if (abortRun) return false;
        int64_t left = target_us - esp_timer_get_time();
        if (left <= 300000) return true;
        int secs = (int)((left + 999999) / 1000000);
        if (secs != lastShown && (secs <= 10 || secs % 10 == 0)) {
            Serial.printf("  %s in %d s\n", label, secs);
            lastShown = secs;
        }
        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

// Count down, press, report, hold, release. Returns the actual press time or -1 on abort.
static int64_t timedPress(const char* label, uint8_t mask, int64_t at_us, uint32_t hold_ms = TAP_MS) {
    if (!countdown(label, at_us) || !waitUntil(at_us)) return -1;
    applyMask(mask);
    int64_t actual = esp_timer_get_time();
    Serial.printf("%s press at %lld us (planned %lld, error %+lld)\n", label,
                  (long long)(actual - t0_us), (long long)(at_us - t0_us), (long long)(actual - at_us));
    bool ok = waitUntil(actual + (int64_t)hold_ms * 1000);
    applyMask(0);
    return ok ? actual : -1;
}

// Tap the menu steps that fall between from_us and the last second before until_us.
static bool runSteps(int64_t from_us, int64_t until_us) {
    const Profile& p = P();
    for (int i = 0; i < p.nSteps; i++) {
        int64_t at = t0_us + (int64_t)p.steps[i].ms * 1000;
        if (at < from_us || at > until_us - 1000000) {
            Serial.printf("step %d skipped: outside the window for menu taps\n", i + 1);
            continue;
        }
        char label[16];
        snprintf(label, sizeof(label), "STEP %d %s", i + 1, maskName(p.steps[i].mask));
        if (timedPress(label, p.steps[i].mask, at) < 0) return false;
    }
    return true;
}

// Debounced power-on detection. t0 = first of SENSE_DEBOUNCE consecutive low samples.
static bool waitForPowerOn() {
    Serial.println("ARMED, waiting for SP power (SENSE). Switch it on.");
    int lowCount = 0;
    int64_t firstLow = 0;
    while (lowCount < SENSE_DEBOUNCE) {
        if (abortRun) return false;
        if (senseActive()) {
            if (lowCount == 0) firstLow = esp_timer_get_time();
            lowCount++;
        } else {
            lowCount = 0;
        }
        vTaskDelay(pdMS_TO_TICKS(1));
    }
    t0_us = firstLow;
    return true;
}

// ---- games -----------------------------------------------------------------
// Emerald: the RNG starts at 0 and advances once per frame, so one timed A press
// on the right frame creates the target Pokemon.
static bool runEmerald(bool armed) {
    const Profile& p = P();
    int64_t targetAt;
    if (armed) {
        Serial.println("t0: SP powered on");
        targetAt = t0_us + (int64_t)framesUs(p.advance) + (int64_t)p.calBootMs * 1000;
        if (!runSteps(t0_us, targetAt)) return false;
    } else {
        Serial.println("t0: go");
        int64_t ref = timedPress("START A", BTN_A, t0_us);
        if (ref < 0) return false;
        targetAt = ref + (int64_t)framesUs(p.advance);
    }
    Serial.printf("target press in %.1f s\n", (targetAt - esp_timer_get_time()) / 1e6);
    if (timedPress("TARGET", BTN_A, targetAt) < 0) return false;
    Serial.println("Check the Pokemon's nature and stats.");
    return true;
}

// FireRed / LeafGreen: the seed comes from a timer read when A is pressed on the
// title screen, counted from power-on, so nothing may be pressed during the intro.
// The target advance counts from the seed press.
static bool runFrlg(bool armed) {
    const Profile& p = P();
    Serial.println(armed ? "t0: SP powered on. Hands off until the file select screen." : "t0: go");
    int64_t seedAt = t0_us + (int64_t)p.seedMs * 1000;
    int64_t seedActual = timedPress("SEED (hold A)", BTN_A, seedAt, p.holdMs);
    if (seedActual < 0) return false;
    int64_t targetAt = seedActual + (int64_t)framesUs(p.advance) + (int64_t)p.calAdvMs * 1000;
    if (!runSteps(seedActual + (int64_t)p.holdMs * 1000, targetAt)) return false;
    Serial.printf("target press in %.1f s\n", (targetAt - esp_timer_get_time()) / 1e6);
    if (timedPress("TARGET", BTN_A, targetAt) < 0) return false;
    Serial.println("Check the Pokemon's nature and stats.");
    return true;
}

// ---- the attempt -----------------------------------------------------------
static void runTask(void* arg) {
    bool armed = (bool)(uintptr_t)arg;
    bool ok;
    if (armed) {
        state = ARMED;
        ok = waitForPowerOn();
    } else {
        t0_us = esp_timer_get_time();
        ok = true;
    }
    if (ok) {
        state = RUNNING;
        switch (cfg.game) {
            case GAME_EMERALD: ok = runEmerald(armed); break;
            case GAME_FRLG:    ok = runFrlg(armed); break;
        }
    }
    applyMask(0);
    Serial.println(ok ? "DONE" : "ABORTED");
    state = IDLE;
    vTaskDelete(NULL);
}

static void startRun(bool armed) {
    if (state != IDLE) { Serial.println("busy, abort first"); return; }
    if (armed && senseActive()) { Serial.println("SP is already on. Switch it off, then arm."); return; }
    abortRun = false;
    xTaskCreatePinnedToCore(runTask, "run", 4096, (void*)(uintptr_t)armed, configMAX_PRIORITIES - 1, NULL, 1);
}

// ---- self-test -------------------------------------------------------------
// Checks a freshly soldered DevKit for shorts and solder bridges. Run it on the
// bare board, before resistors and optocouplers go in: an LED path on a pin
// makes the pull-up reading meaningless.
// Not tested: GPIO 0 and 2 (BOOT button and on-board LED on many boards),
// 5 (reads HIGH against the internal pull-down on the ELEGOO USB-C DevKit with
// no bridge present, so it is pulled up on the board), 1 and 3 (serial port,
// which works if you can read this), 6 to 11 (flash), 34 to 39 (input only,
// no internal pull-ups).
static const int TEST_PINS[] = { 32, 33, 25, 26, 27, 14, 12, 13,
                                 23, 22, 21, 19, 18, 17, 16, 4, 15 };

static void selfTest() {
    if (state != IDLE) { Serial.println("busy, abort first"); return; }
    const int n = sizeof(TEST_PINS) / sizeof(TEST_PINS[0]);
    bool psram = psramFound();
    bool skip[n] = {};
    int faults = 0;

    Serial.printf("chip %s rev %d, flash %lu MB, psram %s\n", ESP.getChipModel(), ESP.getChipRevision(),
                  (unsigned long)(ESP.getFlashChipSize() >> 20), psram ? "yes" : "no");
    for (int i = 0; i < n; i++)
        if (psram && (TEST_PINS[i] == 16 || TEST_PINS[i] == 17)) skip[i] = true;  // PSRAM lines on WROVER

    // 1. With pull-up every pin must read HIGH, otherwise it touches GND.
    for (int i = 0; i < n; i++) if (!skip[i]) pinMode(TEST_PINS[i], INPUT_PULLUP);
    delay(5);
    for (int i = 0; i < n; i++) {
        if (skip[i] || digitalRead(TEST_PINS[i]) == HIGH) continue;
        Serial.printf("FAULT  GPIO %d reads LOW with pull-up: touches GND\n", TEST_PINS[i]);
        skip[i] = true;
        faults++;
    }

    // 2. With pull-down every pin must read LOW, otherwise it touches 3V3.
    for (int i = 0; i < n; i++) if (!skip[i]) pinMode(TEST_PINS[i], INPUT_PULLDOWN);
    delay(5);
    for (int i = 0; i < n; i++) {
        if (skip[i] || digitalRead(TEST_PINS[i]) == LOW) continue;
        Serial.printf("FAULT  GPIO %d reads HIGH with pull-down: touches 3V3\n", TEST_PINS[i]);
        skip[i] = true;
        faults++;
    }

    // 3. Drive one pin LOW at a time. A pulled-up pin that follows it is bridged to it.
    for (int i = 0; i < n; i++) if (!skip[i]) pinMode(TEST_PINS[i], INPUT_PULLUP);
    delay(5);
    for (int i = 0; i < n; i++) {
        if (skip[i]) continue;
        digitalWrite(TEST_PINS[i], LOW);
        pinMode(TEST_PINS[i], OUTPUT);
        delayMicroseconds(500);
        for (int j = i + 1; j < n; j++) {
            if (skip[j] || digitalRead(TEST_PINS[j]) == HIGH) continue;
            Serial.printf("FAULT  GPIO %d and GPIO %d are bridged\n", TEST_PINS[i], TEST_PINS[j]);
            faults++;
        }
        pinMode(TEST_PINS[i], INPUT_PULLUP);
    }

    // Back to the normal pin setup.
    for (int i = 0; i < n; i++)
        if (!(psram && (TEST_PINS[i] == 16 || TEST_PINS[i] == 17))) pinMode(TEST_PINS[i], INPUT);
    setupPins();

    if (faults == 0) Serial.printf("selftest PASS: %d pins, no shorts to GND or 3V3, no bridges\n", n - (psram ? 2 : 0));
    else Serial.printf("selftest FAIL: %d fault(s), see above\n", faults);
}

// ---- serial ----------------------------------------------------------------
static void help() {
    Serial.println(
        "commands:\n"
        "  arm                  wait for SP power-on, then run the current game's sequence\n"
        "  go                   run the sequence now (emerald: A now, target adv frames later)\n"
        "  abort                stop and release all buttons\n"
        "  status               state, SENSE, time since t0\n"
        "  mode emerald|frlg    game; each game keeps its own settings\n"
        "  adv <frames>         target advance\n"
        "  ppm <n>              clock drift correction (all games), negative if the Game Boy runs fast\n"
        "  calboot <ms>         emerald: power-on calibration\n"
        "  seed <ms>            frlg: seed press, ms after power-on\n"
        "  hold <ms>            frlg: how long the seed press holds A\n"
        "  caladv <ms>          frlg: target press correction, counted from the seed press\n"
        "  step <ms> <a|b|start> add a tap at ms after power-on (arm runs, max 8)\n"
        "  steps [clear]        list or clear the taps\n"
        "  test <a|b|start> [ms] press a button, 300 ms or up to 10000\n"
        "  selftest             check a freshly soldered board for shorts and bridges\n"
        "  show | save | help");
}

static void handleLine(String line) {
    line.trim();
    int sp = line.indexOf(' ');
    String cmd = sp < 0 ? line : line.substring(0, sp);
    String arg = sp < 0 ? "" : line.substring(sp + 1);
    arg.trim();
    cmd.toLowerCase();
    arg.toLowerCase();
    Profile& p = P();

    if (cmd == "arm") startRun(true);
    else if (cmd == "go") startRun(false);
    else if (cmd == "abort") abortRun = true;
    else if (cmd == "status") {
        Serial.printf("state %s, SENSE %s", STATE_NAMES[state], senseActive() ? "active (SP on)" : "inactive (SP off)");
        if (state == RUNNING) Serial.printf(", %.3f s since t0", (esp_timer_get_time() - t0_us) / 1e6);
        Serial.println();
    }
    else if (cmd == "mode") {
        if (state != IDLE) { Serial.println("busy, abort first"); return; }
        int g = -1;
        for (unsigned i = 0; i < GAME_COUNT; i++) if (arg == GAME_NAMES[i]) g = i;
        if (g < 0) { Serial.println("usage: mode emerald|frlg"); return; }
        cfg.game = (uint8_t)g;
        showCfg();
    }
    else if (cmd == "adv") { p.advance = arg.toInt(); showCfg(); }
    else if (cmd == "ppm") { cfg.ppm = arg.toInt(); showCfg(); }
    else if (cmd == "calboot") { p.calBootMs = arg.toInt(); showCfg(); }
    else if (cmd == "seed") { p.seedMs = arg.toInt(); showCfg(); }
    else if (cmd == "hold") { p.holdMs = constrain(arg.toInt(), (long)TAP_MS, 10000L); showCfg(); }
    else if (cmd == "caladv") { p.calAdvMs = arg.toInt(); showCfg(); }
    else if (cmd == "step") {
        int sp2 = arg.indexOf(' ');
        long ms = sp2 < 0 ? 0 : arg.substring(0, sp2).toInt();
        String ch = sp2 < 0 ? "" : arg.substring(sp2 + 1);
        ch.trim();
        uint8_t m = channelMask(ch);
        if (ms <= 0 || !m) { Serial.println("usage: step <ms after power-on> <a|b|start>"); return; }
        if (p.nSteps >= MAX_STEPS) { Serial.println("full, steps clear first"); return; }
        int i = p.nSteps++;
        while (i > 0 && p.steps[i - 1].ms > (uint32_t)ms) { p.steps[i] = p.steps[i - 1]; i--; }
        p.steps[i] = { (uint32_t)ms, m };
        listSteps();
    }
    else if (cmd == "steps") {
        if (arg == "clear") p.nSteps = 0;
        listSteps();
    }
    else if (cmd == "test") {
        if (state != IDLE) { Serial.println("busy, abort first"); return; }
        int sp2 = arg.indexOf(' ');
        String ch = sp2 < 0 ? arg : arg.substring(0, sp2);
        long ms = constrain(sp2 < 0 ? 300 : arg.substring(sp2 + 1).toInt(), 1, 10000);
        uint8_t m = channelMask(ch);
        if (!m) { Serial.println("usage: test <a|b|start> [ms]"); return; }
        Serial.printf("pressing %s for %ld ms\n", maskName(m), ms);
        applyMask(m); delay(ms); applyMask(0);
        Serial.println("released");
    }
    else if (cmd == "selftest") selfTest();
    else if (cmd == "show") showCfg();
    else if (cmd == "save") { saveCfg(); Serial.println("saved"); }
    else help();
}

// ---- arduino ---------------------------------------------------------------
void setup() {
    setupPins();
    Serial.begin(115200);
    delay(300);
    loadCfg();
    Serial.println("\nGBA SP RNG bot");
    showCfg();
    help();
}

void loop() {
    static String line;
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '\n' || c == '\r') { if (line.length()) handleLine(line); line = ""; }
        else line += c;
    }
    delay(5);
}
