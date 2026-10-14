#include <mpi.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank = -1;
    char host[256] = {0};
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    gethostname(host, sizeof(host) - 1);
    printf("MPI rank=%d pid=%ld host=%s\n", rank, (long)getpid(), host);
    FILE *f = fopen("/proc/self/status", "r");
    if (f) {
        char line[512];
        while (fgets(line, sizeof(line), f)) {
            if (strncmp(line, "Cpus_allowed_list:", 18) == 0) {
                printf("%s", line);
            }
        }
        fclose(f);
    }
    fflush(stdout);
    sleep(30);
    MPI_Finalize();
    return 0;
}
