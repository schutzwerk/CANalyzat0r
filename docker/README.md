# CANalyzat0r-docker

This contains a dockerized version of the [CANalyzat0r](https://github.com/schutzwerk/CANalyzat0r) project.

## Starting and building
If you have the `Makefile` of the CANalyzat0r repository you can use `make build` and `make run` to build the image and run the container. Please note that there's an automated build process in place that pushes the newest version of this project to [Docker Hub](https://hub.docker.com/r/schutzwerk/canalyzat0r/), so `make build` is not a strict requirement. To use the pre-built image, invoke `docker pull schutzwerk/canalyzat0r` followed by a `docker run` command. This command can be generated and executed automatically when using `make run`: This uses the location of the `Makefile` as workspace.

You can also use the following commands to get the image and run the container manually. Please make sure to replace the placeholders with the correct values for your setup:

```
$ docker pull schutzwerk/canalyzat0r # Pull the image
$ touch /path/to/CANalyzat0r/files/database.db # Create the database
$ xhost +local:root # Allow spawning the GUI from the container
$ docker run \
	-it \
	--name canalyzat0r \
	-e DISPLAY=$DISPLAY \
	--net=host \
	--privileged \
	--cap-add=CAP_SYS_MODULE \
	--device /dev/snd \
	-v /tmp/.X11-unix:/tmp/.X11-unix:ro \
	-v /lib/modules:/lib/modules \
	-v /path/to/CANalyzat0r/files/database.db:/opt/CANalyzat0r/data/database.db \
	-v /path/to/sharedFolder:/root/sharedFolder \
	schutzwerk/canalyzat0r:latest
```

## Shared files and folders
- To make all data persistent, the file `database.db` is shared with the container.
- Additionally, the folder `sharedFolder` is mounted into `/root/sharedFolder/` of the container.

## Docker Capabilities and Privileges

- `privileged`: Used to access all CAN interfaces of the host
- `CAP_SYS_MODULE`: Used to load the `can` kernel module from the container
- `--net=host`: Required to access the CAN interfaces of the host
- `xhost +local:root`: Used to spawn the GUI using a shared display. If you don't want to add this rule, it's also possible to [remap](https://docs.docker.com/engine/security/userns-remap/) your user ID to UID `0` inside of the container. Please note that loading the required kernel modules from inside of the container may not work when using this approach.
