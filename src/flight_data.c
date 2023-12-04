#include <stdbool.h>

typedef struct FlightHeader
{
    int flight_number;
    char *date;
    char *flags;
    bool isF;
    double interval_secs;
};

typedef struct FlightData
{
};