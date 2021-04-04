for i in bt cg sp lu is; do
    python3 script.py r5xlarge $i D 4 15
    python3 script.py c59xlarge $i D 4 15
    python3 script.py i34xlarge $i D 4 15
    python3 script.py r5a8xlarge $i D 4 15
    python3 script.py r58xlarge $i D 4 15
    python3 script.py c54xlarge $i D 4 15
    python3 script.py t32xlarge $i D 4 15
    python3 script.py c5a4xlarge $i D 4 15
    python3 script.py r5axlarge $i D 4 15
    python3 script.py r52xlarge $i D 4 15
    python3 script.py c512xlarge $i D 4 15
    python3 script.py c5n4xlarge $i D 4 15
    python3 script.py i32xlarge $i D 4 15
    python3 script.py r5a2xlarge $i D 4 15
    python3 script.py r512xlarge $i D 4 15
    python3 script.py c5a8xlarge $i D 4 15
    python3 script.py r5n8xlarge $i D 4 15
    python3 script.py c5n9xlarge $i D 4 15
    python3 script.py r54xlarge $i D 4 15
    python3 script.py r5n12xlarge $i D 4 15
done
for i in 4 16; do
    python3 script.py i34xlarge ft D $i 15
    python3 script.py r5a8xlarge ft D $i 15
    python3 script.py r5n8xlarge ft D $i 15
    python3 script.py r58xlarge ft D $i 15
    python3 script.py r5n12xlarge ft D $i 15
    python3 script.py r54xlarge ft D $i 15
    python3 script.py r512xlarge ft D $i 15
done

python3 script.py r5xlarge ep E 4 15
python3 script.py c59xlarge ep E 4 15
python3 script.py i34xlarge ep E 4 15
python3 script.py r5a8xlarge ep E 4 15
python3 script.py r58xlarge ep E 4 15
python3 script.py c54xlarge ep E 4 15
python3 script.py t32xlarge ep E 4 15
python3 script.py c5a4xlarge ep E 4 15
python3 script.py r5axlarge ep E 4 15
python3 script.py r52xlarge ep E 4 15
python3 script.py c512xlarge ep E 4 15
python3 script.py c5n4xlarge ep E 4 15
python3 script.py i32xlarge ep E 4 15
python3 script.py r5a2xlarge ep E 4 15
python3 script.py r512xlarge ep E 4 15
python3 script.py c5a8xlarge ep E 4 15
python3 script.py r5n8xlarge ep E 4 15
python3 script.py c5n9xlarge ep E 4 15
python3 script.py r54xlarge ep E 4 15
python3 script.py r5n12xlarge ep E 4 15