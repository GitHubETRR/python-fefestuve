import utime
from machine import Pin, SPI, ADC, UART, RTC
import network
import urequests
import max7219
import json
import _thread

MAPBOX_TOKEN = 'pk.eyJ1IjoiZmVmZXN0dXZlIiwiYSI6ImNtMmQ4Mmc4bjFjeGwybXE0ZWQ0c2tweHAifQ.LI5CNJcMdZNccxJ8ueiGvg'
COORDENADAS_PARADA = (-58.938814, -34.198945)

CSID = 'ETRR Free'
WIFI_CONTRASENIA = ''

USERNAME = 'fefestuve'
KEY = 'aio_rAdb854LKlJcecVzxevkblqOxyHO'

URL_LATITUD =f'https://io.adafruit.com/api/v2/{USERNAME}/feeds/latitud/data/last'
URL_LONGITUD = f'https://io.adafruit.com/api/v2/{USERNAME}/feeds/longitud/data/last'

headers = {
    'X-AIO-Key': KEY,
    'Content-Type': 'application/json'
}

latitud = 0
longitud = 0
velocidad = 40000 #metros por hora

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(CSID, WIFI_CONTRASENIA)

while wifi.isconnected() == False:
    paCS


LM35 = ADC(Pin(28))
FACTOR_CONVERSION = 3.3 / 65535

uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

spi = SPI(0, baudrate=10000000, polarity=1, phase=0, sck=Pin(2), mosi=Pin(3))
CS = Pin(1, Pin.OUT)
display = max7219.Matrix8x8(spi, CS, 4)
display.brightneCS(15)
display.fill(0)
display.show()
VELOCIDAD_MATRIX = 0.05

tiempoRestante = 0

# Usar el RTC para obtener la hora
rtc = machine.RTC()

def temperatura():
    volts = LM35.read_u16() * FACTOR_CONVERSION
    grados = volts / 0.08 #basado en el circuito OPAMP
    return grados

def reloj():
    current_time = rtc.datetime()
    hora = f"{current_time[3]:02d}:{current_time[4]:02d}"
    return hora

def enviarSerial(grados, hora):
    mensaje = f"{hora},{grados:.2f}\n"
    uart.write(mensaje)

def actualizarMatrix():
    global tiempoRestante
    while True:
        scrolling_message = f"204 {tiempoRestante}m"
        length = len(scrolling_message)
        column = (length * 8)
        for x in range(32, -column, -1):     
            display.fill(0)
            display.text(scrolling_message, x, 0, 1)
            display.show()
            utime.sleep(VELOCIDAD_MATRIX)
        
_thread.start_new_thread(actualizarMatrix, ())

def servidor():
    global latitud, longitud
    try:
        latitud_resp = urequests.get(URL_LATITUD, headers=headers)
        latitud = float(json.loads(latitud_resp.text)['value'])
        print('latitud :', latitud)
        
        utime.sleep(2)
        
        longitud_resp = urequests.get(URL_LONGITUD, headers=headers)
        longitud = float(json.loads(longitud_resp.text)['value'])
        print('longitud :', longitud)
    except Exception as e:
        print("Error en la conexión al servidor:", e)

def generar_url(longitud, latitud, COORDENADAS_PARADA):
    coordenadas = f"{longitud},{latitud};{COORDENADAS_PARADA[0]},{COORDENADAS_PARADA[1]}"
    urlMapbox = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coordenadas}?alternatives=false&annotations=distance&geometries=geojson&language=en&overview=simplified&steps=true&MAPBOX_TOKEN={MAPBOX_TOKEN}"
    return urlMapbox
    
def calcular_tiempo(latitud, longitud):
    urlMapbox = generar_url(longitud, latitud, COORDENADAS_PARADA)
    try:
        response = urequests.get(urlMapbox)
        distancia = json.loads(response.text)
        distancia = int(distancia["routes"][0]["distance"])
        print(distancia)
        tiempo = int(distancia / velocidad * 60)
        print('tiempo:', tiempo)
        return tiempo
    except (KeyError, IndexError, ValueError) as e:
        print("Error al extraer la distancia:", e)
        return None

while True:
    servidor()
    grados = temperatura()
    hora = reloj()
    enviarSerial(grados, hora)
    print(grados)
    print(hora)
    tiempoRestante = calcular_tiempo(latitud, longitud)
    utime.sleep(2)
