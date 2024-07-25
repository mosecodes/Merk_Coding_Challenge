## Pear File Overview

The pear files followed a simple format of a header, body, and footer. The header and footer were simple placeholders with repeating integer values of 72 and 70, respectively. The body is where the data was, with simple big-endian, unsigned integers with alternating values for time and intensity running the entire length of the body. The table below shows the format for the first set of values.

| __Location__ | __Length (bytes)__ | __Endianess__ | __format__ | __Value__    |
|--------------|--------------------|---------------|------------|--------------|
| 0x140        | 4                  | big           | uint       | time[0]      |
| 0x144        | 4                  | big           | uint       | intensity[0] |
| ...          |                    |               |            |              |

## Scale File Overview

The scale files were a bit more complicated. There was a header, which held an integer divisor to divide all data point integers by, a tuple of (start, end, interval) giving the start and end indices from which to create the list of ylabels and the size of each ylabel in bytes, and finally an integer that held the number of xlabels. After the header, each row of data began with two '0x48' bytes ('H' character in ASCII) and was followed by 32-bit floating point values for the length of the row. These integers needed to be divided by the file's divisor before being put into the final data array. The below table shows the format for the beginning of the sample file, after which the pattern of 'row header, value, value, value, etc' continues for the rest of the file.

| __Location__ | __Length (bytes)__ | __Endianess__ | __format__ | __Value__                |
|--------------|--------------------|---------------|------------|--------------------------|
| 0x80         | 2                  | big           | uint       | divisor[20]              |
| 0x100        | 2                  | big           | uint       | first ylabel[190]        |
| 0x102        | 2                  | big           | uint       | last ylabel[360]         |
| 0x104        | 2                  | big           | uint       | ylabel step[10]          |
| 0x180        | 2                  | big           | uint       | number of xlabels[11527] |
| 0x200        | 2                  | big           | uint8 (2)  | marker for new row[HH]   |
| 0x202        | 4                  | big           | uint32     | first data value[0]      |
| 0x206        | 4                  | big           | uint32     | second data value[-20]   |
| ...          |                    |               |            |                          |

## Sixtysix Files Overview

The third problem seemed to resemble CSR compression format for compressing sparse data. Each problem consisted of three files, A, B, and C. In my solution, I found that I was able to reconstruct the data without any issues using only files A and B, though I have no way to verify my csv files. 
#### File A
File A consisted of a 10-byte format. Each 10-byte sequence of data corresponded to a xlabel and row for the final data table. The first 4 bytes were an integer offset (in decimal) where you could find the non-zero ylabels and data for the current row in file B. The second 4 bytes were the integer value for the xlabel in milliseconds, which needed to be converted into a float in minutes format for the final table, rounded to 4 decimals. The final 2 bytes were a 16-bit integer giving how many non-zero columns to read from file B. This file essentially was a map to file B for constructing the data rows and gathering the xlabels. The table below outlines the first two 10-byte sequences and their corresponding values.

| __Location__ | __Length (bytes)__ | __Endianess__ | __format__ | __Value__                     |
|--------------|--------------------|---------------|------------|-------------------------------|
| 0x00         | 4                  | big           | uint32     | File B offset[24876]          |
| 0x04         | 4                  | big           | uint32     | xlabel (ms)[0]                |
| 0x08         | 2                  | big           | uint16     | number of non-zero columns[0] |
| 0x0A         | 4                  | big           | uint32     | File B offset[261834]         |
| 0x0E         | 4                  | big           | uint32     | xlabel (ms)[11]               |
| 0x12         | 2                  | big           | uint16     | number of non-zero columns[0] |
| ...          |                    |               |            |                               |

#### File B
File B consisted of a 6-byte, little endian format, where each sequence gave both a ylabel and a data value for that ylabel. The first two bytes were a 16-bit integer for the ylabel and the following 4 bytes were for the data value. I essentially accessed this file to fill the non-zero parts of the data rows using the information from file A. The below table shows the format for the first two sequences of the sample file.

| __Location__ | __Length (bytes)__ | __Endianess__ | __format__ | __Value__    |
|--------------|--------------------|---------------|------------|--------------|
| 0x00         | 2                  | little        | uint16     | ylabel[306]  |
| 0x02         | 4                  | little        | uint32     | value[31]    |
| 0x06         | 2                  | little        | uint16     | ylabel[316]  |
| 0x08         | 4                  | little        | uint32     | value[32893] |
| ...          |                    |               |            |              |

#### File C
It seemed that file C did not have any helpful data. Every instance of file C across all the problems and the sample was the same, except for the 5th byte which was either b'0x42' or b'0x43' (66 or 67 in base-10). The tie between this value and the name of the problem made it seem important but ended up not providing anything I needed to put together the solutions. 


