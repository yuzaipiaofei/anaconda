#ifndef _DUD_UTILS_H_
#define _DUD_UTILS_H_

/* DD extract flags */
enum {
    dup_nothing = 0,
    dup_modules = 1,
    dup_firmwares = 2,
    dup_binaries = 4,
    dup_libraries = 8
} _dup_extract;

#endif /* _DUD_UTILS_H_ */
