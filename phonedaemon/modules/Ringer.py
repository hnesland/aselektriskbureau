from threading import Timer
import time
import alsaaudio
import wave
import os


class Device(object):
    """
    This class represents an Alsa device as a playback target for the class.
    Each ringer will be created as an object for use in the ringer class.
    """

    device = None
    play = False
    kill = False

    def __init__(self, device):
        """
        Create an alsa object for the sound device.
        """
        self.device = alsaaudio.PCM(card=device)

    def play_once(self, source):
        '''
        Play a file for 320 samples, or until stop() called.
        '''
        stream = wave.open(source, 'rb')
        self.device.setchannels(stream.getnchannels())
        self.device.setrate(stream.getframerate())
        self.device.setperiodsize(320)
        data = stream.readframes(320)
        self.play = True
        while data and self.play and not self.kill:
            self.device.write(data)
            data = stream.readframes(320)
        stream.rewind()
        stream.close()

    def play_loop(self, source, interval=None):
        '''
        Play a file on loop until stop() called.
        '''
        stream = wave.open(source, 'rb')
        self.device.setchannels(stream.getnchannels())
        self.device.setrate(stream.getframerate())
        self.device.setperiodsize(320)
        self.play = True
        while self.play:
            data = stream.readframes(320)
            while data and not self.kill:
                self.device.write(data)
                data = stream.readframes(320)

            stream.rewind()
            if interval:
                time.sleep(interval)

    def stop(self):
        '''
        
        '''
        self.play = False

    def close(self):
        """
        This should be called on any abnormal hangup. I also don't know if I
        need to be explicitly allowing access for the SIP layer once I've 
        finished playing on the earphone device.
        """
        self.kill = True
        time.sleep(0.3)
        self.device.close()
        print "closed ALSA target."


class Ring(object):
    """
    Superclass to support both mechanical ringers and virtual ringers. Should
    handle all the stuff about 'Should I ring', and interfacing with the
    daemon.

    Subclasses should then implement the start/continue/stop ringing functions
    for their specific hardware implementations.
    """


class Ringer(Ring):
    """
    Stub class to implement software control for a hardware ringer, like the
    bells of an early manual or automatic telephone from the first half of the
    20th century.
    """


class Ringer(Ring):
    """
    Class to implement a software ringer that outputs over ALSA. Should get the
    ALSA device name from config.
    """

    tone_path = None
    shouldring = 0
    ringtone = None
    ringfile = None

    ringstart = 0

    shouldplayhandset = 0
    handsetfile = None
    timerHandset = None

    sound_files = None

    ringer = None
    earpiece = None

    def __init__(self, sound_files, alsa_devices):
        current_path = os.path.dirname(os.path.abspath(__file__))
        parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
        self.tone_path = os.path.join(parent_path, "ringtones")
        print "[INFO] Loading ringtones from path:", self.tone_path

        self.sound_files = sound_files
        for sound in self.sound_files:
            self.sound_files[sound] = os.path.join(self.tone_path,
                                                   self.sound_files[sound])

        self.ringer = Device(alsa_devices["ringer"])
        self.earpiece = Device(alsa_devices["earpiece"])

    def start(self):
        self.shouldring = 1
        self.ringtone = Timer(0, self.doring)
        self.ringtone.start()
        self.ringstart = time.time()

    def stop(self):
        self.shouldring = 0
        if self.ringtone is not None:
            self.ringtone.cancel()

    def starthandset(self, tone):
        self.shouldplayhandset = 1
        self.handsetfile = self.sound_files[tone]
        if self.timerHandset is not None:
            print "[RINGTONE] Handset already playing?"
            return

        self.timerHandset = Timer(0, self.playhandset)
        self.timerHandset.start()

    def stophandset(self):
        self.shouldplayhandset = 0
        if self.timerHandset is not None:
            self.timerHandset.cancel()
            self.timerHandset = None
    
    def cleanexit(self):
        """
        Cleanly exit by stopping playback and closing any ALSA devices.
        """
        self.earpiece.close()
        self.ringer.close()
        print "finished clean exit of ringer."

    def playhandset(self):
        print "Starting dialtone"

        self.earpiece.play_loop(self.sound_files["dialtone"])


    def playfile(self, tone):
        wv = wave.open(self.sound_files[tone])
        # TODO: Get from config, but should NOT be Pulseaudio.
        self.device = alsaaudio.PCM(card="pulse")
        self.device.setchannels(wv.getnchannels())
        self.device.setrate(wv.getframerate())
        self.device.setperiodsize(320)

        data = wv.readframes(320)
        while data:
            self.device.write(data)
            data = wv.readframes(320)
        wv.rewind()
        wv.close()

    def doring(self):
        if self.ringfile is not None:
            self.ringfile.rewind()
        else:
            self.ringfile = wave.open(self.sound_files["ringtone"], 'rb')



        while self.shouldring:
            data = self.ringfile.readframes(320)
            while data:
                self.device.write(data)
                data = self.ringfile.readframes(320)

            self.ringfile.rewind()
            time.sleep(2)
            if time.time() - 60 > self.ringstart:
                self.stop()
