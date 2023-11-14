#include<conio.h>
#include<stdio.h>

void main() {
    int i, j, k = 4, a, b;

    for (i = 0; i <= 4; i++) {
        for (j = 0; j <= 4; j++) {
            a = k + j;
            b = k - j;  // Corrected line
            if (i <= a && i >= b) {
                printf("*");
            }
            else {
                printf(" ");
            }
        }
        printf("\n");
    }
    getch(); // Pauses the output until a key is pressed
}
