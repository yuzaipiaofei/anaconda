/*
 * WIDESTR (a small and simple library for editing DBCS strings)
 * Copyright (C) 2000  Adrian D. Havill
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Adrian D. Havill can be reached at havill@redhat.com or by mailing
 * to:
 *     Red Hat Japan
 *     Sotokanda 3-14-10
 *     Chiyoda-ku, Tokyo-to
 *     JAPAN  101-0021
 */

#include <assert.h>
#include <ctype.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "widestr.h"

static const unsigned		right_margin	= 76;
static const unsigned		tab_spaces	= 8;
static const size_t		init_bufsiz	= 16;
static const unsigned char	euc_ss2		= 0x8E;
static const unsigned char	euc_ss3		= 0x8F;
static const wide_char          wide_nl		= 0x000A;

/*
 *  FIXME: full-width farenheit symbol is not here because the
 *         list is euc-jp, which doesn't include the code. this
 *         really should be in ucs-2.
 */

static const wide_char kinsoku_begin[] = { /* ascend sorted */
  0xA1A2, 0xA1A3, 0xA1A4, 0xA1A5, 0xA1A7, 0xA1A8, 0xA1A9, 0xA1AA, 0xA1AB,
  0xA1AC, 0xA1B3, 0xA1B4, 0xA1B5, 0xA1B6, 0xA1B9, 0xA1BC, 0xA1BD, 0xA1BE,
  0xA1C7, 0xA1C9, 0xA1CB, 0xA1CD, 0xA1CF, 0xA1D1, 0xA1D3, 0xA1D5, 0xA1D7,
  0xA1D9, 0xA1DB, 0xA1EB, 0xA1EC, 0xA1ED, 0xA1EE, 0xA1F1, 0xA1F3, 0xA2F3,
  0xA4A1, 0xA4A3, 0xA4A5, 0xA4A7, 0xA4A9, 0xA4C3, 0xA4E3, 0xA4E5, 0xA4E7,
  0xA4EE, 0xA5A1, 0xA5A3, 0xA5A5, 0xA5A7, 0xA5A9, 0xA5C3, 0xA5E3, 0xA5E5,
  0xA5E7, 0xA5EE, 0xA5F5, 0xA5F6
};
static const wide_char kinsoku_end[] = { /* ascend sorted */
  0xA1C7, 0xA1C9, 0xA1CB, 0xA1CD, 0xA1CF, 0xA1D1, 0xA1D3, 0xA1D5, 0xA1D7,
  0xA1D9, 0xA1DB, 0xA1EF, 0xA1F0, 0xA1F2, 0xA1F4, 0xA1F7, 0xA1F8, 0xA2A9
};

wide_str *
wide_alloc_str (wide_str *s, size_t n) {
  wide_char *buf;
  size_t size;
#if !defined NDEBUG
  char debug_msg[64];
#endif

  /*
   *  the allocation strategy currently used is to allocate a new chunk as
   *  soon as the current chunk can't hold any more data (and allocate as
   *  many chunks as needed).
   *
   *  chunks are deallocated only when two or more chunks are not used. as
   *  a special case, if no bytes are being used in any chunk, all chunks
   *  are deallocated, even if only one (not two) chunks are allocated.
   *
   *  the delay in deallocating allows for temporary small shrinkage of the
   *  amount of data in the chunks followed by a return to the previous
   *  size to not cause an unnecessary deallocate/allocate.
   *
   *  chunks increments may be linear (fixed size increments) or may
   *  be doubling (1, 2, 4, 8, 16, 32).
   */

  if (n > s->bufsiz) {
    size_t excess, next;

    if (0 == s->inc) {

      /*
       * FIXME: I'm mathematically challenged... is there a more
       *        efficient way to find the next multiple of two without
       *        using a loop?
       */

      next = 0 == s->bufsiz ? 1 : s->bufsiz * 2;
      while (next < n)
        next *= 2;
    }
    else {
      excess = (n + s->inc) % s->inc;
      next = n + s->inc - excess;
    }
    size = next * sizeof(wide_char);
    assert(0 != size);
    if (NULL == (buf = realloc(s->buf, size))) {
#     if !defined NDEBUG
        if (snprintf(debug_msg, sizeof(debug_msg),
                     "wide_alloc_str(%p, %zu); realloc(%p, %zu)",
                     (void *) s, n, (void *) s->buf, size) < 0)
          debug_msg[sizeof(debug_msg) - 1] = '\0';
        perror(debug_msg);
#     endif
      return NULL;
    }
    else {
      s->bufsiz = next;
      s->buf = buf;
    }
  }
  else {
    size_t threshold;
    size_t prev;

    threshold = 0 == s->inc ? s->bufsiz / 4
                : (s->bufsiz < s->inc * 2 ? 0 : s->bufsiz - s->inc * 2);
    prev = 0 == s->inc ? s->bufsiz / 2
           : (s->bufsiz < s->inc ? 0 : s->bufsiz - s->inc);
    if (n <= threshold) {
      size = prev * sizeof(wide_char);
      if (0 == size) {
        if (NULL != s->buf)
          free(s->buf);
        s->buf = NULL;
        s->bufsiz = 0;
      }
      else if (NULL == (buf = realloc(s->buf, size))) {
#       if !defined NDEBUG
          if (snprintf(debug_msg, sizeof(debug_msg),
                       "wide_alloc_str(%p, %zu); realloc(%p, %zu)",
                       (void *) s, n, (void *) s->buf, size) < 0)
            debug_msg[sizeof(debug_msg) - 1] = '\0';
          perror(debug_msg);
#       endif
        return NULL;
      }
      else {
        s->bufsiz = prev;
        s->buf = buf;
      }
    }
  }
  return s;
}

wide_str *
wide_clone_str (const wide_str *s) {
  wide_str *duplicate;

  assert(NULL != s);

  if (NULL == (duplicate = malloc(sizeof(wide_str))))
    return NULL;
  duplicate->enc = s->enc;
  duplicate->inc = s->inc;
  duplicate->bufsiz = s->bufsiz;
  duplicate->len = s->len;
  if (0 != s->bufsiz) {
    if (NULL == (duplicate->buf = malloc(s->bufsiz * sizeof(wide_char)))) {
      free(duplicate);
      return NULL;
    }
  }
  else duplicate->buf = NULL;
  if (0 != s->len) {
    assert(s->len <= s->bufsiz);
    memcpy(duplicate->buf, s->buf, s->len * sizeof(wide_char));
  }
  return duplicate;
}

wide_str *
wide_init_str (wide_str *s, size_t inc, wide_enc enc) {
  if (NULL != s) {
    s->enc = enc;
    s->inc = inc;
    s->bufsiz = s->len = 0;
    s->buf = NULL;
  }
  return s;
}

size_t
wide_get_len (const wide_str *s) {
  assert(NULL != s);

  return s->len;
}

size_t
wide_get_inc (const wide_str *s) {
  assert(NULL != s);

  return s->inc;
}

wide_enc
wide_get_enc (const wide_str *s) {
  assert(NULL != s);

  return s->enc;
}

wide_char
wide_get_char (const wide_str *src, size_t pos) {
  assert(NULL != src);
  assert(pos < src->len);

  return src->buf[pos];
}

wide_str *
wide_get_str (wide_str *dest, const wide_str *src, size_t pos, size_t n) {
  void *memdest;
  const void *memsrc;
  size_t memn;

  assert(NULL != dest);
  assert(NULL != src);
  assert(pos < src->len);
  assert(pos + n <= src->len);

  if (NULL == wide_alloc_str(dest, n)) return NULL;
  memdest = dest->buf;
  memsrc = src->buf + pos;
  memn = n * sizeof(wide_char);
  memcpy(memdest, memsrc, memn);
  dest->len = n;
  dest->enc = src->enc;
  return dest;
}

int
wide_check_char (wide_char c, wide_enc enc) {
  unsigned char hi, lo;

  hi = (c >> 8) & 0xFF;
  lo = c & 0xFF;

  /*
   *  the checks here aren't as strict as they could be in that with
   *  the exception of Unicode/UTF-8, checks are only done for the
   *  ranges and not as to whether the codepoint points to a valid
   *  character or not.
   */

  switch (enc) {
  case wide_iso_8859_1: return c <= 0xFF;
  case wide_utf_8: return c != 0xFFFF && c != 0xFFFE;
  case wide_euc_tw: return 1;
  case wide_euc_jp:
    return (0 == hi && (lo & 0x80) == 0)
           || ((hi > 0xA0 && hi < 0xFF) && (lo > 0xA0 && lo < 0xFF))
           || (0 == hi && (lo > 0xA0 && lo < 0xFF))
           || ((hi > 0xA0 && hi < 0xFF) && (lo > 0x20 && lo < 0x7F));
  case wide_euc_cn:
  case wide_euc_kr:
  case wide_euc_kp:
    return (0 == hi && (lo & 0x80) == 0)
           || ((hi > 0xA0 && hi < 0xFF) && (lo > 0xA0 && lo < 0xFF));
  case wide_euc_vn:
    return (0 == hi)
           || ((hi > 0xA0 && hi < 0xFF) && (lo > 0xA0 && lo < 0xFF));
  }
  return 0;
}

wide_str *
wide_ins_char (wide_str *dest, wide_char src, size_t pos) {
  assert(NULL != dest);
  assert(pos <= dest->len);
  assert(wide_check_char(src, dest->enc));

  if (NULL == wide_alloc_str(dest, dest->len + 1))
    return NULL;
  if (0 != dest->len && pos != dest->len) {
    void *memdest;
    const void *memsrc;
    size_t n;

    memdest = dest->buf + pos + 1;
    memsrc = dest->buf + pos;
    n = (dest->len - pos) * sizeof(wide_char);
    memmove(memdest, memsrc, n);
  }
  dest->buf[pos] = src;
  dest->len++;
  return dest;
}

wide_str *
wide_ins_str (wide_str *dest, const wide_str *src, size_t pos) {
  void *memdest;
  const void *memsrc;
  size_t memn;

  assert(NULL != dest);
  assert(NULL != src);
  assert(pos <= dest->len);
  assert(src->enc == dest->enc);

  if (NULL == wide_alloc_str(dest, dest->len + src->len)) return NULL;
  if (0 != dest->len && pos != dest->len) {
    memn = (dest->len - pos) * sizeof(wide_char);
    memdest = dest->buf + pos + src->len;
    memsrc = dest->buf + pos;
    memmove(memdest, memsrc, memn);
  }
  if (0 != src->len) {
    memn = src->len * sizeof(wide_char);
    memsrc = src->buf;
    memdest = dest->buf + pos;
    memcpy(memdest, memsrc, memn);
    dest->len += src->len;
  }
  return dest;
}

wide_str *
wide_ovwr_char (wide_str *dest, wide_char src, size_t pos) {
  assert(NULL != dest);
  assert(pos <= dest->len);
  assert(wide_check_char(src, dest->enc));

  if (pos == dest->len) {
    if (NULL == wide_alloc_str(dest, dest->len + 1)) return NULL;
    dest->len++;
  }
  dest->buf[pos] = src;
  return dest;
}

wide_str *
wide_ovwr_str (wide_str *dest, const wide_str *src, size_t pos) {
  const void *memsrc;
  void *memdest;
  size_t memn;

  assert(NULL != dest);
  assert(NULL != src);
  assert(pos <= dest->len);
  assert(src->enc == dest->enc);

  if (src->len + pos >= dest->len) {
    if (NULL == wide_alloc_str(dest, src->len + pos)) return NULL;
    dest->len = src->len + pos;
  }
  memdest = dest->buf + pos;
  memsrc = src->buf;
  memn = src->len * sizeof(wide_char);
  memcpy(memdest, memsrc, memn);
  return dest;
}

wide_str *
wide_del_str (wide_str *s, size_t pos, size_t n) {
  assert(NULL != s);
  assert(pos + n <= s->len);

  if (0 != n) {
    if (pos != s->len - 1) {
      void *dest;
      const void *src;
      size_t size;

      dest = s->buf + pos;
      src = s->buf + pos + n;
      size = (s->len - pos - n) * sizeof(wide_char);
      memmove(dest, src, size);
    }
    s->len -= n;
  }
  if (NULL == wide_alloc_str(s, s->len)) return NULL;
  return s;
}

static size_t
conv_mbs_n (wide_str *dest, const unsigned char *p, unsigned n) {
  wide_char c;

  assert(NULL != dest);
  assert(NULL != p);

  if (p[0] < 0x80) {
    switch (dest->enc) {
    default:

      /*
       * ASCII, JIS-Roman (JIS X 0201), GB-Roman (GB 1988),
       * CNS-Roman (CNS 5205), KS-Roman (KS X 1003)
       * or the first half of VSCII-2
       */

      c = p[0];
    }
    if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
    return 1;
  }
  else if (wide_utf_8 == dest->enc) {
    if ((p[0] & 0xE0) == 0xC0 && n > 1) {
      if ((p[1] & 0xC0) == 0x80) {
        c  = (p[0] & 0x1F) << 6;
        c |=  p[1] & 0x3F;
        if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
        return 2;
      }
    }
    else if ((p[0] & 0xF0) == 0xE0 && n > 2) {
      if ((p[1] & 0xC0) == 0x80 && (p[2] & 0xC0) == 0x80) {
        c  = (p[0] & 0x0F) << 12;
        c |= (p[1] & 0x3F) << 6;
        c |=  p[2] & 0x3F;
        if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
        return 3;
      }
    }
    else if ((p[0] & 0xF8) == 0xF0 && n > 3) {
      if ((p[1] & 0xC0) == 0x80 && (p[2] & 0xC0) == 0x80
          && (p[3] & 0xC0) == 0x80) {
        unsigned long u;
        wide_char hi, lo;

        u  = (p[0] & 0x07) << 18;
        u |= (p[1] & 0x3F) << 12;
        u |= (p[2] & 0x3F) << 6;
        u |=  p[3] & 0x3F;
        hi = (u - 0x10000) / 0x400 + 0xD800;
        lo = (u - 0x10000) % 0x400 + 0xDC00;
        if (NULL == wide_ins_char(dest, hi, dest->len)) return 0;
        if (NULL == wide_ins_char(dest, lo, dest->len)) return 0;
        return 4;
      }
    }
    return 0;
  }
  else if (euc_ss2 == p[0]) {
    switch (dest->enc) {
    case wide_iso_8859_1:
      c = p[0];
      if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
      return 1;
    case wide_euc_jp: /* JIS X 0201 half-width katakana */
      if (n > 1 && p[1] >= 0x80) {
        c = p[1];
        if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
        return 2;
      }
      return 0;
    case wide_euc_vn: /* TCVN 5773:1993 */
      if (n > 2 && p[1] >= 0x80 && p[2] >= 0x80) {
        c = (p[1] << 8) | (p[2] & 0x7F);
        if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
        return 3;
      }
      return 0;
    case wide_euc_tw:
      if (n > 3 && p[1] >= 0x80 && p[2] >= 0x80 && p[3] >= 0x80) {
        if (p[1] < 0xA1 || p[2] < 0xA1 || p[3] < 0xA1) return 0;

        /*
         * We can't fit into two bytes the EUC-TW 7*94*94 using the
         * usual EUC fixed-width packing method of setting/resetting the
         * high bits on the octets for identifying the codeset,
         * so pack them in using base 94, offsetting the whole thing
         * by 128 so that ASCII stays preserved as-is.
         */

        c = (p[1] - 0xA1) * 8836 + (p[2] - 0xA1) * 94 + (p[3] - 0xA1);
        c += 0x80;
        if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
        return 4;
      }
      else return 0;
      if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
      return 4;
    default: return 0;
    }
  }
  else if (euc_ss3 == p[0]) {
    switch (dest->enc) {
    case wide_iso_8859_1:
      c = p[0];
      if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
      return 1;
    case wide_euc_jp: /* JIS X 0212:1990 */
      if (n > 2 && p[1] >= 0x80 && p[2] >= 0x80) {
        c = (p[1] << 8) | (p[2] & 0x7F);
        if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
        return 3;
      }
      return 0;
    default: return 0;
    }
  }
  else if (p[0] >= 0x80) {
    switch (dest->enc) {
    case wide_euc_cn: /* GB 2312-80 */
    case wide_euc_tw: /* CNS 11643-1992 Plane 1 */
    case wide_euc_jp: /* JIS X 0208:1997 */
    case wide_euc_kr: /* KS X 1001:1992 */
    case wide_euc_kp: /* KPS 9566-97 */
      if (n > 1 && p[1] >= 0x80) {
        c = (p[0] << 8) | p[1];
        if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
        return 2;
      }
      return 0;
    case wide_euc_vn: /* TCVN 5712:1993 VN2 aka VSCII-2 top half */
    case wide_iso_8859_1:
      c = p[0];
      if (NULL == wide_ins_char(dest, c, dest->len)) return 0;
      return 1;
    default: return 0;
    }
  }
  return 0;
}

wide_str *
wide_conv_mbs (wide_str *dest, const unsigned char *src) {
  const unsigned char *p;

  assert(NULL != dest);
  assert(NULL != src);

  dest->len = 0;
  p = src;
  while ('\0' != p[0]) {
    size_t inc;

    inc = conv_mbs_n(dest, p, UINT_MAX);
    if (0 == inc) return NULL;
    p += inc;
  }
  return dest;   
}

wide_str *
wide_conv_mbs_n (wide_str *dest, const unsigned char *src, size_t n) {
  const unsigned char *p;
  size_t i;

  assert(NULL != dest);
  assert(NULL != src);

  dest->len = 0;
  if (0 == n)
    if (NULL == wide_alloc_str(dest, n)) return NULL;
  p = src;
  for (i = 0; i < n; i++) {
    size_t inc;

    inc = conv_mbs_n(dest, p, n - i);
    if (0 == inc) return NULL;
    p += inc;
  }
  return dest;   
}

static size_t
conv_wcs (unsigned char *p, unsigned long c, unsigned n, wide_enc enc) {
  assert(NULL != p);

  switch (enc) {
  case wide_iso_8859_1:
    if (0 == n) return 0;
    *p++ = c;
    return 1;
  case wide_euc_tw:
    if (c < 0x80) {
      if (0 == n) return 0;
      *p++ = c;
      return 1;
    }
    else {
      unsigned x, y, z;

      /*
       *  Funky slow division is used to unpack the huge CNS
       *  character set (> 50,000 characters)
       */

      c -= 0x80;
      x = c / 8836 + 0xA1;
      c %= 8836;
      y = c / 94 + 0xA1;
      c %= 94;
      z = c + 0xA1;

      /*
       *  Plane 1 characters can be encoded in EUC-TW via codeset 1
       *  or codeset 2. We encode Plane 1 always as codeset 1 (the
       *  most compact). On the other hand, pure round-trip compatibility
       *  is lost.
       */

      if (x > 0xA1) {
        if (n < 4) return 0;
        *p++ = euc_ss2;
        *p++ = x;
        *p++ = y;
        *p = z;
        return 4;
      }
      if (n < 2) return 0;
      *p++ = y;
      *p = z;
      return 2;
    }
  case wide_euc_cn:
  case wide_euc_kr:
  case wide_euc_kp:
    if (c < 0x80) {
      if (0 == n) return 0;
      *p = c;
      return 1;
    }
    else if ((0x8080 & c) == 0x8080) {
      if (n < 2)
        return 0;
      *p++ = (c >> 8) & 0xFF;
      *p = c & 0xFF;
      return 2;
    }
    return 0;
  case wide_euc_jp:
    if (c < 0x80) {
      if (0 == n) return 0;
      *p = c;
      return 1;
    }
    else if ((0x8080 & c) == 0x8080) {
      if (n < 2) return 0;
      *p++ = (c >> 8) & 0xFF;
      *p = c & 0xFF;
      return 2;
    }
    else if ((0xFF80 & c) == 0x0080) {
      if (n < 2) return 0;
      *p++ = euc_ss2;
      *p = c & 0xFF;
      return 2;
    }
    else if ((0x8080 & c) == 0x8000) {
      if (n < 3) return 0;
      *p++ = euc_ss3;
      *p++ = (c >> 8) & 0xFF;
      *p = (c & 0xFF) | 0x80;
      return 3;
    }
    return 0;
  case wide_euc_vn:
    if (c <= 0xFF) {
      if (0 == n) return 0;
      *p = c;
      return 1;
    }
    else {
      if (n < 3) return 0;
      *p++ = euc_ss2;
      *p++ = (c >> 8) & 0xFF;
      *p = c & 0xFF;
    }
    return 3;
  case wide_utf_8:
    if (c <= 0x80) {
      if (0 == n) return 0;
      *p = c;
      return 1;
    }
    else if (c < 0x800) {
      unsigned char x, y;

      x = 0xC0 | ((c >> 8) & 0x1F);
      y = 0x80 | (c & 0x3F);
      if (n < 2) return 0;
      *p++ = x;
      *p   = y;
    }
    else if (c <= 0xFFFF) {
      unsigned char x, y, z;

      x = 0xE0 | ((c >> 12) & 0x0F);
      y = 0x80 | ((c >>  6) & 0x3F);
      z = 0x80 | (c         & 0x3F);
      if (n < 3) return 0;
      *p++ = x;
      *p++ = y;
      *p   = z;
    }
    else if (c <= 0x10FFFF) {
      unsigned char w, x, y, z;

      w = 0xF0 | ((c >> 18) & 0x07);
      x = 0x80 | ((c >> 12) & 0x3F);
      y = 0x80 | ((c >>  6) & 0x3F);
      z = 0x80 | (c         & 0x3F);
      if (n < 4) return 0;
      *p++ = w;
      *p++ = x;
      *p++ = y;
      *p   = z;
    }
  }
  return 0;
}

static int
is_high_surrogate (wide_char c, wide_enc enc) {
  return wide_utf_8 == enc && c >= 0xD800 && c <= 0xDBFF;
}

static int
is_low_surrogate (wide_char c, wide_enc enc) {
  return wide_utf_8 == enc && c >= 0xDC00 && c <= 0xDFFF;
}

unsigned char *
wide_conv_wcs (unsigned char *dest, const wide_str *src) {
  unsigned char *p;
  size_t i, n;
  int allocated;

  assert(NULL != src);

  allocated = NULL == dest;
  if (allocated)
    if (NULL == (dest = malloc(src->len * 4 + 1))) return NULL;
  p = dest;
  n = 0;
  for (i = 0; i < src->len; i++) {
    size_t stored;
    unsigned long c;

    c = src->buf[i];
    if (is_high_surrogate(c, src->enc) && (i + 1 < src->len)
        && is_low_surrogate(src->buf[i + 1], src->enc)) {
      c = (c - 0xD800) * 400 + (src->buf[i + 1] - 0xDC00) + 0x10000;
      i++;
    }
    if (0 == (stored = conv_wcs(p, c, UINT_MAX, src->enc))) return NULL;
    p += stored;
    n += stored;
  }
  *p = '\0';
  n++;
  if (allocated) {
    void *q;

    assert(0 != n);
    if (NULL != (q = realloc(dest, n)))
      dest = q;
  }
  return dest;
}

unsigned char *
wide_conv_wcs_n (unsigned char *dest, const wide_str *src, size_t n) {
  unsigned char *p;
  size_t i, total;

  assert(NULL != dest);
  assert(NULL != src);

  total = n;
  p = dest;
  for (i = 0; i < src->len; i++) {
    size_t stored;
    unsigned long c;

    c = src->buf[i];
    if (is_high_surrogate(c, src->enc) && (i + 1 < src->len)
        && is_low_surrogate(src->buf[i + 1], src->enc)) {
      c = (c - 0xD800) * 400 + (src->buf[i + 1] - 0xDC00) + 0x10000;
      i++;
    }
    if (0 == (stored = conv_wcs(p, c, total, src->enc))) return NULL;
    p += stored;
    total -= stored;
  }
  if (total != 0)
    *p = '\0';
  else return NULL;
  return dest;
}

int
wide_find_char (const wide_str *s, wide_char key, size_t *pos, int rtl) {
  size_t i;

  assert(NULL != s);
  assert(NULL != pos);
  assert(*pos < s->len);

  i = *pos;
  for (;;) {
    if (s->buf[i] == key) {
      *pos = i;
      return 1;
    }
    else if (rtl) {
      if (i == 0) break;
      i--;
    }
    else {
      if (i >= s->len) break;
      i++;
    }
  }
  return 0;
}

int
wide_find_str (const wide_str *s, const wide_str *key, size_t *pos,
               int rtl) {
  wide_char c;
  size_t i, n;
  const void *x, *y;

  assert(NULL != s);
  assert(NULL != pos);
  assert(NULL != key);
  assert(*pos < s->len);

  if (key->len == 0) return 1;
  if (key->enc != s->enc) return 0;
  x = key->buf;
  n = key->len * sizeof(wide_char);

  for (i = *pos, c = *key->buf; wide_find_char(s,c,&i,rtl); rtl ? i--:i++) {
    y = s->buf + i;
    if (memcmp(x, y, n) == 0) {
      *pos = i;
      return 1;
    }
  }
  return 0;
}

static int
is_cjkv (wide_char c, wide_enc enc) {
  assert(wide_check_char(c, enc));

  switch (enc) {
  case wide_iso_8859_1: return 0;
  case wide_euc_vn: return c > 0xFF;
  case wide_euc_tw: return c > 0x80; /* FIXME: adjust for hanzi range */
  case wide_euc_kp: /* XXX: is the below really valid for KP? */ 
  case wide_euc_kr: return c >= 0xB0A1 || (c >= 0xAAA1 && c <= 0xABFE);
  case wide_euc_jp:
    if (c >= 0xA1B3 && c <= 0xA1BC) return 1;
  case wide_euc_cn:
    return c >= 0xB0A1 || (c >= 0xA4A1 && c <= 0xA5FE);
  case wide_utf_8:

    /*
     *  data current as of Unicode 2.1
     */

    if (c >= 0x3006 && c <= 0x3007) return 1; /* ideographs */
    if (c >= 0x3021 && c <= 0x3029) return 1;
    if (c >= 0x4E00 && c <= 0x9FA5) return 1;
    if (c >= 0xF900 && c <= 0xFA2D) return 1;
    if (c >= 0xAC00 && c <= 0xD7AF) return 1; /* hangul precomposed */
    if (c >= 0x3040 && c <= 0x309F) return 1; /* hiragana */
    if (c >= 0x30A0 && c <= 0x30FF) return 1; /* katakana */
    if (c >= 0x3005 && c <= 0x3007) return 1;
    return 0;
  }
  return 0;
}

int
wide_get_char_width (wide_char c, wide_enc enc) {
  assert(wide_check_char(c, enc));

  switch (enc) {
  case wide_euc_vn:

    /*
     *  This table is for the vn1 table, even though we have to use
     *  vn2 for correctness with euc-vn because euc needs ss2 and ss3
     *  (0x8e and 0x8f), which are already used in vn1.
     *
     *  many Vietnamese users will probably use vn1 anyway, and deal
     *  with the fact that two characters are unavailable, and the
     *  extra Vietnamese characters are in rarely used c0/c1 points
     *  anyway, so we'll support them.
     */

    switch (c) {
      case 0x01: case 0x02: case 0x04: case 0x05: case 0x06: case 0x11:
      case 0x12: case 0x13: case 0x14: case 0x15: case 0x16: case 0x17:
        return 1;
      default: if (c >= 0x80 && c <= 0x9F) return 1;
    }
    if (c >= 0xB0 && c <= 0xB4) return 0; /* combining diacritics */
  case wide_euc_cn: case wide_euc_tw: case wide_euc_jp: case wide_euc_kr:
  case wide_euc_kp: if (c > 0xFF) return 2;
  case wide_iso_8859_1:
    if (0x00 == c || 0x07 == c) return 0;
    else if (0x08 == c) return -1;
    else if ((c < 0x20 || c == 0x7F) || (c >= 0x80 && c < 0xA0)) return 0;
    break;
  case wide_utf_8:

    /*
     *  this below nowhere near complete, but gets the job done for cjkv
     *  and european langs without combining diacritics. it won't
     *  work with Korean combining jamo either, so use the precomposed
     *  hangul syllables instead.
     */

    switch (c) {
    case 0x0008: return -1;
    case 0x3000: return 2; /* ideographic space */
    case 0x0000: case 0x0007: case 0x200B: case 0x200C: case 0x200D:
    case 0x200E: case 0x200F: case 0xFEFF:
      return 0;
    default:
      if (c >= 0xFF00 && c <= 0xFF5F) return 2; /* fullwidth letters */
      if (c >= 0xFFE0 && c <= 0xFFE6) return 2; /* fullwidth syms */
    }
    /* TODO: implement UAX #11: East Asian Width */
  }
  return is_cjkv(c, enc) ? 2 : 1;
}

static int
can_break (wide_char c, wide_enc enc) {
  switch (c) {
  default:
    if (wide_iso_8859_1 != enc && wide_utf_8 != enc && c > 0xFF) return 1;
    return wide_utf_8 == enc && c >= 0x2000 && c <= 0x200B && c != 0x2007;
  case 0x3000: return wide_utf_8 == enc;
  case 0x0009: case 0x000A: case 0x000B: case 0x000C: case 0x000D:
  case 0x0020:
    return 1;

  /*
   *  as half-width katakana space is non-std, it's unclear as to whether
   *  we can break or not. i think we can.
   */

  case 0x00A0: return wide_euc_jp == enc;
  case 0xA1A1:
    return wide_euc_jp == enc || wide_euc_kr == enc || wide_euc_cn == enc;
  case 0x0080: return wide_euc_tw == enc;
  }
  return 0;
}

static int
is_whitespace (wide_char c, wide_enc enc) {
  switch (c) {
  default: return wide_utf_8 == enc && c >= 0x2000 && c <= 0x200B;
  case 0x0009: case 0x000A: case 0x000B: case 0x000C: case 0x000D:
  case 0x0020: return 1;
  case 0x00A0:
    return wide_iso_8859_1 == enc || wide_utf_8 == enc || wide_euc_vn == enc
           || wide_euc_jp == enc; /* non-std for Japanese */
  case 0xA1A1:
    return wide_euc_jp == enc || wide_euc_kr == enc || wide_euc_cn == enc;
  case 0x0080: return wide_euc_tw == enc;
  }
  return 0;
}

static int
is_newline (wide_char c, wide_enc enc) {
  switch (c) {
  case 0x000A: case 0x000B: case 0x000C: case 0x000D: return 1;
  case 0x2028: case 0x2029: return wide_utf_8 == enc;
  }
  return 0;
}

static int
cmp (const void *ck, const void *ce) {
  wide_char x, y;

  if (NULL == ck && ce != NULL) return -1;
  else if (NULL != ck && ce == NULL) return 1;
  else if (NULL == ck && ce == NULL) return 0;

  x = *((const wide_char *) ck);
  y = *((const wide_char *) ce);
  if (x < y) return -1;
  else if (x > y) return 1;
  return 0;
}

static int
is_kinsoku_begin (wide_char c, wide_enc enc) {
  const void *key, *base;
  size_t nelem, size;

  assert(wide_check_char(c, enc));

  switch (enc) {
  /* TODO: support other enc through iconv */
  case wide_euc_jp: key = &c; break;
  default: key = NULL;
  }
  base = kinsoku_begin;
  size = sizeof(wide_char);
  nelem = sizeof(kinsoku_begin) / size;
  return bsearch(key, base, nelem, size, cmp) != NULL;
}

static int
is_kinsoku_end (wide_char c, wide_enc enc) {
  const void *key, *base;
  size_t nelem, size;

  assert(wide_check_char(c, enc));

  switch (enc) {
  /* TODO: support other enc through iconv */
  case wide_euc_jp: key = &c; break;
  default: key = NULL;
  }
  base = kinsoku_end;
  size = sizeof(wide_char);
  nelem = sizeof(kinsoku_end) / size;
  return bsearch(key, base, nelem, size, cmp) != NULL;
}

unsigned long
wide_hash_str (const wide_str *s) {
  unsigned long crc;
  size_t j;
  double len, i, inc;
  static const unsigned long table[256] = {
    0x00000000UL,0x77073096UL,0xEE0E612CUL,0x990951BAUL,0x076DC419UL,
    0x706AF48FUL,0xE963A535UL,0x9E6495A3UL,0x0EDB8832UL,0x79DCB8A4UL,
    0xE0D5E91EUL,0x97D2D988UL,0x09B64C2BUL,0x7EB17CBDUL,0xE7B82D07UL,
    0x90BF1D91UL,0x1DB71064UL,0x6AB020F2UL,0xF3B97148UL,0x84BE41DEUL,
    0x1ADAD47DUL,0x6DDDE4EBUL,0xF4D4B551UL,0x83D385C7UL,0x136C9856UL,
    0x646BA8C0UL,0xFD62F97AUL,0x8A65C9ECUL,0x14015C4FUL,0x63066CD9UL,
    0xFA0F3D63UL,0x8D080DF5UL,0x3B6E20C8UL,0x4C69105EUL,0xD56041E4UL,
    0xA2677172UL,0x3C03E4D1UL,0x4B04D447UL,0xD20D85FDUL,0xA50AB56BUL,
    0x35B5A8FAUL,0x42B2986CUL,0xDBBBC9D6UL,0xACBCF940UL,0x32D86CE3UL,
    0x45DF5C75UL,0xDCD60DCFUL,0xABD13D59UL,0x26D930ACUL,0x51DE003AUL,
    0xC8D75180UL,0xBFD06116UL,0x21B4F4B5UL,0x56B3C423UL,0xCFBA9599UL,
    0xB8BDA50FUL,0x2802B89EUL,0x5F058808UL,0xC60CD9B2UL,0xB10BE924UL,
    0x2F6F7C87UL,0x58684C11UL,0xC1611DABUL,0xB6662D3DUL,0x76DC4190UL,
    0x01DB7106UL,0x98D220BCUL,0xEFD5102AUL,0x71B18589UL,0x06B6B51FUL,
    0x9FBFE4A5UL,0xE8B8D433UL,0x7807C9A2UL,0x0F00F934UL,0x9609A88EUL,
    0xE10E9818UL,0x7F6A0DBBUL,0x086D3D2DUL,0x91646C97UL,0xE6635C01UL,
    0x6B6B51F4UL,0x1C6C6162UL,0x856530D8UL,0xF262004EUL,0x6C0695EDUL,
    0x1B01A57BUL,0x8208F4C1UL,0xF50FC457UL,0x65B0D9C6UL,0x12B7E950UL,
    0x8BBEB8EAUL,0xFCB9887CUL,0x62DD1DDFUL,0x15DA2D49UL,0x8CD37CF3UL,
    0xFBD44C65UL,0x4DB26158UL,0x3AB551CEUL,0xA3BC0074UL,0xD4BB30E2UL,
    0x4ADFA541UL,0x3DD895D7UL,0xA4D1C46DUL,0xD3D6F4FBUL,0x4369E96AUL,
    0x346ED9FCUL,0xAD678846UL,0xDA60B8D0UL,0x44042D73UL,0x33031DE5UL,
    0xAA0A4C5FUL,0xDD0D7CC9UL,0x5005713CUL,0x270241AAUL,0xBE0B1010UL,
    0xC90C2086UL,0x5768B525UL,0x206F85B3UL,0xB966D409UL,0xCE61E49FUL,
    0x5EDEF90EUL,0x29D9C998UL,0xB0D09822UL,0xC7D7A8B4UL,0x59B33D17UL,
    0x2EB40D81UL,0xB7BD5C3BUL,0xC0BA6CADUL,0xEDB88320UL,0x9ABFB3B6UL,
    0x03B6E20CUL,0x74B1D29AUL,0xEAD54739UL,0x9DD277AFUL,0x04DB2615UL,
    0x73DC1683UL,0xE3630B12UL,0x94643B84UL,0x0D6D6A3EUL,0x7A6A5AA8UL,
    0xE40ECF0BUL,0x9309FF9DUL,0x0A00AE27UL,0x7D079EB1UL,0xF00F9344UL,
    0x8708A3D2UL,0x1E01F268UL,0x6906C2FEUL,0xF762575DUL,0x806567CBUL,
    0x196C3671UL,0x6E6B06E7UL,0xFED41B76UL,0x89D32BE0UL,0x10DA7A5AUL,
    0x67DD4ACCUL,0xF9B9DF6FUL,0x8EBEEFF9UL,0x17B7BE43UL,0x60B08ED5UL,
    0xD6D6A3E8UL,0xA1D1937EUL,0x38D8C2C4UL,0x4FDFF252UL,0xD1BB67F1UL,
    0xA6BC5767UL,0x3FB506DDUL,0x48B2364BUL,0xD80D2BDAUL,0xAF0A1B4CUL,
    0x36034AF6UL,0x41047A60UL,0xDF60EFC3UL,0xA867DF55UL,0x316E8EEFUL,
    0x4669BE79UL,0xCB61B38CUL,0xBC66831AUL,0x256FD2A0UL,0x5268E236UL,
    0xCC0C7795UL,0xBB0B4703UL,0x220216B9UL,0x5505262FUL,0xC5BA3BBEUL,
    0xB2BD0B28UL,0x2BB45A92UL,0x5CB36A04UL,0xC2D7FFA7UL,0xB5D0CF31UL,
    0x2CD99E8BUL,0x5BDEAE1DUL,0x9B64C2B0UL,0xEC63F226UL,0x756AA39CUL,
    0x026D930AUL,0x9C0906A9UL,0xEB0E363FUL,0x72076785UL,0x05005713UL,
    0x95BF4A82UL,0xE2B87A14UL,0x7BB12BAEUL,0x0CB61B38UL,0x92D28E9BUL,
    0xE5D5BE0DUL,0x7CDCEFB7UL,0x0BDBDF21UL,0x86D3D2D4UL,0xF1D4E242UL,
    0x68DDB3F8UL,0x1FDA836EUL,0x81BE16CDUL,0xF6B9265BUL,0x6FB077E1UL,
    0x18B74777UL,0x88085AE6UL,0xFF0F6A70UL,0x66063BCAUL,0x11010B5CUL,
    0x8F659EFFUL,0xF862AE69UL,0x616BFFD3UL,0x166CCF45UL,0xA00AE278UL,
    0xD70DD2EEUL,0x4E048354UL,0x3903B3C2UL,0xA7672661UL,0xD06016F7UL,
    0x4969474DUL,0x3E6E77DBUL,0xAED16A4AUL,0xD9D65ADCUL,0x40DF0B66UL,
    0x37D83BF0UL,0xA9BCAE53UL,0xDEBB9EC5UL,0x47B2CF7FUL,0x30B5FFE9UL,
    0xBDBDF21CUL,0xCABAC28AUL,0x53B39330UL,0x24B4A3A6UL,0xBAD03605UL,
    0xCDD70693UL,0x54DE5729UL,0x23D967BFUL,0xB3667A2EUL,0xC4614AB8UL,
    0x5D681B02UL,0x2A6F2B94UL,0xB40BBE37UL,0xC30C8EA1UL,0x5A05DF1BUL,
    0x2D02EF8DUL
  };
  
  assert(NULL != s);

  len = s->len;
  inc = len / 48.0;
  for (i = 0.0, crc = 0xFFFFFFFFUL; i < len; i += inc) {
    wide_char c;
    unsigned char hi, lo;

    c = s->buf[(size_t) i];
    hi = c >> 8;
    lo = c & 0xFF;
    crc = ((crc >> 8) & 0x00FFFFFFUL) ^ table[(crc ^ hi) & 0xFF];
    crc = ((crc >> 8) & 0x00FFFFFFUL) ^ table[(crc ^ lo) & 0xFF];
  }
  crc = ((crc >> 8) & 0x00FFFFFFUL) ^ table[(crc ^ s->enc) & 0xFF];
  for (j = 0; j < sizeof(s->len); j++) {
    unsigned char c;

    c = (s->len >> (24 - j * 8)) & 0xFF;
    crc = ((crc >> 8) & 0x00FFFFFFUL) ^ table[(crc ^ c) & 0xFF];
  }
  return crc ^ 0xFFFFFFFFUL;
}

wide_str *
wide_fmt_str (wide_str *s, const wide_fmt *fmt) {
  size_t i, y;
  int x, breakable;
  wide_enc enc;

  assert(NULL != s);
  assert(NULL != fmt);

  enc = s->enc;
  if (fmt->reformat) {
    int is_run;

    for (i = 0, is_run = 0; i < s->len; i++) {
      if (is_whitespace(s->buf[i], enc))
        if (is_run) {
          size_t pos, n, j;

          pos = i;
          n = 1;
          for (j = i + 1; j < s->len && is_whitespace(s->buf[j], enc); j++)
            n++;
          if (NULL == wide_del_str(s, pos, n))
            return NULL;
          is_run = 0;
        }
        else {
          s->buf[i] = 0x20; /* this SHOULD be constant for all enc */
          is_run = 1;
        }
      else is_run = 0;
    }
  }

  for (i = y = 0, x = breakable = 0; i < s->len; i++) {
    size_t j, start, end;
    int len, width;
    unsigned margin;

    width = wide_get_char_width(s->buf[i], enc);
    if (NULL != fmt->margin && UINT_MAX == fmt->margin[y] && y != 0)
      margin = fmt->margin[--y];
    else if (NULL != fmt->margin && fmt->margin[y] > 3)
      margin = fmt->margin[y];
    else margin = UINT_MAX;
    if (x + width > margin) {
      if (0 != i)
        --i;

      /*
       *  if the character is forbidden to appear at the beginning of the
       *  line, break before this character and skip the search for the
       *  beginning and end of the word.
       */

      if (is_kinsoku_begin(s->buf[i], enc)) {
        if (NULL == wide_ins_char(s, wide_nl, ++i)) return NULL;
        x = breakable = 0;
      }
      else {
        if (i + 1 < s->len && is_kinsoku_end(s->buf[i + 1], enc)
	    && is_cjkv(s->buf[i], enc)) {
          if (NULL == wide_ins_char(s, wide_nl, i++)) return NULL;
          x = breakable = 0;
          y++;
        }
        else {

          /*
           *  find the start and end boundaries for the word. if the
           *  character is a cjkv ideograph, etc., the "word" will be
           *  exactly one character.
           */

          for (start = i; start != 0; start--)
            if (can_break(s->buf[start], enc)) {
              if (is_kinsoku_begin(s->buf[start], enc)
	          || (width > 1 && x + width == margin
		  && !is_kinsoku_end(s->buf[start], enc) && width > 1))
                start++;
              break;
            }
          for (end = i; end < s->len; end++)
            if (can_break(s->buf[end], enc)) {
              if (!is_kinsoku_end(s->buf[end], enc))
                end++;
              else if (0 != end)
	        end--;
              break;
            }

          /*
           * if the word is so long that it takes more than
           * one line, break the word at the right margin.
           */

          for (j = start, len = 0; j < s->len && j <= end; j++) {
            len += wide_get_char_width(s->buf[j], enc);
            if (len > margin && !breakable) {
              start = j;
              break;
            }
          }
          if (is_whitespace(s->buf[start], enc)) {
            if (NULL == wide_ovwr_char(s, wide_nl, start)) return NULL;
            i = start + 1;
          }
          else if (is_kinsoku_begin(s->buf[start], enc)
                   && 0 != start && is_cjkv(s->buf[start - 1], enc)) {
            if (NULL == wide_ins_char(s, wide_nl, start - 1)) return NULL;
            i = start;
          }
          else if (0 != start && is_whitespace(s->buf[start - 1], enc)) {
            if (NULL == wide_ovwr_char(s, wide_nl, start - 1)) return NULL;
            i = start + 1;
          }
          else {
            if (NULL == wide_ins_char(s, wide_nl, start)) return NULL;
            i = start + 1;
          }
          x = breakable = 0;
          y++;
        }
      }
    }
    x += wide_get_char_width(s->buf[i], enc);
    if (0 != i && is_newline(s->buf[i], enc)) {
      x = breakable = 0;
      y++;
    }
    else if (can_break(s->buf[i], enc))
      breakable++;
  }
  return s;
}

int
wide_cmp_str (const wide_str *x, const wide_str *y) {
  size_t i;

  assert(NULL != x);
  assert(NULL != y);

  for (i = 0; i < x->len; i++)
    if (x->enc == y->enc || (x->buf[i] < 0x80 && y->buf[i] < 0x80)) {
      if (x->buf[i] < y->buf[i]) return -1;
      else if (x->buf[i] > y->buf[i]) return 1;
    }
    else if (x->enc < y->enc) return -1;
    else if (x->enc > y->enc) return 1;
  if (x->len < y->len) return -1;
  else if (x->len > y->len) return 1;
  return 0;
}

void
wide_debug_str (FILE *stream, wide_str *s, int v, const char *expr,
                const char *file, unsigned long line) {
  unsigned total;
  char tmp[80];

  total = v ? 0 : right_margin;
  if (NULL == stream) stream = stderr;
  strcpy(tmp, "<");
  if (NULL == file)
    file = "";
  strcat(tmp, "%s");
  sprintf(tmp + strlen(tmp), 0 == line ? "" : "%s%lu ",
          0 != strlen(file) ? ":" : "", line);
  if (NULL == expr) {
    expr = "";
    strcat(tmp, "%s");
  }
  else strcat(tmp, "(%s) ");
  if (v) strcat(tmp, "{%p} ");
  if (v || 0 != strlen(expr)) strcat(tmp, "... ");
  if (fprintf(stream, tmp, file, expr, (void *) s) < 0) {
    perror(NULL); return;
  }
  if (NULL != s) {
    size_t i;

    strcpy(tmp, "enc=%d len=%zu inc=%zu ");
    if (v)
      strcat(tmp, "bufsize=%zu buf={%p} ");
    strcat(tmp, "[");
    if (fprintf(stream, tmp, (int) s->enc, s->len, s->inc, s->bufsiz,
	(void *) s->buf) < 0) {
      perror(NULL); return;
    }
    for (i = 0; i < s->len; i++) {
      wide_char c;
      char x[7];
      int subtotal;

      c = s->buf[i];
      if (!v && total + sizeof(x) >= right_margin) {
        if (EOF == fputs("\n\t", stream)) { perror(NULL); return; }
        total = tab_spaces;
      }
      if (v || c >= 0x80) {
        if ((subtotal = fprintf(stream, "0x%04hX", c)) < 0) {
          perror(NULL); return;
        }
      }
      else {

        /*
         *  the length of the string in stored in x is always
         *  six to line up the terminal formatting with the hexadecimal
         *  escapes.
         */

        switch (c) {
	  const char *fmt;

        case '\b': snprintf(x, sizeof(x), "%s", "  '\\b'"); break;
        case '\f': snprintf(x, sizeof(x), "%s", "  '\\f'"); break;
        case '\t': snprintf(x, sizeof(x), "%s", "  '\\t'"); break;
        case '\r': snprintf(x, sizeof(x), "%s", "  '\\r'"); break;
        case '\n': snprintf(x, sizeof(x), "%s", "  '\\n'"); break;
        case '\v': snprintf(x, sizeof(x), "%s", "  '\\v'"); break;
        case '\a': snprintf(x, sizeof(x), "%s", "  '\\a'"); break;
        case '\\': snprintf(x, sizeof(x), "%s", "  '\\\\'"); break;
        case '\'': snprintf(x, sizeof(x), "%s", "  '\\''"); break;
        default:
          if ('<' == c || '>' == c) fmt = "'\\x%hX'";
	  else fmt = isprint(c) ? "   '%c'" : "'\\x%hX'";
	  snprintf(x, sizeof(x), fmt, c);
        }
        if ((subtotal = fprintf(stream, "%s", x)) < 0) {
          perror(NULL); return;
        }
      }
      total += (unsigned) subtotal;
      if (i + 1 < s->len) {
        if (EOF == fputc(',', stream)) { perror(NULL); return; }
        total++;
      }
    }
  }
  strcpy(tmp, NULL == s ? ">" : total <= tab_spaces || v ? "]>" : "\n]>");
  if (fprintf(stream, "%s\n", tmp) < 0) perror(NULL);
}
