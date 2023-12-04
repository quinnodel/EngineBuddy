#include <stdio.h>
#include <string.h>
#include <jpi_parser.h>
#include <flight_data.h>
#include <csv_writer.h>
#include <jpi_utils.h>

int main(int argc, char *argv[])
{
    if (argc != 2)
    {
        fprintf(stderr, "Usage: %s <file.jpi>\n", argv[0]);
        return 1;
    }

    printRawJPI(argv[1]);
    return 0;
}