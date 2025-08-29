"""Performance tests for the Flask application.

This module contains performance tests to measure response times,
throughput, memory usage, and other performance characteristics.
"""

import pytest
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.extensions import db, cache


@pytest.mark.performance
class TestResponseTimePerformance:
    """Test response time performance."""
    
    def test_root_endpoint_response_time(self, client):
        """Test root endpoint response time."""
        times = []
        
        # Warm up
        client.get('/')
        
        # Measure response times
        for _ in range(10):
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        max_time = max(times)
        min_time = min(times)
        
        # Performance assertions
        assert avg_time < 0.1  # Average response time < 100ms
        assert max_time < 0.5  # Max response time < 500ms
        assert min_time < 0.05  # Min response time < 50ms
    
    def test_examples_endpoint_response_time(self, client):
        """Test examples endpoints response time."""
        endpoints = [
            '/examples/',
            '/examples/hello',
            '/examples/echo?message=test',
            '/examples/json'
        ]
        
        for endpoint in endpoints:
            times = []
            
            # Warm up
            client.get(endpoint)
            
            # Measure response times
            for _ in range(5):
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                assert response.status_code == 200
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times)
            assert avg_time < 0.2, f"Endpoint {endpoint} too slow: {avg_time}s"
    
    def test_database_query_performance(self, app):
        """Test database query performance."""
        with app.app_context():
            # Create test table with data
            db.engine.execute("""
                CREATE TABLE IF NOT EXISTS perf_test (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    value INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test data
            for i in range(100):
                db.engine.execute(
                    "INSERT INTO perf_test (name, value) VALUES (?, ?)",
                    (f'test_{i}', i)
                )
            
            # Measure query performance
            times = []
            for _ in range(10):
                start_time = time.time()
                result = db.engine.execute(
                    "SELECT * FROM perf_test WHERE value > ? ORDER BY value LIMIT 10",
                    (50,)
                )
                rows = result.fetchall()
                end_time = time.time()
                
                assert len(rows) > 0
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times)
            assert avg_time < 0.01  # Database queries should be very fast
    
    def test_cache_performance(self, app):
        """Test cache operation performance."""
        with app.app_context():
            # Test cache set performance
            set_times = []
            for i in range(100):
                start_time = time.time()
                cache.set(f'perf_key_{i}', f'value_{i}', timeout=60)
                end_time = time.time()
                set_times.append(end_time - start_time)
            
            # Test cache get performance
            get_times = []
            for i in range(100):
                start_time = time.time()
                value = cache.get(f'perf_key_{i}')
                end_time = time.time()
                assert value == f'value_{i}'
                get_times.append(end_time - start_time)
            
            # Performance assertions
            avg_set_time = statistics.mean(set_times)
            avg_get_time = statistics.mean(get_times)
            
            assert avg_set_time < 0.001  # Cache set < 1ms
            assert avg_get_time < 0.001  # Cache get < 1ms


@pytest.mark.performance
class TestThroughputPerformance:
    """Test throughput and concurrent request handling."""
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        num_threads = 10
        requests_per_thread = 5
        results = []
        
        def make_requests():
            thread_results = []
            for _ in range(requests_per_thread):
                start_time = time.time()
                response = client.get('/examples/hello')
                end_time = time.time()
                
                thread_results.append({
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                })
            return thread_results
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_requests) for _ in range(num_threads)]
            
            for future in as_completed(futures):
                results.extend(future.result())
        
        # Analyze results
        total_requests = num_threads * requests_per_thread
        successful_requests = sum(1 for r in results if r['status_code'] == 200)
        response_times = [r['response_time'] for r in results]
        
        # Performance assertions
        assert successful_requests == total_requests  # All requests should succeed
        assert statistics.mean(response_times) < 1.0  # Average response time < 1s
        assert max(response_times) < 2.0  # Max response time < 2s
    
    def test_sustained_load(self, client):
        """Test sustained load handling."""
        duration = 5  # Test for 5 seconds
        start_time = time.time()
        request_count = 0
        response_times = []
        
        while time.time() - start_time < duration:
            req_start = time.time()
            response = client.get('/examples/hello')
            req_end = time.time()
            
            assert response.status_code == 200
            request_count += 1
            response_times.append(req_end - req_start)
        
        # Calculate throughput
        throughput = request_count / duration
        avg_response_time = statistics.mean(response_times)
        
        # Performance assertions
        assert throughput > 10  # Should handle at least 10 requests/second
        assert avg_response_time < 0.5  # Average response time < 500ms
    
    def test_database_concurrent_access(self, app):
        """Test concurrent database access performance."""
        with app.app_context():
            # Create test table
            db.engine.execute("""
                CREATE TABLE IF NOT EXISTS concurrent_test (
                    id INTEGER PRIMARY KEY,
                    thread_id INTEGER NOT NULL,
                    operation_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            num_threads = 5
            operations_per_thread = 10
            results = []
            
            def database_operations(thread_id):
                thread_results = []
                for op_id in range(operations_per_thread):
                    start_time = time.time()
                    
                    # Insert operation
                    db.engine.execute(
                        "INSERT INTO concurrent_test (thread_id, operation_id) VALUES (?, ?)",
                        (thread_id, op_id)
                    )
                    
                    # Query operation
                    result = db.engine.execute(
                        "SELECT COUNT(*) as count FROM concurrent_test WHERE thread_id = ?",
                        (thread_id,)
                    )
                    count = result.fetchone()['count']
                    
                    end_time = time.time()
                    thread_results.append({
                        'thread_id': thread_id,
                        'operation_id': op_id,
                        'duration': end_time - start_time,
                        'count': count
                    })
                
                return thread_results
            
            # Execute concurrent database operations
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(database_operations, i) for i in range(num_threads)]
                
                for future in as_completed(futures):
                    results.extend(future.result())
            
            # Analyze results
            durations = [r['duration'] for r in results]
            avg_duration = statistics.mean(durations)
            max_duration = max(durations)
            
            # Performance assertions
            assert len(results) == num_threads * operations_per_thread
            assert avg_duration < 0.1  # Average operation < 100ms
            assert max_duration < 0.5  # Max operation < 500ms


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryPerformance:
    """Test memory usage and performance."""
    
    def test_memory_usage_under_load(self, client):
        """Test memory usage under sustained load."""
        import psutil
        import os
        
        # Get current process
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate load
        for _ in range(100):
            response = client.get('/examples/hello')
            assert response.status_code == 200
        
        # Check memory after load
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024
    
    def test_cache_memory_efficiency(self, app):
        """Test cache memory efficiency."""
        with app.app_context():
            # Store large amount of data in cache
            large_data = 'x' * 1000  # 1KB string
            
            for i in range(100):
                cache.set(f'large_key_{i}', large_data, timeout=60)
            
            # Verify data is stored
            for i in range(100):
                value = cache.get(f'large_key_{i}')
                assert value == large_data
            
            # Clear cache
            cache.clear()
            
            # Verify cache is cleared
            for i in range(100):
                value = cache.get(f'large_key_{i}')
                assert value is None
    
    def test_database_connection_efficiency(self, app):
        """Test database connection efficiency."""
        with app.app_context():
            # Test that connections are properly managed
            connections = []
            
            try:
                # Create multiple connections
                for _ in range(10):
                    conn = db.engine.connect()
                    connections.append(conn)
                    
                    # Use connection
                    result = conn.execute('SELECT 1 as test')
                    assert result.fetchone()['test'] == 1
                
                # All connections should work
                assert len(connections) == 10
                
            finally:
                # Clean up connections
                for conn in connections:
                    conn.close()


@pytest.mark.performance
class TestScalabilityPerformance:
    """Test application scalability characteristics."""
    
    def test_response_time_scaling(self, client):
        """Test how response time scales with request size."""
        # Test with different payload sizes
        payload_sizes = [100, 1000, 5000, 10000]  # bytes
        
        for size in payload_sizes:
            payload = {'message': 'x' * size}
            headers = {'Content-Type': 'application/json'}
            
            times = []
            for _ in range(5):
                start_time = time.time()
                response = client.post(
                    '/examples/echo',
                    json=payload,
                    headers=headers
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    times.append(end_time - start_time)
            
            if times:  # Only check if requests succeeded
                avg_time = statistics.mean(times)
                # Response time should scale reasonably with payload size
                max_expected_time = 0.1 + (size / 100000)  # Base time + scaling factor
                assert avg_time < max_expected_time, f"Size {size}: {avg_time}s > {max_expected_time}s"
    
    def test_concurrent_user_simulation(self, client):
        """Simulate multiple concurrent users."""
        num_users = 5
        actions_per_user = 10
        
        def simulate_user(user_id):
            user_results = []
            
            for action in range(actions_per_user):
                # Simulate different user actions
                endpoints = [
                    '/examples/hello',
                    '/examples/json',
                    f'/examples/echo?message=user_{user_id}_action_{action}'
                ]
                
                endpoint = endpoints[action % len(endpoints)]
                
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                user_results.append({
                    'user_id': user_id,
                    'action': action,
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                })
                
                # Simulate user think time
                time.sleep(0.01)  # 10ms think time
            
            return user_results
        
        # Simulate concurrent users
        all_results = []
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(simulate_user, i) for i in range(num_users)]
            
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        # Analyze results
        successful_requests = sum(1 for r in all_results if r['status_code'] == 200)
        total_requests = num_users * actions_per_user
        success_rate = successful_requests / total_requests
        
        response_times = [r['response_time'] for r in all_results if r['status_code'] == 200]
        avg_response_time = statistics.mean(response_times) if response_times else float('inf')
        
        # Performance assertions
        assert success_rate > 0.95  # 95% success rate
        assert avg_response_time < 1.0  # Average response time < 1s