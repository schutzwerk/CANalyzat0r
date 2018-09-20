# This Dockerfile variant uses a previously cloned CANalyzat0r folder instead
# of cloning it from GitHub - useful for development purposes.

FROM ubuntu:latest
LABEL maintainer "Philipp Schmied <pschmied@schutzwerk.com>"


# Install git
RUN apt-get update && \
    apt-get -y install \
        sudo \
        kmod

# Prepare the GUI
RUN mkdir ~/.config
ADD Trolltech.conf /tmp/Trolltech.conf
RUN cat /tmp/Trolltech.conf >> ~/.config/Trolltech.conf && \
    rm /tmp/Trolltech.conf

# Fix for QT in Docker containers
ENV QT_X11_NO_MITSHM 1

# Add the CANalyzat0r folder
ADD CANalyzat0r /opt/CANalyzat0r

# Install the CANalyzat0r dependencies using the bundled script
RUN /opt/CANalyzat0r/install_requirements.sh

WORKDIR /opt/CANalyzat0r
# Test the image
RUN ./CANalyzat0r.sh "smoketest"

CMD ["/bin/bash", "CANalyzat0r.sh"]
