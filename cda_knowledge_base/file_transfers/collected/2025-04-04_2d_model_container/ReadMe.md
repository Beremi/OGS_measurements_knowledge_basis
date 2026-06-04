# OGS with docker

Either build container image from Dockerfile: `docker buildx build -f Dockerfile .`

Or alternatively load container image from tar file, e.g. in case build wither Dockerfile fails: `docker load < docker_ogs6.5.4.tar.gz`

[How to use docker load](https://docs.docker.com/reference/cli/docker/image/load/#load-images-from-stdin)

Run container with mounting bin (replace src and dst if needed): `docker run -it --mount type=bind,src=/home/,dst=/home master_ogs_container`

In container check if ogs works: `ogs --version`

If it works, navigate to folder container OGS project and execute: `ogs cd_a_open_niche_quad.prj`

# OGS with apptainer

We are mainly using apptainer containers. So, if this is an option for you, you can use `apptainer_ogs6.5.4.sif`. If so, you need to install the apptainer package for your Linux, e.g. [Ubuntu](https://apptainer.org/docs/admin/main/installation.html#install-ubuntu-packages)
Navigate to the folder with the OGS project and run: `apptainer exec apptainer_ogs6.5.4.sif ogs cd_a_open_niche_quad.prj`

(The current folder is mounted automatically.)


