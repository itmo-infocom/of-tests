#define _GNU_SOURCE     /* resolves u_char typedef in scsi/scsi.h [lk 2.4] */

#include <pthread.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <ctype.h>
#include <signal.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <scsi/sg.h>


#define handle_error_en(en, msg) \
        do { errno = en; perror(msg); exit(EXIT_FAILURE); } while (0)

#define handle_error(msg) \
        do { perror(msg); exit(EXIT_FAILURE); } while (0)

struct thread_info {    /* Used as argument to thread_start() */
    pthread_t thread_id;        /* ID returned by pthread_create() */
    int       thread_num;       /* Application-defined thread # */
    char     *device;           /* Device name */
    int       time;             /* Time of execution in secs */
    int       size;             /* Size of data for transfer in bytes */
};

#define INQ_REPLY_LEN 96        /* logic assumes >= sizeof(inqCmdBlk) */
#define INQ_CMD_LEN 6

/* Thread start function: read testing */

static void *
thread_start(void *arg)
{
    struct thread_info *tinfo = (struct thread_info *) arg;
    int f;
    long int *cnt;
    time_t secs;
    unsigned char inqCmdBlk [INQ_CMD_LEN] =
                                {0x12, 0, 0, 0, INQ_REPLY_LEN, 0};
    unsigned char inqBuff[INQ_REPLY_LEN];
    sg_io_hdr_t io_hdr;
    unsigned char sense_buffer[32];

    printf("Thread %d: transfering %d bytes from %s\n",
            tinfo->thread_num, tinfo->size, tinfo->device);

    f = open(tinfo->device,O_RDONLY|O_DIRECT);
    if (f < 0)
        handle_error("open");

    cnt = calloc(1, sizeof(int));
    if (cnt == NULL)
        handle_error("calloc");
    *cnt = 0;

    secs = time(NULL) + tinfo->time;

    /* Prepare INQUIRY command */
    memset(&io_hdr, 0, sizeof(sg_io_hdr_t));
    io_hdr.interface_id = 'S';
    io_hdr.cmd_len = sizeof(inqCmdBlk);
    /* io_hdr.iovec_count = 0; */  /* memset takes care of this */
    io_hdr.mx_sb_len = sizeof(sense_buffer);
    io_hdr.dxfer_direction = SG_DXFER_FROM_DEV;
    io_hdr.dxfer_len = INQ_REPLY_LEN;
    io_hdr.dxferp = inqBuff;
    io_hdr.cmdp = inqCmdBlk;
    io_hdr.sbp = sense_buffer;
    io_hdr.timeout = 20000;     /* 20000 millisecs == 20 seconds */
    /* io_hdr.flags = 0; */     /* take defaults: indirect IO, etc */
    /* io_hdr.pack_id = 0; */
    /* io_hdr.usr_ptr = NULL; */

    while(time(NULL) <= secs) {
        if (ioctl(f, SG_IO, &io_hdr) < 0) {
            perror("sg_simple2: Inquiry SG_IO ioctl error");
            close(f);
        return cnt;
        }
        (*cnt)++;
    }
    close(f);

    return cnt;
}

void usage(char *name)
{
    fprintf(stderr, "Usage: %s /dev/device time [threads]\n",
            name);
    exit(EXIT_FAILURE);
}

int
main(int argc, char *argv[])
{
    int s, tnum, opt, num_threads;
    struct thread_info *tinfo;
    void *res;
    FILE *p;
    long int cnt=0;
    time_t time;

    if(argc == 1) usage(argv[0]);
    while ((opt = getopt(argc, argv, "h:")) != -1) {
        switch (opt) {
        case 'h':
        default:
            usage(argv[0]);
        }
    }

    time = atoi(argv[2]);    

    if (argc >= 4) { num_threads = atoi(argv[3]); }
    else {
        /* By default num_threads == CPUs -1 */
        p = popen("/usr/bin/getconf _NPROCESSORS_ONLN", "r");
        fscanf(p,"%d",&num_threads);
        pclose(p);
        num_threads--;
    }

    /* Allocate memory for pthread_create() arguments */

    tinfo = calloc(num_threads, sizeof(struct thread_info));
    if (tinfo == NULL)
        handle_error("calloc");

    /* Create one thread for each command-line argument */

    for (tnum = 0; tnum < num_threads; tnum++) {
        tinfo[tnum].thread_num = tnum + 1;
        tinfo[tnum].device = argv[1];
        tinfo[tnum].time = time;

        /* The pthread_create() call stores the thread ID into
           corresponding element of tinfo[] */

        s = pthread_create(&tinfo[tnum].thread_id, NULL,
                           &thread_start, &tinfo[tnum]);
        if (s != 0)
            handle_error_en(s, "pthread_create");
    }

    /* Now join with each thread, and display its returned value */

    for (tnum = 0; tnum < num_threads; tnum++) {
        s = pthread_join(tinfo[tnum].thread_id, &res);
        if (s != 0)
            handle_error_en(s, "pthread_join");

        s = *(int *)res;
        cnt += s;
        printf("Joined with thread %d; returned value was %d\n",
                tinfo[tnum].thread_num, s);
        free(res);      /* Free memory allocated by thread */
    }

    printf("Result: %f requests/sec (%d/%d)\n", (float)cnt/(float)time, cnt, time);

    free(tinfo);
    exit(EXIT_SUCCESS);
}
