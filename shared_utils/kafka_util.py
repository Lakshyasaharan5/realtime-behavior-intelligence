from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
import json
import logging

class KafkaNetworkProducer:
    def __init__(self, bootstrap_servers, topic):
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )
    
    def send_network_data(self, timestamp, app_usage_data):
        """Send network data to Kafka"""
        message = {
            'timestamp': timestamp.isoformat(),
            'app_usage': app_usage_data
        }
        
        try:
            future = self.producer.send(self.topic, value=message)
            # Optional: wait for confirmation
            # future.get(timeout=10)
            return True
        except Exception as e:
            logging.error(f"Failed to send to Kafka: {e}")
            return False
    
    def close(self):
        self.producer.close()

class KafkaNetworkConsumer:
    def __init__(self, bootstrap_servers, topic, group_id):
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',  # Start from latest messages
            enable_auto_commit=True
        )
    
    def consume_network_data(self):
        """Generator that yields network data messages"""
        for message in self.consumer:
            try:
                data = message.value
                timestamp_str = data['timestamp']
                app_usage = data['app_usage']
                
                # Convert timestamp back to datetime
                from datetime import datetime
                timestamp = datetime.fromisoformat(timestamp_str)
                
                yield timestamp, app_usage
                
            except Exception as e:
                logging.error(f"Error processing Kafka message: {e}")
                continue
    
    def close(self):
        self.consumer.close()

# Factory functions 
def create_kafka_producer():
    """Create configured Kafka producer for network data"""
    from config.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_NETWORK_DATA
    
    return KafkaNetworkProducer(KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_NETWORK_DATA)

def create_kafka_consumer():
    """Create configured Kafka consumer for network data"""
    from config.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_NETWORK_DATA, KAFKA_CONSUMER_GROUP
    
    return KafkaNetworkConsumer(KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_NETWORK_DATA, KAFKA_CONSUMER_GROUP)

def create_topic_if_not_exists():
    """Create the network metrics topic if it doesn't exist"""
    from config.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_NETWORK_DATA
    
    admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    
    try:
        existing_topics = admin_client.list_topics()
        if KAFKA_TOPIC_NETWORK_DATA in existing_topics:
            print(f"✅ Topic '{KAFKA_TOPIC_NETWORK_DATA}' already exists")
            return
        
        topic = NewTopic(
            name=KAFKA_TOPIC_NETWORK_DATA,
            num_partitions=3,
            replication_factor=1
        )
        
        admin_client.create_topics([topic])
        print(f"✅ Created topic '{KAFKA_TOPIC_NETWORK_DATA}'")
        
    except Exception as e:
        print(f"❌ Failed to create topic: {e}")
    finally:
        admin_client.close()