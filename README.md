# NeoBlock
Alternative implementation of a TiX clock, with advanced options in a Python interface when connected over USB.

## Arduino requirements:
 - **NeoPixels**. The code is configured to use the NeoPixel Shield, but with some effort it can be configured for any pixel layout.
 - **Power supply**. I run my NeoBlock on low brightness settings using the Arduino power supply, but I do not recommend this. USB power is out of the question, it introduces strange artifacts in the LEDs.
 - **CmdMessenger**, for talking to the client.
 - **FastLED**, for pretty effects and better performance than the Adafruit NeoPixel library.
 - **Time**, for keeping track of time. This library also supports syncing to an external RTC, which would eliminate the need for a PC sync.

## Python requirements:
 - **Python 3.x**
 - **PyCmdMessenger**, for talking to the Arduino.
 - **Tkinter**, for the client visuals.
 - **time**, for time syncing.
 - **sched** (optional), for a Tkinter-less sync option
