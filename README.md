# <strong>Raspberry Pi CD Player </Strong> <sub>(in python)</sub>
A simple and very lightweight cd player written in python (using vlc) made for raspberry pi (in my case Rpi 3b+, but it uses ~1.5% Cpu) with 1602 lcd and six buttons.

## Why i made it?
Some time ago i made an amplifier using tpa3116 (i will put the shematic someday) to replace my cheap Panasonic. As i was suprised with change of quality event with same speakers i thought that it would also be nice if i made an cd player (i mostly play music from my cd collection). For ~1.5 year i was using either [Volumio](https://volumio.com/en/get-started/)  and [Raudio](https://github.com/rern/raudio). Why either? Each one has some problems, so i was changing from time to time. On Volumio cd playback is behind a paywall, nanomesher cd plugin runs cd drive too fast (its very loud). Raudio on the other hand tends to lag and interrupt cd playback. So i thought that maybe i would be able to make one. Yes, without a web interface, but lcd and buttons are even better for me. 

## What is not yet done?
-airplay integration<br>
-text scrolling<br>
-scrobbler<br>
-maybe spotify connect<br>
-maybe usb playback<br>
-maybe webui as an alternative to buttons<br>
...<br>

## Dependencies
⚠ I'm sure that this list is not full and not in correct order. Its also for pip and apt
<ul>
  <li>Pip</li>
    <ul>
      <li>pycdio (❗ I couldn't install it on windows idk why, on linux on rpi it installed flawlessy)</li>
      <li>setuptools </li>
      <li>pytest  </li>
      <li>gpep517  </li>  
      <li>python-vlc</li>
      <li>musicbrainzngs </li>
      <li>discid </li>
      <li>board</li>
      <li>adafruit-circuitpython-charlcd</li>
      <li>digitalio</li>
    </ul>
  <li>Apt</li>
    <ul>
      <li>libiso9660-dev</li>
      <li>libcdio-dev</li>
      <li>libcdio-utils</li>
      <li>swig</li>
      <li>cython</li>
      <li>libdiscid0-dev</li>
      <li>python3-pip (I assume that python is already installed by default)</li>
      <li>vlc</li>
    </ul>
  <li>Useful links</li>
    <ul>
      <li><a href="https://blog.himbeer.me/2018/12/27/how-to-connect-a-pcm5102-i2s-dac-to-your-raspberry-pi/">DAC PCM5102 setup</a></li>
      <li><a href="https://www.youtube.com/watch?v=cVdSc8VYVBM">1602 LCD setup</a></li>
      <li><a href="https://pimylifeup.com/raspberry-pi-airplay-receiver/">Airplay setup</a></li>
      <li><a href="https://medium.com/@gamunu/enable-high-quality-audio-on-linux-6f16f3fe7e1f">PulseAudio quality settings</a></li>
    </ul>
</ul>
