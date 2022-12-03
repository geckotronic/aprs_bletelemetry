
# Telemetría APRS de sensores BLE 

Usando un gateway Minew G1 (BLE/Wifi) obtenemos la data de dos sensores de temperatura BLE. Con esos datos enviamos datos de telemetria a la plataforma APRS via TCP/IP. 

## Equipos y Materiales:

[Gateway G1 Minew](https://www.minew.com/product/g1-iot-gateway/)

[Sensor Xiaomi](https://www.amazon.com/saikang-Bluetooth-Thermometer-Wireless-Hygrometer/dp/B083Y1D8WB)

[Sensor S3 Minew](https://www.minew.com/product/s3-temp-and-humidity-sensor/)

## Notas de implementación

1. Modificamos el FW del sensor de Xiaomi usando las herramientas e instrucciones que encontramos [aquí](https://github.com/atc1441/ATC_MiThermometer).

2. Configuramos el GW de Minew para que entregue la data en formato JSON Long en la URL de nuestro server local. 

3. Configuramos el script con las opciones necesarias de CALLSIGN, PASSWORD y posición.


