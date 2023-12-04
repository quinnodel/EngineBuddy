cmake_minimum_required(VERSION 3.10)  # Set the minimum version of CMake

# Set your project name and version
project(EngineBuddy VERSION 1.0)

# Specify the C standard
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED True)

# Set compiler flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall")

# Add executable - list all source files needed for the executable
add_executable(enginebuddy 
    src/main.c
    src/jpi_parser.c
    src/flight_data.c
    src/csv_writer.c
    src/jpi_utils.c
    # Add other source files here
)

# Include directories for header files
# Assuming your headers are in the 'include' directory
target_include_directories(enginebuddy PRIVATE include)

# If you have external libraries to link, uncomment and modify the following lines
# find_package(CURL REQUIRED)
# target_link_libraries(enginebuddy ${CURL_LIBRARIES})
