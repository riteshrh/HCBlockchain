# Blockchain Consensus Algorithm Performance Comparison

This benchmark compares three consensus algorithms:
- **Proof of Work (PoW)** - Current implementation
- **Proof of Stake (PoS)** - Stake-based validation
- **PBFT** - Voting-based consensus

## Running the Benchmark

From the `backend` directory:

```bash
python -m tests.benchmark.benchmark_consensus
```

Or directly:

```bash
python tests/benchmark/benchmark_consensus.py
```

## Generating Report

After running benchmarks:

```bash
python tests/benchmark/generate_report.py
```

## Output Files

Results are saved in `tests/benchmark/results/`:
- `results.json` - Raw benchmark data
- `summary.txt` - Text summary
- `performance_report.txt` - Detailed report
- `comparison_charts.png` - Performance charts (if matplotlib installed)

## Requirements

- Python 3.13+
- psutil (optional, for CPU time measurement)
- matplotlib (optional, for chart generation)

Install optional dependencies:
```bash
pip install psutil matplotlib
```

