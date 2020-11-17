Working under v3.0.0-alpha.2 

It turns out the multi-broker configuration file has two very specific key words (somewhat unexpectedly): "master" and "comms"

```json
{
  "master":{
    "coreType": "test"
  },
  "comms": [
    {
      "coreType": "zmq",
      "port": 23500
    },
    {
      "coreType": "tcp",
      "port": 23700
    },
    {
      "coreType": "udp",
      "port": 23900
    }
  ]
}
```
The `master` coreType was tested on both `zmq` and `test` and both work.
