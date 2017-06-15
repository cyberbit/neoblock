#include <CmdMessenger.h>
#include <TimeLib.h>
#include <FastLED.h>
#include <stdio.h>

#define BAUD            9600

#define TIME_HEADER     "T"
#define TIME_REQUEST    7

#define DEFAULT_TIME    1357041600 // Jan 1 2013

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

#define FF(x) (char*)F(x)

//typedef struct led_arr { CRGB leds[NUM_LEDS] } led_arr;

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

typedef struct led_arr { CRGB leds[NUM_LEDS]; } led_arr;

// Attach CmdMessenger
CmdMessenger cmd = CmdMessenger(Serial);

// Flag signaling client is ready
bool clientReady = false;

// Flags for animations
bool anim_fade = true;
bool anim_rainbow_border = false;
bool anim_tix = false;

bool anim_breathe = false;
uint8_t anim_breathe_hue = 0;
uint8_t anim_breathe_frame = 0;

bool anim_gx = false;

// Known commands
enum {
    CMD_READY,                  // 0
    CMD_ACK,                    // 1
    CMD_SUCCESS,                // 2
    CMD_ERROR,                  // 3
    CMD_TIME_SYNC,              // 4
    CMD_TIME_SYNC_RETURN,       // 5
    CMD_SET_BRIGHTNESS,         // 6
    CMD_COLOR_BREATHE,          // 7
    CMD_COLOR_BREATHE_CANCEL,   // 8
    CMD_GX,                     // 9
    CMD_GX_CANCEL,              // 10
    CMD_BINARY_TEST             // 11
};

const uint8_t BORDER_SIZE = 22;
const uint8_t border[BORDER_SIZE] = {
    0, 1, 2, 3, 4, 5, 6, 7,         // Top
    15, 23, 31,                     // Right
    39, 38, 37, 36, 35, 34, 33, 32, // Bottom
    24, 16, 8                       // Left
};

// Positions for binaryClock
const uint8_t hourPos[HOUR_BITS]        = {0, 1, 2, 3, 4};
const uint8_t minutePos[MINUTE_BITS]    = {8, 9, 10, 11, 12, 13};
const uint8_t secondPos[SECOND_BITS]    = {16, 17, 18, 19, 20, 21};

// Positions for tixClock
uint8_t hhPos[HH_TIX] = {1, 2, 3};
uint8_t hPos[H_TIX]   = {17, 18, 19, 25, 26, 27, 33, 34, 35};
uint8_t mmPos[MM_TIX] = {4, 5, 6, 12, 13, 14};
uint8_t mPos[M_TIX]   = {20, 21, 22, 28, 29, 30, 36, 37, 38};
uint8_t ssPos[S_TIX]  = {0, 8, 16, 24, 32};
uint8_t sPos[SS_TIX]  = {7, 15, 23, 31, 39};
uint8_t sendPos = 9;
uint8_t receivePos = 10;

void attachCommandCallbacks() {
    cmd.attach(onUnknownCmd);
    cmd.attach(CMD_READY, onReady);
//    cmd.attach(CMD_TIME_SYNC, onTimeSync);
//    cmd.attach(CMD_TIME_SYNC_RETURN, onTimeSyncReturn);
//    cmd.attach(CMD_SET_BRIGHTNESS, onSetBrightness);
//    cmd.attach(CMD_COLOR_BREATHE, onColorBreathe);
//    cmd.attach(CMD_COLOR_BREATHE_CANCEL, onColorBreatheCancel);
    cmd.attach(CMD_GX, onGx);
    cmd.attach(CMD_GX_CANCEL, onGxCancel);
    cmd.attach(CMD_BINARY_TEST, onBinaryTest);
}

// Unknown command received
void onUnknownCmd() {
    onGet();
    
    cmd.sendCmdStart(CMD_ERROR);
    cmd.sendCmdfArg("Unattached command: %d", cmd.commandID());
    cmd.sendCmdEnd();
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
//void onTimeSync() {
//    onGet();
//
//    // Get weekday and month strings
//    /*char dayString[4],
//       monthString[4];
//       
//    strcpy(dayString, dayShortStr(weekday()));
//    strcpy(monthString, monthShortStr(month()));*/
//
//    // Send current time
//    cmd.sendCmd(CMD_TIME_SYNC_RETURN, now());
//    onSend();
//    
//    // Send current formatted time (memory expensive)
//    /*cmd.sendCmdStart(CMD_SUCCESS);
//    cmd.sendCmdfArg("Current time is %02d:%02d:%02d %s %d %s %d",
//        hour(),
//        minute(),
//        second(),
//        dayString,
//        day(),
//        monthString,
//        year());
//    cmd.sendCmdEnd();
//    onSend();*/
//}

// Receive time sync
//void onTimeSyncReturn() {
//    onGet();
//    
//    unsigned long pctime = cmd.readBinArg<unsigned long>();
//    
//    cmd.sendCmd(CMD_ACK, F("Time sync received"));
//    onSend();
//
//    // Integer is a valid time (greater than Jan 1 2013)
//    if (pctime >= DEFAULT_TIME) {
//        setTime(pctime);
//
//        // Get weekday and month strings
//        /*char dayString[4],
//           monthString[4];
//           
//        strcpy(dayString, dayShortStr(weekday()));
//        strcpy(monthString, monthShortStr(month()));*/
//
//        // Send new formatted time (memory expensive)
//        /*cmd.sendCmdStart(CMD_SUCCESS);
//        cmd.sendCmdfArg("Time synced to %02d:%02d:%02d %s %d %s %d",
//            hour(),
//            minute(),
//            second(),
//            dayString,
//            day(),
//            monthString,
//            year());
//        cmd.sendCmdEnd();*/
//
//        cmd.sendCmd(CMD_SUCCESS, F("Time synced"));
//        onSend();
//        return;
//    }
//
//    // Integer is not a valid time
//    cmd.sendCmd(CMD_ERROR, F("Time is invalid, time not synced"));
//    onSend();
//}

//void onSetBrightness() {
//  onGet();
//
//  uint8_t brightness = cmd.readInt16Arg();
//  uint8_t brightnessConstraint = constrain(brightness, 0, 255);
//  
//  /*cmd.sendCmdStart(CMD_ACK);
//  cmd.sendCmdfArg("Setting brightness to %d (constrained to %d)...", brightness, brightnessConstraint);
//  cmd.sendCmdEnd();*/
//  cmd.sendCmd(CMD_ACK, F("Setting brightness..."));
//  onSend();
//
//  // Set brightness
//  FastLED.setBrightness(brightness);
//
//  /*cmd.sendCmdStart(CMD_SUCCESS);
//  cmd.sendCmdfArg("Brightness set to %d", brightnessConstraint);
//  cmd.sendCmdEnd();*/
//  cmd.sendCmd(CMD_SUCCESS, F("Brightness set"));
//  onSend();
//}

//void onColorBreathe() {
//    onGet();
//    
//    uint8_t hue = cmd.readInt16Arg();
//
//    /*cmd.sendCmdStart(CMD_ACK);
//    cmd.sendCmdfArg("Starting color breathe (hue %d)...", hue);
//    cmd.sendCmdEnd();*/
//    cmd.sendCmd(CMD_ACK, F("Starting color breathe..."));
//    onSend();
//
//    // Start animation
//    anim_breathe = true;
//    anim_breathe_hue = hue;
//
//    cmd.sendCmd(CMD_SUCCESS, F("Color breathe started"));
//    onSend();
//}

//void onColorBreatheCancel() {
//    onGet();
//
//    cmd.sendCmd(CMD_ACK);
//    onSend();
//
//    anim_breathe = false;
//    anim_breathe_frame = 0;
//    
//    cmd.sendCmd(CMD_SUCCESS, F("Color breathe cancelled"));
//    onSend();
//}

/*void onGx() {
    onGet();

    // First argument is length of graphic (up to NUM_LEDS)
    uint8_t length = cmd.readInt16Arg();
    uint8_t arg;

    // Read specified number of arguments
    for (int i = 0; i < length; ++i) {
        arg = cmd.readInt16Arg();
        /*cmd.sendCmdStart(CMD_ACK);
        cmd.sendCmdfArg("Received argument %d of %d: %d", i, length, arg);
        cmd.sendCmdEnd();
        onSend();*

        // Set LEDs to hue based on argument
        leds[i].setHue(arg);
    }

    anim_gx = true;

    cmd.sendCmd(CMD_SUCCESS, F("Graphics set"));
    onSend();
}*/

void onGx() {
    cmd.sendCmd(CMD_ACK, F("Reading graphics"));

    int length = cmd.readInt16Arg();
//    typedef struct led_arr { CRGB leds[NUM_LEDS]; } led_arr;
    
//    led_arr arg = cmd.readBinArg<led_arr>();

//    cmd.sendCmdStart(CMD_ACK);
//    cmd.sendCmdfArg("Length: %d", length);
//    cmd.sendCmdEnd();

    uint8_t arg[length];

    // Read some bytes! Should bypass CmdMessenger's loop
    Serial.readBytes((uint8_t*) arg, length);

    for (int i = 0; i < length; ++i) {
        cmd.sendCmd(CMD_ACK, (int)arg[i]);
    }

    /*cmd.sendCmdStart(CMD_ACK);
    cmd.sendCmdfArg("Length: %d", length);
    cmd.sendCmdEnd();*/
//    for (uint8_t i = 0; i < length; ++i) {
//        cmd.sendCmd(CMD_ACK, ((char*)leds)[i]);
//    }

//    for (int i = 0; i < length; ++i) {
        /*arg = cmd.readBinArg<uint8_t>();
        cmd.sendCmdStart(CMD_ACK);
        cmd.sendCmdfArg("Received %u", pixels[i]);
        cmd.sendCmdEnd();*/

        // Set LEDs to hue based on argument
//        leds[i].setHue((uint8_t) arg[i]);

        // Read raw bytes from Serial into LEDs
//        memcpy(leds, arg.leds, length);
//    }

    anim_gx = true;

    cmd.sendCmd(CMD_SUCCESS, F("Graphics set"));
}

void onGxCancel() {
    onGet();

    cmd.sendCmd(CMD_ACK);
    onSend();

    anim_gx = false;

    cmd.sendCmd(CMD_SUCCESS, F("Graphics cancelled"));
    onSend();
}

void onBinaryTest() {
    cmd.sendCmd(CMD_ACK, F("Reading graphics"));

    uint8_t length = cmd.readBinArg<uint8_t>();
    uint8_t arg;

    /*cmd.sendCmdStart(CMD_ACK);
    cmd.sendCmdfArg("Length: %d", length);
    cmd.sendCmdEnd();*/

    for (uint8_t i = 0; i < length; ++i) {
        arg = cmd.readBinArg<uint8_t>();
        /*cmd.sendCmdStart(CMD_ACK);
        cmd.sendCmdfArg("Received %u", pixels[i]);
        cmd.sendCmdEnd();*/

        // Set LEDs to hue based on argument
        leds[i].setHue(arg);
    }

    anim_gx = true;

    cmd.sendCmd(CMD_SUCCESS, F("Graphics set"));
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
    // Added parity for better accuracy
    Serial.begin(BAUD);

    // Configure commander
    cmd.printLfCr();
    attachCommandCallbacks();

    // Seed RNG with analog noise
    random16_set_seed(analogRead(0));
    
    // Set up LEDs
    FastLED.addLeds<NEOPIXEL, PIN>(leds, NUM_LEDS);
    FastLED.setBrightness(BRIGHTNESS);

    /*unsigned long pctime = DEFAULT_TIME;

    Serial.print("Representation of ");
    Serial.print(pctime);
    Serial.print(" in bits (high to low): ");

    for (int i = 31; i >= 0; --i) {
        Serial.print(bitRead(pctime, i));
        if (i == 24 || i == 16 || i == 8) Serial.print(" ");
    }*/

    // Request time sync
    //cmd.sendCmd(CMD_TIME_SYNC, F("Requesting time sync"));
    //onSend();

    // Set up default sync
    //setTime(1357042600);
}

// Handle CMD_READY
void hCMD_READY() {
    Serial.print(CMD_READY);
    Serial.print(";Arduino ready;\n");
    Serial.flush();
}

// Send CMD_ACK
void sCMD_ACK(char* msg) {
    Serial.print(CMD_ACK);
    Serial.print(";");
    Serial.print(msg);
    Serial.print(";\n");
}

// Send CMD_SUCCESS
void sCMD_SUCCESS(char* msg) {
    Serial.print(CMD_SUCCESS);
    Serial.print(";");
    Serial.print(msg);
    Serial.print(";\n");
    Serial.flush();
}

// Send CMD_ERROR
void sCMD_ERROR(char* msg) {
    Serial.print(CMD_ERROR);
    Serial.print(";");
    Serial.print(msg);
    Serial.print(";\n");
    Serial.flush();
}

// Handle CMD_TIME_SYNC
void hCMD_TIME_SYNC() {
    sCMD_TIME_SYNC_RETURN();
}

// Send CMD_TIME_SYNC_RETURN
void sCMD_TIME_SYNC_RETURN() {
    Serial.print(CMD_TIME_SYNC_RETURN);
    Serial.print(";");
    Serial.print(now());
    Serial.print(";\n");
    Serial.flush();
}

// Handle CMD_TIME_SYNC_RETURN
void hCMD_TIME_SYNC_RETURN() {
//    onGet();

    unsigned long pctime = 0;

    // Read bytes
    unsigned char buffer[50];
    Serial.readBytes(buffer, sizeof(pctime));

    // Parse bytes
    pctime = (unsigned long) buffer[0] << 24 |
             (unsigned long) buffer[1] << 16 |
             (unsigned long) buffer[2] << 8 |
             (unsigned long) buffer[3];

    sCMD_ACK("Time sync received");

//    sprintf(buffer, "Received: %lu", pctime);
//    sCMD_ACK(buffer);

//    for (int i = 0; i < 4; ++i) {
//        char buffer[4];
//        sprintf(buffer, "%d", pctime[i]);
//        
//        sCMD_ACK(buffer);
//    }
    Serial.flush();
//    onGet();
//    
//    unsigned long pctime = cmd.readBinArg<unsigned long>();
//    
//    cmd.sendCmd(CMD_ACK, F("Time sync received"));
//    onSend();
//
//    // Integer is a valid time (greater than Jan 1 2013)
//    if (pctime >= DEFAULT_TIME) {
//        setTime(pctime);
//
//        // Get weekday and month strings
//        /*char dayString[4],
//           monthString[4];
//           
//        strcpy(dayString, dayShortStr(weekday()));
//        strcpy(monthString, monthShortStr(month()));*/
//
//        // Send new formatted time (memory expensive)
//        /*cmd.sendCmdStart(CMD_SUCCESS);
//        cmd.sendCmdfArg("Time synced to %02d:%02d:%02d %s %d %s %d",
//            hour(),
//            minute(),
//            second(),
//            dayString,
//            day(),
//            monthString,
//            year());
//        cmd.sendCmdEnd();*/
//
//        cmd.sendCmd(CMD_SUCCESS, F("Time synced"));
//        onSend();
//        return;
//    }
//
//    // Integer is not a valid time
//    cmd.sendCmd(CMD_ERROR, F("Time is invalid, time not synced"));
//    onSend();
    
//    cmd.sendCmd(CMD_ACK, F("Time sync received"));
//    onSend();

    // Integer is a valid time (greater than Jan 1 2013)
    if (pctime >= DEFAULT_TIME) {
        setTime(pctime);

        // Get weekday and month strings
        /*char dayString[4],
           monthString[4];
           
        strcpy(dayString, dayShortStr(weekday()));
        strcpy(monthString, monthShortStr(month()));*/

        // Send new formatted time (memory expensive)
        /*cmd.sendCmdStart(CMD_SUCCESS);
        cmd.sendCmdfArg("Time synced to %02d:%02d:%02d %s %d %s %d",
            hour(),
            minute(),
            second(),
            dayString,
            day(),
            monthString,
            year());
        cmd.sendCmdEnd();*/

//        cmd.sendCmd(CMD_SUCCESS, F("Time synced"));
//        onSend();

        sCMD_SUCCESS("Time synced");
        return;
    }

    // Integer is not a valid time
//    cmd.sendCmd(CMD_ERROR, F("Time is invalid, time not synced"));
//    onSend();
    sCMD_ERROR("Time is invalid, time not synced");
}

void hCMD_COLOR_BREATHE() {
    // Sync command
    Serial.print(F("CMD_COLOR_BREATHE;"));
    Serial.flush();
    
    // Read hue
    uint8_t hue = Serial.read();

    // Sync command
    Serial.print(hue);
    Serial.flush();

    // Start animation
    anim_breathe = true;
    anim_breathe_hue = hue;

    // Sync command
    Serial.print(F(";END;\n"));

    // Wait for output to finish
    Serial.flush();
    
//    onGet();
//    
//    uint8_t hue = cmd.readInt16Arg();
//
//    /*cmd.sendCmdStart(CMD_ACK);
//    cmd.sendCmdfArg("Starting color breathe (hue %d)...", hue);
//    cmd.sendCmdEnd();*/
//    cmd.sendCmd(CMD_ACK, F("Starting color breathe..."));
//    onSend();
//
//    // Start animation
//    anim_breathe = true;
//    anim_breathe_hue = hue;
//
//    cmd.sendCmd(CMD_SUCCESS, F("Color breathe started"));
//    onSend();
}

void hCMD_COLOR_BREATHE_CANCEL() {
    // Sync command
    Serial.print(F("CMD_COLOR_BREATHE_CANCEL;"));
    Serial.flush();

    // Start animation
    anim_breathe = false;
    anim_breathe_frame = 0;

    // Sync command
    Serial.print(F("END;\n"));

    // Wait for output to finish
    Serial.flush();
    
//    onGet();
//
//    cmd.sendCmd(CMD_ACK);
//    onSend();
//
//    anim_breathe = false;
//    anim_breathe_frame = 0;
//    
//    cmd.sendCmd(CMD_SUCCESS, F("Color breathe cancelled"));
//    onSend();
}

/**
 * CMD_GX bytes:
 *      byte    name    value   description
 *      0       HEAD     9    Command header
 *      1       SIZE     0-255  Length of data
 *      2-n     DATA     0-255  Tuples of RGB bytes (R, G, B, R, G, B, etc.)
 */
void hCMD_GX() {
//    while (Serial.available() > 0) {
//        uint8_t tmp = Serial.read();
//        
//        char buffer[25];
//        sprintf(buffer, "Byte: %d", tmp);
//
//        Serial.print(buffer);
//        Serial.print(";");
//    }
//    Serial.print("\n");
//    return;

    // Sync command
    Serial.print(F("CMD_GX;"));
    Serial.flush();

    anim_gx = true;
    
    // Read length of data
    int length = Serial.read();

    // Sync command
    Serial.print(length);
    Serial.flush();
    
    // Initialize data storage
    uint8_t data[length];
    
    // Read bytes
    Serial.readBytes(data, length);

    // Iterate bytes and convert to LED format
    for (uint8_t i = 0; i < length; ++i) {
        /**
         * Bytes use 8-bit color format:
         * 
         *      Bit     7  6  5  4  3  2  1  0
         *      Data    R  R  R  G  G  G  B  B
         * 
         * The method below masks the appropriate bits for
         * each color, and then shifts them to be the most
         * significant bits.
         */
        uint8_t red = data[i] & B11100000;
        uint8_t green = data[i] & B11100;
        uint8_t blue = data[i] & B11;
        
        leds[i].r = red;
        leds[i].g = green << 3;
        leds[i].b = blue << 6;
    }

    // Sync command
    Serial.print(F(";END;\n"));

    // Wait for output to finish
    Serial.flush();
    
    // Output bytes
//    for (uint8_t i = 0; i < length; ++i) {
//        // Format string
//        char buffer[25];
//        sprintf(buffer, "Byte %d of %d: %d", i, length, data[i]);
//        
//        Serial.print(buffer);
//        Serial.print(";");
//    }
}

void hCMD_GX_CANCEL() {
    // Sync command
    Serial.print(F("CMD_GX_CANCEL;"));
    Serial.flush();

    anim_gx = false;

    // Sync command
    Serial.print(F("Graphics cancelled;END;\n"));

    // Wait for output to finish
    Serial.flush();
}

void loop() {
    // Process serial data
//    cmd.feedinSerialData();

    if (Serial.available() > 0) {
        uint8_t in = Serial.read();

        switch (in) {
            case CMD_READY: hCMD_READY(); break;
//            case CMD_ACK: fCMD_ACK(); break;
            case CMD_TIME_SYNC_RETURN: hCMD_TIME_SYNC_RETURN(); break;
            case CMD_COLOR_BREATHE: hCMD_COLOR_BREATHE(); break;
            case CMD_COLOR_BREATHE_CANCEL: hCMD_COLOR_BREATHE_CANCEL(); break;
            case CMD_GX: hCMD_GX(); break;
            case CMD_GX_CANCEL: hCMD_GX_CANCEL(); break;
                
            default:
                Serial.print(CMD_ERROR);
                Serial.print(";Unattached command;\n");
                break;
        }
        
//        Serial.print(Serial.read(), DEC);
    }
    
    // Time not set
    if (timeStatus() == timeNotSet) {
        anim_tix = false;
        
        if (clientReady) {
            anim_rainbow_border = true;
        }
    }

    // Time is set
    else {
        anim_tix = true;
        anim_rainbow_border = false;
    }

    anim();
    
    //rainbowBorder();
    //binaryClock();
    //tixClock();
}

void anim() {
    // When showing graphics, avoid spending cycles on other animations
    if (anim_gx) {
        /**
         * Graphics are read directly from Serial to LEDs to save memory.
         * Thus, there is no graphics display routine.
         */
    }

//    else {
//        FastLED.delay(1000/FPS);
//    }
    
    else {
        if (anim_fade) {
            fadeToBlackBy(leds, NUM_LEDS, 50);
        }
    
        if (anim_rainbow_border) {
            rainbowBorder();
        }
    
        if (anim_tix) {
            tixClockDisplay();
        }
        
        if (anim_breathe) {
            colorBreathe();
        }
        
    }
    
    FastLED.delay(1000/FPS);
    FastLED.show();
}

void rainbowBorder() {
    static uint8_t hue = 0;
    static int pos = 0;
    
    fadeToBlackBy(leds, NUM_LEDS, 50);
    leds[border[pos++]] = CHSV(hue++, 200, 255);
    if (pos > BORDER_SIZE - 1) pos = 0;
    
    // Display and delay
    /*FastLED.show();
    FastLED.delay(1000/FPS);*/
}

void colorBreathe() {
    static uint8_t step = 2;
    uint8_t brightness = ease8InOutApprox(anim_breathe_frame);

    if (anim_breathe_frame == 256 - step) step = -2;
    else if (anim_breathe_frame == 0) step = 2;

    anim_breathe_frame += step;

    for (int i = 0; i < NUM_LEDS; ++i) {
        leds[i] = nblend(leds[i], CHSV(anim_breathe_hue, 200, 255), brightness);
    }
}

/*void binaryClock() {
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
}*/

/*void binaryClockDisplay() {
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
}*/

//void tixClock() {
//    fadeToBlackBy(leds, NUM_LEDS, 50);
//
//    // Time not set
//    /*if (timeStatus() == timeNotSet) {
//        anim_rainbow_border = true
//    }
//
//    // Time is set
//    else {
//        tixClockDisplay();
//    }*/
//    
//    FastLED.show();
//    FastLED.delay(1000/FPS);
//}

//void wait() {
//    // Only show border if client is ready
//    if (clientReady) {
//        anim_rainbow_border = true;
//    }
//}

void tixClockDisplay() {
    static int counter = TIX_UPDATE;
    static int secCounter = TIX_UPDATE_SEC;

    static uint8_t timeHour, timeMinute, timeSecond,
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

/*void processSyncMessage() {
    unsigned long pctime;
    const unsigned long DEFAULT_TIME = 1357041600; // Jan 1 2013
    
    if (Serial.find(TIME_HEADER)) {
        pctime = Serial.parseInt();
        if (pctime >= DEFAULT_TIME) { // check the integer is a valid time (greater than Jan 1 2013)
            setTime(pctime); // Sync Arduino clock to the time received on the serial port
        }
    }
}*/

// Preform Fisher-Yates shuffle of array
void shuffle(int8_t *o, int i) {
    for (int j, x; i; j = random8(i), x = o[--i], o[i] = o[j], o[j] = x) {}
}
