#include <stdio.h>
#include <stdlib.h>
#include <gmshc.h>
#include "util.h"
#include "cJSON.h" 


int main(int argc, char** argv) {


    FILE *file = fopen("../test.json", "rb");
    if (!file) {
        perror("Cannot open config.json");
        return 1;
    }
    
    long len = utilGetFileSize(file);

    char *buffer = malloc(len + 1);
    if (!buffer) {
        perror("Memory allocation failed");
        fclose(file);
        return 1;
    }

    fread(buffer, 1, len, file);
    buffer[len] = '\0';
    fclose(file);

    cJSON *json = cJSON_Parse(buffer);
    free(buffer);

    if (!json) {
        fprintf(stderr, "Error parsing JSON: %s\n", cJSON_GetErrorPtr());
        return 1;
    }

    cJSON *meshSize = cJSON_GetObjectItem(json, "hello");
    cJSON *length = cJSON_GetObjectItem(json, "test");

    if (cJSON_IsNumber(meshSize)) printf("hello = %f\n", meshSize->valuedouble);
    if (cJSON_IsNumber(length))   printf("test = %f\n", length->valuedouble);

    cJSON_Delete(json);



//     int ierr;
    // gmshInitialize(argc, argv, 1, 0, &ierr);

    // if (!gmshIsInitialized(&ierr)) {
    //     fprintf(stderr, "Error initializing GMSH.\n");
    //     return 1;
    // }


    // gmshModelAdd("line_model", &ierr);

    // int p1 = gmshModelGeoAddPoint(0.0, 0.0, 0.0, 1.0e-3, 1, &ierr);
    // int p2 = gmshModelGeoAddPoint(1.0, 0.0, 0.0, 1.0e-3, 2, &ierr);

    // gmshModelGeoAddLine(p1, p2, 1, &ierr);

    // gmshModelGeoSynchronize(&ierr);

    // gmshFltkRun(&ierr);

    // gmshFinalize(&ierr);


    return 0;
}
