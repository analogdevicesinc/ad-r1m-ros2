How to set up the AD-R1M internal computer
==========================================

Once you have the hardware assembled, the next step is setting up the OS on the Raspberry Pi. You may choose among the following installation variants:

#. :ref:`use-premade-image`
#. :ref:`install-on-top-of-kuiper`

.. _use-premade-image:

Use a pre-made SD card image
----------------------------

.. warning::

   We only provide SD card images for major releases. Since the AD-R1M is currently in pre-release state, **there are no SD card images.**

.. _install-on-top-of-kuiper:

Install on top of Kuiper Linux
------------------------------

For this setup variant, you will first install Kuiper Linux on the Pi, configure the OS, then add the AD-R1M system package.

Install base Kuiper image
^^^^^^^^^^^^^^^^^^^^^^^^^

Download the latest Kuiper Linux release SD card image for arm64 from the `ADI Kuiper Linux release page <https://github.com/analogdevicesinc/kuiper/releases>`__.

Write the image to an SD card (suggested software: `Raspberry Pi Imager <https://github.com/raspberrypi/rpi-imager>`__, `Balena Etcher <https://etcher.balena.io/>`__, *Kuiper Imager (coming soon)*).

Load the SD card into the AD-R1M's Raspberry Pi and power the robot on.

When booting for the first time, the Pi will not connect to any WiFi network. For first-time configuration, you have two options to gain control:

#. Attach a USB keyboard, mouse, and HDMI screen to the Raspberry Pi, and use the graphical interface. Press :kbd:`Ctrl+Alt+T` to open a terminal window.
#. Attach an Ethernet cable to the Raspberry Pi and connect with SSH:

   .. shell::

      $ ssh analog@analog.local
      Password: analog

   This works both if you connect to a LAN, as well as directly to your PC (link-local).

Set hostname
^^^^^^^^^^^^

The default hostname in ADI Kuiper Linux is ``analog``. Choose an appropriate hostname and edit the ``/etc/hosts`` and ``/etc/hostname`` files to replace ``analog`` with your chosen hostname:

.. shell::

   $ sudo nano /etc/hosts
   ... replace "analog" with your hostname
   $ sudo nano /etc/hostname
   ... replace "analog" with your hostname

In our documentation, you will typically see hostnames of the form ``ad-r1m-SERIALNUMBER``, but that is not a requirement.

Connect to Wi-Fi
^^^^^^^^^^^^^^^^

To connect the Raspberry Pi to your Wi-Fi network, use the graphical interface or run:

.. shell::

   $ sudo nmtui

Install system package
^^^^^^^^^^^^^^^^^^^^^^

With networking set up, install the ``ad-r1m-system-rpi5`` package to set everything else up:

.. shell::

   $ sudo apt-get update
   $ sudo apt-get install ad-r1m-system-rpi5

This will install the latest released version. After this command finishes, restart the Raspberry Pi:

.. shell::

   $ sudo reboot

**And enjoy!** After the reboot, you should have a working AD-R1M.

Keeping up to date
------------------

To get the latest system-level updates, just use the usual apt-get upgrade combo:

.. shell::

   $ sudo apt-get update
   $ sudo apt-get upgrade

