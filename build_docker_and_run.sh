#!/bin/bash
set -e 
docker build -t 'delay_fault_image_fedora' .
docker run -ti --entrypoint /bin/bash -v $(realpath .):/current_dir delay_fault_image_fedora
