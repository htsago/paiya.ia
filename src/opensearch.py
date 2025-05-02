import os
import time
from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionError

host = os.getenv("OPENSEARCH_HOST", "opensearch")
port = int(os.getenv("OPENSEARCH_PORT", "9200"))

def get_opensearch_client():
    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
    )
    return client

def create_feedback_index_if_not_exists(max_retries=5, retry_delay=5):
    client = get_opensearch_client()
    index_name = "chat-feedback"

    for attempt in range(max_retries):
        try:
            if not client.indices.exists(index=index_name):
                print(f"Index '{index_name}' wird erstellt...")
                mapping = {
                    "settings": {
                        "index": {
                            "number_of_shards": 1,
                            "number_of_replicas": 0
                        }
                    },
                    "mappings": {
                        "properties": {
                            "timestamp": {"type": "date"},
                            "thumbs": {"type": "keyword"},
                            "model": {"type": "keyword"},
                            "provider": {"type": "keyword"},
                            "message_index": {"type": "integer"},
                            "feedback_text": {"type": "text"},
                            "id": {"type": "keyword"}
                        }
                    }
                }
                client.indices.create(index=index_name, body=mapping)
                print(f"Index '{index_name}' wurde erfolgreich erstellt.")
            else:
                print(f"Index '{index_name}' existiert bereits.")
            return  # Erfolgreich, beende die Funktion
        except ConnectionError as e:
            print(f"Verbindungsfehler: {e}. Versuch {attempt + 1}/{max_retries}...")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise Exception(f"Maximale Versuche erreicht. Kann keine Verbindung zu OpenSearch herstellen: {e}")
