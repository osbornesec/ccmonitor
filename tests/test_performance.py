"""
Performance benchmark tests for Phase 2 Core Pruning Engine
Validates processing speed, memory usage, and compression efficiency targets

Performance Targets:
- Speed: Process 1000-line JSONL file in <1 second  
- Memory: Use <100MB for largest session files
- Compression: Achieve 50-80% size reduction
- Accuracy: Maintain <1% false positive rate for important content
"""

import pytest
import json
import tempfile
import time
import psutil
import os
import threading
from pathlib import Path
from unittest.mock import patch
from contextlib import contextmanager

import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))


@contextmanager
def memory_monitor():
    """Context manager to monitor memory usage during operations"""
    process = psutil.Process(os.getpid())
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    yield
    
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_used = memory_after - memory_before
    
    # Store in context for access
    memory_monitor.memory_used = memory_used


class TestProcessingSpeedBenchmarks:
    """Benchmark tests for processing speed targets"""
    
    @pytest.fixture
    def benchmark_data_1k(self):
        """Generate exactly 1000 messages for benchmark testing"""
        messages = []
        for i in range(1000):
            msg_type = ["user", "assistant", "tool_call", "system"][i % 4]
            parent = f"msg-{i:04d}" if i > 0 else None
            
            # Vary content complexity
            if msg_type == "tool_call":
                tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "MultiEdit", "TodoWrite"]
                tool = tools[i % len(tools)]
                
                # Some tools have large outputs
                if tool in ["Read", "Bash"] and i % 10 == 0:
                    result = "Large output:\n" + "\n".join([f"Line {j}: Content with details" for j in range(50)])
                else:
                    result = f"Tool {tool} executed successfully"
                
                content = {
                    "tool": tool,
                    "parameters": {"file_path": f"/test/file_{i}.py", "command": f"test command {i}"},
                    "result": result
                }
            else:
                # Vary message lengths
                base_content = f"Message {i} content"
                if i % 20 == 0:
                    base_content += " with extended details about the implementation and reasoning behind the changes"
                content = {"content": base_content}
            
            messages.append({
                "uuid": f"msg-{i+1:04d}",
                "type": msg_type,
                "parentUuid": parent,
                "message": content,
                "timestamp": f"2025-08-01T{i//3600:02d}:{(i%3600)//60:02d}:{i%60:02d}.000000"
            })
        
        return messages
    
    @pytest.fixture
    def benchmark_data_10k(self, benchmark_data_1k):
        """Generate 10,000 messages for large-scale testing"""
        # Replicate 1k data 10 times with UUID adjustments
        large_data = []
        for batch in range(10):
            for msg in benchmark_data_1k:
                new_msg = msg.copy()
                new_msg["uuid"] = f"batch{batch}-{msg['uuid']}"
                if msg.get("parentUuid"):
                    new_msg["parentUuid"] = f"batch{batch}-{msg['parentUuid']}"
                large_data.append(new_msg)
        return large_data
    
    def test_1k_messages_under_1_second(self, benchmark_data_1k):
        """Test processing 1000 messages in under 1 second"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner(pruning_level='medium')
        
        # Create input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in benchmark_data_1k:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # Measure processing time
            start_time = time.perf_counter()
            result = pruner.process_file(input_path, output_path)
            end_time = time.perf_counter()
            
            processing_time = end_time - start_time
            
            # Verify speed target
            assert processing_time < 1.0, f"Processing took {processing_time:.3f}s, expected <1.0s"
            
            # Verify metrics
            assert result['messages_processed'] == 1000
            assert result['processing_time'] < 1.0
            
            # Calculate throughput
            throughput = 1000 / processing_time
            assert throughput > 1000, f"Throughput {throughput:.0f} msg/s, expected >1000 msg/s"
            
            print(f"✓ Processed 1000 messages in {processing_time:.3f}s ({throughput:.0f} msg/s)")
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    def test_streaming_performance_large_files(self, benchmark_data_10k):
        """Test streaming performance with 10k+ messages"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner(pruning_level='medium')
        
        # Create large input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in benchmark_data_10k:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            start_time = time.perf_counter()
            result = pruner.process_file(input_path, output_path)
            end_time = time.perf_counter()
            
            processing_time = end_time - start_time
            
            # Should maintain >1000 msg/s throughput even for large files
            throughput = 10000 / processing_time
            assert throughput > 1000, f"Large file throughput {throughput:.0f} msg/s, expected >1000 msg/s"
            
            # Should process linearly (not exponentially slower)
            assert processing_time < 15.0, f"10k messages took {processing_time:.3f}s, expected <15s"
            
            print(f"✓ Processed 10k messages in {processing_time:.3f}s ({throughput:.0f} msg/s)")
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    def test_pattern_matching_performance(self):
        """Test that pattern matching doesn't become a bottleneck"""
        from src.pruner.core import JSONLPruner
        from src.jsonl_analysis.patterns import PatternAnalyzer
        
        # Create content-heavy messages
        complex_messages = []
        for i in range(100):
            content = {
                "content": f"""
                This is a complex message with multiple patterns to detect.
                It contains code like: def function_{i}(): return 'value'
                It has errors: NameError: undefined_variable_{i} 
                It discusses architecture: using microservices pattern
                It has hooks: Hook: pre_tool_validator executed successfully
                And system status: validation check passed
                """
            }
            complex_messages.append({
                "uuid": f"complex-{i:03d}",
                "type": "assistant",
                "parentUuid": None,
                "message": content,
                "timestamp": f"2025-08-01T10:{i//60:02d}:{i%60:02d}"
            })
        
        # Measure pattern analysis time
        analyzer = PatternAnalyzer()
        
        start_time = time.perf_counter()
        for msg in complex_messages:
            analyzer.analyze_message(msg)
        end_time = time.perf_counter()
        
        analysis_time = end_time - start_time
        analysis_throughput = 100 / analysis_time
        
        # Pattern analysis should be fast enough not to bottleneck
        assert analysis_throughput > 500, f"Pattern analysis {analysis_throughput:.0f} msg/s, expected >500 msg/s"
        
        print(f"✓ Pattern analysis: {analysis_throughput:.0f} msg/s")


class TestMemoryUsageBenchmarks:
    """Benchmark tests for memory usage efficiency"""
    
    def test_memory_usage_1k_messages(self, benchmark_data_1k):
        """Test memory usage stays reasonable for 1k messages"""
        from src.pruner.core import JSONLPruner
        
        with memory_monitor():
            pruner = JSONLPruner(pruning_level='medium')
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for entry in benchmark_data_1k:
                    json.dump(entry, f)
                    f.write('\n')
                input_path = Path(f.name)
            
            with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
                output_path = Path(f.name)
            
            try:
                pruner.process_file(input_path, output_path)
            finally:
                input_path.unlink()
                output_path.unlink()
        
        # Should use <10MB for 1k messages
        assert memory_monitor.memory_used < 10, f"Memory usage {memory_monitor.memory_used:.1f}MB, expected <10MB"
        print(f"✓ 1k messages: {memory_monitor.memory_used:.1f}MB memory used")
    
    def test_memory_usage_10k_messages(self, benchmark_data_10k):
        """Test memory usage stays under 100MB for 10k messages"""
        from src.pruner.core import JSONLPruner
        
        with memory_monitor():
            pruner = JSONLPruner(pruning_level='medium')
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for entry in benchmark_data_10k:
                    json.dump(entry, f)
                    f.write('\n')
                input_path = Path(f.name)
            
            with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
                output_path = Path(f.name)
            
            try:
                pruner.process_file(input_path, output_path)
            finally:
                input_path.unlink()
                output_path.unlink()
        
        # Should use <100MB even for 10k messages
        assert memory_monitor.memory_used < 100, f"Memory usage {memory_monitor.memory_used:.1f}MB, expected <100MB"
        print(f"✓ 10k messages: {memory_monitor.memory_used:.1f}MB memory used")
    
    def test_streaming_memory_efficiency(self):
        """Test that streaming doesn't accumulate memory"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner()
        
        # Simulate processing very large file in chunks
        memory_readings = []
        process = psutil.Process(os.getpid())
        
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Process 5 batches of 1000 messages
        for batch in range(5):
            # Create batch data
            batch_data = []
            for i in range(1000):
                batch_data.append({
                    "uuid": f"batch{batch}-msg{i:03d}",
                    "type": "user",
                    "message": {"content": f"Batch {batch} message {i}"},
                    "timestamp": f"2025-08-01T10:00:{i//60:02d}"
                })
            
            # Process batch
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for entry in batch_data:
                    json.dump(entry, f)
                    f.write('\n')
                input_path = Path(f.name)
            
            with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
                output_path = Path(f.name)
            
            try:
                pruner.process_file(input_path, output_path)
                
                # Record memory usage
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_readings.append(current_memory - initial_memory)
                
            finally:
                input_path.unlink()
                output_path.unlink()
        
        # Memory usage should not grow significantly between batches
        max_memory = max(memory_readings)
        final_memory = memory_readings[-1]
        
        # Final memory should not be much higher than max (no significant accumulation)
        memory_growth = final_memory - memory_readings[0]
        assert memory_growth < 20, f"Memory grew by {memory_growth:.1f}MB across batches"
        
        print(f"✓ Streaming memory readings: {[f'{m:.1f}MB' for m in memory_readings]}")
    
    def test_garbage_collection_efficiency(self):
        """Test that memory is properly released after processing"""
        import gc
        from src.pruner.core import JSONLPruner
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Process several files
        for i in range(3):
            pruner = JSONLPruner()
            
            # Create temporary data
            data = [
                {
                    "uuid": f"test-{i}-{j:03d}",
                    "type": "user",
                    "message": {"content": f"Test message {j}" + "x" * 1000},  # Add some bulk
                    "timestamp": f"2025-08-01T10:{j//60:02d}:{j%60:02d}"
                }
                for j in range(500)
            ]
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for entry in data:
                    json.dump(entry, f)
                    f.write('\n')
                input_path = Path(f.name)
            
            with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
                output_path = Path(f.name)
            
            try:
                pruner.process_file(input_path, output_path)
            finally:
                input_path.unlink()
                output_path.unlink()
            
            # Force cleanup
            del pruner
            del data
            gc.collect()
        
        # Memory should return close to initial level
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_retained = final_memory - initial_memory
        
        assert memory_retained < 50, f"Retained {memory_retained:.1f}MB after processing"
        print(f"✓ Memory cleanup: retained {memory_retained:.1f}MB")


class TestCompressionBenchmarks:
    """Benchmark tests for compression ratio targets"""
    
    @pytest.fixture
    def realistic_conversation_mix(self):
        """Generate realistic conversation with varying importance levels"""
        messages = []
        
        # 30% high importance: user questions, code changes, error solutions
        for i in range(150):
            if i % 3 == 0:  # User questions
                messages.append({
                    "uuid": f"high-user-{i:03d}",
                    "type": "user",
                    "message": {"content": f"How do I fix this error in my code? {i}"},
                    "timestamp": f"2025-08-01T10:{i//60:02d}:{i%60:02d}"
                })
            elif i % 3 == 1:  # Code changes
                messages.append({
                    "uuid": f"high-code-{i:03d}",
                    "type": "tool_call",
                    "message": {
                        "tool": "Edit",
                        "parameters": {"file_path": f"/code/module_{i}.py"},
                        "result": f"Successfully modified function_{i}"
                    },
                    "timestamp": f"2025-08-01T10:{i//60:02d}:{i%60:02d}"
                })
            else:  # Error solutions
                messages.append({
                    "uuid": f"high-solution-{i:03d}",
                    "type": "assistant", 
                    "message": {"content": f"The error is caused by undefined variable. Fix: define variable_{i} = value"},
                    "timestamp": f"2025-08-01T10:{i//60:02d}:{i%60:02d}"
                })
        
        # 40% medium importance: file operations, debugging
        for i in range(200):
            if i % 2 == 0:  # File operations
                messages.append({
                    "uuid": f"med-file-{i:03d}",
                    "type": "tool_call",
                    "message": {
                        "tool": "Read",
                        "parameters": {"file_path": f"/code/file_{i}.py"},
                        "result": f"File content for analysis {i}"
                    },
                    "timestamp": f"2025-08-01T11:{i//60:02d}:{i%60:02d}"
                })
            else:  # Debugging info
                messages.append({
                    "uuid": f"med-debug-{i:03d}",
                    "type": "assistant",
                    "message": {"content": f"Analyzing the code structure in file_{i}. Looking for patterns."},
                    "timestamp": f"2025-08-01T11:{i//60:02d}:{i%60:02d}"
                })
        
        # 30% low importance: hooks, validations, empty outputs
        for i in range(150):
            if i % 3 == 0:  # Hook logs
                messages.append({
                    "uuid": f"low-hook-{i:03d}",
                    "type": "system",
                    "message": {"content": f"Hook: pre_tool_validator_{i} executed successfully"},
                    "timestamp": f"2025-08-01T12:{i//60:02d}:{i%60:02d}"
                })
            elif i % 3 == 1:  # System validations
                messages.append({
                    "uuid": f"low-validation-{i:03d}",
                    "type": "system",
                    "message": {"content": f"System validation {i}: all checks passed"},
                    "timestamp": f"2025-08-01T12:{i//60:02d}:{i%60:02d}"
                })
            else:  # Empty/minimal outputs
                messages.append({
                    "uuid": f"low-empty-{i:03d}",
                    "type": "tool_call",
                    "message": {
                        "tool": "Bash",
                        "parameters": {"command": f"echo 'done {i}'"},
                        "result": f"done {i}"
                    },
                    "timestamp": f"2025-08-01T12:{i//60:02d}:{i%60:02d}"
                })
        
        return messages
    
    def test_light_pruning_compression_ratio(self, realistic_conversation_mix):
        """Test light pruning achieves 20-40% compression"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner(pruning_level='light')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in realistic_conversation_mix:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = pruner.process_file(input_path, output_path)
            compression_ratio = result['compression_ratio']
            
            assert 0.20 <= compression_ratio <= 0.40, f"Light pruning: {compression_ratio:.2f}, expected 0.20-0.40"
            print(f"✓ Light pruning: {compression_ratio:.2f} compression ratio")
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    def test_medium_pruning_compression_ratio(self, realistic_conversation_mix):
        """Test medium pruning achieves 40-60% compression"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner(pruning_level='medium')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in realistic_conversation_mix:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = pruner.process_file(input_path, output_path)
            compression_ratio = result['compression_ratio']
            
            assert 0.40 <= compression_ratio <= 0.60, f"Medium pruning: {compression_ratio:.2f}, expected 0.40-0.60"
            print(f"✓ Medium pruning: {compression_ratio:.2f} compression ratio")
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    def test_aggressive_pruning_compression_ratio(self, realistic_conversation_mix):
        """Test aggressive pruning achieves 60-80% compression"""
        from src.pruner.core import JSONLPruner
        
        pruner = JSONLPruner(pruning_level='aggressive')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in realistic_conversation_mix:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = pruner.process_file(input_path, output_path)
            compression_ratio = result['compression_ratio']
            
            assert 0.60 <= compression_ratio <= 0.80, f"Aggressive pruning: {compression_ratio:.2f}, expected 0.60-0.80"
            print(f"✓ Aggressive pruning: {compression_ratio:.2f} compression ratio")
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    def test_compression_consistency_across_runs(self, realistic_conversation_mix):
        """Test that compression ratios are consistent across multiple runs"""
        from src.pruner.core import JSONLPruner
        
        ratios = []
        
        for run in range(5):
            pruner = JSONLPruner(pruning_level='medium')
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for entry in realistic_conversation_mix:
                    json.dump(entry, f)
                    f.write('\n')
                input_path = Path(f.name)
            
            with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
                output_path = Path(f.name)
            
            try:
                result = pruner.process_file(input_path, output_path)
                ratios.append(result['compression_ratio'])
                
            finally:
                input_path.unlink()
                output_path.unlink()
        
        # Results should be consistent (variance < 5%)
        avg_ratio = sum(ratios) / len(ratios)
        max_deviation = max(abs(r - avg_ratio) for r in ratios)
        
        assert max_deviation < 0.05, f"Inconsistent results: {ratios}, max deviation {max_deviation:.3f}"
        print(f"✓ Compression consistency: {ratios} (avg: {avg_ratio:.3f})")


class TestAccuracyBenchmarks:
    """Benchmark tests for preservation accuracy targets"""
    
    def test_false_positive_rate_under_1_percent(self):
        """Test that <1% of important content is incorrectly removed"""
        from src.pruner.core import JSONLPruner
        
        # Create messages with known importance levels
        known_important = []
        known_unimportant = []
        
        # Definitely important messages
        for i in range(50):
            known_important.append({
                "uuid": f"important-{i:03d}",
                "type": "user",
                "message": {"content": f"CRITICAL: How do I fix this error in function_{i}?"},
                "timestamp": f"2025-08-01T10:{i//60:02d}:{i%60:02d}"
            })
        
        # Definitely unimportant messages
        for i in range(200):
            known_unimportant.append({
                "uuid": f"unimportant-{i:03d}",
                "type": "system",
                "message": {"content": f"Hook: minor_validation_{i} completed successfully"},
                "timestamp": f"2025-08-01T11:{i//60:02d}:{i%60:02d}"
            })
        
        all_messages = known_important + known_unimportant
        important_uuids = {msg["uuid"] for msg in known_important}
        
        pruner = JSONLPruner(pruning_level='aggressive')  # Most aggressive for testing
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in all_messages:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = pruner.process_file(input_path, output_path)
            
            # Load preserved messages
            preserved_uuids = set()
            with open(output_path, 'r') as f:
                for line in f:
                    if line.strip():
                        msg = json.loads(line)
                        preserved_uuids.add(msg['uuid'])
            
            # Calculate false positive rate (important messages incorrectly removed)
            important_removed = important_uuids - preserved_uuids
            false_positive_rate = len(important_removed) / len(important_uuids) if important_uuids else 0
            
            assert false_positive_rate < 0.01, f"False positive rate {false_positive_rate:.3f}, expected <0.01"
            print(f"✓ False positive rate: {false_positive_rate:.3f} ({len(important_removed)}/{len(important_uuids)})")
            
        finally:
            input_path.unlink()
            output_path.unlink()
    
    def test_conversation_dependency_accuracy(self):
        """Test that conversation dependencies are preserved with high accuracy"""
        from src.pruner.core import JSONLPruner
        
        # Create conversation with clear dependency chains
        messages = []
        
        # Main conversation thread
        messages.append({"uuid": "thread1-1", "type": "user", "parentUuid": None, 
                        "message": {"content": "I need help with error in my code"}})
        messages.append({"uuid": "thread1-2", "type": "assistant", "parentUuid": "thread1-1",
                        "message": {"content": "Let me examine your code file"}})
        messages.append({"uuid": "thread1-3", "type": "tool_call", "parentUuid": "thread1-2",
                        "message": {"tool": "Read", "result": "Error code found"}})
        messages.append({"uuid": "thread1-4", "type": "assistant", "parentUuid": "thread1-3", 
                        "message": {"content": "Found the issue - here's the fix"}})
        messages.append({"uuid": "thread1-5", "type": "tool_call", "parentUuid": "thread1-4",
                        "message": {"tool": "Edit", "result": "Fixed successfully"}})
        
        # Branch conversation
        messages.append({"uuid": "branch1-1", "type": "user", "parentUuid": "thread1-2",
                        "message": {"content": "Actually, let me also check another file"}})
        messages.append({"uuid": "branch1-2", "type": "tool_call", "parentUuid": "branch1-1",
                        "message": {"tool": "Read", "result": "Additional file content"}})
        
        # Add noise messages that should be removed
        for i in range(20):
            messages.append({
                "uuid": f"noise-{i:03d}",
                "type": "system",
                "parentUuid": None,
                "message": {"content": f"Hook validation {i} completed"},
                "timestamp": f"2025-08-01T12:{i//60:02d}:{i%60:02d}"
            })
        
        pruner = JSONLPruner(pruning_level='medium')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for entry in messages:
                json.dump(entry, f)
                f.write('\n')
            input_path = Path(f.name)
        
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = pruner.process_file(input_path, output_path)
            
            # Load preserved messages
            preserved_messages = []
            with open(output_path, 'r') as f:
                for line in f:
                    if line.strip():
                        preserved_messages.append(json.loads(line))
            
            preserved_uuids = {msg['uuid'] for msg in preserved_messages}
            
            # Check main thread preservation
            main_thread = ["thread1-1", "thread1-2", "thread1-3", "thread1-4", "thread1-5"]
            main_preserved = sum(1 for uuid in main_thread if uuid in preserved_uuids)
            main_accuracy = main_preserved / len(main_thread)
            
            # Check branch preservation  
            branch_thread = ["branch1-1", "branch1-2"]
            branch_preserved = sum(1 for uuid in branch_thread if uuid in preserved_uuids)
            branch_accuracy = branch_preserved / len(branch_thread)
            
            # Main conversation should be highly preserved
            assert main_accuracy >= 0.8, f"Main thread accuracy {main_accuracy:.2f}, expected >=0.8"
            
            # Verify dependency integrity
            uuid_to_msg = {msg['uuid']: msg for msg in preserved_messages}
            orphaned = 0
            
            for msg in preserved_messages:
                parent_uuid = msg.get('parentUuid')
                if parent_uuid and parent_uuid not in uuid_to_msg:
                    orphaned += 1
            
            orphan_rate = orphaned / len(preserved_messages) if preserved_messages else 0
            assert orphan_rate < 0.05, f"Orphan rate {orphan_rate:.3f}, expected <0.05"
            
            print(f"✓ Dependency accuracy: main {main_accuracy:.2f}, branch {branch_accuracy:.2f}, orphans {orphan_rate:.3f}")
            
        finally:
            input_path.unlink()
            output_path.unlink()


class TestConcurrencyBenchmarks:
    """Benchmark tests for concurrent processing safety"""
    
    def test_concurrent_pruning_safety(self):
        """Test that multiple pruner instances can run safely in parallel"""
        from src.pruner.core import JSONLPruner
        import threading
        
        results = []
        errors = []
        
        def run_pruning(thread_id):
            try:
                pruner = JSONLPruner(pruning_level='medium')
                
                # Create thread-specific test data
                messages = [
                    {
                        "uuid": f"t{thread_id}-msg{i:03d}",
                        "type": "user",
                        "message": {"content": f"Thread {thread_id} message {i}"},
                        "timestamp": f"2025-08-01T10:{i//60:02d}:{i%60:02d}"
                    }
                    for i in range(100)
                ]
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                    for entry in messages:
                        json.dump(entry, f)
                        f.write('\n')
                    input_path = Path(f.name)
                
                with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
                    output_path = Path(f.name)
                
                try:
                    result = pruner.process_file(input_path, output_path)
                    results.append((thread_id, result))
                finally:
                    input_path.unlink()
                    output_path.unlink()
                    
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=run_pruning, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors in concurrent processing: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        
        # All threads should complete successfully
        for thread_id, result in results:
            assert 'messages_processed' in result
            assert result['messages_processed'] == 100
        
        print(f"✓ Concurrent processing: {len(results)} threads completed successfully")


if __name__ == "__main__":
    # Run with performance markers
    pytest.main([__file__, "-v", "-m", "not slow", "--tb=short"])