#!/bin/sh
sudo date '+%s' > /home/ubuntu/$1.$3.$4.$2.infos
sudo apt update
sudo apt install -y gcc gfortran make libmpich-dev
wget https://lmcad-zabbix-agent.s3.us-east-2.amazonaws.com/NPB3.4-MPI-instrumentado.tar.xz
sudo tar -xf NPB3.4-MPI-instrumentado.tar.xz
cd NPB3.4-MPI/config
gcc -c kernel_stats.c
mkdir -p ../bin
mv kernel_stats.o ../bin
cd ../..
make -C NPB3.4-MPI $3 CLASS=$4
timeout $5 mpiexec -np $2 NPB3.4-MPI/bin/$3.$4.x > /home/ubuntu/$1.$3.$4.$2.exp
sudo date '+%s' >> /home/ubuntu/$1.$3.$4.$2.infos
curl http://169.254.169.254/latest/meta-data/instance-id >> /home/ubuntu/$1.$3.$4.$2.infos
echo "" >> /home/ubuntu/$1.$3.$4.$2.infos
sudo cat /proc/cpuinfo >> /home/ubuntu/$1.$3.$4.$2.infos