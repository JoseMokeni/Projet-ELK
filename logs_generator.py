import json
import random
import time
from datetime import datetime
import os

class LogGenerator:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.endpoints = ['/api/users', '/api/products', '/api/orders', '/api/auth', '/api/search']
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Mozilla/5.0 (Linux; Android 10; SM-A505F)'
        ]
        self.ip_addresses = [
            f'192.168.1.{i}' for i in range(1, 256)
        ]
        self.sql_queries = [
            "SELECT * FROM users WHERE last_login > DATE_SUB(NOW(), INTERVAL 24 HOUR)",
            "SELECT p.*, c.name FROM products p JOIN categories c ON p.category_id = c.id",
            "SELECT COUNT(*) FROM orders WHERE status = 'pending' GROUP BY user_id",
            "SELECT * FROM inventory WHERE stock < threshold ORDER BY stock ASC",
            "SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id"
        ]
        self.status_codes = [200, 200, 200, 200, 201, 301, 302, 400, 401, 403, 404, 500]
        
        # Créer les répertoires de logs s'ils n'existent pas
        os.makedirs(f"{log_dir}/nginx", exist_ok=True)
        os.makedirs(f"{log_dir}/mysql", exist_ok=True)
        os.makedirs(f"{log_dir}/system", exist_ok=True)

    def generate_nginx_log(self):
        """Génère un log Nginx au format JSON"""
        now = datetime.now().isoformat()
        request_time = random.uniform(0.1, 2.0)
        status = random.choice(self.status_codes)
        body_bytes = random.randint(500, 5000)

        log_entry = {
            "timestamp": now,
            "remote_addr": random.choice(self.ip_addresses),
            "request_method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "request_uri": random.choice(self.endpoints),
            "status": status,
            "body_bytes_sent": body_bytes,
            "request_time": round(request_time, 3),
            "http_user_agent": random.choice(self.user_agents),
            "http_x_forwarded_for": random.choice(self.ip_addresses)
        }

        with open(f"{self.log_dir}/nginx/access.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def generate_mysql_slow_log(self):
        """Génère un log MySQL slow query"""
        now = datetime.now()
        query_time = random.uniform(1.0, 10.0)
        lock_time = random.uniform(0, 0.5)
        rows_sent = random.randint(1, 1000)
        rows_examined = rows_sent * random.randint(1, 100)

        log_entry = f"""# Time: {now.strftime('%Y-%m-%dT%H:%M:%S.%f')}
# User@Host: user[user] @ localhost []
# Query_time: {query_time:.6f}  Lock_time: {lock_time:.6f} Rows_sent: {rows_sent}  Rows_examined: {rows_examined}
SET timestamp={int(now.timestamp())};
{random.choice(self.sql_queries)};\n"""

        with open(f"{self.log_dir}/mysql/slow-query.log", "a") as f:
            f.write(log_entry)

    def generate_system_metrics(self):
        """Génère des métriques système"""
        metrics = {
            "cpu_usage": random.uniform(20, 95),
            "memory_usage": random.uniform(40, 90),
            "disk_usage": random.uniform(50, 85),
            "network_in": random.uniform(100, 1000),
            "network_out": random.uniform(100, 1000),
            "load_average": random.uniform(0.1, 4.0)
        }

        with open(f"{self.log_dir}/system/metrics.log", "a") as f:
            for metric, value in metrics.items():
                f.write(f"{metric} {value:.2f}\n")

def main():
    generator = LogGenerator("logs2")
    
    print("Démarrage de la génération des logs...")
    
    try:
        while True:
            # Générer des logs avec des fréquences différentes
            generator.generate_nginx_log()  # Logs plus fréquents
            
            if random.random() < 0.3:  # 30% de chance de générer un slow query log
                generator.generate_mysql_slow_log()
            
            if random.random() < 0.1:  # 10% de chance de générer des métriques système
                generator.generate_system_metrics()
            
            # Attendre un court instant entre chaque génération
            time.sleep(random.uniform(0.1, 0.5))
            
    except KeyboardInterrupt:
        print("\nArrêt de la génération des logs")

if __name__ == "__main__":
    main()