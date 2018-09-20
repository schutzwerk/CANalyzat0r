FROM ubuntu:18.04
LABEL maintainer "Philipp Schmied <pschmied@schutzwerk.com>"


# Install git
RUN apt-get update && \
    apt-get -y install \
    git-core \
    sudo \
    kmod

# Prepare the GUI
RUN mkdir ~/.config
ADD Trolltech.conf /tmp/Trolltech.conf
RUN cat /tmp/Trolltech.conf >> ~/.config/Trolltech.conf && \
    rm /tmp/Trolltech.conf

# Fix for QT in Docker containers
ENV QT_X11_NO_MITSHM 1

# Clone the CANalyzat0r repository
RUN git clone https://github.com/schutzwerk/CANalyzat0r /opt/CANalyzat0r

# Install the CANalyzat0r dependencies using the bundled script
RUN /opt/CANalyzat0r/install_requirements.sh

WORKDIR /opt/CANalyzat0r
# Test the image
RUN ./CANalyzat0r.sh "smoketest"


CMD ["/bin/bash", "CANalyzat0r.sh"]
