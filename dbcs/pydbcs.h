#define STRING_INST_DOC \
  "An immutable string where every character is 16-bits wide.\n"\
  "\n"\
  "As the string is immutable, assignment to items and assignment to\n"\
  "slices is not permitted. All other sequence methods and standard\n"\
  "methods are available, including hashing so the string may be used as\n"\
  "a key for mapping.\n"\
  "\n"\
  "Acceptable conversions to and the double byte are the same as the\n"\
  "allowed conversions for the dbcs module String function."

#define STRINGBUFFER_INST_DOC \
  "An mutable string where every character is 16-bits wide.\n"\
  "\n"\
  "As the string is mutable, the hash function is not available. All\n"\
  "other sequence methods and standard methods are available, including\n"\
  "assignment to items and slices.\n"\
  "\n"\
  "Acceptable conversions to and the double byte are the same as the\n"\
  "allowed conversions for the dbcs module String function."

#define DBCS_MOD_STR_F_DOC \
  "A function which creates a double-byte character string.\n"\
  "\n"\
  "All parameters are optional.\n"\
  "\n"\
  "The first parameter, keyword s, is an object which can be converted\n"\
  "to a wide string. It defaults to None.\n"\
  "\n"\
  "The second parameter, the encoding (keyword enc), may be any of the\n"\
  "strings in the list returned by the function Encodings. If enc is\n"\
  "None or length zero, an appropriate encoding is chosen based on the\n"\
  "global LC_CTYPE locale. It defaults to None if the first object is\n"\
  "not a dbcs.String or dbcs.StringBuffer type, otherwise it inherits\n"\
  "the encoding of the dbcs string.\n"\
  "\n"\
  "The third parameter, keyword inc, is an unsigned number used to tune\n"\
  "the buffer for mutable string insertion and deletion. It defaults to\n"\
  "the integer returned by the function Increment.\n"\
  "\n"\
  "The fourth parameter (keyword mutable), if it evaluates to true,\n"\
  "creates and returns a instance of a StringBuffer type object that is\n"\
  "mutable, otherwise it returns an immutable String type object. It\n"\
  "defaults to false.\n"\
  "\n"\
  "NOTE: dbcs StringBuffer type objects, which are mutable, are not the\n"\
  "same type as immutable objects, which is what this is. They cannot be\n"\
  "compared to each other, although most other operations, (except for\n"\
  "assign item, assign slice, and hash) are interchangeable.\n"\
  "\n"\
  "Conversion to the double byte string can be done with a\n"\
  "variety of Python standard types, including strings (interpreted as\n"\
  "multibyte), integers and longs (convert to length one strings), None\n"\
  "(converts to the string of zero length), and lists which may consist\n"\
  "of any of the above, including nested lists, as items. The internal\n"\
  "coding is not necessarily Unicode/ISO-10646, but depends on the\n"\
  "encoding set during instantiation."

#define DBCS_MOD_STRBUF_F_DOC \
  "A function which creates a double-byte character string.\n"\
  "\n"\
  "All parameters are optional.\n"\
  "\n"\
  "The first parameter, keyword s, is an object which can be converted\n"\
  "to a wide string. It defaults to None.\n"\
  "\n"\
  "The second parameter, the encoding (keyword enc), may be any of the\n"\
  "strings in the list returned by the function Encodings. If enc is\n"\
  "None or length zero, an appropriate encoding is chosen based on the\n"\
  "global LC_CTYPE locale. It defaults to None if the first object is\n"\
  "not a dbcs.String or dbcs.StringBuffer type, otherwise it inherits\n"\
  "the encoding of the dbcs string.\n"\
  "\n"\
  "The third parameter, keyword inc, is an unsigned number used to tune\n"\
  "the buffer for mutable string insertion and deletion. It defaults to\n"\
  "the integer returned by the function Increment.\n"\
  "\n"\
  "The fourth parameter (keyword mutable), if it evaluates to true,\n"\
  "creates and returns a instance of a StringBuffer type object that is\n"\
  "mutable, otherwise it returns an immutable String type object. It\n"\
  "defaults to true.\n"\
  "\n"\
  "NOTE: dbcs String type objects, which are immutable, are not the same\n"\
  "type as mutable objects, which is what this is. They cannot be\n"\
  "compared to each other, although most other operations, (except for\n"\
  "assign item, assign slice, and hash) are interchangeable.\n"\
  "\n"\
  "Conversion to the double byte string can be done with a\n"\
  "variety of Python standard types, including strings (interpreted as\n"\
  "multibyte), integers and longs (convert to length one strings), None\n"\
  "(converts to the string of zero length), and lists which may consist\n"\
  "of any of the above, including nested lists, as items. The internal\n"\
  "coding is not necessarily Unicode/ISO-10646, but depends on the\n"\
  "encoding set during instantiation."

#define DBCS_MOD_ENC_F_DOC \
  "A function which returns a list of supported multi-byte encodings.\n"\
  "\n"\
  "The list are the multibyte encodings that the dbcs module can convert\n"\
  "to and from. The internal wide characters set and encoding depends\n"\
  "on the multibyte encoding and is not necessarily Unicode/ISO-10646.\n"\
  "\n"\
  "Some of the encodings may be aliases for other encodings."

#define DBCS_MOD_INC_F_DOC \
  "A function which returns the default buffer increment used.\n"\
  "\n"\
  "If the increment is not specified when creating a new instance and no\n"\
  "source string exists to copy the increment from, this value is used.\n"\
  "A value of zero indicates the buffer size is doubled or halved as\n"\
  "necessary."

#define DBCS_MOD_DOC \
  "A module for supporting editable strings of wide characters.\n"\
  "\n"\
  "The module is not designed to be a complete Unicode string\n"\
  "implementation. It is designed to be a small, lightweight set of\n"\
  "string classes designed to supplement the current locale specific\n"\
  "multibyte strings in environments where a Unicode string environment\n"\
  "is not available or too big, but the advantages of wide string\n"\
  "manipulation are needed.\n"\
  "\n"\
  "A few filters have been included with are CJKV (Chinese/Japanese/\n"\
  "Korean/Vietnamese) related, as these are the most common locale-\n"\
  "specific multibyte string environments."

#define DBCS_WW_METHOD_DOC \
  "A method to add/remove whitespace and newlines for wordwrapping.\n"\
  "\n"\
  "Depending on the encoding of the wide string, CJKV wordwrap may be\n"\
  "supported. The first parameter, keyword margin, is a list of integers\n"\
  "where each integer represents the width of the line (currently\n"\
  "measured in half-width fixed-width character cells). A width of zero\n"\
  "indicates an effectively unlimited line. A width of sys.maxint\n"\
  "in the second position or beyond means to repeat the last width\n"\
  "endlessly. If there are more lines than there are margins and the\n"\
  "margin list is not set to repeat forever, the lines without margin\n"\
  "settings will not be wrapped.\n"\
  "\n"\
  "The rest of the parameters are optional. The second parameter,\n"\
  "keyword strip, causes all runs of whitespace to be converted to a\n"\
  "single space before wordwrapping. The third parameter, keyword htab,\n"\
  "is a list of horizontal tab positions with a format identical to the\n"\
  "margin list. The fourth parameter, keyword vtab, is a list of\n"\
  "vertical tabs, also with a margin list format. The fifth parameter,\n"\
  "keyword ff, is an ordinal indicating the page size for form feeds. A\n"\
  "zero indicates unlimited page size."
