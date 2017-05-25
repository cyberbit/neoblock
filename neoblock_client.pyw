# ------------------------------------------------------------------------------
# Python program using the library to interface with the arduino sketch above.
# ------------------------------------------------------------------------------

import PyCmdMessenger, time, sched
from tkinter import *
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
        
        self.brightness_low = Button(frame, text="Low Brightness (32)", command=lambda: self.cmd_set_brightness(32))
        self.brightness_low.grid(row=4, column=1, sticky=W+E)
        
        self.brightness_normal = Button(frame, text="Normal Brightness (64)", command=lambda: self.cmd_set_brightness(64))
        self.brightness_normal.grid(row=4, column=2, sticky=W+E)
        
        self.brightness_high = Button(frame, text="High Brightness (128)", command=lambda: self.cmd_set_brightness(128))
        self.brightness_high.grid(row=4, column=3, sticky=W+E)
        
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
        print(self.cmd.receive()) # CMD_TIME_SYNC_RETURN
        print(self.cmd.receive()) # CMD_SUCCESS
    
    def cmd_time_sync_return(self):
        print(" * CMD_TIME_SYNC_RETURN: Sending time sync...")
        self.cmd.send("CMD_TIME_SYNC_RETURN", int(time.time()) + 60 * 60 * -5) # adjust for UTC-5
        print(self.cmd.receive()) # CMD_ACK
        print(self.cmd.receive()) # CMD_SUCCESS or CMD_ERROR
    
    def cmd_set_brightness(self, v):
        print(" * CMD_SET_BRIGHTNESS: Sending brightness value...")
        self.cmd.send("CMD_SET_BRIGHTNESS", v)
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

print(" * Connecting to Arduino...")

# Initialize an ArduinoBoard instance.  This is where you specify baud rate and
# serial timeout.  If you are using a non ATmega328 board, you might also need
# to set the data sizes (bytes for integers, longs, floats, and doubles).  
arduino = PyCmdMessenger.ArduinoBoard("COM4",baud_rate=9600)

# List of command names (and formats for their associated arguments). These must
# be in the same order as in the sketch.
commands = [["CMD_READY", "s"],
            ["CMD_ACK", "s"],
            ["CMD_SUCCESS", "s"],
            ["CMD_ERROR", "s"],
            ["CMD_TIME_SYNC", "s"],
            ["CMD_TIME_SYNC_RETURN", "s"],
            ["CMD_SET_BRIGHTNESS", "s"]]

# Initialize the messenger
cmd = PyCmdMessenger.CmdMessenger(arduino,commands)

# Run app
app = App(cmd)
app.mainloop()
