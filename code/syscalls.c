/* Includes */
#include <sys/stat.h>
#include <stdlib.h>
#include <errno.h>
#include <stdio.h>
#include <signal.h>
#include <time.h>
#include <sys/time.h>
#include <sys/times.h>

/* Variables */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wstrict-prototypes"
extern int errno;
#pragma GCC diagnostic pop

register char * stack_ptr asm("sp");

char *__env[1] = { 0 };
char **environ = __env;

void _init(void);
void _init(void) {

}

/* Functions */
void initialise_monitor_handles(void);
void initialise_monitor_handles() {
}

int _getpid(void);
int _getpid(void) {
  return 1;
}

int _kill(int pid, int sig);
int _kill(int pid, int sig) {
  errno = EINVAL;
  return -1;
}

void _exit(int status);
void _exit(int status) {
  _kill(status, -1);
  while (1) {
  }
}

int _read(int file, char *ptr, int len);
int _read(int file, char *ptr, int len) {
  return len;
}

int _write(int file, char *ptr, int len);
int _write(int file, char *ptr, int len) {
  return len;
}

caddr_t _sbrk(int incr);
caddr_t _sbrk(int incr) {
  extern char end asm ("end"); /* Defined by the linker.  */
  static char * heap_end;
  char * prev_heap_end;
  if (heap_end == NULL) heap_end = &end;

  prev_heap_end = heap_end;

  if (heap_end + incr > stack_ptr) {
    /* Some of the libstdc++-v3 tests rely upon detecting
     out of memory errors, so do not abort here.  */
#if 0
    extern void abort (void);
    _write (1, "_sbrk: Heap and stack collision\n", 32);

    abort ();
#else
    errno = ENOMEM;
    return (caddr_t) -1;
#endif
  }

  heap_end += incr;
  return (caddr_t) prev_heap_end;
}

int _close(int file);
int _close(int file) {
  return -1;
}

int _fstat(int file, struct stat *st);
int _fstat(int file, struct stat *st) {
  st->st_mode = S_IFCHR;
  return 0;
}

int _isatty(int file);
int _isatty(int file) {
  return 1;
}

int _lseek(int file, int ptr, int dir);
int _lseek(int file, int ptr, int dir) {
  return 0;
}

int _open(char *path, int flags, ...);
int _open(char *path, int flags, ...) {
  return -1;
}

int _wait(int *status);
int _wait(int *status) {
  errno = ECHILD;
  return -1;
}

int _unlink(char *name);
int _unlink(char *name) {
  errno = ENOENT;
  return -1;
}

int _times(struct tms *buf);
int _times(struct tms *buf) {
  return -1;
}

int _stat(char *file, struct stat *st);
int _stat(char *file, struct stat *st) {
  st->st_mode = S_IFCHR;
  return 0;
}

int _link(char *old, char *new);
int _link(char *old, char *new) {
  errno = EMLINK;
  return -1;
}

int _fork(void);
int _fork(void) {
  errno = EAGAIN;
  return -1;
}

int _execve(char *name, char **argv, char **env);
int _execve(char *name, char **argv, char **env) {
  errno = ENOMEM;
  return -1;
}
