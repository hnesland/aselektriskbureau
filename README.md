# Software for Rotary VOIP Phone mod based on Raspbery Pi

Code for using a Raspberry Pi for a rotary phone via SIP. Originally written by Github @hnesland, improved by Github @swistak, ruined by @mo-g.

For consistency, I'm prototyping on a Raspberry Pi 3B, with a final target of a Pi 0W. Using the 'Fe-Pi 2' as a sound card on both, for hardware i2s audio.

This Python-script integrates the old rotary dial and handset on the AS Elektrisk Bureau pulse phone to use SIP. 

It uses GPIO on Raspberry Pi to communicate with the rotary dial, and the onboard soundcard for ringtone. An USB-soundcard is used for mic and handset audio. 

Some configuration on the Raspberry Pi is needed to make everything work, including installing the dependencies and configuring PulseAudio and ALSA to enable software mixing of sounds. 

Linphone (linphonec for console) is also required because it handles the SIP-connection. 

There is some code to use Pjsip, but it's not finished. 

For more information on the build, see http://imgur.com/a/HECDL/.


---

## Bill of Materials

### Basic

* Respbery Pi 0W.
* Fe-Pi 2 audio card.
* USB cable and power source.
* Rotary Phone.
 
### Extras

* Custom board to drive hardware bells.

---

## Raspberry Pi Setup

Main modifications: overlays for gadget ethernet mode (Pi 0W only), and the Fe-Pi.

Avahi and SSH-Server should be running and configured so that admin/user can conduct headless network configuration.

### Update your system (Needs verifying)

    # Install pything dependencies. This step is optional.
    sudo apt-get install python-dev libffi-dev libssl-dev -y
  
### Installing linphone (Remove when no-longer needed)

Installing Linphone on Raspberry Pi based on https://wiki.linphone.org/wiki/index.php/Raspberrypi:start

    # Download linphone for raspberry. Make sure uit's the newest release.
    wget http://linphone.org/releases/linphone-python-raspberry/linphone4raspberry-3.8.0-cp27-none-any.whl

    # Rest needs to be done as root.

    # Install pip (Python package manager)
    sudo apt-get install python-setuptools -y
    sudo easy_install pip

    # Install wheel packages
    sudo pip install wheel
    sudo pip install pip --upgrade
    sudo pip install setuptools --upgrade

    # Install security update to requests library. Optional (will clear warnings), requires python-dev libffi-dev and libssl-dev installed in step above
    sudo pip install requests[security]

    # Finaly install linphone package
    sudo pip install linphone4raspberry-3.8.0-cp27-none-any.whl
    
    python -c 'import linphone; print "Ok"'
    # If it prints just "OK" then it's ok. If it throws a fit, you've fucked up something :)


---

# Work log by @swistak. (Remove when no-longer needed)

First of all I had to figure out how the dial works.

Breadboard work was quite nice mapping that can be found in [RPi2Breadboard.md](RPi2Breadboard.md) except for unfortunate short of Pin 7 and 14 rest of mapping is 1-1 from markings on Breadboard to RPi board numbering. This works assuming the 15 wide tape is connected in the middle leaving 2 empty rows on each side of Raspberry Pi B.

Next step was to setup a three external pull up resistors to make sure I don't fry RPi while debugging the rotary dial.

To help with the debugging I wrote a small [tester](tester.py) which would light leds if cables get connected. My rotary dial had 4 cables so I quickly tested 6 possible connections making sure to rotate dial with each connection.

The result was that White and Brown cables would be **on** when dial was rotated and Blue-Yellow pair would be **on** all the time except when number was passed.

This was promissing developemnt, in theory I could have just started counting _HIGH_ impulses after the rotating pin goes _LOW_. It turned out that it's not that simple. First of all impulses are triggered both on the way up and on the way down. Ok. So you can just count impulses and then divide them by 2. Right, except aparently some impulses can be triggered before rotating pin going _LOW_. So what now?

First I've tried counting impulses all the time and then just displaying result when rotating pin goes _HIGH_ again.

That didn't exactly work well, and exprimenting with debouncing did not yield expected results, so I threw out all the debouncing and instead created a counter class which counts all triggers and after half a second since last one prints the timing table. 
See [counter.py @ 2079f98](https://github.com/Szpeja/RotaryPi/blob/2079f98/counter.py)

After reviewing timing tables tehre clearly needs to be some debouncing done. I've started with value of 10ms. Unfortunately it turned out the GPIO library for Raspberry Pi is buggy and doesn't handle debouncing that well + aparently detecting edges does not work correctly either whebn set to _FALLING_ or _RISING_ and only _BOTH_ seems to work. This means I'll have to implement the whole logic on my side just like it was done by original author.

After carefully inspecting the hardware rotor I've also found why sometimes extra pulses were emmited. The flywheel sometimes backed few milimeters causing old connection to disjoint and emit a very short pulse.

Next I spent several hours learnign more python and trying to implement sane debouncing to work around concurency problems in RPi.GPIO module.
After I was reasonably sure my code is correct, and I've discovered all the bugs/problems in the RPi.GPIO I started working on a rotary dial again.
It turned out that one of the stoppers that should have stopped a flywheel from backing got worn out and after bending it back into shape, I manged to get consistent results with the rotary dial.

It's quite interesting/frustrating how combination of two _bugs_ one in software library and one in hardware itself - both trivial to solve on their own - created a problem that took me several hours to figure out.

At this point I have a working IO library ( Rio :) ), with working and testable debouncing, working counter script, and I'm ready to move forward. The revision is 59ea9f1a60d18da8fe8ce6a17f3f5a125ff85902

---

## TO DO LIST (in no particular order)

* Update for new RPi GPIO stack.

* Bugfix.

* Complete web interface for remote config of SIP account and api/web-controlled dialling (for when one is too lazy to actually dial, or for use with an electronic phonebook.)

* Complete work to use pjsip instead of linphone (cleanliness, integration).

* Modify to allow multiple SIP accounts with rotary-control and dialtone feedback.

* Breakout ringtone to support using high voltage bells (include Open Hardware circuit diagram.)

* Hardware filter for pulses to simplify code?

* Simple baseboard for Pi and audio card.

---------------------------------------------------------------------

