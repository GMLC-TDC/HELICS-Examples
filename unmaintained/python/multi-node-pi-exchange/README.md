# multi-node-pi-exchange

```bash
helics_broker -f 2 --interface=tcp://0.0.0.0:4545 --loglevel=7
```

```bash
python pisender.py '0.0.0.0:4545'
```

```bash
python pireceiver.py '0.0.0.0:4545'
```



