# Plant Buddy
A plant caring embedded system.

## Equipment
* Raspberry Pi 3 Model B+
* Particle Argon
* Immersible Pump and Water Tube (SKU: FIT0200)
* DHT11 Temperature and Relative Humidity Sensor (SKU: CE05172)
* 12" E-Tape Liquid Level Sensor (SKU: ADA464)
* Soil Moisture Sensor (SKU: SEN0114)

## Dependencies on RPi
* Update apt-get
  * `$ sudo apt-get update`
* Particle Agent
  * `$ bash <( curl -sL https://particle.io/install-pi )`
* Particle CLI
  * `$ bash <( curl -sL https://particle.io/install-cli )`
* PySide (GUI)
  * `$ sudo pip3 install PySide`
* Adafruit_DHT
  * `$ sudo pip3 install Adafruit_DHT`
