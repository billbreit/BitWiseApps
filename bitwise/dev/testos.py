
import os
from collections import namedtuple
import time

nl = print

print('dir(time)    ', dir(time))
print('time.time()  ', time.time())
print('time.gmtime()  ', time.gmtime())
print('time.localtime()  ', time.localtime())
print('time.localtime(time)  ', time.localtime(time.time()))
print('time.mktime(gmtime)  ', time.mktime(time.gmtime()))
print('time.strftime(localtime)  ', time.mktime(time.localtime()))
nl()

print('dir(os)      ', dir(os)) #  mpy

"""
# ['__class__', '__name__', 'remove', 'VfsFat', 'VfsLfs2', '__dict__', 'chdir',
*'dupterm', *'dupterm_notify', 'getcwd', *'ilistdir', 'listdir', 'mkdir', *'mount',
'rename', 'rmdir', 'stat', 'statvfs', 'sync', *'umount', 'uname', 'unlink', 'urandom']

unlink == os.remove
"""

# * myp only

stat_result_fields = ['st_mode', 'st_ino', 'st_dev', 'st_nlink', 'st_uid', 'st_gid',
                           'st_size', 'st_atime', 'st_mtime', 'st_ctime' ]

stat_result = namedtuple('stat_result', stat_result_fields )  


nl()
print('uname                  ', os.uname())
nl()
print('urandom                ', os.urandom(16))
nl()
print('getcwd                 ', os.getcwd())
nl()
print('listdir                ', os.listdir())
nl()
print("stat '/'               ", stat_result(*os.stat('/')))
print("bin (stat '/').st_mode ", bin(stat_result(*os.stat('/')).st_mode))
print("stat '/dev'            ", stat_result(*os.stat('/dev')))
print("stat 'liststore.py'    ", stat_result(*os.stat('tuplestore.py')))
nl()
print("statvfs '/'            ", stat_result(*os.statvfs('/')))
print("bin (statvfs '/').st_mode ", bin(stat_result(*os.statvfs('/')).st_mode))
print("statvfs '/dev'         ", stat_result(*os.statvfs('/dev')))
print("statvfs 'liststore.py' ", stat_result(*os.stat('tupletore.py')))


"""
os.stat_result(st_mode=33188, st_ino=7876932, st_dev=234881026,
st_nlink=1, st_uid=501, st_gid=501, st_size=264, st_atime=1297230295,
st_mtime=1297230027, st_ctime=1297230027)


lass os.stat_result
Object whose attributes correspond roughly to the members of the stat structure. It is used for the result of os.stat(), os.fstat() and os.lstat().

Attributes:

st_mode
File mode: file type and file mode bits (permissions).

st_ino
Platform dependent, but if non-zero, uniquely identifies the file for a given value of st_dev. Typically:

the inode number on Unix,

the file index on Windows

st_dev
Identifier of the device on which this file resides.

st_nlink
Number of hard links.

st_uid
User identifier of the file owner.

st_gid
Group identifier of the file owner.

st_size
Size of the file in bytes, if it is a regular file or a symbolic link. The size of a symbolic link is the length of the pathname it contains, without a terminating null byte.

Timestamps:

st_atime
Time of most recent access expressed in seconds.

st_mtime
Time of most recent content modification expressed in seconds.

st_ctime
Time of most recent metadata change expressed in seconds.

Changed in version 3.12: st_ctime is deprecated on Windows. Use st_birthtime for the file creation time. In the future, st_ctime will contain the time of the most recent metadata change, as for other platforms.

st_atime_ns
Time of most recent access expressed in nanoseconds as an integer.

New in version 3.3.

st_mtime_ns
Time of most recent content modification expressed in nanoseconds as an integer.

New in version 3.3.

st_ctime_ns
Time of most recent metadata change expressed in nanoseconds as an integer.

New in version 3.3.

Changed in version 3.12: st_ctime_ns is deprecated on Windows. Use st_birthtime_ns for the file creation time. In the future, st_ctime will contain the time of the most recent metadata change, as for other platforms.
"""
