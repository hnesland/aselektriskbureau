# Software for Rotary VOIP Phone mod based on Raspbery Pi

After seeing [This reddit post](https://www.reddit.com/r/raspberry_pi/comments/2y21sd/i_converted_an_old_phone_to_voip_using_raspberry/) and [image gallery](http://imgur.com/a/HECDL/) I've decided to create my own :)

This repository of code - based on https://github.com/hnesland/aselektriskbureau also documents my progress and can serve as a tutorial on building your own phone.

I have next to zero expirience with Raspbery Pi, electronics and very little python expirience, so this project is a way for me to learn all of those :)

Guide is localized to Poland, most links to shops, items, etc. will lead to polish shops and allegro. But google and ebay are your friend and _all_ of the components are available worldwide (and usually the cheapest option comes from alliexpress).

---

## Bill of Materials

### Basic

* Respbery Pi - Version 2 or 1B - Costs around 120 PLN - [Allegro](http://allegro.pl/listing/listing.php?order=d&string=raspberry+pi+512&search_scope=wszystkie+dzia%C5%82y)
* USB sound card - 5 PLN [Allegro](http://allegro.pl/listing/listing.php?order=d&string=karta+dźwiękowa+usb&search_scope=wszystkie+działy) - As above, check if it works on Linux, but practically all of them do.
* MicroSD Card - 20PLN - You can buy a SD card especially formated for RPi (with bootloader called NOOBs) from  [Official Shop](http://swag.raspberrypi.org/collections/frontpage/products/noobs-8gb-sd-card). You can also buy any other brand one from allegro. RPi recommends Class 4 SD card with 8GB capacity. I got a GoodRAM one. Check http://elinux.org/RPi_SD_cards if card works with RPi before you buy! 
* Micro USB power adapter. To power your raspberry Pi. If you have standard mobile usb charger, it'll work.

### Optional

* WIFI USB Dongle - 15 PLN - [Allegro](http://allegro.pl/listing/listing.php?order=d&string=USB+wifi+&search_scope=wszystkie+dzia%C5%82y), [Official shop](http://swag.raspberrypi.org/collections/pi-kits/products/official-raspberry-pi-wifi-dongle) - It's good to check if the model you choose is supported under Linux (everything that works under linux should also work under RPi). Buy if you want to use Wifi instead of Ethernet cable
* Xiaomi Power Bank - 70 PLN [Allegro](http://allegro.pl/listing/listing.php?order=d&string=xiaomi+5200&search_scope=wszystkie+działy). Buy if you plan on making your phone completelly wireless (at least for periods of time). It's absolutelly _crucial_ that the power bank has _pass-through_ feature, that allows it to charge while at the same time providing power to RPi. Make sure you get genuine Xiami Mi power bank - counterfits do not offer that feature [Identification Guide](https://www.techmesto.com/identify-fake-xiaomi-power-bank/). You can get larger versions of power bank to (10400 and 160000 mAh) if you want for your phone to last longer on battery, keep in mind they also have larger physical dimensions.
 
### Extras

* Keyboard
* HDMI cable (at least on one end :) )

---

## Raspberry Pi Setup

Folllow a guide at https://www.raspberrypi.org/documentation/installation/ or steps bellow if you're on Linux (based on: http://qdosmsq.dunbar-it.co.uk/blog/2013/06/noobs-for-raspberry-pi/ )

    # Download NOOBS from the site. 
    wget http://downloads.raspberrypi.org/NOOBS_latest

    # While it's downloading insert SD Card into a reader.
    # Check which device it's listed at. 
    ls /dev/mmc*

    # Check if it's not mounted. Make _sure_ you're using correct device. 
    export RPI_SD_CARD=/dev/mmcblk0

    # Wipe the SD Card partition table 
    parted $RPI_SD_CARD mklabel msdos

    # Make partition for whole drive 
    parted $RPI_SD_CARD mkpart primary fat32 0% 100%
    
    # Format the partition 
    export RPI_PARTITION="${RPI_SD_CARD}p1"
    mkfs.vfat $RPI_PARTITION

    # Mount the partition
    mkdir rpi
    mount $RPI_PARTITION rpi
    cd rpi

    # unzip the NOOBS
    unzip ../NOOBS_v1_*.zip 

    # Unmount SD card
    cd ../
    umount rpi
    rmdir rpi

### Installing and running Raspbian

1. Insert the SD card into your RaspberryPi, **with the power disconnected** and then connect or turn on the power.
1. After powering up. Install Raspbian (+ optional data partition) on your RPi (this might take a while ~ 30min).
2. After installation you can configure machine (eg. change password, set time zone, languages, etc.). You should configure:
  * Hostname (for logging in later).
  * Enable the SSH server
  * Time zone
  * **Change password!**
3. After configuration, reset RPi. and log in. Defaults are login: pi password: raspberry

### Setting up the network connection

If you're using ethernet then simply plugging in the cable should be enough.

If you're using WIFI you might need to configure it either through GUI (which you start with `startx`), or via console by following this guide: https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md

    sudo -i
    iwlist wlan0 scan

    nano /etc/wpa_supplicant/wpa_supplicant.conf
    # Fill network details.
    
    ifup wlan0
    tail -f /var/log/syslog
    # Observe logs and check if it connects sucessfully
    
    # Check your IP address. Replace wlan0 with eth0 if you're using cable. You can simply call `ifconfig` to get all the information.
    ifconfig wlan0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'

Once you get the IP address you can perform rest of the operations by logging in to your RPi via ssh.

    ssh pi@192.168.1.2 # Set IP number you've got in previous step. In some cases you might be able to use hostname you've set in setup.

### Setup SSH keys.

We'll now setup a public key on our raspberry pi to login without password.

    # Login to RPi.
    ssh pi@192.168.1.23

    mkdir .ssh
    chmod 700 .ssh
    touch .ssh/authorized_keys
    chmod 600 .ssh/authorized_keys 

    exit # Logout

    # Generate a private/public SSH keys if needed.
    if [ ! -f ~/.ssh/id_rsa.pub ]; then ssh-keygen -t rsa -b 4096 -C "your_email@example.com"; fi

    cat ~/.ssh/id_rsa.pub | ssh pi@192.168.1.23 'cat >> ~/.ssh/authorized_keys'
    # type in password for the last time.

### Update your system

    # Updates a system
    sudo apt-get update && sudo apt-get upgrade
    
    # Install pything dependencies. This step is optional.
    sudo apt-get install python-dev libffi-dev libssl-dev -y
  
### Installing linphone


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

### Download software.

    git clone https://github.com/Szpeja/RotaryPi.git


---

# Hardware setup

First of all I had to figure out how the dial works.

I set up a breadboard and connected it to Raspberry PI. The breadboard and 2 other connecting boards I've used came from failed Kickstarter project I've contributed to (I got _some_ of the parts I've paid for). 
I hoped the'll be useful here as they allowed me to easilly connect Raspberry PI to a breadboard using cable. It turned out not to be as easy. 
First of all boards were initialy made for arduino pins, second, while idea behind those was quite nice, the implementation was shity, mislabeled pins, shorted traces, etc.

So after figuring out which pin on cable connects to which pin on breadboard I've come to the conclusion that some pins on breadboard were shorted, which could unfortunately fry RPi if I connected it to the breadboard. Luckilly I caught it in time and severed few traces on PCB which resulted in Pin 14 on BB to be connected to Pin 7 on RPi, and pin 14 to be not connected at all. But besides that everything seemed to work fine.

Surprisingly the result of all that work was quite nice mapping that can be found in [RPi2Breadboard.md](RPi2Breadboard.md) except for unfortunate short of Pin 7 and 14 rest of mapping is 1-1 from markings on Breadboard to RPi board numbering. This works assuming the 15 wide tape is connected in the middle leaving 2 empty rows on each side of Raspberry Pi B.

Next step was to setup a three external pull up resistors to make sure I don't fry RPi while debugging the rotary dial.

To help with the debugging I wrote a small [tester](tester.py) which would light leds if cables get connected. My rotary dial had 4 cables so I quickly tested 6 possible connections making sure to rotate dial with each connection.

The result was that White and Brown cables would be **on** when dial was rotated and Blue-Yellow pair would be **on** all the time except when number was passed.

This was promissing developemnt, in theory I could have just started counting _HIGH_ impulses after the rotating pin goes _LOW_. It turned out that it's not that simple. First of all impulses are triggered both on the way up and on the way down. Ok. So you can just count impulses and then divide them by 2. Right, except aparently some impulses can be triggered before rotating pin going _LOW_. So what now?

First I've tried counting impulses all the time and then just displaying result when rotating pin goes _HIGH_ again.

That didn't exactly work well, and exprimenting with debouncing did not yield expected results, so I threw out all the debouncing and instead created a counter class which counts all triggers and after half a second since last one prints the timing table. 
See [counter.py @ 2079f98](https://github.com/Szpeja/RotaryPi/blob/2079f98/counter.py)

After reviewing timing tables tehre clearly needs to be some debouncing done. I've started with value of 10ms. Unfortunately itturned out the GPIO library for Raspberry Pi is buggy and doesn't handle debouncing that well + aparently detecting edges does not work correctly either whebn set to _FALLING_ or _RISING_ and only _BOTH_ seems to work. This means I'll have to implement the whole logic on my side just like it was done by original author.

After carefully inspecting the hardware rotor I've also found why sometimes extra pulses were emmited. The flywheel sometimes backed few milimeters causing old connection to disjoint and emit a very short pulse.


---

## Links

* 














---------------------------------------------------------------------
This Python-script integrates the old rotary dial and handset on the 
AS Elektrisk Bureau pulse phone to use SIP. 

It uses GPIO on Raspberry Pi to communicate with the rotary dial, and
the onboard soundcard for ringtone. An USB-soundcard is used for mic
and handset audio. 

Some configuration on the Raspberry Pi is needed to make everything work, 
including installing the dependencies and configuring PulseAudio and ALSA
to enable software mixing of sounds. 

Linphone (linphonec for console) is also required because it handles the 
SIP-connection. 

There is some code to use Pjsip, but it's not finished. 

For more information on the build, see http://imgur.com/a/HECDL/.
