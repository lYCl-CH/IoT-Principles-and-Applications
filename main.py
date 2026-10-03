from machine import Pin, I2C
from time import sleep, ticks_ms, ticks_diff
from max30100 import MAX30100
from umqtt.simple import MQTTClient
import network
import wifi
import json
import _thread

CLIENT_ID ='esp32_sensor2'
SERVER='140.127.196.119'
PORT=18305
USERNAME='iot'
PASSWORD='123456789'
TOPIC='heatrate'
TOPIC2='SpO'
led = Pin(2, Pin.OUT)
led.value(0)
def connect():
    client = MQTTClient(CLIENT_ID, SERVER, PORT, USERNAME, PASSWORD)
    client.connect()
    print('Connected to MQTT Broker "{server}"'.format(server = SERVER))
    return client
if wifi.ip()!= None:
    if wifi.wifi_ssid() == 3719:
        SERVER='192.168.251.15'
        PORT=1883
    client = connect()



def mqtt_text(json_data,json_data2):
    client.publish(TOPIC.encode(), json_data)
    client.publish(TOPIC2.encode(), json_data2)

def calculate_ac_dc(values):
    dc = sum(values) / len(values)
    ac = max(values) - min(values)
    return ac, dc

ir_values = []
red_values = []


i2c = I2C(0, scl=Pin(22), sda=Pin(21)) 
sensor = MAX30100(i2c)
def sensor_loop():
        while True:
            ir, red = sensor.read_fifo()
            led.value(0)
            if ir>10000 and red>10000 :
#             while True:
                for i in range(0,6):
                    
                    ir_values = []
                    red_values = []
                    ir=0
                    red=0
                    
                    start_time = ticks_ms()
                    duration = 10000  # 10 秒
                   
                    
                    ir, red = sensor.read_fifo()
                    print(ir, red,"1")
                    print("📡 收集資料中... 請將手指放在感測器上")
                  
                    
                    while ticks_diff(ticks_ms(), start_time) < duration:
                        try:
                            
                            ir, red = sensor.read_fifo()
                            ir_values.append(ir)
                            red_values.append(red)
                            
                            print("IR:", ir, "RED:", red)
                            led.value(1)
                            sleep(0.05)
                            led.value(0)
                        except Exception as e:
                            print("讀取感測器錯誤:", e)
                            continue

                    ac_red, dc_red = calculate_ac_dc(red_values)
                    ac_ir, dc_ir = calculate_ac_dc(ir_values)
                
                    if dc_red == 0 or dc_ir == 0:
                        print("⚠️ 無效資料")

                    else:
                        ratio = (ac_red / dc_red) / (ac_ir / dc_ir)
                        spo2 = 110 - 25 * ratio
                        spo2 = max(0, min(100, spo2))
                        print("估算 SpO₂：", round(spo2, 1), "%")

                        # 計算心率
                        peaks = 0
                     
                        for i in range(1, len(ir_values) - 1):
                            if ir_values[i] > ir_values[i-1] and ir_values[i] > ir_values[i+1]:
                                peaks += 1

                        bpm = peaks * (60 / 10)
                        print("估算心率：", bpm, "bpm")

                        data = {
                            "bpm": bpm        
                        }
                        data2 = {
                            "SpO₂": f"{spo2:.1f}%"
                        }
                        json_data = json.dumps(data).encode()
                        json_data2 = json.dumps(data2).encode()
                        if client:
                            _thread.start_new_thread(mqtt_text, (json_data,json_data2))
                           
                        else:
                            print("⚠️ MQTT 尚未連線，無法傳送")
                
                print("📡 收集結束")
                sleep(10)
                while ir>20000 and red>30000:
                     ir, red = sensor.read_fifo()
                     led.value(1)   
          
# 啟動背景執行緒
if wifi.ip()!=None:
    sensor_loop()