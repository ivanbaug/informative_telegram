# informative_telegram
Uses the telegram bot to send automated messages with info from various APIs
The bot now persists data of the jobs in a sqlite database, and sets them back if the bot resets or has a power failure.


## Volume to save logging data

```bash
docker volume create vol_telegram
```

Reading data from the volume:

```
docker run --rm -i -v=vol_telegram:/tmp/myvolume busybox find /tmp/myvolume
```

Once verified that the log file exists

```
sudo docker run --rm -i -v=vol_telegram:/tmp/myvolume busybox cat /tmp/myvolume/app.log
```

## Attach to container
```bash
docker exec -it <containerid> /bin/sh
```
Exit container
```
ctrl + p ctrl + q
```