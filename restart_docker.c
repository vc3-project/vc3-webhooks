#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main()
{
    setuid(0);
    char *args[] = {"/bin/systemctl", "restart", "website.service", '\0'};
    char *env[] = {};
    execve("/bin/systemctl", args, env);
    return 0;
 }
