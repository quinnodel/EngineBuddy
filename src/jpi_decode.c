#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

void print_file_contents(const char *filename)
{
    FILE *file = fopen(filename, "rb");
    if (file == NULL)
    {
        perror("Error opening file");
        return;
    }

    unsigned char byte;
    while (fread(&byte, sizeof(byte), 1, file) == 1)
    {
        if (isprint(byte))
        {
            // If the byte is a printable character, print it as a character
            printf("%c", byte);
        }
        else
        {
            // If the byte is not printable, print it in hexadecimal
            printf("\\x%02x", byte);
        }
    }

    fclose(file);
}

int main(int argc, char *argv[])
{
    if (argc != 2)
    {
        fprintf(stderr, "Usage: %s <file.jpi>\n", argv[0]);
        return 1;
    }

    print_file_contents(argv[1]);
    return 0;
}
