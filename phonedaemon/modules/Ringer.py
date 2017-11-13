"""
Ringer. This module contains classes to represent the 'ringing hardware', the
phone bell (PCM or analogue bell), the earpiece and the playing of tones
through both. It is not inherently threaded, though it will call a timer for
tones which are internally time limited, such as error codes and the busy
signal. It should be called in a way that other threaded elements like the
HardwareAbstractionLayer can trigger it's termination, through stop_ringer,
stop_earpiece and clean_exit. The Device() class can in theory be called
outside of the module, but is mostly intended for internal use by Ringer()
"""


from threading import Timer
import time
import wave
import os
import alsaaudio


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
        Cleanly stop playing at the end of the file (play_loop) or end of the
        current frame (play_once)
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


class Ringer(object):
    """
    Superclass to support both mechanical ringers and virtual ringers. Should
    handle all the stuff about 'Should I ring', and interfacing with the
    daemon.

    Subclasses should then implement the start/continue/stop ringing functions
    for their specific hardware implementations.
    """

    end_earpiece = False
    ringtone = None
    ringfile = None

    tone_path = None

    sound_files = None

    earpiece = None

    def __init__(self, sound_files=None, alsa_devices=None):
        current_path = os.path.dirname(os.path.abspath(__file__))
        parent_path = os.path.abspath(os.path.join(current_path, os.pardir))
        self.tone_path = os.path.join(parent_path, "ringtones")
        print "[INFO] Loading ringtones from path:", self.tone_path

        self.sound_files = sound_files
        for sound in self.sound_files:
            self.sound_files[sound] = os.path.join(self.tone_path,
                                                   self.sound_files[sound])

        self.earpiece = Device(alsa_devices["earpiece"])

    def clean_exit(self):
        """
        Cleanly exit by stopping playback and closing any ALSA devices.
        """
        self.earpiece.close()

    def stop_earpiece(self):
        """
        Stop the earpiece from playing, when a call is dialled or answered.
        """
        self.end_earpiece = True
        time.sleep(0.3)
        self.earpiece.stop()

    def play_dialtone(self):
        """
        Play the dialtone when the phone is off-hook and SIP is connected.
        """
        self.earpiece.play_loop(self.sound_files["dialtone"])

    def play_ringing(self):
        """
        Play the ringing tone when dialling is completed and SIP is
        connecting.
        """
        self.earpiece.play_loop(self.sound_files["ringing"], 0.7)

    def play_busy(self):
        """
        Play a busy tone when SIP returns an engaged signal.
        Play for 30s and cut.
        """
        self.end_earpiece = False
        endtimer = Timer(30, self.stop_earpiece)
        endtimer.start()
        while not self.end_earpiece:
            self.earpiece.play_once(self.sound_files["busy"])
            time.sleep(0.7)

    def play_error(self):
        """
        Play an error tone. E.G. use cases:
         *  Sip fails and handset is lifted.
         *  Dialling times out without a number entered.
         *  Sip connection
        Play for 30s and cut.
        """
        self.end_earpiece = False
        endtimer = Timer(30, self.stop_earpiece)
        endtimer.start()
        while not self.end_earpiece:
            self.earpiece.play_once(self.sound_files["error"])


class BellRinger(Ringer):
    """
    Stub class to implement software control for a hardware ringer, like the
    bells of an early manual or automatic telephone from the first half of the
    20th century.
    """
    def __init__(self, *args, **kwargs):
        super(BellRinger, self).__init__(*args, **kwargs)

    def stop_ringer(self):
        """
        Stop the ringer from sounding, when answered or the caller hangs up.
        """
        return None  # Silence the hardware bell.

    def play_ringer(self):
        """
        Play the ringer on an incoming call.
        """
        return None  # Ring the hardware bell.


class AlsaRinger(Ringer):
    """
    Class to implement a software ringer that outputs over ALSA. Should get the
    ALSA device name from config.
    """

    ringer = None

    def __init__(self, *args, **kwargs):
        alsa_devices = kwargs["alsa_devices"]
        super(AlsaRinger, self).__init__(*args, **kwargs)
        self.ringer = Device(alsa_devices["ringer"])

    def clean_exit(self):
        """
        Cleanly exit by stopping playback and closing any ALSA devices.
        """
        super(AlsaRinger, self).clean_exit()
        self.ringer.close()

    def stop_ringer(self):
        """
        Stop the ringer from playing, when answered or the caller hangs up.
        """
        self.ringer.stop()

    def play_ringer(self):
        """
        Play the ringer on an incoming call.
        """
        self.ringer.play_loop(self.sound_files["ringtone"], 2)


