# syntax=docker/dockerfile:1.4

FROM ubuntu:24.04 AS build

# Generated with ogs-container-maker 2.5.0

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        make \
        patch \
        tar \
        unzip \
        wget && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        tzdata && \
    rm -rf /var/lib/apt/lists/*

ENV TZ=Europe/Berlin

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

ENV PIP_BREAK_SYSTEM_PACKAGES=1

# --- Begin compiler.py ---

# GNU compiler
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        g++ \
        gcc && \
    rm -rf /var/lib/apt/lists/*

# --- End compiler.py ---

# --- Begin ogs.py ---

# OGS base building block
# Python
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3 \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3-pip \
        python3-virtualenv && \
    rm -rf /var/lib/apt/lists/*
RUN pip3 install pre-commit cmake-format
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        git \
        ninja-build \
        python-is-python3 \
        python3-venv && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /apps /scratch /lustre /work /projects /data

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        gnupg \
        wget && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/share/keyrings && \
    rm -f /usr/share/keyrings/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2023.gpg && \
    wget -qO - https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2023.PUB | gpg --dearmor -o /usr/share/keyrings/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2023.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2023.gpg] https://apt.repos.intel.com/oneapi all main" >> /etc/apt/sources.list.d/hpccm.list && \
    apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        intel-oneapi-mkl-devel-2021.4.0 && \
    rm -rf /var/lib/apt/lists/*

ENV LD_LIBRARY_PATH=/opt/intel/oneapi/tbb/2021.4.0/env/../lib/intel64/gcc4.8:/opt/intel/oneapi/mkl/2021.4.0/lib/intel64:/opt/intel/oneapi/compiler/2021.4.0/linux/lib:/opt/intel/oneapi/compiler/2021.4.0/linux/lib/x64:/opt/intel/oneapi/compiler/2021.4.0/linux/lib/emu:/opt/intel/oneapi/compiler/2021.4.0/linux/compiler/lib/intel64_lin:$LD_LIBRARY_PATH

# CMake version 3.22.3
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        make \
        wget && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/tmp && wget -q -nc --no-check-certificate -P /var/tmp https://github.com/Kitware/CMake/releases/download/v3.22.3/cmake-3.22.3-linux-x86_64.sh && \
    mkdir -p /usr/local && \
    /bin/sh /var/tmp/cmake-3.22.3-linux-x86_64.sh --prefix=/usr/local --skip-license && \
    rm -rf /var/tmp/cmake-3.22.3-linux-x86_64.sh
ENV PATH=/usr/local/bin:$PATH

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        libxml2-dev \
        xsltproc && \
    rm -rf /var/lib/apt/lists/*

# https://gitlab.kitware.com/vtk/vtk/-/archive/v9.3.0/vtk-v9.3.0.tar.gz
RUN mkdir -p /var/tmp && wget -q -nc --no-check-certificate -P /var/tmp https://gitlab.kitware.com/vtk/vtk/-/archive/v9.3.0/vtk-v9.3.0.tar.gz && \
    mkdir -p /var/tmp && tar -x -f /var/tmp/vtk-v9.3.0.tar.gz -C /var/tmp -z && \
    mkdir -p /var/tmp/vtk-v9.3.0/build && cd /var/tmp/vtk-v9.3.0/build && CC=gcc CFLAGS='-march=x86-64 -mtune=generic' CXX=g++ CXXFLAGS='-march=x86-64 -mtune=generic' cmake -DCMAKE_INSTALL_PREFIX=/usr/local/vtk -DVTK_MODULE_ENABLE_VTK_FiltersSources=YES -DVTK_MODULE_ENABLE_VTK_FiltersGeneral=YES -DVTK_MODULE_ENABLE_VTK_FiltersParallel=YES -DVTK_MODULE_ENABLE_VTK_FiltersGeneral=YES -DVTK_MODULE_ENABLE_VTK_IOLegacy=YES -DVTK_MODULE_ENABLE_VTK_IOXML=YES -DVTK_USE_64BIT_IDS=ON -DVTK_ENABLE_WRAPPING=OFF -DVTK_BUILD_TESTING=OFF -DVTK_BUILD_EXAMPLES=OFF -DBUILD_TESTING=OFF -DVTK_GROUP_ENABLE_StandAlone=DONT_WANT -DVTK_GROUP_ENABLE_Rendering=DONT_WANT /var/tmp/vtk-v9.3.0 && \
    cmake --build /var/tmp/vtk-v9.3.0/build --target all -- -j$(nproc) && \
    cmake --build /var/tmp/vtk-v9.3.0/build --target install -- -j$(nproc) && \
    echo "/usr/local/vtk/lib" >> /etc/ld.so.conf.d/hpccm.conf && ldconfig && \
    rm -rf /var/tmp/vtk-v9.3.0 /var/tmp/vtk-v9.3.0.tar.gz
ENV VTK_ROOT=/usr/local/vtk

ENV CMAKE_GENERATOR=Ninja

# https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz
RUN mkdir -p /var/tmp && wget -q -nc --no-check-certificate -P /var/tmp https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz && \
    mkdir -p /var/tmp && tar -x -f /var/tmp/eigen-3.4.0.tar.gz -C /var/tmp -z && \
    mkdir -p /var/tmp/eigen-3.4.0/build && cd /var/tmp/eigen-3.4.0/build && CC=gcc CFLAGS='-march=x86-64 -mtune=generic' CXX=g++ CXXFLAGS='-march=x86-64 -mtune=generic' cmake -DCMAKE_INSTALL_PREFIX=/usr/local/eigen /var/tmp/eigen-3.4.0 && \
    cmake --build /var/tmp/eigen-3.4.0/build --target all -- -j$(nproc) && \
    cmake --build /var/tmp/eigen-3.4.0/build --target install -- -j$(nproc) && \
    rm -rf /var/tmp/eigen-3.4.0 /var/tmp/eigen-3.4.0.tar.gz
ENV Eigen3_DIR=/usr/local/eigen \
    Eigen3_ROOT=/usr/local/eigen

# HDF5 version 1.10.7
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        bzip2 \
        file \
        make \
        wget \
        zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/tmp && wget -q -nc --no-check-certificate -P /var/tmp https://support.hdfgroup.org/ftp/HDF5/releases/hdf5-1.10/hdf5-1.10.7/src/hdf5-1.10.7.tar.bz2 && \
    mkdir -p /var/tmp && tar -x -f /var/tmp/hdf5-1.10.7.tar.bz2 -C /var/tmp -j && \
    cd /var/tmp/hdf5-1.10.7 &&  CC=gcc CFLAGS='-march=x86-64 -mtune=generic' CXX=g++ CXXFLAGS='-march=x86-64 -mtune=generic' ./configure --prefix=/usr/local/hdf5 --enable-cxx && \
    make -j$(nproc) && \
    make -j$(nproc) install && \
    echo "/usr/local/hdf5/lib" >> /etc/ld.so.conf.d/hpccm.conf && ldconfig && \
    rm -rf /var/tmp/hdf5-1.10.7 /var/tmp/hdf5-1.10.7.tar.bz2
ENV CPATH=/usr/local/hdf5/include:$CPATH \
    HDF5_DIR=/usr/local/hdf5 \
    LIBRARY_PATH=/usr/local/hdf5/lib:$LIBRARY_PATH \
    PATH=/usr/local/hdf5/bin:$PATH

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        patchelf \
        pkg-config && \
    rm -rf /var/lib/apt/lists/*

ARG OGS_COMMIT_HASH=cb5b3235101edecf3ba55e1039fe3c19bc13c636

# OpenGeoSys build from repo ogs/ogs, branch 6.5.4
RUN mkdir -p /usr/local/ogs && cd /usr/local/ogs && \
    git clone --filter=blob:limit=100k --branch 6.5.4 https://gitlab.opengeosys.org/ogs/ogs src && \
    (cd src && git reset --hard cb5b3235101edecf3ba55e1039fe3c19bc13c636) && \
    (cd src && git fetch --tags) && \
    echo '{\n  "version": 3,\n  "cmakeMinimumRequired": {\n    "major": 3,\n    "minor": 21,\n    "patch": 0\n  },\n  "configurePresets": [\n    {\n      "name": "_binary_dir_bgr",\n      "hidden" : true,\n      "binaryDir": "$env{WORKSPACE}/build-root/build"\n    },\n    {\n      "name": "bgr-container",\n      "inherits": [\n        "_container"\n      ],\n      "cacheVariables": {\n        "OGS_CPU_ARCHITECTURE": "generic"\n      }\n    },\n    {\n      "name": "petsc-bgr-container",\n      "inherits": [\n        "_container",\n        "_petsc_pardiso_on_container",\n        "_mkl_on_container"\n      ],\n      "cacheVariables": {\n        "OGS_CPU_ARCHITECTURE": "generic"\n      }\n    },\n    {\n      "name": "_release_bgr",\n      "hidden" : true,\n      "generator": "Unix Makefiles",\n      "cacheVariables": {\n        "CMAKE_BUILD_TYPE": "Release",\n        "OGS_TEST_NOTEBOOKS": "OFF",\n        "BUILD_SHARED_LIBS": "ON"\n      }\n    },\n    {\n      "name": "_debug_bgr",\n      "hidden" : true,\n      "generator": "Unix Makefiles",\n      "cacheVariables": {\n        "CMAKE_BUILD_TYPE": "Debug",\n        "OGS_TEST_NOTEBOOKS": "OFF",\n        "BUILD_SHARED_LIBS": "ON"\n      }\n    },\n    {\n      "name": "_container",\n      "hidden" : true,\n      "cacheVariables": {\n        "CMAKE_BUILD_TYPE": "Release",\n        "OGS_TEST_NOTEBOOKS": "OFF",\n        "OGS_CPU_ARCHITECTURE": "generic"\n      }\n    },\n    {\n      "name": "_mkl_on",\n      "hidden" : true,\n      "cacheVariables": {\n        "OGS_USE_MKL": "ON"\n      }\n    },\n    {\n      "name": "_mkl_on_container",\n      "hidden" : true,\n      "cacheVariables": {\n        "OGS_USE_MKL": "ON"\n      }\n    },\n    {\n      "name": "_mkl_off",\n      "hidden" : true,\n      "cacheVariables": {\n        "OGS_USE_MKL": "OFF"\n      }\n    },\n    {\n      "name": "_mfront_on",\n      "hidden" : true,\n      "inherits": [\n        "_install_dependencies"\n      ],\n      "cacheVariables": {\n        "OGS_USE_MFRONT": "ON",\n        "OGS_BUILD_TFEL": "ON"\n      }\n    },\n    {\n      "name": "_mfront_off",\n      "hidden" : true,\n      "cacheVariables": {\n        "OGS_USE_MFRONT": "OFF",\n        "OGS_BUILD_TFEL": "OFF"\n      }\n    },\n    {\n      "name": "_petsc_on",\n      "hidden" : true,\n      "inherits": [\n        "_install_dependencies"\n      ],\n      "cacheVariables": {\n        "OGS_USE_PYTHON": "OFF",\n        "BUILD_SHARED_LIBS": "ON",\n        "OGS_USE_PETSC": "ON",\n        "CMAKE_C_COMPILER": "/usr/lib64/mpi/gcc/openmpi/bin/mpicc",\n        "CMAKE_CXX_COMPILER": "/usr/lib64/mpi/gcc/openmpi/bin/mpic++",\n        "OGS_BUILD_UTILS": "ON",\n        "OGS_PETSC_CONFIG_OPTIONS": "--download-fc=1;--with-openmpi3;--download-mumps;--download-scalapack;--download-ptscotch;--download-hypre",\n        "OGS_EIGEN_PARALLEL_BACKEND": "OpenMP",\n        "OGS_BUILD_HDF5": "ON",\n        "OGS_BUILD_ZLIB": "ON",\n        "OGS_BUILD_PETSC": "ON"\n      }\n    },\n    {\n      "name": "_petsc_on_container",\n      "hidden" : true,\n      "cacheVariables": {\n        "OGS_USE_PYTHON": "OFF",\n        "BUILD_SHARED_LIBS": "ON",\n        "OGS_USE_PETSC": "ON",\n        "OGS_BUILD_UTILS": "ON"\n      }\n    },\n    {\n      "name": "_petsc_pardiso_on",\n      "hidden" : true,\n      "inherits": [\n        "_install_dependencies"\n      ],\n      "cacheVariables": {\n        "OGS_USE_PYTHON": "OFF",\n        "BUILD_SHARED_LIBS": "ON",\n        "OGS_USE_PETSC": "ON",\n        "CMAKE_C_COMPILER": "/usr/lib64/mpi/gcc/openmpi/bin/mpicc",\n        "CMAKE_CXX_COMPILER": "/usr/lib64/mpi/gcc/openmpi/bin/mpic++",\n        "OGS_BUILD_UTILS": "ON",\n        "OGS_PETSC_CONFIG_OPTIONS": "--download-f2cblaslapack=0;--with-blaslapack-dir=/opt/intel/compilers_and_libraries_2019.5.281/linux/mkl/;--with-mkl_pardiso-dir=/opt/intel/compilers_and_libraries_2019.5.281/linux/mkl/;--download-fc=1;--with-openmpi3;--download-mumps;--download-scalapack;--download-ptscotch;--download-hypre;--with-mkl_cpardiso-dir=/opt/intel/compilers_and_libraries_2019.5.281/linux/mkl/",\n        "OGS_EIGEN_PARALLEL_BACKEND": "OpenMP",\n        "OGS_BUILD_HDF5": "ON",\n        "OGS_BUILD_ZLIB": "ON",\n        "OGS_BUILD_PETSC": "ON"\n      }\n    },\n    {\n      "name": "_petsc_pardiso_on_container",\n      "hidden" : true,\n      "cacheVariables": {\n        "OGS_USE_PYTHON": "OFF",\n        "BUILD_SHARED_LIBS": "ON",\n        "OGS_USE_PETSC": "ON",\n        "OGS_EIGEN_PARALLEL_BACKEND": "OpenMP",\n        "OGS_BUILD_UTILS": "ON"\n      }\n    },\n    {\n      "name": "_install_dependencies",\n      "hidden" : true,\n      "cacheVariables": {\n        "OGS_INSTALL_DEPENDENCIES": "ON"\n      }\n    },\n    {\n      "name": "_selected_processes",\n      "hidden" : true,\n      "cacheVariables": {\n        "OGS_BUILD_PROCESSES": "RichardsMechanics;TH2M;ThermoHydroMechanics;ThermoRichardsMechanics"\n      }\n    }\n  ],\n  "testPresets": [\n    {\n      "name": "bgr",\n      "configurePreset": "bgr-container",\n      "output": {\n        "outputOnFailure": true\n      },\n      "filter": {\n        "exclude": {\n          "label": "large",\n          "name": "3D_3BHEs_array"\n        }\n      },\n      "execution": {\n        "repeat": {\n          "mode": "until-pass",\n          "count": 2\n        }\n      }\n    }\n  ]\n}\n' >> /usr/local/ogs/src/CMakeUserPresets.json && \
    . /opt/intel/oneapi/setvars.sh && \
    mkdir -p /usr/local/ogs/build && cd /usr/local/ogs/build && CC=gcc CFLAGS='-march=x86-64 -mtune=generic' CXX=g++ CXXFLAGS='-march=x86-64 -mtune=generic' cmake -DCMAKE_INSTALL_PREFIX=/usr/local  -DOGS_USE_MKL=ON -G Ninja -DCMAKE_INSTALL_PREFIX=/usr/local/ogs -DOGS_CPU_ARCHITECTURE=OFF -DOGS_INSTALL_DEPENDENCIES=ON -DBUILD_SHARED_LIBS=ON --preset=bgr-container -B /usr/local/ogs/build /usr/local/ogs/src && \
    cmake --build /usr/local/ogs/build --target all -- -j8
ENV PATH=/usr/local/ogs/build/bin:$PATH
LABEL cmake_args=' -DOGS_USE_MKL=ON -G Ninja -DCMAKE_INSTALL_PREFIX=/usr/local/ogs -DOGS_CPU_ARCHITECTURE=OFF -DOGS_INSTALL_DEPENDENCIES=ON -DBUILD_SHARED_LIBS=ON --preset=bgr-container -B /usr/local/ogs/build' \
    version='ogs/ogs@6.5.4 (cb5b3235101edecf3ba55e1039fe3c19bc13c636)'

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        libgl1 \
        libglu1-mesa \
        libglx-mesa0 \
        xvfb && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        fuse2fs \
        time && \
    rm -rf /var/lib/apt/lists/*
