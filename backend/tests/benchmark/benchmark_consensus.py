#!/usr/bin/env python3

import sys
import os
import time
import statistics
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from app.blockchain.simple_blockchain import SimpleBlockchain, Block
from app.blockchain.pos_blockchain import ProofOfStakeBlockchain
from app.blockchain.pbft_blockchain import PBFTBlockchain

class BlockchainBenchmark:
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(__file__).parent / output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}
    
    def create_test_transaction(self, index: int) -> Dict:
        return {
            "type": "medical_record_hash",
            "record_id": f"test_record_{index}",
            "patient_id": f"patient_{index % 10}",
            "hash": f"hash_{index}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def benchmark_throughput(self, blockchain, name: str, num_transactions: int = 100) -> Dict:
        print(f"  Testing {name}: {num_transactions} transactions...", end=" ", flush=True)
        
        start_time = time.time()
        
        for i in range(num_transactions):
            tx = self.create_test_transaction(i)
            try:
                blockchain.add_transaction_and_mine(tx)
            except Exception as e:
                print(f"\n    Error: {e}")
                return {"error": str(e)}
        
        end_time = time.time()
        duration = end_time - start_time
        tps = num_transactions / duration if duration > 0 else 0
        
        print(f"[OK] {tps:.2f} TPS")
        
        return {
            "transactions": num_transactions,
            "duration": duration,
            "tps": tps
        }
    
    def benchmark_latency(self, blockchain, name: str, num_tests: int = 50) -> Dict:
        print(f"  Testing {name}: {num_tests} transactions...", end=" ", flush=True)
        
        latencies = []
        
        for i in range(num_tests):
            tx = self.create_test_transaction(i)
            start = time.time()
            try:
                blockchain.add_transaction_and_mine(tx)
                end = time.time()
                latency = (end - start) * 1000
                latencies.append(latency)
            except Exception as e:
                print(f"\n    Error: {e}")
                return {"error": str(e)}
        
        avg_latency = statistics.mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0
        
        sorted_latencies = sorted(latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)] if len(sorted_latencies) > 1 else sorted_latencies[-1]
        
        print(f"[OK] Avg: {avg_latency:.2f}ms")
        
        return {
            "average_latency": avg_latency,
            "min_latency": min_latency,
            "max_latency": max_latency,
            "median_latency": p50,
            "p95_latency": p95,
            "p99_latency": p99,
            "std_dev": std_dev,
            "samples": len(latencies)
        }
    
    def benchmark_energy(self, blockchain, name: str, num_blocks: int = 10) -> Dict:
        print(f"  Testing {name}: {num_blocks} blocks...", end=" ", flush=True)
        
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            cpu_times_before = process.cpu_times()
            memory_before = process.memory_info().rss / 1024 / 1024
            start_time = time.time()
            
            initial_chain_length = len(blockchain.chain)
            
            for i in range(num_blocks):
                tx = self.create_test_transaction(i)
                blockchain.add_transaction_and_mine(tx)
            
            end_time = time.time()
            cpu_times_after = process.cpu_times()
            memory_after = process.memory_info().rss / 1024 / 1024
            cpu_time = (cpu_times_after.user - cpu_times_before.user) + \
                      (cpu_times_after.system - cpu_times_before.system)
            wall_time = end_time - start_time
            memory_used = memory_after - memory_before
            final_chain_length = len(blockchain.chain)
            blocks_created = final_chain_length - initial_chain_length
            
            cpu_per_block = cpu_time / num_blocks if num_blocks > 0 else 0
            
            print(f"[OK] {cpu_time:.2f} CPU sec")
            
            return {
                "cpu_time": cpu_time,
                "wall_time": wall_time,
                "cpu_time_per_block": cpu_per_block,
                "memory_used_mb": memory_used,
                "blocks": num_blocks,
                "blocks_created": blocks_created
            }
        except ImportError:
            print("[WARN] psutil not available, using wall time")
            start_time = time.time()
            initial_chain_length = len(blockchain.chain)
            
            for i in range(num_blocks):
                tx = self.create_test_transaction(i)
                blockchain.add_transaction_and_mine(tx)
            
            end_time = time.time()
            wall_time = end_time - start_time
            final_chain_length = len(blockchain.chain)
            blocks_created = final_chain_length - initial_chain_length
            
            return {
                "cpu_time": None,
                "wall_time": wall_time,
                "cpu_time_per_block": wall_time / num_blocks if num_blocks > 0 else 0,
                "memory_used_mb": None,
                "blocks": num_blocks,
                "blocks_created": blocks_created
            }
        except Exception as e:
            print(f"\n    Error: {e}")
            return {"error": str(e)}
    
    def benchmark_scalability(self, blockchain, name: str) -> Dict:
        print(f"  Testing {name} scalability...", end=" ", flush=True)
        
        scalability_results = {}
        test_loads = [10, 50, 100, 200]
        base_index = 10000
        
        for load in test_loads:
            start_time = time.time()
            success_count = 0
            
            for i in range(load):
                tx = self.create_test_transaction(base_index + i)
                try:
                    blockchain.add_transaction_and_mine(tx)
                    success_count += 1
                except Exception:
                    pass
            
            end_time = time.time()
            duration = end_time - start_time
            tps = success_count / duration if duration > 0 else 0
            success_rate = (success_count / load) * 100 if load > 0 else 0
            
            scalability_results[f"{load}_tx"] = {
                "transactions": load,
                "successful": success_count,
                "success_rate": success_rate,
                "duration": duration,
                "tps": tps
            }
            base_index += load
        
        print("[OK]")
        return scalability_results
    
    def initialize_blockchains(self):
        print("\n[1/6] Initializing blockchains...")
        
        pow_bc = SimpleBlockchain(storage_path="pow_test.json")
        print("  Proof of Work initialized")
        
        pos_bc = ProofOfStakeBlockchain(storage_path="pos_test.json")
        pos_bc.add_validator("hospital1", 1000.0)
        pos_bc.add_validator("hospital2", 500.0)
        pos_bc.add_validator("hospital3", 750.0)
        pos_bc.add_validator("hospital4", 300.0)
        print("  Proof of Stake initialized")
        
        pbft_bc = PBFTBlockchain(
            validators=["hospital1", "hospital2", "hospital3", "hospital4"],
            storage_path="pbft_test.json"
        )
        print("  PBFT initialized")
        
        return {
            "pow": pow_bc,
            "pos": pos_bc,
            "pbft": pbft_bc
        }
    
    def run_benchmarks(self, blockchains: Dict):
        print("\n[2/6] Running throughput benchmarks...")
        for name, bc in blockchains.items():
            self.results[name] = {}
            self.results[name]["throughput"] = self.benchmark_throughput(bc, name.upper(), 100)
        
        print("\n[3/6] Running latency benchmarks...")
        for name, bc in blockchains.items():
            self.results[name]["latency"] = self.benchmark_latency(bc, name.upper(), 50)
        
        print("\n[4/6] Running energy consumption benchmarks...")
        for name, bc in blockchains.items():
            self.results[name]["energy"] = self.benchmark_energy(bc, name.upper(), 10)
        
        print("\n[5/6] Running scalability benchmarks...")
        for name, bc in blockchains.items():
            self.results[name]["scalability"] = self.benchmark_scalability(bc, name.upper())
    
    def generate_summary(self):
        print("\n" + "=" * 60)
        print("Performance Summary")
        print("=" * 60)
        
        print(f"\n{'Algorithm':<12} {'Throughput':<15} {'Avg Latency':<15} {'Energy':<15}")
        print("-" * 60)
        
        for name in ["pow", "pos", "pbft"]:
            if name not in self.results:
                continue
            
            tps = self.results[name].get("throughput", {}).get("tps", 0)
            latency = self.results[name].get("latency", {}).get("average_latency", 0)
            energy = self.results[name].get("energy", {}).get("cpu_time")
            
            if energy is None:
                energy = self.results[name].get("energy", {}).get("wall_time", 0)
            
            print(f"{name.upper():<12} {tps:<15.2f} {latency:<15.2f} {energy:<15.2f}")
        
        print("=" * 60)
    
    def save_results(self):
        print("\n[6/6] Generating performance report...")
        
        output_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "algorithms": self.results
        }
        
        results_file = self.output_dir / "results.json"
        with open(results_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"  Results saved to {results_file}")
        
        summary_file = self.output_dir / "summary.txt"
        with open(summary_file, 'w') as f:
            f.write("Blockchain Consensus Algorithm Performance Comparison\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Timestamp: {output_data['timestamp']}\n\n")
            
            for name, data in self.results.items():
                f.write(f"{name.upper()} Results:\n")
                f.write("-" * 30 + "\n")
                
                if "throughput" in data:
                    f.write(f"  Throughput: {data['throughput'].get('tps', 0):.2f} TPS\n")
                
                if "latency" in data:
                    f.write(f"  Avg Latency: {data['latency'].get('average_latency', 0):.2f} ms\n")
                
                if "energy" in data:
                    energy = data['energy'].get('cpu_time') or data['energy'].get('wall_time', 0)
                    if energy is not None:
                        f.write(f"  Energy: {energy:.2f} sec\n")
                    else:
                        f.write(f"  Energy: N/A\n")
                    memory = data['energy'].get('memory_used_mb')
                    if memory is not None:
                        f.write(f"  Memory Used: {memory:.2f} MB\n")
                
                if "latency" in data:
                    if "median_latency" in data['latency']:
                        f.write(f"  Median Latency: {data['latency']['median_latency']:.2f} ms\n")
                    if "p95_latency" in data['latency']:
                        f.write(f"  P95 Latency: {data['latency']['p95_latency']:.2f} ms\n")
                    if "p99_latency" in data['latency']:
                        f.write(f"  P99 Latency: {data['latency']['p99_latency']:.2f} ms\n")
                
                if "scalability" in data:
                    f.write(f"  Scalability: Tested with 10, 50, 100, 200 transactions\n")
                
                f.write("\n")
        
        print(f"  Summary saved to {summary_file}")
    
    def cleanup_test_files(self):
        test_files = ["pow_test.json", "pos_test.json", "pbft_test.json"]
        for file in test_files:
            path = Path(file)
            if path.exists():
                path.unlink()
    
    def run(self):
        print("=" * 60)
        print("Blockchain Consensus Algorithm Performance Comparison")
        print("=" * 60)
        
        try:
            blockchains = self.initialize_blockchains()
            self.run_benchmarks(blockchains)
            self.generate_summary()
            self.save_results()
            
            print("\nBenchmark complete! Check results/ folder")
            
        except Exception as e:
            print(f"\nError during benchmarking: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup_test_files()

if __name__ == "__main__":
    benchmark = BlockchainBenchmark()
    benchmark.run()

