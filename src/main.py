from paho.mqtt import client as mqtt_client
from file_datasource import FileDatasource
from schema.aggregated_data_schema import AggregatedDataSchema
import config


def connect_mqtt(broker, port):
    print(f'CONNECT TO {broker}:{port}')

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f'Connected to MQTT Broker ({broker}:{port})')
        else:
            print(f'Failed to connect, return code {rc}')

    client = mqtt_client.Client()
    client.on_connect = on_connect
    client.connect(broker, port)
    client.loop_start()
    return client


def publish(client, topic, datasource, delay):
    datasource.startReading()
    while True:
        import time

        time.sleep(delay)
        data = datasource.read()
        msg = AggregatedDataSchema().dumps(data)
        result = client.publish(topic, msg)
        status = result[0]
        if status == 0:
            print(f'Sent to topic `{topic}`: {msg}')
        else:
            print(f'Failed to send message to topic {topic}')


def run():
    client = connect_mqtt(config.MQTT_BROKER_HOST, config.MQTT_BROKER_PORT)
    datasource = FileDatasource(
        '../data/lab5/accelerometer.csv',
        '../data/lab5/gps.csv',
        '../data/lab5/parking.csv',
    )
    publish(client, config.MQTT_TOPIC, datasource, config.DELAY)


if __name__ == '__main__':
    run()
