import gzip
import sys
import os

if len(sys.argv) == 1:
    print "Please provide a filename."

filename = sys.argv[1]    
    
print "Fixing %s..." % filename

gzf = gzip.GzipFile(filename)
ngzf = gzip.GzipFile(filename + ".new", "wb")

# Write the size header
ngzf.write(gzf.read(4))

# Write each byte, checking for out-of-range
chunk = gzf.read(2048)
while chunk:
    ngzf.write("".join([("\0" if ord(byte) > 41 else byte) for byte in chunk]))
    chunk = gzf.read(2048)

gzf.close()
ngzf.close()
os.rename(filename+".new", filename)