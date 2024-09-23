sudo apk add gcc g++ musl-dev make
git clone https://github.com/joan2937/lg.git
cd lg
make
sudo make install
ls /usr/local/lib | grep lgpio
pip install lgpio
