#https://github.com/OSGeo/gdal/pkgs/container/gdal
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.4

# Install python3-pip, git, and git LFS
RUN apt-get update && \
    apt-get install -y python3-pip software-properties-common && \
    add-apt-repository ppa:git-core/ppa && \
    apt-get update && \
    apt-get install -y git-lfs && \
    git lfs install

#folder&reqs for streamlit app
COPY ./app .
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

#setup csc allas reqs
RUN python -m pip install python-openstackclient && \
    apt-get install -y restic && \
    curl https://rclone.org/install.sh | bash && \
    apt-get install -y wget && \
    pip3 install s3cmd

#clean apt install files
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#workdirs
VOLUME /notebooks
WORKDIR /notebooks

# Expose port 8888 for Jupyter Notebook
EXPOSE 8888

# Start Jupyter Notebook when docker run
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]