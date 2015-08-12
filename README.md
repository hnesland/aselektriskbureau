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
* Xiaomi Power Bank - 70 PLN [Allegro](http://allegro.pl/listing/listing.php?order=d&string=xiaomi+5200&search_scope=wszystkie+działy). Buy if you plan on making your phone completelly wireless (at least for periods of time). It's absolutelly _crucial_ that the power bank has _pass-through_ feature, that allows it to charge while at the same time providing power to RPi. Make sure you get genuine Xiami Mi power bank - counterfits do not offer that feature. You can get large versions of power bank to (10400 and 160000 mAh) if you want for your phone to last longer on battery.
 
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
    sudo pip install --upgrade pip

    # Finaly instaLL linphone package
    sudo pip install linphone4raspberry-3.8.0-cp27-none-any.whl
    
    python -c 'import linphone; print "Ok"'
    # If it prints just "OK" then it's ok. If it throws a fit, you've fucked up something :)

### Download software.

    git clone https://github.com/Szpeja/RotaryPi.git


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
