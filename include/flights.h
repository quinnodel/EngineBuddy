#ifndef FLIGHTS_H
#define FLIGHTS_H

#include <stddef.h> // For size_t

typedef struct
{
    int flight_number;
    char *date; // Consider using a more structured type for dates
    char *flags;
    char *isF; // Is this a string or a boolean/integer type?
    double interval_secs;
} Header;

typedef struct
{
    // OIL_T, etc.
    // Flags grabbed from the Header
    // ... other relevant data members
} MemBlock;

typedef struct
{
    MemBlock *dataSnapshots; // Dynamic array of data snapshots
    size_t count;            // Number of data snapshots
    size_t capacity;         // Capacity of the dataSnapshots array
    // ... other relevant data members
} FlightData;

typedef struct
{
    Header *headers;        // Dynamic array of headers (if multiple)
    FlightData *flights;    // Dynamic array of flight data
    size_t flight_count;    // Number of flights
    size_t flight_capacity; // Capacity of the flights array
    // ... other relevant data members
} Flights;

// Function prototypes
Flights *createFlights(size_t initial_capacity);
FlightData *createFlightData(size_t initial_capacity);
MemBlock *createMemBlock();

void destroyFlights(Flights *flights);
void destroyFlightData(FlightData *flightdata);
void destroyMemBlock(MemBlock *memblock);

#endif // FLIGHTS_H
