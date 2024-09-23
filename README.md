# <strong>Raspberry Pi CD Player </Strong> <sub>(in python)</sub>
A simple and very lightweight cd player written in python (using vlc) made for raspberry pi (in my case Rpi 3b+, but it uses ~1.5% Cpu) with 1602 lcd and six buttons. I highly recommend using it inside a venv!

## Why i made it?
Some time ago i made an amplifier using tpa3116 (i will put the shematic someday) to replace my cheap Panasonic. As i was suprised with change of quality event with same speakers i thought that it would also be nice if i made an cd player (i mostly play music from my cd collection). For ~1.5 year i was using either [Volumio](https://volumio.com/en/get-started/)  and [Raudio](https://github.com/rern/raudio). Why either? Each one has some problems, so i was changing from time to time. On Volumio cd playback is behind a paywall, nanomesher cd plugin runs cd drive too fast (its very loud). Raudio on the other hand tends to lag and interrupt cd playback. So i thought that maybe i would be able to make one. Yes, without a web interface, but lcd and buttons are even better for me. 

## Plan for nearest future
 - add webui
 - make display refresh only if something changed


## Dependencies
<ul>
  <li>Pip</li> 
    <ul>
      <li>requirements.txt</li>
    </ul>
  <li>Apt</li> 
    <ul>
      <li><s>libiso9660-dev</s></li>
      <li>libcdio-dev</li>
      <li><s>libcdio-utils</s></li>
      <li>swig</li>
      <li>cython</li>
      <li>libdiscid0-dev</li>
      <li>python3-pip</li>
      <li>py3-gpiozero</li>
      <li>vlc</li>
      <li>gcc</li>
      <li>python3.11-dev</li>
      <li>libcairo2-dev</li>
      <li>python3.11-venv</li>
      <li>libxt-dev</li>
      <li>libgirepository1.0-dev</li>
    </ul>
  <li>Useful links</li>
    <ul>
      <li><a href="https://blog.himbeer.me/2018/12/27/how-to-connect-a-pcm5102-i2s-dac-to-your-raspberry-pi/">DAC PCM5102 setup</a></li>
      <li><a href="https://www.youtube.com/watch?v=cVdSc8VYVBM">1602 LCD setup</a></li>
      <li><s><a href="https://pimylifeup.com/raspberry-pi-airplay-receiver/">Airplay setup</a></s></li>
      <li><s><a href="https://medium.com/@gamunu/enable-high-quality-audio-on-linux-6f16f3fe7e1f">PulseAudio quality settings</a></s></li>
      <li><s><a href="https://peppe8o.com/epaper-eink-raspberry-pi/">Epaper display tutorial (EPD comming soon)</a></s></li>
      <li><a href="https://github.com/nicokaiser/rpi-audio-receiver">Bluetooth</a></li>
      <li><a href="https://stackoverflow.com/questions/74657226/receiving-audio-data-and-metadata-from-iphone-over-bluetooth-python">Bluetooth metadata readout</a></li>
    </ul>
</ul>
