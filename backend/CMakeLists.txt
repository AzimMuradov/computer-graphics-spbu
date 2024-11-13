cmake_minimum_required(VERSION 3.29)
project(backend C)

set(CMAKE_C_STANDARD 11)

add_library(backend SHARED library.c third-party/kdtree/kdtree.c)
