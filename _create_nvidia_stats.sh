#!/bin/bash

PID=$1
ENC=$(( RANDOM % 100 ))
if [ -z "$PID" ]; then
	PID="12345"
fi

mkdir -p /var/run/nvidia_stats
cat <<EOF > /var/run/nvidia_stats/pmon 
# gpu        pid  type    sm   mem   enc   dec   command
# Idx          #   C/G     %     %     %     %   name
    0       6662     C     0     0     0     4   ffmpeg         
    0       $PID     C    34     7    23     2   ffmpeg 
EOF
cat <<EOF > /var/run/nvidia_stats/usage
driver_version, count, name, serial, uuid, pci.bus_id, index, fan.speed [%], pstate, memory.total [MiB], memory.used [MiB], memory.free [MiB], utilization.memory [%], utilization.gpu [%], temperature.gpu
440.100, 1, Tesla T4, 1325219083788, GPU-bbd3f1b1-660a-44b0-911f-169e11579607, 00000000:AF:00.0, 0, [N/A], P0, 15109 MiB, 2003 MiB, 13106 MiB, 9 %, 36 %, 45
EOF
cat <<EOF > /var/run/nvidia_stats/compute_query
timestamp, gpu_name, gpu_bus_id, pid, process_name, used_gpu_memory [MiB]
2020/10/27 19:41:10.301, Tesla T4, 00000000:AF:00.0, 6662, /usr/local/bin/ffmpeg, 761 MiB
2020/10/27 19:41:10.301, Tesla T4, 00000000:AF:00.0, $PID, /usr/local/bin/ffmpeg, 1227 MiB
EOF

cat <<EOF > /var/run/nvidia_stats/dmon
# gpu   pwr gtemp mtemp    sm   mem   enc   dec  mclk  pclk
# Idx     W     C     C     %     %     %     %   MHz   MHz
    0    34    44     -    36     8    $ENC    10  5000   810
EOF
