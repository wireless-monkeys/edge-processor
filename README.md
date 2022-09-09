# edge-processor

To initialize environment:
1. Initialize venv
```bash
$ python3 -m venv venv
```
2. Activate venv
```bash
$ source venv/bin/activate
```
3. Install packages
```bash
$ pip3 install -r requirements.txt
```

To compile proto:
```bash
$ python3 -m grpc_tools.protoc -I protos --python_out=src/stubs --grpc_python_out=src/stubs protos/*.proto
```
This will generate stubs in `src/stubs` directory.
