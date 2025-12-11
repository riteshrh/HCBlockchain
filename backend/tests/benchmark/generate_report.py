#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from typing import Dict
from datetime import datetime, timezone

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Charts will not be generated.")

class ReportGenerator:
    def __init__(self, results_file: str = "results/results.json", output_dir: str = "results"):
        self.results_file = Path(__file__).parent / results_file
        self.output_dir = Path(__file__).parent / output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}
    
    def load_results(self):
        if not self.results_file.exists():
            raise FileNotFoundError(f"Results file not found: {self.results_file}")
        
        with open(self.results_file, 'r') as f:
            data = json.load(f)
        
        self.results = data.get("algorithms", {})
        return self.results
    
    def generate_charts(self):
        if not HAS_MATPLOTLIB:
            print("Skipping chart generation (matplotlib not available)")
            return
        
        algorithms = ["PoW", "PoS", "PBFT"]
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1"]
        
        throughput_data = []
        latency_data = []
        energy_data = []
        
        for algo in ["pow", "pos", "pbft"]:
            if algo in self.results:
                throughput = self.results[algo].get("throughput", {}).get("tps", 0)
                latency = self.results[algo].get("latency", {}).get("average_latency", 0)
                energy = self.results[algo].get("energy", {}).get("cpu_time", 0)
                if energy is None:
                    energy = self.results[algo].get("energy", {}).get("wall_time", 0)
                
                throughput_data.append(throughput)
                latency_data.append(latency)
                energy_data.append(energy)
            else:
                throughput_data.append(0)
                latency_data.append(0)
                energy_data.append(0)
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle('Blockchain Consensus Algorithm Performance Comparison', fontsize=14, fontweight='bold')
        
        axes[0].bar(algorithms, throughput_data, color=colors)
        axes[0].set_title('Throughput (Transactions per Second)')
        axes[0].set_ylabel('TPS')
        axes[0].grid(axis='y', alpha=0.3)
        
        axes[1].bar(algorithms, latency_data, color=colors)
        axes[1].set_title('Average Latency (milliseconds)')
        axes[1].set_ylabel('ms')
        axes[1].grid(axis='y', alpha=0.3)
        
        axes[2].bar(algorithms, energy_data, color=colors)
        axes[2].set_title('Energy Consumption (CPU seconds)')
        axes[2].set_ylabel('seconds')
        axes[2].grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        chart_file = self.output_dir / "comparison_charts.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  Charts saved to {chart_file}")
    
    def generate_text_report(self):
        report_file = self.output_dir / "performance_report.txt"
        
        with open(report_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("Blockchain Consensus Algorithm Performance Comparison Report\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            
            f.write("Executive Summary\n")
            f.write("-" * 70 + "\n")
            f.write("This report compares three consensus algorithms:\n")
            f.write("1. Proof of Work (PoW) - Current implementation\n")
            f.write("2. Proof of Stake (PoS) - Stake-based validation\n")
            f.write("3. PBFT - Voting-based consensus\n\n")
            
            f.write("Results\n")
            f.write("-" * 70 + "\n\n")
            
            for algo_name, algo_key in [("Proof of Work", "pow"), ("Proof of Stake", "pos"), ("PBFT", "pbft")]:
                if algo_key not in self.results:
                    continue
                
                f.write(f"{algo_name} ({algo_key.upper()})\n")
                f.write("-" * 30 + "\n")
                
                data = self.results[algo_key]
                
                if "throughput" in data:
                    tps = data["throughput"].get("tps", 0)
                    duration = data["throughput"].get("duration", 0)
                    f.write(f"  Throughput: {tps:.2f} TPS\n")
                    f.write(f"  Duration: {duration:.2f} seconds\n")
                
                if "latency" in data:
                    avg = data["latency"].get("average_latency", 0)
                    min_lat = data["latency"].get("min_latency", 0)
                    max_lat = data["latency"].get("max_latency", 0)
                    median = data["latency"].get("median_latency", 0)
                    p95 = data["latency"].get("p95_latency", 0)
                    p99 = data["latency"].get("p99_latency", 0)
                    std_dev = data["latency"].get("std_dev", 0)
                    f.write(f"  Average Latency: {avg:.2f} ms\n")
                    f.write(f"  Median Latency: {median:.2f} ms\n")
                    f.write(f"  Min Latency: {min_lat:.2f} ms\n")
                    f.write(f"  Max Latency: {max_lat:.2f} ms\n")
                    f.write(f"  P95 Latency: {p95:.2f} ms\n")
                    f.write(f"  P99 Latency: {p99:.2f} ms\n")
                    f.write(f"  Std Deviation: {std_dev:.2f} ms\n")
                
                if "energy" in data:
                    energy = data["energy"].get("cpu_time") or data["energy"].get("wall_time", 0)
                    energy_per_block = data["energy"].get("cpu_time_per_block", 0)
                    memory = data["energy"].get("memory_used_mb")
                    blocks_created = data["energy"].get("blocks_created", 0)
                    f.write(f"  Energy Consumption: {energy:.2f} seconds\n")
                    f.write(f"  Energy per Block: {energy_per_block:.2f} seconds\n")
                    if memory is not None:
                        f.write(f"  Memory Used: {memory:.2f} MB\n")
                    f.write(f"  Blocks Created: {blocks_created}\n")
                
                if "scalability" in data:
                    f.write(f"  Scalability Results:\n")
                    for load_key, load_data in sorted(data["scalability"].items()):
                        tx_count = load_data.get("transactions", 0)
                        tps = load_data.get("tps", 0)
                        success_rate = load_data.get("success_rate", 0)
                        f.write(f"    {tx_count} transactions: {tps:.2f} TPS, {success_rate:.1f}% success\n")
                
                f.write("\n")
            
            f.write("Detailed Comparison Table\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Algorithm':<15} {'Throughput':<15} {'Avg Latency':<15} {'P95 Latency':<15} {'Energy':<15}\n")
            f.write("-" * 70 + "\n")
            
            for algo_name, algo_key in [("PoW", "pow"), ("PoS", "pos"), ("PBFT", "pbft")]:
                if algo_key not in self.results:
                    continue
                
                data = self.results[algo_key]
                tps = data.get("throughput", {}).get("tps", 0)
                latency = data.get("latency", {}).get("average_latency", 0)
                p95 = data.get("latency", {}).get("p95_latency", 0)
                energy = data.get("energy", {}).get("cpu_time")
                if energy is None:
                    energy = data.get("energy", {}).get("wall_time", 0)
                
                f.write(f"{algo_name:<15} {tps:<15.2f} {latency:<15.2f} {p95:<15.2f} {energy:<15.2f}\n")
            
            f.write("\nScalability Comparison\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Algorithm':<15} {'10 TX TPS':<15} {'50 TX TPS':<15} {'100 TX TPS':<15} {'200 TX TPS':<15}\n")
            f.write("-" * 70 + "\n")
            
            for algo_name, algo_key in [("PoW", "pow"), ("PoS", "pos"), ("PBFT", "pbft")]:
                if algo_key not in self.results or "scalability" not in self.results[algo_key]:
                    continue
                
                scalability = self.results[algo_key]["scalability"]
                tps_10 = scalability.get("10_tx", {}).get("tps", 0)
                tps_50 = scalability.get("50_tx", {}).get("tps", 0)
                tps_100 = scalability.get("100_tx", {}).get("tps", 0)
                tps_200 = scalability.get("200_tx", {}).get("tps", 0)
                
                f.write(f"{algo_name:<15} {tps_10:<15.2f} {tps_50:<15.2f} {tps_100:<15.2f} {tps_200:<15.2f}\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("Analysis\n")
            f.write("-" * 70 + "\n\n")
            
            best_tps = max([(k, self.results[k].get("throughput", {}).get("tps", 0)) for k in self.results.keys()], key=lambda x: x[1])
            best_latency = min([(k, self.results[k].get("latency", {}).get("average_latency", 0)) for k in self.results.keys()], key=lambda x: x[1])
            
            energy_values = []
            for k in self.results.keys():
                energy_data = self.results[k].get("energy", {})
                cpu_time = energy_data.get("cpu_time")
                wall_time = energy_data.get("wall_time")
                energy_value = cpu_time if cpu_time is not None else (wall_time if wall_time is not None else float('inf'))
                if energy_value is not None:
                    energy_values.append((k, energy_value))
            
            best_energy = min(energy_values, key=lambda x: x[1]) if energy_values else ("N/A", 0)
            
            f.write(f"Best Throughput: {best_tps[0].upper()} ({best_tps[1]:.2f} TPS)\n")
            f.write(f"Best Latency: {best_latency[0].upper()} ({best_latency[1]:.2f} ms)\n")
            if best_energy[0] != "N/A":
                f.write(f"Best Energy Efficiency: {best_energy[0].upper()} ({best_energy[1]:.2f} sec)\n\n")
            else:
                f.write(f"Best Energy Efficiency: N/A\n\n")
            
            f.write("Performance Analysis\n")
            f.write("-" * 70 + "\n\n")
            
            pow_tps = self.results.get("pow", {}).get("throughput", {}).get("tps", 0)
            pos_tps = self.results.get("pos", {}).get("throughput", {}).get("tps", 0)
            pbft_tps = self.results.get("pbft", {}).get("throughput", {}).get("tps", 0)
            
            if pos_tps > 0 and pow_tps > 0:
                pos_improvement = ((pos_tps - pow_tps) / pow_tps) * 100
                f.write(f"PoS is {pos_improvement:.1f}% faster than PoW in throughput\n")
            
            if pbft_tps > 0 and pow_tps > 0:
                pbft_improvement = ((pbft_tps - pow_tps) / pow_tps) * 100
                f.write(f"PBFT is {pbft_improvement:.1f}% faster than PoW in throughput\n")
            
            pow_latency = self.results.get("pow", {}).get("latency", {}).get("average_latency", 0)
            pos_latency = self.results.get("pos", {}).get("latency", {}).get("average_latency", 0)
            
            if pos_latency > 0 and pow_latency > 0:
                latency_improvement = ((pow_latency - pos_latency) / pow_latency) * 100
                f.write(f"PoS has {latency_improvement:.1f}% lower latency than PoW\n")
            
            f.write("\nRecommendations for Healthcare Use Case:\n")
            f.write("-" * 70 + "\n")
            f.write("PoW: Best for maximum security and decentralization, but slowest\n")
            f.write("     and most energy-intensive. Use when security is paramount.\n\n")
            f.write("PoS: Best overall performance - fastest, most energy-efficient,\n")
            f.write("     and maintains good security. Recommended for production use.\n\n")
            f.write("PBFT: Very fast with deterministic finality, but requires\n")
            f.write("      trusted validators. Best for private/consortium networks.\n")
        
        print(f"  Report saved to {report_file}")
    
    def generate(self):
        print("Generating performance report...")
        self.load_results()
        self.generate_charts()
        self.generate_text_report()
        print("Report generation complete!")

if __name__ == "__main__":
    generator = ReportGenerator()
    generator.generate()

