# ------------------------------------------------------------------------------
# Python program using the library to interface with the arduino sketch above.
# ------------------------------------------------------------------------------

# Fix for Unicode characters
import win_unicode_console
win_unicode_console.enable()

import PyCmdMessenger, time, sched, os, threading, json, cryptography, array, serial, random, csv, numpy as np, re, copy
from pushbullet.pushbullet import PushBullet
from tkinter import *
from websocket import create_connection

# Grab Pushbullet API key from environment
API_KEY = os.environ.get('PUSHBULLET_API_KEY')
ENCRYPTION_PASSWORD = os.environ.get('PUSHBULLET_ENCRYPTION_PASSWORD')
ARDUINO_PORT = os.environ.get('ARDUINO_PORT')
# print("environment:")
# print(os.environ)

# List of command names These must be in the same order as in the sketch.
commands = [
    "CMD_READY",
    "CMD_ACK",
    "CMD_SUCCESS",
    "CMD_ERROR",
    "CMD_TIME_SYNC",
    "CMD_TIME_SYNC_RETURN",
    "CMD_SET_BRIGHTNESS",
    "CMD_COLOR_BREATHE",
    "CMD_COLOR_BREATHE_CANCEL",
    "CMD_GX",
    "CMD_GX_CANCEL",
    "CMD_BINARY_TEST"
]

# Set FPS
FPS = 12

s = sched.scheduler(time.time, time.sleep)

class App(Tk):
    def __init__(self, cmd, arduino):
        Tk.__init__(self)
        frame = Frame(self)
        frame.pack()
        
        # PyCmdMessenger instance
        self.cmd = cmd
        
        # Arduino instance
        self.arduino = arduino
        
        # Initial sync schedule is off
        self.doSync = False
        
        # Graphics thread ID
        self.gxThread = "stop"
        
        # Hues for apps
        self.appHues = {
            "default": 0,
            "com.snapchat.android": 64,
            "com.pushbullet.android": 96
        }
        
        # 256 color schemes for apps
        self.app256Schemes = {
            "default": {"fg": 255, "bg": 0},
            "com.snapchat.android": {"fg": 252, "bg": 108},
            "com.pushbullet.android": {"fg": 28, "bg": 8}
        }
        
        self.quit = Button(
           frame, text="QUIT", fg="red", command=frame.quit
        )
        self.quit.grid(columnspan=4, sticky=W+E)
        
        self.ready = Button(frame, text="CMD_READY", command=self.cmd_ready)
        self.ready.grid(row=1, sticky=W+E)
        
        self.ack = Button(frame, text="CMD_ACK", command=self.cmd_ack)
        self.ack.grid(row=1, column=1, sticky=W+E)
        
        self.success = Button(frame, text="CMD_SUCCESS", command=self.cmd_success)
        self.success.grid(row=1, column=2, sticky=W+E)
        
        self.error = Button(frame, text="CMD_ERROR", command=self.cmd_error)
        self.error.grid(row=1, column=3, sticky=W+E)
        
        self.time_sync = Button(frame, text="CMD_TIME_SYNC", command=self.cmd_time_sync)
        self.time_sync.grid(row=2, column=1, sticky=W+E)
        
        self.time_sync_return = Button(frame, text="CMD_TIME_SYNC_RETURN", command=self.cmd_time_sync_return)
        self.time_sync_return.grid(row=2, column=2, sticky=W+E)
        
        self.start_schedule = Button(frame, text="Schedule sync", command=self.startSchedule)
        self.start_schedule.grid(row=3, column=1, sticky=W+E)
        
        self.stop_schedule = Button(frame, text="Unschedule sync", command=self.stopSchedule)
        self.stop_schedule.grid(row=3, column=2, sticky=W+E)
        
        self.brightness_off = Button(frame, text="Display off", command=lambda: self.cmd_set_brightness(0))
        self.brightness_off.grid(row=4, sticky=W+E)
        
        self.brightness_low = Button(frame, text="Low brightness (32)", command=lambda: self.cmd_set_brightness(32))
        self.brightness_low.grid(row=4, column=1, sticky=W+E)
        
        self.brightness_normal = Button(frame, text="Normal brightness (64)", command=lambda: self.cmd_set_brightness(64))
        self.brightness_normal.grid(row=4, column=2, sticky=W+E)
        
        self.brightness_high = Button(frame, text="High brightness (128)", command=lambda: self.cmd_set_brightness(128))
        self.brightness_high.grid(row=4, column=3, sticky=W+E)
        
        self.pushbullet_test = Button(frame, text="Start PushBullet watchdog", command=self.pushbulletWatchdog)
        self.pushbullet_test.grid(row=5, sticky=W+E)
        
        self.binary_arg_test = Button(frame, text="Test binary argument", command=self.cmd_binary_test)
        self.binary_arg_test.grid(row=5, column=1, sticky=W+E)
        
        self.gx_text_test = Button(frame, text="Test experimental marquee", command=self.cmd_text_test)
        self.gx_text_test.grid(row=5, column=2, sticky=W+E)
        
        # self.gx_test = Button(frame, text="Test graphics", command=self.cmd_gx_test)
        # self.gx_test.grid(row=5, column=2, sticky=W+E)
        
        self.gx_ex_test = Button(frame, text="Test experimental graphics", command=self.cmd_gx_ex)
        self.gx_ex_test.grid(row=3, column=3, sticky=W+E)
        
        self.gx_cancel = Button(frame, text="Cancel graphics", command=self.cmd_gx_cancel)
        self.gx_cancel.grid(row=5, column=3, sticky=W+E)
        
        self.color_breathe_cancel = Button(frame, text="Cancel color breathe", command=self.cmd_color_breathe_cancel)
        self.color_breathe_cancel.grid(row=6, sticky=W+E)
        
        self.color_breathe_red = Button(frame, text="Color breathe (red)", command=lambda: self.cmd_color_breathe(0))
        self.color_breathe_red.grid(row=6, column=1, sticky=W+E)
        
        self.color_breathe_green = Button(frame, text="Color breathe (green)", command=lambda: self.cmd_color_breathe(96))
        self.color_breathe_green.grid(row=6, column=2, sticky=W+E)
        
        self.color_breathe_blue = Button(frame, text="Color breathe (blue)", command=lambda: self.cmd_color_breathe(160))
        self.color_breathe_blue.grid(row=6, column=3, sticky=W+E)
        
        # Ready signal (plus dramatic pause)
        # self.cmd_ready()
        # time.sleep(2)
        
        # Auto-schedule
        self.startSchedule()
        
        # Start PushBullet watchdog
        self.pushbulletWatchdog()
    
    def cmd_ready(self):
        print(" * CMD_READY: Client ready")
        
        self.sendCmd("CMD_READY")
        
        # Wait for everything to write
        self.arduino.comm.flush()
        
        print(self.readCmd()) # CMD_READY
    
    def cmd_ack(self):
        print(" * CMD_ACK: Command acknowledged")
        
        self.sendCmd("CMD_ACK", list(b'Command acknowledged'))
        
        # Wait for everything to write
        self.arduino.comm.flush()
        
        print(self.readCmd()) # CMD_ACK
        # self.cmd.send("CMD_ACK", "Command acknowledged")
        # print(self.cmd.receive())
    
    def cmd_success(self):
        print(" * CMD_SUCCESS: Command successful!")
        self.cmd.send("CMD_SUCCESS", "Command successful!")
        print(self.cmd.receive())
    
    def cmd_error(self):
        print(" * CMD_ERROR: Command encountered an error")
        self.cmd.send("CMD_ERROR", "Command encountered an error")
        print(self.cmd.receive())
    
    def cmd_time_sync(self):
        print(" * CMD_TIME_SYNC: Requesting current time")
        self.cmd.send("CMD_TIME_SYNC", "Requesting current time")
        print(self.cmd.receive("s")) # CMD_TIME_SYNC_RETURN
        # print(self.cmd.receive("s")) # CMD_SUCCESS
    
    def cmd_time_sync_return(self):
        # print(" * CMD_TIME_SYNC_RETURN: Sending time sync...")
        # self.cmd.send("CMD_TIME_SYNC_RETURN", int(time.time()) + 60 * 60 * -5) # adjust for UTC-5
        # print(self.cmd.receive("s")) # CMD_ACK
        # print(self.cmd.receive("s")) # CMD_SUCCESS or CMD_ERROR
        print(" * CMD_TIME_SYNC_RETURN: Sending time sync...")
        
        # Create bytes for timestamp
        # (via https://stackoverflow.com/a/6188017/3402854)
        timestamp = [(int(time.time()) + 60 * 60 * -5 >> i & 255) for i in (24,16,8,0)]
        
        self.arduino.write(array.array('B', [
            # Command header
            commands.index("CMD_TIME_SYNC_RETURN")
        ] + timestamp).tostring())
        
        # Wait for everything to write
        self.arduino.comm.flush()
        
        # Data bytes
        # 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255, 255,255,255,
        # 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255, 255,255,255, 0,0,0, 255,0,0,
        # 0,0,255, 255,0,255, 0,255,255, 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0,
        # 0,255,255, 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255,
        # 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255,
        
        print(self.readCmd()) # CMD_ACK
        # print(self.readCmd()) # CMD_ACK (debug)
        # print(self.readCmd()) # CMD_ACK (debug)
        # print(self.readCmd()) # CMD_ACK (debug)
        # print(self.readCmd()) # CMD_ACK (debug)
        print(self.readCmd()) # CMD_SUCCESS or CMD_ERROR
    
    def cmd_set_brightness(self, v):
        print(" * CMD_SET_BRIGHTNESS: Sending brightness value...")
        
        # Send command
        self.sendCmd("CMD_SET_BRIGHTNESS", [v])
        
        # Receive response
        print(self.readCmd())
        
        # print(" * CMD_SET_BRIGHTNESS: Sending brightness value...")
        # self.cmd.send("CMD_SET_BRIGHTNESS", v)
        # print(self.cmd.receive()) # CMD_ACK
        # print(self.cmd.receive()) # CMD_SUCCESS
    
    def cmd_color_breathe(self, hue):
        print(" * CMD_COLOR_BREATHE: Starting color breathe...")
        
        # Send command
        self.arduino.write(array.array('B', [
            # Command header
            commands.index("CMD_COLOR_BREATHE"),
            
            # Hue
            hue
        ]).tostring())
        
        # Wait for everything to write
        self.arduino.comm.flush()
        
        # Read command
        result = self.readCmd()
        
        # Output lines
        print(*result, sep='\n')
    
    def cmd_color_breathe_cancel(self):
        print(" * CMD_COLOR_BREATHE_CANCEL: Cancelling color breathe...")
        
        # Send command
        self.arduino.write(array.array('B', [
            # Command header
            commands.index("CMD_COLOR_BREATHE_CANCEL")
        ]).tostring())
        
        # Wait for everything to write
        self.arduino.comm.flush()
        
        # Read command
        result = self.readCmd()
        
        # Output lines
        print(*result, sep='\n')
    
    def cmd_binary_test(self):
        print(" * CMD_BINARY_TEST: Sending binary arguments...")
        for i in range(0, 40):
            # Make array of 40 zeros
            arr = [0] * 40
            
            # Set single pixel to cycled hue
            arr[i] = i * 5
            
            self.cmd.send("CMD_BINARY_TEST", 40, *arr)
            print(self.cmd.receive()) # CMD_ACK (Reading graphics)
            print(self.cmd.receive()) # CMD_SUCCESS (Graphics set)
    
    def cmd_gx_test(self):
        print(" * CMD_GX: Testing graphics...")
        
        num_leds = 10
        
        for i in range(0, num_leds):
            print("start cmd")
            
            print("send CMD_GX")
            self.cmd.send("CMD_GX", num_leds*3)
            
            print(self.cmd.receive()) # CMD_ACK (Reading graphics)
            # print(self.cmd.receive()) # CMD_ACK (Length)
            
            # Make array of num_leds rgb(0, 0, 0) pixels
            arr = [[0, 0, 0]] * num_leds
            
            # Set single pixel to watch
            arr[i] = [255, 255, 255]
            
            print("write bytes")
            self.cmd.board.write(array.array('B', [item for sublist in arr for item in sublist]).tostring())
            
            # 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255, 255,255,255,
            # 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255, 255,255,255, 0,0,0, 255,0,0,
            # 0,0,255, 255,0,255, 0,255,255, 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0,
            # 0,255,255, 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255,
            # 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255,
            
            for j in range(0, num_leds):
                print(self.cmd.receive()) # CMD_ACK (byte echo)
            
            print("receive success")
            print(self.cmd.receive()) # CMD_SUCCESS
        
        # self.cmd.board.write(b'9,3,\xff\x00\x00;')
        # 
        # print(self.cmd.receive()) # CMD_ACK (Reading graphics)
        # print(self.cmd.receive()) # CMD_ACK (Length)
        # print(self.cmd.receive()) # CMD_ACK (char 1)
        # print(self.cmd.receive()) # CMD_ACK (char 2)
        # print(self.cmd.receive()) # CMD_ACK (char 3)
        # print(self.cmd.receive()) # CMD_SUCCESS
        
        # Manually send bytes
        # self.cmd.board.write(array.array('B', [
        #     1, 5, 10, 15, 20, 25, 30, 35,
        #     40, 45, 50, 55, 60, 65, 70, 75,
        #     80, 85, 90, 95, 100, 105, 110, 115,
        #     120, 125, 130, 135, 140, 145, 150, 155,
        #     160, 165, 170, 175, 180, 185, 190, 195
        # ]).tostring())
        # self.cmd.board.write(array.array('B', [
        #     255,0,0, 0,255,0, 0,0,255
        # ]).tostring())
    
    def cmd_gx_ex(self):
        print(" * Testing experimental CMD_GX...")
        
        def _thread(tid):
            print(" * * cmd_gx_ex: Thread", tid, "started.")
            num_leds = 40
            
            # Wave of colors to try
            wave = [
                [0, 0, 1],
                [1, 0, 1],
                [2, 0, 1],
                [3, 0, 1],
                [4, 0, 1],
                [5, 0, 1],
                [6, 0, 1],
                [7, 0, 1],
            ]
            
            # Load graphic
            graphicFile = open('bootup.csv')
            
            # Parse graphic
            graphicCsv = csv.reader(graphicFile)
            
            graphic = []
            
            for frame in graphicCsv:
                newFrame = []
                
                for color in frame:
                    newFrame.append(int(color))
                    
                graphic.append(newFrame)
            
            frames = len(graphic)
            
            start = time.time()
            for i in range(0, frames):
                # print("tid: ", tid, " gxThread: ", gxThread)
                # Run thread until priority is removed
                if (tid == self.gxThread):
                    # Bytes use 8-bit color format:
                    # 
                    #       Bit     7  6  5  4  3  2  1  0
                    #       Data    R  R  R  G  G  G  B  B
                    #
                    # This allows the following values:
                    #
                    #       Red     0-7     << 5
                    #       Green   0-7     << 2
                    #       Blue    0-3     << 0
                    #
                    # Bitwise AND them together to get the 8-bit color.
                    
                    # Make array of num_leds 8-bit color pixels
                    # leds = [0] * num_leds
                    
                    # Make array of num_leds random 8-bit color pixels
                    # leds = random.sample(range(0, 255), num_leds)
                    
                    # Set single pixel to some fancy color idk
                    # pixel = wave[i % 8]
                    # leds[i] = (pixel[0] << 5) | (pixel[1] << 2) | pixel[2];
                    # print(leds[i])
                    
                    # Read next frame of graphic
                    leds = graphic[i]
                    
                    # Send command
                    # 
                    # Byte format:
                    #   0       CMD_GX
                    #   1       length
                    #   2-n     data bytes
                    self.sendCmd("CMD_GX", [num_leds] + leds)
                    
                    # Wait for everything to write
                    # self.arduino.comm.flush()
                    
                    # Data bytes
                    # 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255, 255,255,255,
                    # 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255, 255,255,255, 0,0,0, 255,0,0,
                    # 0,0,255, 255,0,255, 0,255,255, 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0,
                    # 0,255,255, 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255,
                    # 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255,
                    
                    # Read command
                    # result = self.readCmd()
                    
                    # Output lines
                    # print(*result, sep='\n')
                    
                    # Sleep a little for FPS limiting
                    time.sleep(1/FPS)
            
            # Flush input buffer
            self.arduino.comm.flushInput()
            
            totalTime = time.time() - start
            
            print(" * * cmd_gx_ex: Thread", tid, "stopped. Desired FPS:", FPS, "Actual FPS:", frames / totalTime)
        
        # Generate thread ID
        # Can't use built-in thread ID as thread is started before ID can be saved
        tid = "%04x" % random.randrange(0x0, 0xffff)
        self.gxThread = tid
        
        # Initialize thread
        print(" * Starting cmd_gx_ex thread...")
        watchdog = threading.Thread(target=lambda: _thread(tid))
        watchdog.daemon = True
        watchdog.start()
    
    def cmd_text_test(self):
        print("Testing experimental text graphics...")
        
        def _thread(tid):
            print(" * * cmd_text_test: Thread", tid, "started.")
            # nt = NeoText(["*pad8", *("Angie Beeson (5)".upper()), "*pad8"], fg=255, bg=0)
            pad8 = NeoText(["*pad8"])
            red = NeoText([*"RED"], fg=224, bg=96)
            orange = NeoText([*"ORANGE"], fg=240, bg=104)
            yellow = NeoText([*"YELLOW"], fg=252, bg=108)
            green = NeoText([*"GREEN"], fg=28, bg=12)
            blue = NeoText([*"BLUE"], fg=3, bg=1)
            indigo = NeoText([*"INDIGO"], fg=75, bg=1)
            violet = NeoText([*"VIOLET"], fg=99, bg=34)
            
            # Random colored string
            # stringy = [*"RANDOM COLORS ARE FUN", "*pad8"]
            # nt = NeoText(["*pad8"])
            # for letter in stringy:
            #     nt += NeoText([letter], fg=random.randint(0, 255), bg=random.randint(0, 255))
            
            nt = pad8 + red + orange + yellow + green + blue + indigo + violet + pad8
            testText = nt.marquee
            # testText = NeoText(["*pad8", *("my career as a Walmart greeter was cut short when the manager noticed me singing \"Welcome to the Jungle\" to every customer").upper(), "*pad8"]).marquee
            
            num_leds = 40
            width = 8
            
            # Number of frames
            frames = testText.shape[1] - (width - 1)
            
            start = time.time()
            for i in range(0, frames):
                # print("tid: ", tid, " self.gxThread: ", self.gxThread)
                if (tid == self.gxThread):
                    # Read next frame of graphic
                    leds = testText[:,i:i+width].flatten().tolist()
                    
                    # Send command
                    # 
                    # Byte format:
                    #   0       CMD_GX
                    #   1       length
                    #   2-n     data bytes
                    self.sendCmd("CMD_GX", [num_leds] + leds)
                    
                    # Wait for everything to write
                    # self.arduino.comm.flush()
                    
                    # Data bytes
                    # 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255, 255,255,255,
                    # 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255, 255,255,255, 0,0,0, 255,0,0,
                    # 0,0,255, 255,0,255, 0,255,255, 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0,
                    # 0,255,255, 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255,
                    # 255,255,255, 0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255,
                    
                    # Read command
                    # result = self.readCmd()
                    
                    # Output lines
                    # print(*result, sep='\n')
                    
                    # Sleep a little for FPS limiting
                    time.sleep(1/FPS)
            
            # Flush input buffer
            self.arduino.comm.flushInput()
            
            totalTime = time.time() - start
            
            print(" * * cmd_text_test: Thread", tid, "stopped. Desired FPS:", FPS, "Actual FPS:", frames / totalTime)
        
        # Generate thread ID
        # Can't use built-in thread ID as thread is started before ID can be saved
        tid = "%04x" % random.randrange(0x0, 0xffff)
        self.gxThread = tid
        
        # Initialize thread
        print(" * Starting cmd_test_text thread...")
        watchdog = threading.Thread(target=lambda: _thread(tid))
        watchdog.daemon = True
        watchdog.start()
    
    def cmd_text(self, msg, options):
        # Generate thread id
        tid = "%04x" % random.randrange(0x0, 0xffff)
        self.gxThread = tid
        
        print(" * Displaying marquee...")
        
        nt = NeoText(["*pad8", *msg.upper(), "*pad8"], **options).marquee
        
        num_leds = 40
        width = 8
        
        # Number of frames
        frames = nt.shape[1] - (width - 1)
        
        start = time.time()
        for i in range(0, frames):
            if (tid == self.gxThread):
                # Read next frame of graphic
                leds = nt[:,i:i+width].flatten().tolist()
                
                # Send command
                # 
                # Byte format:
                #   0       CMD_GX
                #   1       length
                #   2-n     data bytes
                self.sendCmd("CMD_GX", [num_leds] + leds)
                
                # Sleep a little for FPS limiting
                time.sleep(1/FPS)
        
        # Flush input buffer
        self.arduino.comm.flushInput()
        
        # Cancel graphics
        self.cmd_gx_cancel()
    
    def cmd_gx_cancel(self):
        print(" * CMD_GX_CANCEL: Cancelling graphics...")
        
        # Close graphics thread
        self.gxThread = "stop"
        
        # Send command
        self.sendCmd("CMD_GX_CANCEL");
        
        # Wait for everything to write
        self.arduino.comm.flush()
        
        # Read command
        result = self.readCmd()
        
        # Output lines
        print(*result, sep='\n')
    
    def startSchedule(self):
        print(" * Time sync scheduled");
        self.doSync = True
        # s.enter(1, 1, self.scheduleSync, (s,))
        # s.run()
        self.scheduleSync(s)
    
    def stopSchedule(self):
        print(" * Time sync unscheduled");
        self.doSync = False
    
    def scheduleSync(self, sc):
        if self.doSync:
            # self.cmd_time_sync() # Get current time for comparison
            self.cmd_time_sync_return()
            # s.enter(1*60*60, 1, self.scheduleSync, (sc,))
            # time.sleep(1*60*60)
            # self.scheduleSync()
            self.after(1*60*60*1000, lambda: self.scheduleSync(sc))
            # self.after(3000, lambda: self.scheduleSync(sc))
    
    def sendCmd(self, cmd, arr=None):
        if arr is None:
            arr = []
        
        self.arduino.write(array.array('B', [commands.index(cmd)] + arr).tostring())
    
    def readCmd(self):
        # Read as many bytes as possible
        raw_msg = []
        msg_lines = []
        
        # print(self.arduino.readline())
        
        # return
    
        while True:
            # break
            # print("loopy")
            tmp = self.arduino.read()
            
            # print("post read")
            
            # print(tmp)
            
            # End of command
            if tmp == b'\n' or tmp == b'':
                break
            
            elif tmp == b';':
                # msg_lines.append(b''.join(raw_msg).decode("ascii"))
                msg_lines.append(b''.join(raw_msg))
                raw_msg = []
            
            else:
                raw_msg.append(tmp)
        
        return msg_lines
    
    def pushbulletWatchdog(self):
        print(" * Connecting to PushBullet...")
        pb = PushBullet(API_KEY, {'https': os.environ.get('http_proxy')})
        
        # Grab user
        self.user = pb.getUser()
        
        print(" * Processing encryption keys...")
        
        # Set up encryption key
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.user["iden"].encode("ASCII"),
            iterations=30000,
            backend=default_backend()
        )
        
        self.encryption_key = kdf.derive(ENCRYPTION_PASSWORD.encode("UTF-8"))
        
        print(" * Starting watchdog...")
        
        # Initialize thread
        watchdog = threading.Thread(target=lambda: pb.realtime(self.handlePush))
        watchdog.daemon = True
        watchdog.start()
    
    def handlePush(self, data):
        push = None
        
        # Only handle ephemerals
        if data['type'] == "push":
            if data['push']['encrypted'] == True:
                print(" $ Encoded push received. Decoding...")
                
                push = json.loads(self.decryptData(data['push']['ciphertext']))
            else:
                push = data['push']
            
            if push['type'] == "mirror":
                print(" $ New notification!")
                print(" $   ID:", push['notification_id'])
                print(" $   App:", push['package_name'])
                print(" $   Title:", push['title'])
                print(" $   Body:", push['body'])
                
                # Save last push
                self.push = push
                
                # Send color breathe
                self.cmd_color_breathe(self.appToHue(self.push['package_name']))
                
                # Send text marquee
                self.cmd_text(push['title'], self.appTo256Scheme(self.push['package_name']))
            
            elif push['type'] == "dismissal":
                print(" $ Dismissed notification!")
                print(" $   ID:", push['notification_id'])
                print(" $   App:", push['package_name'])
                
                # Cancel color breathe
                self.cmd_color_breathe_cancel()
    
    def appToHue(self, package_name):
        if package_name in self.appHues:
            return self.appHues[package_name]
        else:
            return self.appHues['default']
    
    def appTo256Scheme(self, package_name):
        if package_name in self.app256Schemes:
            return self.app256Schemes[package_name]
        else:
            return self.app256Schemes['default']
    
    def decryptData(self, data):
        assert self.encryption_key
        
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        from binascii import a2b_base64
        
        key = self.encryption_key
        encoded_message = a2b_base64(data)
        
        version = encoded_message[0:1]
        tag = encoded_message[1:17]
        initialization_vector = encoded_message[17:29]
        encrypted_message = encoded_message[29:]
        
        if version != b"1":
            raise Exception(" $ Invalid version!")
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(initialization_vector, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        decrypted = decryptor.update(encrypted_message) + decryptor.finalize()
        decrypted = decrypted.decode()
        
        return(decrypted)

class NeoText():
    symbols = {
        "*letsp": np.array([
            [0],
            [0],
            [0],
            [0],
            [0],
        ]),
        "*pad8": np.array([
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]),
        " ": np.array([
            [0, 0],
            [0, 0],
            [0, 0],
            [0, 0],
            [0, 0],
        ]),
        "A": np.array([
            [0, 1, 0],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
        ]),
        "B": np.array([
            [1, 1, 0],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 0],
        ]),
        "C": np.array([
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [0, 1, 1],
        ]),
        "D": np.array([
            [1, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 0],
        ]),
        "E": np.array([
            [0, 1, 1],
            [1, 0, 0],
            [1, 1, 0],
            [1, 0, 0],
            [0, 1, 1],
        ]),
        "F": np.array([
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 0],
            [1, 0, 0],
            [1, 0, 0],
        ]),
        "G": np.array([
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 1],
            [1, 1, 1],
        ]),
        "H": np.array([
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
        ]),
        "I": np.array([
            [1, 1, 1],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 1],
        ]),
        "J": np.array([
            [1, 1, 1],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 0],
        ]),
        "K": np.array([
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
        ]),
        "L": np.array([
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0],
            [1, 1, 1],
        ]),
        "M": np.array([
            [1, 0, 1],
            [1, 1, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
        ]),
        "N": np.array([
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
        ]),
        "O": np.array([
            [0, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0],
        ]),
        "P": np.array([
            [1, 1, 0],
            [1, 0, 1],
            [1, 1, 0],
            [1, 0, 0],
            [1, 0, 0],
        ]),
        "Q": np.array([
            [0, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 1],
        ]),
        "R": np.array([
            [1, 1, 0],
            [1, 0, 1],
            [1, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
        ]),
        "S": np.array([
            [0, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 0],
        ]),
        "T": np.array([
            [1, 1, 1],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
        ]),
        "U": np.array([
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
        ]),
        "V": np.array([
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0],
        ]),
        "W": np.array([
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 1, 1],
            [1, 0, 1],
        ]),
        "X": np.array([
            [1, 0, 1],
            [1, 0, 1],
            [0, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
        ]),
        "Y": np.array([
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 1, 0],
            [0, 1, 0],
        ]),
        "Z": np.array([
            [1, 1, 1],
            [0, 0, 1],
            [0, 1, 0],
            [1, 0, 0],
            [1, 1, 1],
        ]),
        "0": np.array([
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
        ]),
        "1": np.array([
            [1, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 1],
        ]),
        "2": np.array([
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
        ]),
        "3": np.array([
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
        ]),
        "4": np.array([
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 0, 1],
            [0, 0, 1],
        ]),
        "5": np.array([
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
        ]),
        "6": np.array([
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ]),
        "7": np.array([
            [1, 1, 1],
            [0, 0, 1],
            [0, 0, 1],
            [0, 0, 1],
            [0, 0, 1],
        ]),
        "8": np.array([
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ]),
        "9": np.array([
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
        ]),
        "?": np.array([
            [1, 1, 1],
            [0, 0, 1],
            [0, 1, 0],
            [0, 0, 0],
            [0, 1, 0],
        ]),
    }
    
    def __init__(self, *text, fg=255, bg=0):
        self.text = text
        self.marquee = np.hstack([*map(self.char, *text)])
        
        # Set colors
        for x in np.nditer(self.marquee, op_flags=['readwrite']):
            # Background mask
            if (x == 0): x[...] = bg
            
            # Foreground mask
            elif (x == 1): x[...] = fg
    
    def __add__(self, other):
        newText = copy.copy(self)
        newText.text = self.text + other.text
        newText.marquee = np.hstack((self.marquee, other.marquee))
        return newText
    
    def char(self, sym):
        # Replace unknown symbols with "?"
        value = NeoText.symbols.get(sym)
        if (value is None): value = NeoText.symbols.get("?")
        
        # Add letter spacing to non-special symbols
        if (not re.match(r'^\*.*', sym)):
            value = np.hstack((value, NeoText.symbols.get("*letsp")))
        
        return value

print(" * Connecting to Arduino...")

# Initialize an ArduinoBoard instance.  This is where you specify baud rate and
# serial timeout.  If you are using a non ATmega328 board, you might also need
# to set the data sizes (bytes for integers, longs, floats, and doubles).  
arduino = PyCmdMessenger.ArduinoBoard(ARDUINO_PORT,baud_rate=9600)

# Initialize the messenger
# cmd = PyCmdMessenger.CmdMessenger(arduino,commands)

# Run app
app = App(None, arduino)
app.mainloop()
