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

#include <stdio.h> /* for size_t, NULL & FILE */

typedef enum {
  wide_iso_8859_1, wide_euc_cn, wide_euc_tw, wide_euc_jp, wide_euc_kr,
  wide_euc_kp, wide_euc_vn, wide_utf_8
} wide_enc;
/*
 *  as of 2000-09-26, there is no such thing as euc-kp and euc-vn.
 *  euc-kp is encoded almost identically to euc-kr (ascii/ks-roman in
 *  codeset 0, kps 9566-97 in codeset 1), and euc-vn is encoded by
 *  putting the first ascii half of vscii-2 in codeset 0, the second
 *  half in codeset 1, and ideographic dbcs tcvn 5773:1993 in codeset
 *  2. This gives (almost) backwards compatibility with single byte
 *  Vietnamese, with the exception of ss2 (0x8e), which is why we
 *  say we USE c0/c1 safe vscii-2 instead of vscii-1.
 *
 *  do not give values to the enumeration constants, as this will break
 *  code that depends on the first one being zero, the second one, etc.
 */

typedef unsigned short wide_char;
/*
 *  as the sizeof() for this is two with many compilers, Unicode/ISO-10646
 *  characters greater than U-FFFF (which are rare) will be encoded using
 *  two byte surrogate form and need two wide_char to represent them.
 */

typedef struct {
  wide_enc enc;
  size_t len, bufsiz, inc;
  wide_char *buf;
} wide_str;
/*
 *  most of the contents of this structure can be manipulated like a
 *  black box with the wide_* functions and the fields need not be directly
 *  read or written.
 */

typedef struct {
  int capitalize; /* TODO */
  /*
   *  if negative, all uppercase will be converted to lowercase. if
   *  positive, all lowercase will be converted to uppercase. if zero,
   *  the first letter of every run of capitalizable sequences will be
   *  capitalized.
   */

  int separate; /* TODO */
  /*
   *  if separate is true/non-zero then a space will separate english text
   *  from cjkv ideographs.
   */

  int punctuation; /* TODO */
  /*
   *  if punctuation is positive non-zero/true then full-width commas and
   *  full stops will be changed to ideographic commas and full stops. if
   *  it is negative then ideographic commas and full-stops will be changed
   *  to non-ideographic full-width versions. if the fullwidth field is
   *  true/non-zero, this step is done BEFORE the full-width/half-width
   *  conversion.
   */

  int fullwidth; /* TODO */
  /*
   *  if fullwidth positive true/non-zero then full-width latin/roman text
   *  is changed to half-width. if it is negative then half-width text
   *  is changed to full-width. if the katakana field is non-zero/true,
   *  this step is done BEFORE the katakana conversion.
   */

  int katakana; /* TODO */
  /*
   *  if katakana is negative full-width katakana is changed to half-width.
   *  if it is positive non-zero/true half-width katakana is changed to
   *  full-width.
   */
   
  int reformat;
  /*
   *  if reformat is true/non-zero tabs, vertical tabs, newlines, carriage
   *  returns, runs of spaces, and non-standard spaces are all changed to 
   *  a single space. if the expand_tabs is non-zero/true, this step will be
   *  done BEFORE the expand_tabs conversion.
   */

  int expand_tabs; /* TODO */
  /*
   *  if positive, all horizontal tabs will be converted an appropriate
   *  amount of spaces and vertical tabs and formfeeds will be converted to
   *  an appropriate amount of newlines. if negative, horizontal and
   *  vertical space will be compressed into tabs, vertical tabs, and form
   *  feeds.
   */

  unsigned *h_tab; /* TODO */
  unsigned *v_tab; /* TODO */
  /*
   *  h_tab and v_tab are arrays indicating the columns/lines that the tabs
   *  are set on. it is used by word-wrapping, justification, and
   *  expand_tabs. it is measured in character cells and lines, although in
   *  the future this could be the amount of pixels or points. zero is the
   *  first column/point/pixel, not one. a value equal to UINT_MAX in the
   *  second element or beyond means to repeat the difference between the
   *  last tab. if the tab stop is greater than the margin or the page size,
   *  the tab advances to the start of the next line or page.
   */

  unsigned page_size; /* TODO */
  /*
   *  page_size is the number of lines (or pixels/points) per virtual
   *  page. a page_size of zero indicates an unlimited page. it is used
   *  by expand_tabs.
   */

  unsigned *margin;
  /*
   *  margin is an array indicating the number of character cells
   *  available on each line, although in the future this could be the
   *  amount of pixels or points per line. widths less than four character
   *  cells will not word-wrap unless an explicit newline is present in the
   *  text and the reformat field is false/zero. a width equal to UINT_MAX
   *  in the second element or beyond means to use the last width specified
   *  over and over. this step is done after all other processing EXCEPT for
   *  justification. if the pointer is NULL then word-wrap is not done.
   *  a newline, either implicitly inserted by the word wrap, or explicity
   *  through vertical whitespace in the original text, causes wide_fmt_str
   *  to use the next element in the array iff the next element is not
   *  UINT_MAX.
   */

  int justification; /* TODO */
  /*
   *  if negative, the text is left-justified, if positive, the text is
   *  right-justified. if zero, the text is centered. this step is done
   *  after word-wrapping.
   */
} wide_fmt;

wide_str * wide_clone_str (const wide_str *s);
/*
 *  wide_clone_str is used to duplicate a string.
 *
 *  the function returns a copy of s if successful, or NULL if
 *  allocation failed.
 */

wide_str * wide_alloc_str (wide_str *s, size_t n);
/*
 *  wide_alloc_str is used reserve at least n bytes in the string buffer
 *
 *  all of the other functions call this when needed, so it need not
 *  be called explicitly. one may want to call it explicitly for
 *  performance (when the total size needed is known) or to
 *  deallocate all free store being internally referenced.
 *
 *  if n is zero, the internal string buffer is completely deallocated.
 *
 *  the function returns s if successful, or NULL if n is not zero and
 *  the allocation failed.
 *
 *  if allocation fails and NDEBUG is not defined, a diagnostic will
 *  appear on the error stream. as all other functions use this to
 *  reserve memory, all other functions will also generate a diagnostic if
 *  NDEBUG is not defined during compile.
 */

wide_str * wide_init_str (wide_str *s, size_t inc, wide_enc codeset);
/*
 *  wide_init_str prepares an uninitialized wide_str structure.
 *
 *  codeset is set so the mbs/wcs conversion routines know how to
 *  translate.
 *
 *  inc is the chunk factor which indicates how many bytes to allocate
 *  at a time for holding information. If it is 0, allocation is doubled
 *  every time (1, 2, 4, 8, 16, 32...).
 *
 *  If s points to a wide string that has has characters assigned or
 *  inserted in it, be sure to call wide_alloc_str with a n of zero
 *  to release the internal memory or you'll leak memory
 *
 *  the function returns s, or it returns NULL if s is NULL.
 */

size_t wide_get_len (const wide_str *s);
/*
 *  wide_get_len returns the number of wide characters in the string.
 */

size_t wide_get_inc (const wide_str *s);
/*
 *  wide_get_len returns the increment set for the string s.
 */

wide_enc wide_get_enc (const wide_str *s);
/*
 *  wide_get_enc returns the encoding used for translation to mbs.
 *
 *  the encoding of the wide chars is related to the mbs encoding. no
 *  translation to/from ISO-10646/Unicode is done.
 */

wide_char wide_get_char (const wide_str *src, size_t pos);
/*
 *  wide_get_char returns the wide character at an index.
 *
 *  a pos of zero refers to the first character.
 *
 *  the encoding is iso-10646/Unicode iff the mbs encoding is utf-8.
 *  the encoding is ASCII iff the character is less than 0x80 (seven bits).
 *  the encoding is custom for EUC-TW. all other encodings are variants
 *  in the style of Japanese fixed 2-byte width euc.
 */

wide_str * wide_get_str (wide_str *dest, const wide_str *src,
                         size_t pos, size_t n);
/*
 *  wide_get_str copies the substring of length n beginning at pos.
 *
 *  the string dest, if it held anything before, is clobbered. it is
 *  not necessary to use wide_alloc_str with n of zero (to deallocate
 *  the free store referenced) on dest. this is done automatically.
 *
 *  the function returns dest if successful, or NULL if allocation failed.
 */

wide_str * wide_ins_char (wide_str *dest, wide_char src, size_t pos);
/*
 *  wide_ins_char inserts the character before the character at pos.
 *
 *  if pos is equal to the length of the string, the character is appended
 *  to the end of the string. src must be in a format compatible
 *  with the encoding of dest.
 *
 *  the function returns dest if successful, or NULL if allocation failed.
 */

wide_str * wide_ins_str (wide_str *dest, const wide_str *src, size_t pos);
/*
 *  wide_ins_str is just like wide_ins_char, except the source is a string.
 *
 *  the encoding of both strings must be the same. the entire string src
 *  is inserted.
 *
 *  the function returns dest if successful, or NULL if allocation failed.
 */
  
wide_str * wide_ovwr_char  (wide_str *dest, wide_char src, size_t pos);
/*
 *  wide_ovwr_char replaces the character is dest at pos with src.
 *
 *  if the pos is equal to the length of the string, the character src
 *  doesn't overwrite anything and is instead appended to the end of the
 *  string. the character src must be compatible with the encoding
 *  used by dest.
 *
 *  the function returns dest if successful, or NULL if allocation failed.
 */

wide_str * wide_ovwr_str (wide_str *dest, const wide_str *src, size_t pos);
/*
 *  wide_ovwr_str is just like wide_ovwr_char, except src is a string.
 *
 *  if the length of the src string plus the pos is greater than the
 *  length of the dest string, the dest string is lengthened to hold the
 *  entire contents of the src string. the encodings of src and dest must
 *  be the same.
 *
 *  the function returns dest if successful, or NULL if allocation failed.
 */

wide_str * wide_del_str (wide_str *s, size_t pos, size_t n);
/*
 *  wide_del_str deletes n characters starting at pos from s.
 *
 *  the sum of pos and n must be less than the length of s. if all the
 *  characters in s are deleted, the free store referenced by object s
 *  is deallocated, making the string safe for disposal.
 *
 *  the function returns s if successful, or NULL if allocation failed.
 */

wide_str * wide_conv_mbs (wide_str *dest, const unsigned char *src);
/*
 *  wide_conv_mbs converts the multi-byte src to a wide character string.
 *
 *  the string dest, if it held anything before, is clobbered. it is
 *  not necessary to use wide_alloc_str with n of zero (to deallocate
 *  the free store referenced) on dest. this is done automatically.
 *
 *  the multi-byte encoding and charset used depends on the encoding
 *  set in the wide-character string dest. the multi-byte string must
 *  start and end in an initial state (ready to receive ascii).
 *
 *  the function returns s if successful, or NULL if allocation failed
 *  or the multi-byte string is invalid.
 */
   
wide_str * wide_conv_mbs_n (wide_str *dest, const unsigned char *src,
                            size_t n);
/*
 *  wide_conv_mbs_n is just like wide_conv_mbs, except the src length is n.
 *
 *  this function will process null characters, whereas wide_conv_mbs will
 *  stop conversion on a null character.
 */

int wide_find_char (const wide_str *s, wide_char key, size_t *pos, int rtl);
/*
 *  wide_find_char will search for a wide character key within string s.
 *
 *  the search will start at the index pointed to by pos. it will store the
 *  position of the key in the location pointed to by pos. pos must point to
 *  a value that is less than the length of the s.
 *
 *  if the character is not already at the index pointed to by pos, it will
 *  search to the right (if rtl is false/zero) or to the left (if rtl
 *  is non-zero/true) to the end of the string.
 *
 *  the function returns zero/false if the string is not found, or
 *  non-zero/true is the string is found.
 */

int wide_find_str (const wide_str *s, const wide_str *key, size_t *pos,
                   int rtl);
/*
 *  wide_find_str is just like wide_find_char, except the key is a string.
 *
 *  the function will always return false if the encodings of key and s are
 *  not the same. the function will always return true if the length of key
 *  is zero.
 */

unsigned char * wide_conv_wcs (unsigned char *dest, const wide_str *src);
/*
 *  wide_conv_wcs converts the wide string into multibyte dest.
 *
 *  wide_conv_wcs will write a maximum of wide_get_len(src) * 4 bytes
 *  into dest, followed by a null character. the multibyte encoding of
 *  src will be used. if dest is NULL, the space required to hold
 *  the string will be allocated from the free store and a pointer
 *  to the mbs which can be passed to the free function will be
 *  returned.
 *
 *  the function will return dest, or NULL if allocation failed.
 */

unsigned char *	wide_conv_wcs_n (unsigned char *dest, const wide_str *src,
                                 size_t n);
/*
 *  wide_conv_wcs_n is just like wide_conv_wcs, with a write limit of n.
 *
 *  the function will return dest, unless the entire string, including the
 *  null character terminator, cannot be written in n bytes, in which
 *  case NULL is returned.
 */

int wide_get_char_width (wide_char c, wide_enc enc);
/*
 *  wide_get_width returns the amount of space a character needs.
 *
 *  the output units is character cells for a terminal, although
 *  in theory it could be pixels or points in the future. a return of zero
 *  indicates that the character is a combining character or a non-printable
 *  control character. a negative value indicates a backspace like control
 *  code.
 *
 *  with cjkv, a 2 indicates a full-width (2 character cell) ideographic
 *  character, and a 1 indicates a "half-width" (1 character cell... normal
 *  English character) character.
 */

wide_str * wide_fmt_str (wide_str *s, const wide_fmt *fmt);
/*
 *  wide_fmt_str will run a string through various filters set via fmt.
 *
 *  for more information as to the filters and the order they are
 *  processed in, see the wide_fmt structure type definition.
 *
 *  wide_fmt_str understands asian and european word wrap, but it
 *  understands only monospaced fonts, and does not take proportional
 *  spacing and/or kerning into account. not all character encodings
 *  and character sets may be supported.
 *
 *  if fmt is NULL then a standard format for the language/locale most
 *  commonly associated with the character encoding of s will be used.
 *
 *  the function returns s if successful, or NULL if allocation failed.
 */

int wide_cmp_str (const wide_str *x, const wide_str *y);
/*
 *  wide_cmp_str will compare two strings for bsearch or qsort.
 *
 *  comparing all characters left to right, if the encoding is the same or
 *  the character compared is 7 bits long, then the characters themselves
 *  are compared as a and b, otherwise the encodings are compared as a and
 *  b. a negative number is returned if a < b, a positive number is returned
 *  if a > b, and zero is returned if a is equal to b. if one string is
 *  a truncated version another, that string is considered less than the
 *  other.
 */

unsigned long wide_hash_str (const wide_str *s);
/*
 *  wide_hash_str will generate a 32-bit hash code for the given string.
 *
 *  hash values will be equal if the length and the string and the encoding
 *  is the same. the buffer inc passed to wide_init_str does not influence
 *  the hash code, nor does the current size of the internal buffer holding
 *  the dbcs characters.
 */

int wide_check_char (wide_char c, wide_enc enc);
/*
 *  wide_check_char will return true if the character c is valid for enc.
 *
 *  it will return false/zero iff the character cannot be converted to
 *  a multi-byte string.
 */

void wide_debug_str (FILE *stream, wide_str *s, int v, const char *label,
                     const char *file, unsigned long line); 
/*
 *  wide_character_str will print the internal contents of s.
 *
 *  data will be output in a human-readable form to stream. if stream is
 *  null, it defaults to the error stream. s, expr, and file may be null.
 *  line may be zero.
 *
 *  if v is non-zero/true, more detail is emitted, and all characters
 *  are displayed in hexadecimal. if v is zero/false, ascii characters
 *  are printed in human readable "pretty" format, and buffer management
 *  fields are omitted. expr is the C expression used to pass s.
 *
 *  usually this function is not directly used. the macro wrapper
 *  WIDE_DEBUG, which removes calls to this function when NDEBUG is
 *  defined and automatically inserts the filename and line number, is
 *  the preferred usage.
 *
 *  if a stream error occurs, the strerror will attempt to be printed to
 *  stderr then the function will exit prematurely.
 */

#if !defined NDEBUG
#  define WIDE_DEBUG(s,v) wide_debug_str(NULL,(s),(v),#s,__FILE__,__LINE__)
#else
#  define WIDE_DEBUG(s,v) (void)(0)
#endif

#if defined DMALLOC
#  include "dmalloc.h"
#endif
