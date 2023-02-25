# 1950called

1910 Called. It Wants It's Phone Back.

## About

Code for using a Raspberry Pi for a rotary phone via SIP. Originally written by Github @hnesland, improved by Github @swistak, completely rewritten fro scratch by mo-g. Honestly this will be entirely new software, so has a new licence for everything outside the Legacy folder.

It uses GPIO on Raspberry Pi to communicate with the rotary dial, and the onboard soundcard for ringtone. An i2s-soundcard is used for mic and handset audio. The target is the Pi 3B+ and Pi 4B to allow the whole device to be run on a PoE ethernet line, like a standard VoIP phone.

## Bill of Materials

### Basic

* Raspbery Pi 3B+ or 4B.
* Waveshare PoE hat type C.
* Fe-Pi 2 audio card.
* Rotary Phone.
* PoE switch or injector for power and network.
 
### Extras

* Custom board to drive hardware bells, or custom power amp and speaker for
playing simulated bell tones. (Uses BCM DAC)

## Raspberry Pi Setup

Main modifications: overlays for gadget ethernet mode (Pi 0W only), and the Fe-Pi.

    # In /boot/config.txt
    dtoverlay=fe-pi-audio # enable Fe-Pi
    dtoverlay=i2s-mmap # enable i2s audio support for Fe-Pi

Avahi and SSH-Server should be running and configured so that admin/user can conduct headless network configuration.

## TO DO LIST (in no particular order)

* Rewrite from scratch with NodeJS and rpi-gpio.

* Basic rest API for remote config of SIP account and dialling (for when one is too lazy to actually dial, or for use with an electronic phonebook.)

* Use the SIP library being written for Spindoctor.

* ~~Breakout ringtone to support using high voltage bells (include Open Hardware circuit diagram.)~~ I'd still like to do this, but the phone I'm using turns out to just have fake bells and a speaker on the back, so I won't be implementing it for this build.

* Hardware filter for pulses to simplify code? This shouldn't be necessary, but until I move from the main code rewrite to messing with the hardware, I won't know.

* Simple "Hat" addon with any additional hardware for interfacing to the phone prebuilt.
