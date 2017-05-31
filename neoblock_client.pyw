# ------------------------------------------------------------------------------
# Python program using the library to interface with the arduino sketch above.
# ------------------------------------------------------------------------------

import PyCmdMessenger, time, sched, os, threading, json, cryptography, array
from pushbullet.pushbullet import PushBullet
from tkinter import *
from websocket import create_connection

# Grab Pushbullet API key from environment
API_KEY = os.environ.get('PUSHBULLET_API_KEY')
ENCRYPTION_PASSWORD = os.environ.get('PUSHBULLET_ENCRYPTION_PASSWORD')
# print("environment:")
# print(os.environ)

s = sched.scheduler(time.time, time.sleep)

class App(Tk):
    def __init__(self, cmd):
        Tk.__init__(self)
        frame = Frame(self)
        frame.pack()
        
        # PyCmdMessenger instance
        self.cmd = cmd
        
        # Initial sync schedule is off
        self.doSync = False
        
        # Hues for apps
        self.appHues = {
            "default": 0,
            "com.snapchat.android": 64,
            "com.pushbullet.android": 96
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
        
        self.gx_test = Button(frame, text="Test graphics", command=self.cmd_gx_test)
        self.gx_test.grid(row=5, column=2, sticky=W+E)
        
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
        self.cmd_ready()
        time.sleep(2)
        
        # Auto-schedule
        self.startSchedule()
    
    def cmd_ready(self):
        print(" * CMD_READY: Client ready")
        self.cmd.send("CMD_READY", "Client ready")
        print(self.cmd.receive())
    
    def cmd_ack(self):
        print(" * CMD_ACK: Command acknowledged")
        self.cmd.send("CMD_ACK", "Command acknowledged")
        print(self.cmd.receive())
    
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
        print(" * CMD_TIME_SYNC_RETURN: Sending time sync...")
        self.cmd.send("CMD_TIME_SYNC_RETURN", int(time.time()) + 60 * 60 * -5) # adjust for UTC-5
        print(self.cmd.receive("s")) # CMD_ACK
        print(self.cmd.receive("s")) # CMD_SUCCESS or CMD_ERROR
    
    def cmd_set_brightness(self, v):
        print(" * CMD_SET_BRIGHTNESS: Sending brightness value...")
        self.cmd.send("CMD_SET_BRIGHTNESS", v)
        print(self.cmd.receive()) # CMD_ACK
        print(self.cmd.receive()) # CMD_SUCCESS
    
    def cmd_color_breathe(self, v):
        print(" * CMD_COLOR_BREATHE: Sending color breathe...")
        self.cmd.send("CMD_COLOR_BREATHE", v)
        print(self.cmd.receive()) # CMD_ACK
        print(self.cmd.receive()) # CMD_SUCCESS
    
    def cmd_color_breathe_cancel(self):
        print(" * CMD_COLOR_BREATHE_CANCEL: Cancelling color breathe...")
        self.cmd.send("CMD_COLOR_BREATHE_CANCEL")
        print(self.cmd.receive()) # CMD_ACK
        print(self.cmd.receive()) # CMD_SUCCESS
    
    def cmd_binary_test(self):
        print(" * CMD_BINARY_TEST: Sending binary arguments...")
        self.cmd.send("CMD_BINARY_TEST", 40,
            0, 5, 10, 15, 20, 25, 30, 35,
            40, 45, 50, 55, 60, 65, 70, 75,
            80, 85, 90, 95, 100, 105, 110, 115,
            120, 125, 130, 135, 140, 145, 150, 155,
            160, 165, 170, 175, 180, 185, 190, 195
        )
        print(self.cmd.receive()) # CMD_ACK (Reading graphics)
        print(self.cmd.receive()) # CMD_SUCCESS (Graphics set)
    
    def cmd_gx_test(self):
        print(" * CMD_GX: Sending data as string...")
        self.cmd.send("CMD_GX", 3, "\x00\x7f\x7f")
        
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
        
        print(self.cmd.receive()) # CMD_ACK (Reading graphics)
        print(self.cmd.receive()) # CMD_ACK (Length)
        print(self.cmd.receive()) # CMD_ACK (char 1)
        print(self.cmd.receive()) # CMD_ACK (char 2)
        print(self.cmd.receive()) # CMD_ACK (char 3)
        print(self.cmd.receive()) # CMD_SUCCESS
    
    def cmd_gx_cancel(self):
        print(" * CMD_GX_CANCEL: Cancelling graphics...")
        self.cmd.send("CMD_GX_CANCEL");
        print(self.cmd.receive()) # CMD_ACK
        print(self.cmd.receive()) # CMD_SUCCESS
    
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
            self.cmd_time_sync() # Get current time for comparison
            self.cmd_time_sync_return()
            # s.enter(1*60*60, 1, self.scheduleSync, (sc,))
            # time.sleep(1*60*60)
            # self.scheduleSync()
            self.after(1*60*60*1000, lambda: self.scheduleSync(sc))
            # self.after(3000, lambda: self.scheduleSync(sc))
    
    def pushbulletWatchdog(self):
        pb = PushBullet(API_KEY, {'https': os.environ['http_proxy']})
        
        # Grab user
        self.user = pb.getUser()
        
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
        

print(" * Connecting to Arduino...")

# Initialize an ArduinoBoard instance.  This is where you specify baud rate and
# serial timeout.  If you are using a non ATmega328 board, you might also need
# to set the data sizes (bytes for integers, longs, floats, and doubles).  
arduino = PyCmdMessenger.ArduinoBoard("COM4",baud_rate=19200)

# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [["CMD_READY", "s"],
            ["CMD_ACK", "s"],
            ["CMD_SUCCESS", "s"],
            ["CMD_ERROR", "s"],
            ["CMD_TIME_SYNC", "s"],
            ["CMD_TIME_SYNC_RETURN", "L"],
            ["CMD_SET_BRIGHTNESS", "s"],
            ["CMD_COLOR_BREATHE", "s"],
            ["CMD_COLOR_BREATHE_CANCEL", "s"],
            ["CMD_GX", "is"],                    # The parameter for CMD_GX is the number of bytes following (r, g, b)
            ["CMD_GX_CANCEL", ""],
            ["CMD_BINARY_TEST", "b*"]]

# Initialize the messenger
cmd = PyCmdMessenger.CmdMessenger(arduino,commands)

# Run app
app = App(cmd)
app.mainloop()
