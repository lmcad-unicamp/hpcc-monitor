#!/bin/sh
sudo date '+%s' > /home/ubuntu/monitoring-impact.infos
sudo apt update
sudo apt install -y gcc gfortran make libmpich-dev
wget https://lmcad-zabbix-agent.s3.us-east-2.amazonaws.com/NPB3.4-MPI-instrumentado.tar.xz
sudo tar -xf NPB3.4-MPI-instrumentado.tar.xz
cd NPB3.4-MPI/config
gcc -c kernel_stats.c
mkdir -p ../bin
mv kernel_stats.o ../bin
cd ../..
make -C NPB3.4-MPI $2 CLASS=$3
timeout $4 mpiexec -np $1 NPB3.4-MPI/bin/$2.$3.x > /home/ubuntu/monitoring-impact.exp
sudo date '+%s' >> /home/ubuntu/monitoring-impact.infos
curl http://169.254.169.254/latest/meta-data/instance-id >> /home/ubuntu/monitoring-impact.infos
echo "" >> /home/ubuntu/monitoring-impact.infos
sudo cat /proc/cpuinfo >> /home/ubuntu/monitoring-impact.infos