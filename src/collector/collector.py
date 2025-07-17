from src.db.influxdb_service import InfluxDBService
from shared_utils.kafka_util import KafkaNetworkConsumer

def collector_thread_func(kafka_consumer: KafkaNetworkConsumer, influxdb_service: InfluxDBService):

    batch_buffer = []
    buffer_limit = 2

    try:
        for timestamp, app_net_usage in kafka_consumer.consume_network_data():
            print(f"\n{timestamp.strftime('%H:%M:%S')}")
            print(app_net_usage)
            
            batch_buffer.append((timestamp, app_net_usage))
            
            if len(batch_buffer) >= buffer_limit:
                print(f"Storing batch of {len(batch_buffer)} records...")
                influxdb_service.write_batch(batch_buffer)
                batch_buffer = []
                
    except KeyboardInterrupt:
        print("Collector stopping...")
        # Flush remaining data
        if batch_buffer:
            influxdb_service.write_batch(batch_buffer)
    finally:
        kafka_consumer.close()

