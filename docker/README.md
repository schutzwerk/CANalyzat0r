# CANalyzat0r-docker

This contains a dockerized version of the [CANalyzat0r](https://github.com/schutzwerk/CANalyzat0r) project.

## Starting and building
If you have the `Makefile` of the CANalyzat0r repository you can use `make build` and `make run` to build the image and run the container.

Otherwise you can use the following commands to get the image and run the container manually:

```
$ docker pull schutzwerk/canalyzat0r # Pull the image
$ touch /path/to/CANalyzat0r/files/database.db
$ xhost +local:root # Allow spawning the GUI from the container
$ docker run \
	-it \
	--name canalyzat0r \
	-e DISPLAY=$DISPLAY \
	--net=host \
	--privileged \
	--cap-add=ALL \
	--device /dev/snd \
	-v /tmp/.X11-unix:/tmp/.X11-unix:ro \
	-v /lib/modules:/lib/modules \
	-v /path/to/CANalyzat0r/file/database.db:/opt/CANalyzat0r/data/database.db \
	-v /path/to/sharedFolder:/root/sharedFolder \
	schutzwerk/canalyzat0r:latest
```

## Shared files and folders
- To make all data persistent, the file `database.db` is shared with the container.
- Additionally, the folder `sharedFolder` is mounted into `/root/sharedFolder/` of the container.
