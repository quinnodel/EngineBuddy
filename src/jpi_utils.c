#include <jpi_parser.h>
#include <stdio.h>
#include <ctype.h>

void printRawJPI(const char *filename)
{
    FILE *file = fopen(filename, "rb");
    if (file == NULL)
    {
        perror("Error opening file");
        return;
    }

    unsigned char byte, last_byte = 0;
    while (fread(&byte, sizeof(byte), 1, file) == 1)
    {
        if (last_byte == '\x0d' && byte == '\x0a')
        {
            printf("\n"); // Insert a newline at the end of a line
        }
        else
        {
            if (isprint(byte))
            {
                printf("%c", byte);
            }
            else
            {
                printf("\\x%02x", byte);
            }
        }
        last_byte = byte;
    }

    fclose(file);
}