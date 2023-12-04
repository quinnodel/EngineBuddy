cmake_minimum_required(VERSION 3.10)  # Set the minimum version of CMake

# Set your project name and version
project(EngineBuddy VERSION 1.0)

# Specify the C standard
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED True)

# Add executable - list all source files needed for the executable
add_executable(enginebuddy src/jpi_decode.c)

# Include directories for header files
target_include_directories(enginebuddy PRIVATE src)

#find_package(CURL REQUIRED)

#target_link_libraries(cweather ${CURL_LIBRARIES})
