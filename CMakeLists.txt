cmake_minimum_required(VERSION 3.16)
project(GameofLife)

option(CompileOpt "Enable running mode on the judger" OFF)

set(CMAKE_CXX_STANDARD 20)

if (CompileOpt)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Ofast")
endif ()

add_executable(GameofLife main.cpp)