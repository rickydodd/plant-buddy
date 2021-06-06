#include <SparkJson.h> // makes use of SparkJSON

#define SERIES_RESISTOR 560
#define WATER_LEVEL_PIN A1
#define SOIL_MOISTURE_PIN A3

void waterLevelHandler(const char *event, const char *data) {
    char buf[256]; // buffer for json using snprintf. over compensates.
    float reading, resistanceReading;
    reading = analogRead(WATER_LEVEL_PIN); // getting the analog reading from the water level sensor
    
    /* converting the reading to its resistance value, per documentation on sensor */
    resistanceReading = (1023 / reading) - 1;
    resistanceReading = SERIES_RESISTOR / resistanceReading;
    
    snprintf(buf, sizeof(buf), "{\"data\":\"%f\"}", resistanceReading); // populating buffer
    
    /* packaging the resistance reading and publishing it */
    Particle.publish("water_level", buf);
}

void soilMoistureHandler(const char *event, const char *data){
    char buf[256];
    int soilMoisture = analogRead(SOIL_MOISTURE_PIN);
    
    snprintf(buf, sizeof(buf), "{\"data\":\"%d\"}", soilMoisture);
    
    Particle.publish("soil_moisture", buf);
}

void setup() {
    // setting up event listening
    Particle.subscribe("req_water_level", waterLevelHandler);
    Particle.subscribe("req_soil_moisture", soilMoistureHandler);
}

void loop() {
    // left empty intentionally
}