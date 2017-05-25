#include <CmdMessenger.h>
#include <TimeLib.h>
#include <FastLED.h>

#define TIME_HEADER     "T"
#define TIME_REQUEST    7

#define HOUR_BITS       5
#define MINUTE_BITS     6
#define SECOND_BITS     6

#define HH_TIX          3
#define H_TIX           9
#define MM_TIX          6
#define M_TIX           9
#define SS_TIX          5
#define S_TIX           5

#define PIN             6
#define NUM_LEDS        40

#define BRIGHTNESS      32
#define FPS             60

#define TIX_UPDATE      FPS * 4
#define TIX_UPDATE_SEC  FPS * 1

/**
 * LED index reference (0-based)
 * 
 * <-- Towards USB and power
 *  00  01  02  03  04  05  06  07
 *  08  09  10  11  12  13  14  15
 *  16  17  18  19  20  21  22  23
 *  24  25  26  27  28  29  30  31
 *  32  33  34  35  36  37  38  39
 */
CRGB leds[NUM_LEDS];

// Attach CmdMessenger
CmdMessenger cmd = CmdMessenger(Serial);

// Flag signaling client is ready
bool clientReady = false;

// Known commands
enum {
    CMD_READY,              // 0
    CMD_ACK,                // 1
    CMD_SUCCESS,            // 2
    CMD_ERROR,              // 3
    CMD_TIME_SYNC,          // 4
    CMD_TIME_SYNC_RETURN,   // 5
    CMD_SET_BRIGHTNESS      // 6
};

const int BORDER_SIZE = 22;
const int border[BORDER_SIZE] = {
    0, 1, 2, 3, 4, 5, 6, 7,         // Top
    15, 23, 31,                     // Right
    39, 38, 37, 36, 35, 34, 33, 32, // Bottom
    24, 16, 8                       // Left
};

// Positions for binaryClock
const int hourPos[HOUR_BITS]        = {0, 1, 2, 3, 4};
const int minutePos[MINUTE_BITS]    = {8, 9, 10, 11, 12, 13};
const int secondPos[SECOND_BITS]    = {16, 17, 18, 19, 20, 21};

// Positions for tixClock
int hhPos[HH_TIX] = {1, 2, 3};
int hPos[H_TIX]   = {17, 18, 19, 25, 26, 27, 33, 34, 35};
int mmPos[MM_TIX] = {4, 5, 6, 12, 13, 14};
int mPos[M_TIX]   = {20, 21, 22, 28, 29, 30, 36, 37, 38};
int ssPos[S_TIX]  = {0, 8, 16, 24, 32};
int sPos[SS_TIX]  = {7, 15, 23, 31, 39};
int sendPos = 9;
int receivePos = 10;

void attachCommandCallbacks() {
    cmd.attach(onUnknownCmd);
    cmd.attach(CMD_READY, onReady);
    cmd.attach(CMD_TIME_SYNC, onTimeSync);
    cmd.attach(CMD_TIME_SYNC_RETURN, onTimeSyncReturn);
    cmd.attach(CMD_SET_BRIGHTNESS, onSetBrightness);
}

// Unknown command received
void onUnknownCmd() {
    onGet();
    
    cmd.sendCmd(CMD_ERROR, F("Unattached command"));
    onSend();
}

// Send ready message
void onReady() {
    onGet();

    clientReady = true;
    
    cmd.sendCmd(CMD_READY, F("Arduino ready"));
    onSend();
}

// Receive request for time
void onTimeSync() {
    onGet();

    // Get weekday and month strings
    char dayString[4],
       monthString[4];
       
    strcpy(dayString, dayShortStr(weekday()));
    strcpy(monthString, monthShortStr(month()));

    // Send current time
    cmd.sendCmd(CMD_TIME_SYNC_RETURN, now());
    onSend();

    // Send current formatted time
    cmd.sendCmdStart(CMD_SUCCESS);
    cmd.sendCmdfArg("Current time is %02d:%02d:%02d %s %d %s %d",
        hour(),
        minute(),
        second(),
        dayString,
        day(),
        monthString,
        year());
    cmd.sendCmdEnd();
    onSend();
}

// Receive time sync
void onTimeSyncReturn() {
    onGet();
    
    unsigned long pctime = (unsigned long) cmd.readInt32Arg();
    const unsigned long DEFAULT_TIME = 1357041600; // Jan 1 2013
    
    cmd.sendCmd(CMD_ACK, F("Time sync received"));
    onSend();

    // Integer is a valid time (greater than Jan 1 2013)
    if (pctime >= DEFAULT_TIME) {
        setTime(pctime);

        // Get weekday and month strings
        char dayString[4],
           monthString[4];
           
        strcpy(dayString, dayShortStr(weekday()));
        strcpy(monthString, monthShortStr(month()));

        cmd.sendCmdStart(CMD_SUCCESS);
        cmd.sendCmdfArg("Time synced to %02d:%02d:%02d %s %d %s %d",
            hour(),
            minute(),
            second(),
            dayString,
            day(),
            monthString,
            year());
        cmd.sendCmdEnd();
        onSend();
        return;
    }

    // Integer is not a valid time
    cmd.sendCmd(CMD_ERROR, F("Time is invalid, time not synced"));
    onSend();
}

void onSetBrightness() {
  onGet();

  int brightness = cmd.readInt16Arg();
  int brightnessConstraint = constrain(brightness, 0, 255);
  
  cmd.sendCmdStart(CMD_ACK);
  cmd.sendCmdfArg("Setting brightness to %d (constrained to %d)...", brightness, brightnessConstraint);
  cmd.sendCmdEnd();
  onSend();

  // Set brightness
  FastLED.setBrightness(brightness);

  cmd.sendCmdStart(CMD_SUCCESS);
  cmd.sendCmdfArg("Brightness set to %d", brightness);
  cmd.sendCmdEnd();
  onSend();
}

// Callback for every sent command
void onSend() {
    leds[sendPos] = CHSV(100, 255, 255);
}

// Callback for every received command
void onGet() {
    leds[receivePos] = CHSV(200, 255, 255);
}

void setup() {
    Serial.begin(9600);

    // Configure commander
    cmd.printLfCr();
    attachCommandCallbacks();

    // Seed RNG with analog noise
    randomSeed(analogRead(0));
    
    // Set up LEDs
    FastLED.addLeds<NEOPIXEL, PIN>(leds, NUM_LEDS);
    FastLED.setBrightness(BRIGHTNESS);

    // Request time sync
    //cmd.sendCmd(CMD_TIME_SYNC, F("Requesting time sync"));
    //onSend();

    // Set up default sync
    //setTime(1357042600);
}

void loop() {
    // Process serial data
    cmd.feedinSerialData();
    
    //rainbowBorder();
    //binaryClock();
    tixClock();
}

void rainbowBorder() {
    static uint8_t hue = 0;
    static int pos = 0;
    
    fadeToBlackBy(leds, NUM_LEDS, 50);
    leds[border[pos++]] = CHSV(hue++, 200, 255);
    if (pos > BORDER_SIZE - 1) pos = 0;
    
    // Display and delay
    FastLED.show();
    FastLED.delay(1000/FPS);
}

void binaryClock() {
    if (Serial.available()) {
        processSyncMessage();
    }
    if (timeStatus() != timeNotSet) {
        fadeToBlackBy(leds, NUM_LEDS, 50);
        binaryClockDisplay();
    }
    //delay(1000);
    FastLED.show();
    FastLED.delay(1000/FPS);
}

void binaryClockDisplay() {
    int timeHour = hour();
    int timeMinute = minute();
    int timeSecond = second();
    
    //Serial.print(F("hour: "));
    for (int i = HOUR_BITS; i--;) {
        //Serial.print(bitRead(timeHour, i));
        if (bitRead(timeHour, i)) leds[hourPos[i]] = CHSV(0, 200, 255);
    }

    //Serial.print(F(" minute: "));
    for (int i = MINUTE_BITS; i--;) {
        //Serial.print(bitRead(timeMinute, i));
        if (bitRead(timeMinute, i)) leds[minutePos[i]] = CHSV(96, 200, 255);
    }

    //Serial.print(F(" second: "));
    for (int i = SECOND_BITS; i--;) {
        //Serial.print(bitRead(timeSecond, i));
        if (bitRead(timeSecond, i)) leds[secondPos[i]] = CHSV(160, 200, 255);
    }
    //Serial.println();
}

void tixClock() {
    fadeToBlackBy(leds, NUM_LEDS, 50);

    // Time not set
    if (timeStatus() == timeNotSet) {
        wait();
    }

    // Time is set
    else {
        tixClockDisplay();
    }
    
    FastLED.show();
    FastLED.delay(1000/FPS);
}

void wait() {
    // Only show border if client is ready
    if (clientReady) {
        rainbowBorder();
    }
}

void tixClockDisplay() {
    static int counter = TIX_UPDATE;
    static int secCounter = TIX_UPDATE_SEC;

    static int timeHour, timeMinute, timeSecond,
        hh, h, mm, m, ss, s;
    
    // Only update time when needed
    if (++counter >= TIX_UPDATE) {
        counter = 0;
        timeHour = hour();
        timeMinute = minute();
    
        hh = timeHour / 10;
        h = timeHour % 10;
        mm = timeMinute / 10;
        m = timeMinute % 10;
    
        // Shuffle positions
        shuffle(hhPos, HH_TIX);
        shuffle(hPos, H_TIX);
        shuffle(mmPos, MM_TIX);
        shuffle(mPos, M_TIX);
    
        /*Serial.print("shuffled hh: ");
        for (int i = 0; i < HH_TIX; ++i) {
            Serial.print(hhPos[i]);
            Serial.print(" ");
        }
    
        Serial.print("\nshuffled h: ");
        for (int i = 0; i < H_TIX; ++i) {
            Serial.print(hPos[i]);
            Serial.print(" ");
        }
        Serial.println();*/
    }

    // Update seconds on a different schedule
    if (++secCounter >= TIX_UPDATE_SEC) {
        secCounter = 0;
        timeSecond = second();

        ss = timeSecond / 10;
        s = timeSecond % 10;

        // Debug seconds
        /*Serial.print("s: ");
        Serial.print(s);
        Serial.print(" s % 5: ");
        Serial.print(s % 5);
        Serial.print(" n = (s % 5) - 1: ");
        int n = (s % 5);
        Serial.print(n);
        Serial.print(" (6 % 5) <= n through (9 % 5) <= n: ");
        Serial.print((6 % 5 <= n) ? '_' : 'o');
        Serial.print((7 % 5 <= n) ? '_' : 'o');
        Serial.print((8 % 5 <= n) ? '_' : 'o');
        Serial.print((9 % 5 <= n) ? '_' : 'o');
        Serial.println();*/
    }

    // Update LEDs
    int i;
    for (i = 0; i < hh; ++i) {
        leds[hhPos[i]] = CHSV(0, 255, 255);
    }

    for (i = 0; i < h; ++i) {
        leds[hPos[i]] = CHSV(160, 255, 255);
    }

    for (i = 0; i < mm; ++i) {
        leds[mmPos[i]] = CHSV(96, 255, 255);
    }

    for (i = 0; i < m; ++i) {
        leds[mPos[i]] = CHSV(64, 255, 255);
    }

    for (i = 0; i < ss; ++i) {
        leds[ssPos[i]] = CHSV(255, 0, 255);
    }

    for (i = 0; i < s; ++i) {
        /**
         * Pattern map for S (o is on, _ is off)
         * 
         * Though unintentional, this map is very
         * similar to how Morse code represents
         * digits.
         * 
         * 0: _ _ _ _ _    _
         * 1: o _ _ _ _     \
         * 2: o o _ _ _      \
         * 3: o o o _ _       > 1-5 are iterated in order
         * 4: o o o o _      /
         * 5: o o o o o    _/
         * 6: _ o o o o     \
         * 7: _ _ o o o      \ 6-9 can be calculated as the map
         * 8: _ _ _ o o      / for 5 with S % 5 off, in order
         * 9: _ _ _ _ o    _/
         */

         if (s > 5 && (i % 5) <= (s % 5) - 1) continue;
         
         leds[sPos[i]] = CHSV(255, 0, 255);
    }
}

void processSyncMessage() {
    unsigned long pctime;
    const unsigned long DEFAULT_TIME = 1357041600; // Jan 1 2013
    
    if (Serial.find(TIME_HEADER)) {
        pctime = Serial.parseInt();
        if (pctime >= DEFAULT_TIME) { // check the integer is a valid time (greater than Jan 1 2013)
            setTime(pctime); // Sync Arduino clock to the time received on the serial port
        }
    }
}

// Preform Fisher-Yates shuffle of array
void shuffle(int *o, int i) {
    for (int j, x; i; j = random(i), x = o[--i], o[i] = o[j], o[j] = x) {}
}
