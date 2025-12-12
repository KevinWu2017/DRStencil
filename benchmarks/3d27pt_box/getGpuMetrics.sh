#!/usr/bin/env bash
cp ../gpuMetrics.csv .
for log in prof/*.csv; do
    python3 getGpuMetrics.py "${log%.csv}"
done

